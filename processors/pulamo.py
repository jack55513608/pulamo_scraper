# processors/pulamo.py
import asyncio
import logging
import config
from factory import get_scraper, get_checker, get_notifier

async def process_pulamo_task(task: dict):
    """
    Processes a single, simple monitoring task for Pulamo.
    """
    task_name = task['name']
    logging.info(f"--- 開始執行 Pulamo 任務: {task_name} ---")

    try:
        scraper = get_scraper(task['scraper'], config.SELENIUM_GRID_URL, browser=task.get('browser', 'chrome'))
        checker = get_checker(task['checker'])
        notifier = get_notifier(task['notifier'])

        with scraper:
            products = scraper.scrape(task['scraper_params'])
            if not products:
                logging.info(f"任務 '{task_name}' 的爬蟲未在頁面上找到任何商品。")
                return

            found_products = checker.check(products, task['checker_params'])

            if found_products:
                logging.info(f"在任務 '{task_name}' 中找到 {len(found_products)} 件目標商品。")
                # Concurrently notify for all found products
                notification_tasks = [
                    notifier.notify(product, task['notifier_params'])
                    for product in found_products
                ]
                await asyncio.gather(*notification_tasks)
            else:
                logging.info(f"任務 '{task_name}' 找到了 {len(products)} 件商品，但沒有任何一件符合篩選條件。")

    except Exception as e:
        logging.error(f"在處理任務 '{task_name}' 時發生錯誤: {e}", exc_info=True)
