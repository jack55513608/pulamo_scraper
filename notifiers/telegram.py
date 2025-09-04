# notifiers/telegram.py
import asyncio
import logging
from telegram import Bot
from telegram.error import TelegramError
from notifiers.base import BaseNotifier
from models import Product
import config
from datetime import datetime
import pytz

class TelegramNotifier(BaseNotifier):
    """A notifier for sending messages via Telegram."""

    def __init__(self, bot=None):
        if bot:
            self.bot = bot
        elif config.TELEGRAM_BOT_TOKEN:
            self.bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
        else:
            self.bot = None
        
        if self.bot:
            # Create a semaphore to limit concurrent requests to Telegram
            self.semaphore = asyncio.Semaphore(1)
        else:
            self.semaphore = None
            logging.warning("Telegram Bot Token 未設定，將不會發送通知。")

    async def notify(self, product: Product, params: dict):
        """
        Sends a notification about a found product, using a semaphore to ensure durability.
        """
        if not self.bot or not self.semaphore or not config.TELEGRAM_CHAT_ID:
            logging.warning("Bot instance, semaphore, or Chat ID 未提供，無法發送通知。")
            return

        product_name = params.get("name", "商品")
        store_name = params.get("store_name", "店家")
        
        taipei_tz = pytz.timezone('Asia/Taipei')
        now = datetime.now(taipei_tz)
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S %Z%z')

        message = f"[{timestamp}]\n店家: {store_name}\n商品: {product.title}\n價格: {product.price}\n狀態: 有貨"
        message += f'\n<a href="{product.url}">點此查看商品頁面</a>'

        # Acquire the semaphore before sending the message
        async with self.semaphore:
            try:
                await self.bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text=message, parse_mode='HTML')
                logging.info(f"已成功為 '{product.title}' 發送 Telegram 通知。")
            except TelegramError as e:
                logging.error(f"為 '{product.title}' 發送 Telegram 通知時發生錯誤: {e}")
