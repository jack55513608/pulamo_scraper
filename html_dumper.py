# html_dumper.py
import sys
import logging
from scraper import PulamoScraper
import config

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def dump_html(url: str):
    """
    Dumps the HTML of a given URL using Selenium.
    """
    logging.info(f"準備從 {url} 抓取 HTML...")
    with PulamoScraper(config.SELENIUM_GRID_URL) as scraper:
        if not scraper.driver:
            logging.error("WebDriver 初始化失敗，無法繼續。")
            return
        
        try:
            scraper.driver.get(url)
            logging.info("頁面載入成功，正在輸出 HTML 內容...")
            # Print the page source to standard output
            print(scraper.driver.page_source)
            logging.info("HTML 內容輸出完畢。")
        except Exception as e:
            logging.error(f"抓取頁面時發生錯誤: {e}", exc_info=True)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("使用方式: python html_dumper.py <URL>")
        sys.exit(1)
    
    target_url = sys.argv[1]
    dump_html(target_url)