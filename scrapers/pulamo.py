# scrapers/pulamo.py
import re
import logging
from typing import List, Optional

from bs4 import BeautifulSoup, Tag
from selenium.common.exceptions import TimeoutException
import time

from scrapers.base import BaseScraper
from models import Product
import config

class PulamoScraper(BaseScraper):
    """A scraper for the Pulamo website."""

    def scrape(self, params: dict) -> List[Product]:
        """
        Fetches the search result page and parses all products.
        """
        url = params.get("search_url")
        if not url:
            logging.error("search_url not provided in params.")
            return []

        if not self.driver:
            logging.error("WebDriver not initialized. Cannot scrape.")
            return []

        for attempt in range(getattr(config, 'MAX_RETRIES', 10)):
            try:
                logging.info(f"Scraping URL: {url} (Attempt {attempt + 1}/{getattr(config, 'MAX_RETRIES', 10)})")
                self.driver.get(url)
                break
            except TimeoutException:
                if attempt < getattr(config, 'MAX_RETRIES', 10) - 1:
                    logging.warning(f"Timeout loading page {url}. Retrying in {config.RETRY_DELAY_SECONDS} seconds...")
                    time.sleep(config.RETRY_DELAY_SECONDS)
                else:
                    logging.error(f"Failed to load page {url} after {getattr(config, 'MAX_RETRIES', 10)} attempts.")
                    return []

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        product_cards = soup.find_all('div', class_='meepshop-meep-ui__productList-index__productCard')

        if not product_cards:
            logging.info(f"在 {url} 上沒有找到任何商品卡片。")
            return []

        products = []
        for card in product_cards:
            product = self._parse_product_card(card, url)
            if product:
                products.append(product)
        return products

    def _parse_product_card(self, card: Tag, page_url: str) -> Optional[Product]:
        """Parses a single product card to extract its details."""
        try:
            title_element = card.find('div', class_='meepshop-meep-ui__productList-index__productTitle')
            price_element = card.find('div', style=re.compile(r'font-size:16px;font-weight:700'))
            
            # If critical elements are missing, return None
            if not title_element or not price_element:
                logging.warning("Missing critical elements (title or price) in product card.")
                return None

            title = title_element.text.strip()
            
            price_text = price_element.text.strip()
            price = int(re.sub(r'[^0-9]', '', price_text))

            sold_out_button = card.find('button', string='已售完', attrs={'disabled': ''})
            in_stock = sold_out_button is None

            product_link_element = card.find('a')
            product_url = product_link_element['href'] if product_link_element else page_url

            return Product(title=title, price=price, in_stock=in_stock, url=product_url)
        except (AttributeError, ValueError) as e:
            logging.warning(f"Could not parse a product card: {e}")
            return None