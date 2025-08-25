
# scraper.py

import re
import time
from typing import List, Optional

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver

# --- Constants ---
MAX_RETRIES = 5
RETRY_DELAY_SECONDS = 2

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
                print(f"[INFO] Attempting to connect to Selenium Grid (Attempt {attempt + 1}/{MAX_RETRIES})...")
                driver = webdriver.Remote(
                    command_executor=self.grid_url, options=chrome_options
                )
                print("[INFO] Successfully connected to Selenium Grid!")
                return driver
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    print(f"[WARN] Connection failed. Retrying in {RETRY_DELAY_SECONDS} seconds...")
                    time.sleep(RETRY_DELAY_SECONDS)
                else:
                    print(f"\n[ERROR] Could not connect to Selenium Grid after {MAX_RETRIES} attempts: {e}")
                    return None
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get_products_from_search(self, base_url: str, search_term: str) -> List[Product]:
        """
        Fetches the search result page and parses all products.

        Args:
            base_url: The base URL of the website.
            search_term: The term to search for.

        Returns:
            A list of Product objects found on the page.
        """
        if not self.driver:
            print("[ERROR] WebDriver not initialized. Cannot scrape.")
            return []

        url = f"{base_url}?search={search_term}"
        print(f"[INFO] Scraping URL: {url}")
        self.driver.get(url)
        time.sleep(3)  # Wait for dynamic content to load

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        product_cards = soup.find_all('div', class_='meepshop-meep-ui__productList-index__productCard')

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
            print(f"[WARN] Could not parse a product card: {e}")
            return None

    def close(self):
        """Closes the browser and quits the driver."""
        if self.driver:
            print("[INFO] Task finished. Closing browser.")
            self.driver.quit()
