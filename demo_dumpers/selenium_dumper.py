import sys
import logging
import time
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
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
    options = FirefoxOptions()
    options.set_preference('permissions.default.image', 2)
    options.set_preference('permissions.default.stylesheet', 2)
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )

    for attempt in range(config.MAX_RETRIES):
        try:
            logging.info(f"Connecting to Selenium Grid (Attempt {attempt + 1}/{config.MAX_RETRIES})...")
            driver = webdriver.Remote(
                command_executor=config.SELENIUM_GRID_URL, options=options
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
        # Wait for the main product container to be present
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        logging.info("Page body has loaded.")

        print("--- Full Page Source ---")
        print(driver.page_source)
        print("------------------------")

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