# main.py
import asyncio
import logging
import config
from logger_config import setup_logger
from factory import get_scraper, get_checker, get_notifier # Import factory functions

async def process_task(task: dict):
    """
    Processes a single monitoring task.
    """
    task_name = task['name']
    logging.info(f"--- 開始執行任務: {task_name} ---")

    try:
        # Use factory functions to get instances
        scraper = get_scraper(task['scraper'], config.SELENIUM_GRID_URL)
        checker = get_checker(task['checker'])
        notifier = get_notifier(task['notifier'])

        with scraper:
            products = scraper.scrape(task['scraper_params'])
            found_product = checker.check(products, task['checker_params'])

            if found_product:
                logging.info(f"在任務 '{task_name}' 中找到目標商品: {found_product.title}")
                await notifier.notify(found_product, task['notifier_params'])
            else:
                logging.info(f"在任務 '{task_name}' 中未找到符合條件的商品。")

    except Exception as e:
        logging.error(f"在處理任務 '{task_name}' 時發生錯誤: {e}", exc_info=True)

async def main():
    """
    Main function to initialize and run the scraper and checks in a loop.
    """
    setup_logger()
    logging.info("--- 開始執行持續監控任務 ---\n") # Added newline for better readability
    try:
        while True:
            logging.info("--- 開始新一輪檢查 ---\n") # Added newline for better readability
            tasks_to_run = [process_task(task) for task in config.TASKS]
            await asyncio.gather(*tasks_to_run)

            logging.info(f"--- 等待 {config.CHECK_INTERVAL_SECONDS} 秒後進行下一次檢查 ---\n") # Added newline
            await asyncio.sleep(config.CHECK_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        logging.info("收到手動中斷訊號，程式即將關閉。")
    except Exception as e:
        logging.critical(f"執行過程中發生未預期的錯誤: {e}", exc_info=True)
    finally:
        logging.info("--- 監控任務執行完畢 ---")

if __name__ == '__main__':
    asyncio.run(main())