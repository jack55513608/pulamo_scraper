# main_debug.py

import asyncio
import sys
import logging
import config
from scraper import PulamoScraper
from html_dumper import dump_html_to_log
from logger_config import setup_logger
from checker import find_target_product
from main import process_check # 導入 process_check
from telegram import Bot

async def main():
    """
    Main function for debugging.
    - Dumps HTML of a given URL.
    - Runs a test case check for Barbatos Gundam.
    """
    # Set up logger for DEBUG level
    setup_logger(logging.DEBUG)

    # --- Initialize Bot (optional) ---
    bot = None
    if config.TELEGRAM_BOT_TOKEN:
        bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
        logging.info("Telegram Bot 已成功初始化。")
    else:
        logging.warning("Telegram Bot Token 未設定，測試案例的通知將不會發送。")

    # --- HTML Dumper ---
    if len(sys.argv) < 2:
        logging.error("Usage: python3 main_debug.py <URL_TO_DUMP>")
        # Even if URL is not provided, we can still run the test case
        target_url = None 
    else:
        target_url = sys.argv[1]

    logging.info("--- 開始執行偵錯任務 ---")

    try:
        with PulamoScraper(config.SELENIUM_GRID_URL) as scraper:
            if not scraper.driver:
                logging.critical("WebDriver 初始化失敗，無法執行偵錯任務。")
                return
            
            # Dump HTML if URL is provided
            if target_url:
                logging.info(f"--- 開始進行 HTML Dump: {target_url} ---")
                dump_html_to_log(target_url, scraper)
                logging.info("--- HTML Dump 結束 ---")

            # --- Test Case Check ---
            logging.info("--- 開始檢查商品狀態 (測試案例) ---")
            await process_check(scraper, bot, config.BARBATOS_GUNDAM_SPEC, test_mode=True)
            logging.info("--- 商品狀態檢查結束 (測試案例) ---")

    except Exception as e:
        logging.critical(f"執行偵錯任務時發生未預期的錯誤: {e}", exc_info=True)
    finally:
        logging.info("--- 偵錯任務執行完畢 ---")

if __name__ == '__main__':
    asyncio.run(main())