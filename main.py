# main.py
import asyncio
import logging
import config
from logger_config import setup_logger
from factory import get_scraper, get_checker, get_notifier

async def process_simple_task(task: dict):
    """
    Processes a single, simple monitoring task (scrape -> check -> notify).
    """
    task_name = task['name']
    logging.info(f"--- 開始執行簡單任務: {task_name} ---")

    try:
        scraper = get_scraper(task['scraper'], config.SELENIUM_GRID_URL)
        checker = get_checker(task['checker'])
        notifier = get_notifier(task['notifier'])

        with scraper:
            products = scraper.scrape(task['scraper_params'])
            if not products:
                logging.info(f"任務 '{task_name}' 的爬蟲未在頁面上找到任何商品。")
                return

            found_product = checker.check(products, task['checker_params'])

            if found_product:
                logging.info(f"在任務 '{task_name}' 中找到目標商品: {found_product.title}")
                await notifier.notify(found_product, task['notifier_params'])
            else:
                logging.info(f"任務 '{task_name}' 找到了 {len(products)} 件商品，但沒有任何一件符合篩選條件。")

    except Exception as e:
        logging.error(f"在處理任務 '{task_name}' 時發生錯誤: {e}", exc_info=True)

async def process_ruten_task(task: dict):
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
    }

    try:
        logging.info("Step 1: Scraping search result page...")
        # Step 1: Scrape the search result page
        search_scraper = get_scraper(task['search_scraper'], config.SELENIUM_GRID_URL)
        with search_scraper:
            all_products = search_scraper.scrape(task['search_scraper_params'])
        stats['total_searched'] = len(all_products)

        if not all_products:
            return

        logging.info("Step 2: Filtering by keywords...")
        # Step 2: Filter by keywords
        keyword_checker = get_checker(task['keyword_checker'])
        filtered_products, keyword_stats = keyword_checker.check(all_products, task['keyword_checker_params'])
        stats['keyword_mismatch'] = len(keyword_stats['rejected_keyword_mismatch'])
        stats['excluded_keyword'] = len(keyword_stats['rejected_excluded_keyword'])

        if not filtered_products:
            return

        logging.info("Step 3: Scraping product pages for stock info...")
        # Step 3: Scrape product pages for stock info (sequential)
        page_scraper = get_scraper(task['page_scraper'], config.SELENIUM_GRID_URL)
        with page_scraper:
            detailed_products, page_scrape_stats = page_scraper.scrape(filtered_products)
        stats['pages_scraped'] = len(detailed_products) - len(page_scrape_stats['failed_to_scrape'])
        stats['pages_failed'] = len(page_scrape_stats['failed_to_scrape'])


        logging.info("Step 4: Checking for stock...")
        # Step 4: Check for stock
        stock_checker = get_checker(task['stock_checker'])
        found_product, stock_stats = stock_checker.check(detailed_products, task.get('stock_checker_params', {}))
        stats['out_of_stock'] = len(stock_stats['out_of_stock_titles'])

        logging.info("Step 5: Notifying if a product is found...")
        # Step 5: Notify if a product is found
        if found_product:
            logging.info(f"在任務 '{task_name}' 中找到目標商品: {found_product.title}")
            notifier = get_notifier(task['notifier'])
            await notifier.notify(found_product, task['notifier_params'])
        else:
            logging.info(f"未找到符合條件且有庫存的商品。")

    except Exception as e:
        logging.error(f"在處理任務 '{task_name}' 時發生錯誤: {e}", exc_info=True)
    finally:
        logging.info(f"Ruten任務總結: 搜尋到 {stats['total_searched']} 件商品。"
                     f"因關鍵字不符被過濾 {stats['keyword_mismatch']} 件。"
                     f"因排除關鍵字被過濾 {stats['excluded_keyword']} 件。"
                     f"成功抓取 {stats['pages_scraped']} 件商品頁面。"
                     f"其中 {stats['pages_failed']} 件抓取失敗。"
                     f"最終 {stats['out_of_stock']} 件商品皆無庫存。")


async def main():
    """
    Main function to initialize and run the scraper and checks in a loop.
    """
    setup_logger()
    logging.info("--- 開始執行持續監控任務 ---")
    try:
        while True:
            logging.info("--- 開始新一輪檢查 ---")
            
            tasks_to_run = []
            for task in config.TASKS:
                task_type = task.get('type', 'simple') # Default to simple
                if task_type == 'ruten':
                    tasks_to_run.append(process_ruten_task(task))
                else:
                    tasks_to_run.append(process_simple_task(task))
            
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
