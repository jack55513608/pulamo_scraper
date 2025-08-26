# main.py

import asyncio
import logging
import config
from scraper import PulamoScraper
from checker import find_target_product
from notifier import send_telegram_message
from telegram import Bot
from logger_config import setup_logger

async def process_check(scraper: PulamoScraper, bot: Bot, spec: dict, test_mode: bool = False):
    """
    Processes a single product check and sends a notification if needed.
    """
    product_name = spec["name"]
    target_url = spec["search_url"]
    try:
        products = scraper.get_products_from_search(target_url)
        found_product = find_target_product(products, spec)
        
        if found_product:
            suffix = " (測試案例)" if test_mode else ""
            message = f"{product_name}有貨{suffix}\n商品名稱: {found_product.title}\n價格: {found_product.price}"
            logging.info(message)
            # 只有在非測試模式下才發送 Telegram 通知
            if bot and config.TELEGRAM_CHAT_ID:
                await send_telegram_message(bot, config.TELEGRAM_CHAT_ID, message)
        else:
            status = "(測試案例) 已售完或未上架" if test_mode else "或已售完/未發售"
            logging.info(f"未找到符合條件的 {product_name} {status}")
    except Exception as e:
        logging.error(f"在 process_check 處理 '{product_name}' 時發生錯誤: {e}", exc_info=True)

async def main():
    """
    Main function to initialize and run the scraper and checks in a loop.
    """
    setup_logger()
    bot = None
    if config.TELEGRAM_BOT_TOKEN:
        bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
        logging.info("Telegram Bot 已成功初始化。")
    else:
        logging.warning("Telegram Bot Token 未設定，將不會發送通知。")

    logging.info("--- 開始執行持續監控任務 ---")
    try:
        while True:
            logging.info("--- 開始新一輪檢查 ---")
            with PulamoScraper(config.SELENIUM_GRID_URL) as scraper:
                if not scraper.driver:
                    logging.critical("WebDriver 初始化失敗，任務中止。")
                    # 如果 WebDriver 初始化失敗，等待一段時間再重試，而不是直接退出
                    await asyncio.sleep(config.RETRY_DELAY_SECONDS * 5) # 等待更長時間
                    continue # 跳過本次檢查，進入下一次迴圈

                # 檢查主要目標
                logging.info("--- 開始檢查目標商品 ---")
                await process_check(scraper, bot, config.WING_GUNDAM_SPEC)
                await process_check(scraper, bot, config.DESTINY_GUNDAM_SPEC)

            logging.info(f"--- 等待 30 秒後進行下一次檢查 ---")
            await asyncio.sleep(30)

    except KeyboardInterrupt:
        logging.info("收到手動中斷訊號，程式即將關閉。")
    except Exception as e:
        logging.critical(f"執行過程中發生未預期的錯誤: {e}", exc_info=True)
    finally:
        logging.info("--- 監控任務執行完畢 ---")


if __name__ == '__main__':
    asyncio.run(main())