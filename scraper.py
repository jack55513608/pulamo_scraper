
# scraper.py

import re
import time
import logging
from typing import List, Optional

from bs4 import BeautifulSoup, Tag
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver
import config # 導入 config 模組

# --- Constants ---
MAX_RETRIES = 10
# RETRY_DELAY_SECONDS = 2 # 已移至 config.py

class Product:
    """Represents a product scraped from the website."""

    def __init__(self, title: str, price: int, in_stock: bool):
        self.title = title
        self.price = price
        self.in_stock = in_stock

    def __repr__(self) -> str:
        stock_status = "有貨" if self.in_stock else "缺貨"
        return f"Product(title='{self.title}', price={self.price}, stock='{stock_status}')"


class PulamoScraper:
    """
    A scraper for the Pulamo website to find and parse product information.
    """

    def __init__(self, grid_url: str):
        """Initializes the scraper and the Selenium WebDriver."""
        self.grid_url = grid_url
        self.driver = self._initialize_driver()
        if self.driver:
            self.driver.set_page_load_timeout(120) # 增加頁面加載超時到 120 秒
            self.driver.implicitly_wait(10) # 增加隱式等待到 10 秒

    def _initialize_driver(self) -> Optional[WebDriver]:
        """
        Sets up and connects to the Selenium Grid.
        Retries connection if it fails.
        """
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )

        for attempt in range(MAX_RETRIES):
            try:
                logging.info(f"Connecting to Selenium Grid (Attempt {attempt + 1}/{MAX_RETRIES})...")
                driver = webdriver.Remote(
                    command_executor=self.grid_url, options=chrome_options
                )
                logging.info("Successfully connected to Selenium Grid!")
                return driver
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    logging.warning(f"Connection failed. Retrying in {config.RETRY_DELAY_SECONDS} seconds...")
                    time.sleep(config.RETRY_DELAY_SECONDS)
                else:
                    logging.error(f"Could not connect to Selenium Grid after {MAX_RETRIES} attempts: {e}", exc_info=True)
                    return None
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get_products_from_search(self, url: str) -> List[Product]:
        """
        Fetches the search result page and parses all products.
        """
        if not self.driver:
            logging.error("WebDriver not initialized. Cannot scrape.")
            return []

        for attempt in range(MAX_RETRIES):
            try:
                logging.info(f"Scraping URL: {url} (Attempt {attempt + 1}/{MAX_RETRIES})")
                self.driver.get(url)
                break  # Success, exit the loop
            except TimeoutException:
                if attempt < MAX_RETRIES - 1:
                    logging.warning(f"Timeout loading page {url}. Retrying in {config.RETRY_DELAY_SECONDS} seconds...")
                    time.sleep(config.RETRY_DELAY_SECONDS)
                else:
                    logging.error(f"Failed to load page {url} after {MAX_RETRIES} attempts.")
                    return []

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        product_cards = soup.find_all('div', class_='meepshop-meep-ui__productList-index__productCard')

        if not product_cards:
            logging.info(f"在 {url} 上沒有找到任何商品卡片。")
            return []

        products = []
        for card in product_cards:
            product = self._parse_product_card(card)
            if product:
                products.append(product)
        return products

    def _parse_product_card(self, card: Tag) -> Optional[Product]:
        """Parses a single product card to extract its details."""
        try:
            title_element = card.find('div', class_='meepshop-meep-ui__productList-index__productTitle')
            price_element = card.find('div', style=re.compile(r'font-size:16px;font-weight:700'))
            
            title = title_element.text.strip() if title_element else ''
            
            price_text = price_element.text.strip() if price_element else 'NT$ 0'
            price = int(re.sub(r'[^0-9]', '', price_text))

            sold_out_button = card.find('button', string='已售完', attrs={'disabled': ''})
            in_stock = sold_out_button is None

            return Product(title=title, price=price, in_stock=in_stock)
        except (AttributeError, ValueError) as e:
            logging.warning(f"Could not parse a product card: {e}")
            return None

    def close(self):
        """Closes the browser and quits the driver."""
        if self.driver:
            try:
                logging.info("Task finished. Closing browser.")
                self.driver.quit()
            except Exception as e:
                logging.error(f"Error while closing WebDriver: {e}", exc_info=True)
