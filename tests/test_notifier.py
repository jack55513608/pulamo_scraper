# test_notifier.py
import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from notifiers.telegram import TelegramNotifier
from models import Product
from telegram.error import TelegramError
import config

class TestTelegramNotifier(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        """Set up a mock bot for all tests."""
        self.mock_bot = AsyncMock()
        config.TELEGRAM_CHAT_ID = "12345"

    async def test_notify_successfully(self):
        """Test that the bot's send_message method is called correctly."""
        notifier = TelegramNotifier(bot=self.mock_bot)
        product = Product(title="Test Product", price=100, in_stock=True, url="http://example.com")
        params = {'name': 'Test', 'store_name': 'Test Store'}

        await notifier.notify(product, params)

        self.assertTrue(self.mock_bot.send_message.called)
        call_args = self.mock_bot.send_message.call_args
        self.assertEqual(call_args.kwargs['chat_id'], "12345")
        self.assertIn("Test Product", call_args.kwargs['text'])
        self.assertIn("Test Store", call_args.kwargs['text'])
        self.assertEqual(call_args.kwargs['parse_mode'], 'HTML')

    async def test_notify_handles_telegram_error(self):
        """Test that the notifier handles TelegramError gracefully."""
        self.mock_bot.send_message.side_effect = TelegramError("Test Error")
        notifier = TelegramNotifier(bot=self.mock_bot)
        product = Product(title="Test Product", price=100, in_stock=True, url="http://example.com")
        params = {'name': 'Test', 'store_name': 'Test Store'}

        # This should not raise an exception
        await notifier.notify(product, params)
        
        self.mock_bot.send_message.assert_called_once()

    async def test_notify_with_no_chat_id(self):
        """Test that notify does not send if chat_id is missing."""
        config.TELEGRAM_CHAT_ID = None # No chat ID
        notifier = TelegramNotifier(bot=self.mock_bot)
        product = Product(title="Test Product", price=100, in_stock=True, url="http://example.com")
        params = {}

        await notifier.notify(product, params)

        self.mock_bot.send_message.assert_not_called()

    async def test_semaphore_limits_concurrency(self):
        """Test that the semaphore correctly limits concurrent notification calls."""
        # Arrange
        active_calls = 0
        max_active_calls = 0

        async def mock_send_message(*args, **kwargs):
            nonlocal active_calls, max_active_calls
            active_calls += 1
            max_active_calls = max(max_active_calls, active_calls)
            await asyncio.sleep(0.01) # Simulate network latency
            active_calls -= 1

        self.mock_bot.send_message = AsyncMock(side_effect=mock_send_message)
        notifier = TelegramNotifier(bot=self.mock_bot)
        notifier.semaphore = asyncio.Semaphore(3) # Use a smaller semaphore for testing

        product = Product(title="Test", price=100, in_stock=True, url="http://a.com")
        params = {}

        # Act
        # Create more tasks than the semaphore limit
        tasks = [notifier.notify(product, params) for _ in range(10)]
        await asyncio.gather(*tasks)

        # Assert
        self.assertEqual(self.mock_bot.send_message.call_count, 10)
        self.assertLessEqual(max_active_calls, 3) # Max concurrency should not exceed semaphore limit


if __name__ == '__main__':
    unittest.main()
