
# notifier.py

import logging
from datetime import datetime
import pytz
from telegram import Bot
from telegram.error import TelegramError

async def send_telegram_message(bot: Bot, chat_id: str, message: str) -> bool:
    """
    Sends a message to a specified Telegram chat using a bot instance.

    Args:
        bot: An initialized telegram.Bot instance.
        chat_id: The ID of the target chat.
        message: The message string to send.

    Returns:
        True if the message was sent successfully, False otherwise.
    """
    if not bot or not chat_id:
        logging.warning("Bot instance 或 Chat ID 未提供，無法發送通知。")
        return False

    try:
        # 取得當前時間並轉換為 +8 時區
        taipei_tz = pytz.timezone('Asia/Taipei')
        now = datetime.now(taipei_tz)
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S %Z%z')

        full_message = f"[{timestamp}] {message}"

        await bot.send_message(chat_id=chat_id, text=full_message)
        logging.info("已成功發送 Telegram 通知。")
        return True
    except TelegramError as e:
        logging.error(f"發送 Telegram 通知時發生錯誤: {e}")
        return False
