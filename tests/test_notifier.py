# test_notifier.py
import unittest
from unittest.mock import AsyncMock, patch
from notifiers.telegram import TelegramNotifier
from models import Product
from telegram.error import TelegramError
import config

class TestTelegramNotifier(unittest.IsolatedAsyncioTestCase):

    @patch('notifiers.telegram.Bot')
    async def test_notify_successfully(self, MockBot):
        """Test that the bot's send_message method is called correctly."""
        mock_bot_instance = AsyncMock()
        MockBot.return_value = mock_bot_instance
        
        # Mock config values
        config.TELEGRAM_BOT_TOKEN = "fake_token"
        config.TELEGRAM_CHAT_ID = "12345"

        notifier = TelegramNotifier()
        product = Product(title="Test Product", price=100, in_stock=True, url="http://example.com")
        params = {'name': 'Test', 'store_name': 'Test Store'}

        await notifier.notify(product, params)

        self.assertTrue(mock_bot_instance.send_message.called)
        call_args = mock_bot_instance.send_message.call_args
        self.assertEqual(call_args.kwargs['chat_id'], "12345")
        self.assertIn("Test Product", call_args.kwargs['text'])
        self.assertIn("Test Store", call_args.kwargs['text'])
        self.assertEqual(call_args.kwargs['parse_mode'], 'HTML')

    @patch('notifiers.telegram.Bot')
    async def test_notify_handles_telegram_error(self, MockBot):
        """Test that the notifier handles TelegramError gracefully."""
        mock_bot_instance = AsyncMock()
        mock_bot_instance.send_message.side_effect = TelegramError("Test Error")
        MockBot.return_value = mock_bot_instance

        config.TELEGRAM_BOT_TOKEN = "fake_token"
        config.TELEGRAM_CHAT_ID = "12345"

        notifier = TelegramNotifier()
        product = Product(title="Test Product", price=100, in_stock=True, url="http://example.com")
        params = {'name': 'Test', 'store_name': 'Test Store'}

        # This should not raise an exception
        await notifier.notify(product, params)
        
        mock_bot_instance.send_message.assert_called_once()

    @patch('notifiers.telegram.Bot')
    async def test_notify_with_no_chat_id(self, MockBot):
        """Test that notify does not send if chat_id is missing."""
        mock_bot_instance = AsyncMock()
        MockBot.return_value = mock_bot_instance

        config.TELEGRAM_BOT_TOKEN = "fake_token"
        config.TELEGRAM_CHAT_ID = None # No chat ID

        notifier = TelegramNotifier()
        product = Product(title="Test Product", price=100, in_stock=True, url="http://example.com")
        params = {}

        await notifier.notify(product, params)

        mock_bot_instance.send_message.assert_not_called()

if __name__ == '__main__':
    unittest.main()
