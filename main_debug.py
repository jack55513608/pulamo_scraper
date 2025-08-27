# main_debug.py
import asyncio
import logging
import config
from logger_config import setup_logger
from main import process_task # Reuse the process_task from main.py

async def main():
    """
    Main function for running test tasks.
    """
    setup_logger(logging.DEBUG)
    logging.info("--- 開始執行測試任務 ---\n") # Added newline for better readability

    try:
        tasks_to_run = [process_task(task) for task in config.TEST_TASKS]
        await asyncio.gather(*tasks_to_run)
    except Exception as e:
        logging.critical(f"執行測試任務時發生未預期的錯誤: {e}", exc_info=True)
    finally:
        logging.info("--- 測試任務執行完畢 ---\n") # Added newline for better readability

if __name__ == '__main__':
    asyncio.run(main())