# main.py
import asyncio
import logging
import config
from logger_config import setup_logger
from task_config_manager import task_config_manager
from processors import process_pulamo_task, process_ruten_task

async def main():
    """
    Main function to initialize and run the scraper and checks in a loop.
    """
    setup_logger(logging.DEBUG)
    logging.info("--- 開始執行持續監控任務 ---")
    try:
        while True:
            logging.info("--- 開始新一輪檢查 ---")
            
            tasks_to_run = []
            for task in task_config_manager.get_tasks():
                task_type = task.get('type', 'pulamo') # Default to pulamo
                if task_type == 'ruten':
                    tasks_to_run.append(process_ruten_task(task))
                elif task_type == 'pulamo':
                    tasks_to_run.append(process_pulamo_task(task))
            
            await asyncio.gather(*tasks_to_run)

            logging.info(f"--- 等待 {config.CHECK_INTERVAL_SECONDS} 秒後進行下一次檢查 ---")
            await asyncio.sleep(config.CHECK_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        logging.info("收到手動中斷訊號，程式即將關閉。")
    except Exception as e:
        logging.critical(f"執行過程中發生未預期的錯誤: {e}", exc_info=True)
    finally:
        logging.info("--- 監控任務執行完畢 ---")

if __name__ == '__main__':
    asyncio.run(main())
