# tests/test_scrapers_pulamo_unit.py
import unittest
from bs4 import BeautifulSoup, Tag
from scrapers.pulamo import PulamoScraper
from models import Product

class TestPulamoScraperUnit(unittest.TestCase):

    def setUp(self):
        # PulamoScraper's __init__ calls _initialize_driver, which tries to connect to Selenium.
        # For unit testing _parse_product_card, we don't need a real driver.
        # So, we'll mock the _initialize_driver method during instantiation.
        with unittest.mock.patch('scrapers.pulamo.PulamoScraper._initialize_driver', return_value=None):
            self.scraper = PulamoScraper(grid_url="http://mock_grid:4444/wd/hub", browser='chrome')

    def test_parse_product_card_in_stock(self):
        html_snippet = """
        <div class="meepshop-meep-ui__productList-index__productCard">
            <div class="meepshop-meep-ui__productList-index__productTitle">MGSD 飛翼鋼彈</div>
            <div style="font-size:16px;font-weight:700">NT$ 1350</div>
            <a href="/products/wing-gundam">View Product</a>
        </div>
        """
        soup = BeautifulSoup(html_snippet, 'html.parser')
        card = soup.find('div', class_='meepshop-meep-ui__productList-index__productCard')
        
        product = self.scraper._parse_product_card(card, "http://pulamo.com.tw/search")
        
        self.assertIsNotNone(product)
        self.assertEqual(product.title, "MGSD 飛翼鋼彈")
        self.assertEqual(product.price, 1350)
        self.assertTrue(product.in_stock)
        self.assertEqual(product.url, "/products/wing-gundam")

    def test_parse_product_card_out_of_stock(self):
        html_snippet = """
        <div class="meepshop-meep-ui__productList-index__productCard">
            <div class="meepshop-meep-ui__productList-index__productTitle">MGSD 命運鋼彈</div>
            <div style="font-size:16px;font-weight:700">NT$ 1400</div>
            <button disabled="">已售完</button>
            <a href="/products/destiny-gundam">View Product</a>
        </div>
        """
        soup = BeautifulSoup(html_snippet, 'html.parser')
        card = soup.find('div', class_='meepshop-meep-ui__productList-index__productCard')
        
        product = self.scraper._parse_product_card(card, "http://pulamo.com.tw/search")
        
        self.assertIsNotNone(product)
        self.assertEqual(product.title, "MGSD 命運鋼彈")
        self.assertEqual(product.price, 1400)
        self.assertFalse(product.in_stock)
        self.assertEqual(product.url, "/products/destiny-gundam")

    def test_parse_product_card_missing_elements(self):
        html_snippet = """
        <div class="meepshop-meep-ui__productList-index__productCard">
            <!-- Missing title and price -->
            <a href="/products/some-product">View Product</a>
        </div>
        """
        soup = BeautifulSoup(html_snippet, 'html.parser')
        card = soup.find('div', class_='meepshop-meep-ui__productList-index__productCard')
        
        product = self.scraper._parse_product_card(card, "http://pulamo.com.tw/search")
        
        self.assertIsNone(product) # Expect None if parsing fails due to missing elements

    def test_parse_product_card_no_link(self):
        html_snippet = """
        <div class="meepshop-meep-ui__productList-index__productCard">
            <div class="meepshop-meep-ui__productList-index__productTitle">MGSD 自由鋼彈</div>
            <div style="font-size:16px;font-weight:700">NT$ 999</div>
            <!-- No link element -->
        </div>
        """
        soup = BeautifulSoup(html_snippet, 'html.parser')
        card = soup.find('div', class_='meepshop-meep-ui__productList-index__productCard')
        
        product = self.scraper._parse_product_card(card, "http://pulamo.com.tw/search")
        
        self.assertIsNotNone(product)
        self.assertEqual(product.title, "MGSD 自由鋼彈")
        self.assertEqual(product.price, 999)
        self.assertTrue(product.in_stock)
        self.assertEqual(product.url, "http://pulamo.com.tw/search") # Should fallback to page_url

if __name__ == '__main__':
    unittest.main()
