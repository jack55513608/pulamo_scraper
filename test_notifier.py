
# test_notifier.py

import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from notifier import send_telegram_message
from telegram.error import TelegramError

class TestNotifier(unittest.IsolatedAsyncioTestCase):

    async def test_send_message_successfully(self):
        """Test that the bot's send_message method is called correctly."""
        mock_bot = AsyncMock()
        chat_id = "12345"
        message = "Hello, Test!"

        with patch('notifier.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "2025-08-26 23:00:00 CST+0800"
            result = await send_telegram_message(mock_bot, chat_id, message)

        full_message = f"[2025-08-26 23:00:00 CST+0800] {message}"
        mock_bot.send_message.assert_called_once_with(chat_id=chat_id, text=full_message)
        self.assertTrue(result)

    async def test_send_message_handles_telegram_error(self):
        """Test that the function handles TelegramError gracefully."""
        mock_bot = AsyncMock()
        mock_bot.send_message.side_effect = TelegramError("Test Error")

        chat_id = "12345"
        message = "Hello, Error!"

        result = await send_telegram_message(mock_bot, chat_id, message)

        mock_bot.send_message.assert_called_once()
        self.assertFalse(result)

    async def test_send_message_with_no_bot(self):
        """Test that the function handles having no bot instance."""
        result = await send_telegram_message(None, "12345", "No bot")
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
