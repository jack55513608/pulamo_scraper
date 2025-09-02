import sys
import logging
import time
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options
import config
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import os

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def initialize_driver() -> WebDriver | None:
    """Sets up and connects to the Selenium Grid."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )

    for attempt in range(config.MAX_RETRIES):
        try:
            logging.info(f"Connecting to Selenium Grid (Attempt {attempt + 1}/{config.MAX_RETRIES})...")
            driver = webdriver.Remote(
                command_executor=config.SELENIUM_GRID_URL, options=chrome_options
            )
            logging.info("Successfully connected to Selenium Grid!")
            return driver
        except Exception as e:
            if attempt < config.MAX_RETRIES - 1:
                logging.warning(f"Connection failed. Retrying in {config.RETRY_DELAY_SECONDS} seconds...")
                time.sleep(config.RETRY_DELAY_SECONDS)
            else:
                logging.error(f"Could not connect to Selenium Grid after {config.MAX_RETRIES} attempts: {e}", exc_info=True)
                return None
    return None

def dump_html(url: str):
    """
    Dumps the HTML of a given URL using Selenium.
    """
    logging.info(f"準備從 {url} 抓取 HTML...")
    driver = initialize_driver()
    if not driver:
        logging.error("WebDriver 初始化失敗，無法繼續。")
        return

    try:
        driver.get(url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "rt-product-card"))
        )
        logging.info("頁面載入成功，正在輸出 HTML 內容...")
        soup = BeautifulSoup(driver.page_source, "html.parser")
        product_links = soup.find_all("a", class_="rt-product-card-name-wrap")
        if product_links:
            print(product_links[2]["href"])
        else:
            logging.warning("沒有找到任何商品連結。")
        logging.info("HTML 內容輸出完畢。")
    except Exception as e:
        logging.error(f"抓取頁面時發生錯誤: {e}", exc_info=True)
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("使用方式: python html_dumper.py <URL>")
        sys.exit(1)
    
    target_url = sys.argv[1]
    dump_html(target_url)