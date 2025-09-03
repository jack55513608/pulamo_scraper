# scrapers/ruten.py
import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup, Tag
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import config
from models import Product
from scrapers.base import BaseScraper
from task_config_manager import task_config_manager


class RutenSearchScraper(BaseScraper):
    """A scraper for the Ruten search result page."""

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
                self.driver.get(url)
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "product-item"))
                )

                # Get scroll height
                last_height = self.driver.execute_script("return document.body.scrollHeight")

                # Number of times to scroll
                for i in range(2):
                    # Scroll down by a fraction of the page height
                    self.driver.execute_script(f"window.scrollBy(0, {last_height/2});")
                    time.sleep(3)

                break
            except TimeoutException:
                if attempt < getattr(config, 'MAX_RETRIES', 10) - 1:
                    logging.warning(f"Timeout waiting for product items on page {url}. Retrying in {config.RETRY_DELAY_SECONDS} seconds...")
                    time.sleep(config.RETRY_DELAY_SECONDS)
                else:
                    logging.error(f"Failed to load page {url} after {getattr(config, 'MAX_RETRIES', 10)} attempts.")
                    return []

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        product_items = soup.find_all('div', class_='product-item')

        if not product_items:
            with open(f"/tmp/ruten_page_source_{time.time()}.html", "w") as f:
                f.write(self.driver.page_source)
            logging.warning(f"在 {url} 上沒有找到任何商品 (class='product-item')")
            return []

        products = []
        for item in product_items:
            product = self._parse_product_item(item)
            if product:
                products.append(product)
        
        logging.info(f"在 {url} 上共找到 {len(products)} 件商品。")
        return products

    def _parse_product_item(self, item: Tag) -> Optional[Product]:
        """Parses a single product item to extract its details."""
        try:
            name_wrap = item.find('a', class_='rt-product-card-name-wrap')
            if not name_wrap:
                return None

            title = name_wrap.find('p', class_='rt-product-card-name').text.strip()
            product_url = name_wrap['href']

            price_element = item.find('span', class_='rt-text-price')
            price_text = price_element.text.strip() if price_element else '0'
            price_match = re.search(r'([0-9,]+)', price_text)
            price = int(price_match.group(1).replace(',', '')) if price_match else 0

            return Product(
                title=title,
                price=price,
                url=product_url,
                in_stock=False  # Placeholder, will be checked by another component
            )
        except (AttributeError, ValueError, TypeError) as e:
            logging.warning(f"Could not parse a product card: {e}")
            logging.warning(f"無法解析商品卡片，HTML 內容: \n{item.prettify()}")
            return None

class RutenProductPageScraper(BaseScraper):
    """
    Scrapes individual Ruten product pages to get detailed information, 
    especially stock status and seller ID.
    """

    def scrape(self, products: List[Product], params: dict) -> Tuple[List[Product], Dict[str, Any]]:
        """
        Receives a list of products, visits each URL, and updates them
        with stock and seller information.
        """
        blacklisted_sellers = params.get('blacklisted_sellers', [])
        stats = {
            'total_processed': len(products),
            'failed_to_scrape': [],
            'out_of_stock_after_scrape': []
        }

        if not self.driver:
            logging.error("WebDriver not initialized. Cannot scrape.")
            stats['failed_to_scrape'] = [p.title for p in products]
            return products, stats

        updated_products = []
        for product in products:
            try:
                self.driver.get(product.url)
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "meta[name='description']"))
                )
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                # Update product with stock info, seller and payment methods
                product.in_stock = self._parse_stock_status(soup)
                product.seller = self._parse_seller_id(soup)
                product.payment_methods = self._parse_payment_methods(soup)

                if product.seller and product.seller in blacklisted_sellers:
                    logging.info(f"Product '{product.title}' seller '{product.seller}' is blacklisted, skipping.")
                    product.in_stock = False

                if not product.in_stock:
                    stats['out_of_stock_after_scrape'].append(product.title)
                updated_products.append(product)

            except Exception as e:
                logging.error(f"Failed to scrape product page {product.url}: {e}", exc_info=True)
                product.in_stock = False
                stats['failed_to_scrape'].append(product.title)
                updated_products.append(product)
        
        logging.info(f"Scraped {len(updated_products)} product pages. {len(stats['failed_to_scrape'])} failed, {len(stats['out_of_stock_after_scrape'])} out of stock.")
        return updated_products, stats

    def _parse_stock_status(self, soup: BeautifulSoup) -> bool:
        """Parses the soup of a product page to determine stock status."""
        # Method 1: Check meta description for stock count
        description_tag = soup.find('meta', {'name': 'description'})
        if description_tag and description_tag.get('content'):
            content = description_tag['content']
            stock_match = re.search(r'庫存: (\d+)', content)
            if stock_match:
                stock_count = int(stock_match.group(1))
                logging.info(f"Meta tag shows stock count: {stock_count}")
                return stock_count > 0

        # Method 2: Check for "sold out" button as a fallback
        sold_out_button = soup.find('input', class_='item-soldout-action')
        if sold_out_button:
            logging.info("Found 'sold out' button.")
            return False

        # If neither the meta tag provides info nor a sold-out button is found,
        # assume it's in stock as a reasonable default.
        logging.warning("Could not determine stock status from meta tag or button, assuming in stock.")
        return True

    def _parse_seller_id(self, soup: BeautifulSoup) -> Optional[str]:
        """Parses the soup of a product page to find the seller's ID."""
        try:
            # Find the link to the seller's store profile
            # The link contains '/store/[seller_id]'
            seller_link = soup.find('a', href=re.compile(r'/store/'))
            if seller_link and seller_link.get('href'):
                href = seller_link['href']
                seller_id = href.split('/')[-1]
                logging.info(f"Found seller ID: {seller_id}")
                return seller_id
            
            # Fallback: Try to find it in the script context
            scripts = soup.find_all('script', type='text/javascript')
            for script in scripts:
                if script.string and 'RT.context' in script.string:
                    match = re.search(r'"nick":"(.*?)"', script.string)
                    if match:
                        seller_id = match.group(1)
                        logging.info(f"Found seller ID from script context: {seller_id}")
                        return seller_id

            logging.warning("Could not find seller ID on the page.")
            return None
        except Exception as e:
            logging.error(f"Error parsing seller ID: {e}", exc_info=True)
            return None

    def _parse_payment_methods(self, soup: BeautifulSoup) -> List[str]:
        """Parses the soup of a product page to find available payment methods."""
        payment_methods = []
        payment_section = soup.find('td', class_='title', string='付款方式：')
        if payment_section:
            payment_list = payment_section.find_next_sibling('td').find('ul', class_='detail-list')
            if payment_list:
                for item in payment_list.find_all('li'):
                    # Extract the class name that starts with 'PW_'
                    pw_class = next((c for c in item.get('class', []) if c.startswith('PW_')), None)
                    if pw_class:
                        payment_methods.append(pw_class)
                    else:
                        # Fallback to text if no PW_ class is found (e.g., for "面交取貨付款")
                        payment_methods.append(item.text.strip())
        return payment_methods