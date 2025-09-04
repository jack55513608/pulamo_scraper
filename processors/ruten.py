# processors/ruten.py
import asyncio
import logging
import config
from factory import get_scraper, get_checker, get_notifier
# processors/ruten.py
import asyncio
import logging
import time
from typing import Dict, Callable, Optional
import config
from factory import get_scraper as default_get_scraper, get_checker as default_get_checker, get_notifier as default_get_notifier

class NotificationManager:
    _instance = None
    _last_notified: Dict[str, float] = {}
    _cooldown_seconds = 1800  # 30 minutes

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NotificationManager, cls).__new__(cls)
        return cls._instance

    def can_notify(self, product_url: str) -> bool:
        """Checks if a notification can be sent for the given product URL."""
        last_notified_time = self._last_notified.get(product_url)
        if last_notified_time:
            elapsed_time = time.time() - last_notified_time
            if elapsed_time < self._cooldown_seconds:
                return False
        return True

    def record_notification(self, product_url: str):
        """Records that a notification has been sent for the given product URL."""
        self._last_notified[product_url] = time.time()

# Singleton instance
notification_manager = NotificationManager()

async def process_ruten_task(
    task: dict,
    get_scraper: Callable = default_get_scraper,
    get_checker: Callable = default_get_checker,
    get_notifier: Callable = default_get_notifier
):
    """
    Processes a multi-step task specifically for Ruten.
    """
    task_name = task['name']
    logging.info(f"--- 開始執行露天任務: {task_name} ---")

    stats = {
        'total_searched': 0,
        'keyword_mismatch': 0,
        'excluded_keyword': 0,
        'pages_scraped': 0,
        'pages_failed': 0,
        'out_of_stock': 0,
        'rejected_due_to_price': 0,
        'rejected_due_to_seller': 0,
        'rejected_due_to_payment_method': 0,
    }

    try:
        # Step 1: Scrape the search result page
        search_scraper = get_scraper(task['search_scraper'], config.SELENIUM_GRID_URL, browser=task.get('browser', 'chrome'))
        with search_scraper:
            all_products = search_scraper.scrape(task['search_scraper_params'])
        stats['total_searched'] = len(all_products)

        if not all_products:
            return

        # Step 2: Filter by keywords
        keyword_checker = get_checker(task['keyword_checker'])
        filtered_products, keyword_stats = keyword_checker.check(all_products, task['keyword_checker_params'])
        stats['keyword_mismatch'] = len(keyword_stats['rejected_keyword_mismatch'])
        stats['excluded_keyword'] = len(keyword_stats['rejected_excluded_keyword'])

        if not filtered_products:
            return

        # Step 3: Scrape product pages for stock info (sequential)
        page_scraper = get_scraper(task['page_scraper'], config.SELENIUM_GRID_URL, browser=task.get('browser', 'chrome'))
        with page_scraper:
            detailed_products, page_scrape_stats = page_scraper.scrape(filtered_products, task.get('stock_checker_params', {}))
        stats['pages_scraped'] = len(detailed_products) - len(page_scrape_stats['failed_to_scrape'])
        stats['pages_failed'] = len(page_scrape_stats['failed_to_scrape'])


        # Step 4: Check for stock
        stock_checker = get_checker(task['stock_checker'])
        found_products, stock_stats = stock_checker.check(detailed_products, task.get('stock_checker_params', {}))
        stats['out_of_stock'] = len(stock_stats['out_of_stock_titles'])
        stats['rejected_due_to_price'] = len(stock_stats.get('rejected_due_to_price', []))
        stats['rejected_due_to_seller'] = len(stock_stats.get('rejected_due_to_seller', []))
        stats['rejected_due_to_payment_method'] = len(stock_stats.get('rejected_due_to_payment_method', []))


        # Step 5: Filter out recently notified products and notify
        if found_products:
            products_to_notify = []
            for product in found_products:
                if notification_manager.can_notify(product.url):
                    products_to_notify.append(product)
                else:
                    logging.info(f"商品 '{product.title}' 在冷卻期間，本次不通知。")
            
            if products_to_notify:
                logging.info(f"在任務 '{task_name}' 中找到 {len(products_to_notify)} 件新商品。")
                notifier = get_notifier(task['notifier'])
                
                notification_tasks = []
                for product in products_to_notify:
                    # By creating a task, we can await its completion
                    # and then record the notification.
                    task_to_run = notifier.notify(product, task['notifier_params'])
                    notification_tasks.append(task_to_run)

                # Wait for all notifications to be sent
                await asyncio.gather(*notification_tasks)

                # Record notifications for products that were successfully notified
                for product in products_to_notify:
                    notification_manager.record_notification(product.url)
            else:
                logging.info(f"所有找到的商品都在冷卻期間，本次不通知。")
        else:
            logging.info(f"未找到符合條件且有庫存的商品。")

    except Exception as e:
        logging.error(f"在處理任務 '{task_name}' 時發生錯誤: {e}", exc_info=True)
    finally:
        summary = (
            f"Ruten任務總結: 搜尋到 {stats['total_searched']} 件商品. "
            f"關鍵字過濾掉 {stats['keyword_mismatch'] + stats['excluded_keyword']} 件. "
            f"成功抓取 {stats['pages_scraped']} 個頁面 ({stats['pages_failed']} 失敗). "
            f"最終, {stats['rejected_due_to_price']} 件因價格過高, "
            f"{stats['rejected_due_to_seller']} 件因賣家黑名單, "
            f"{stats['out_of_stock']} 件無庫存, "
            f"{stats['rejected_due_to_payment_method']} 件因付款方式不符."
        )
        logging.info(summary)
