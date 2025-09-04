# processors/ruten.py
import asyncio
import logging
import time
from typing import Dict, Callable, Optional
from dataclasses import dataclass, field

import config
from factory import get_scraper as default_get_scraper, get_checker as default_get_checker, get_notifier as default_get_notifier

@dataclass
class RutenTaskStats:
    """A dataclass to hold statistics for a Ruten processing task."""
    total_searched: int = 0
    keyword_mismatch: int = 0
    excluded_keyword: int = 0
    pages_scraped: int = 0
    pages_failed: int = 0
    out_of_stock: int = 0
    rejected_due_to_price: int = 0
    rejected_due_to_seller: int = 0
    rejected_due_to_payment_method: int = 0

    def log_summary(self):
        """Logs a formatted summary of the task statistics."""
        keyword_filtered = self.keyword_mismatch + self.excluded_keyword
        summary = (
            f"Ruten任務總結: 搜尋到 {self.total_searched} 件商品. "
            f"關鍵字過濾掉 {keyword_filtered} 件. "
            f"成功抓取 {self.pages_scraped} 個頁面 ({self.pages_failed} 失敗). "
            f"最終, {self.rejected_due_to_price} 件因價格過高, "
            f"{self.rejected_due_to_seller} 件因賣家黑名單, "
            f"{self.out_of_stock} 件無庫存, "
            f"{self.rejected_due_to_payment_method} 件因付款方式不符."
        )
        logging.info(summary)

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
    stats = RutenTaskStats()

    try:
        # Step 1: Scrape the search result page
        search_scraper = get_scraper(task['search_scraper'], config.SELENIUM_GRID_URL, browser=task.get('browser', 'chrome'))
        with search_scraper:
            all_products = search_scraper.scrape(task['search_scraper_params'])
        stats.total_searched = len(all_products)

        if not all_products:
            return

        # Step 2: Filter by keywords
        keyword_checker = get_checker(task['keyword_checker'])
        filtered_products, keyword_stats = keyword_checker.check(all_products, task['keyword_checker_params'])
        stats.keyword_mismatch = len(keyword_stats['rejected_keyword_mismatch'])
        stats.excluded_keyword = len(keyword_stats['rejected_excluded_keyword'])

        if not filtered_products:
            return

        # Step 3: Scrape product pages for stock info
        page_scraper = get_scraper(task['page_scraper'], config.SELENIUM_GRID_URL, browser=task.get('browser', 'chrome'))
        with page_scraper:
            detailed_products, page_scrape_stats = page_scraper.scrape(filtered_products, task.get('stock_checker_params', {}))
        stats.pages_scraped = len(detailed_products) - len(page_scrape_stats['failed_to_scrape'])
        stats.pages_failed = len(page_scrape_stats['failed_to_scrape'])

        # Step 4: Check for stock
        stock_checker = get_checker(task['stock_checker'])
        found_products, stock_stats = stock_checker.check(detailed_products, task.get('stock_checker_params', {}))
        stats.out_of_stock = len(stock_stats['out_of_stock_titles'])
        stats.rejected_due_to_price = len(stock_stats.get('rejected_due_to_price', []))
        stats.rejected_due_to_seller = len(stock_stats.get('rejected_due_to_seller', []))
        stats.rejected_due_to_payment_method = len(stock_stats.get('rejected_due_to_payment_method', []))

        # Step 5: Filter out recently notified products and notify
        if found_products:
            products_to_notify = [p for p in found_products if notification_manager.can_notify(p.url)]
            
            for product in found_products:
                if product not in products_to_notify:
                    logging.info(f"商品 '{product.title}' 在冷卻期間，本次不通知。")

            if products_to_notify:
                logging.info(f"在任務 '{task_name}' 中找到 {len(products_to_notify)} 件新商品。")
                notifier = get_notifier(task['notifier'])
                
                notification_tasks = [notifier.notify(p, task['notifier_params']) for p in products_to_notify]
                await asyncio.gather(*notification_tasks)

                for product in products_to_notify:
                    notification_manager.record_notification(product.url)
            elif found_products: # Found products, but all were on cooldown
                logging.info(f"所有找到的商品都在冷卻期間，本次不通知。")
        else:
            logging.info(f"未找到符合條件且有庫存的商品。")

    except Exception as e:
        logging.error(f"在處理任務 '{task_name}' 時發生錯誤: {e}", exc_info=True)
    finally:
        stats.log_summary()
