# test_checker.py
import unittest
from models import Product
from checkers.product import ProductChecker

class TestChecker(unittest.TestCase):

    def setUp(self):
        """Set up some sample products for testing."""
        self.products = [
            Product(title="MGSD 自由鋼彈", price=1200, in_stock=True, url="http://example.com/1"),
            Product(title="MGSD 飛翼鋼彈 水貼", price=150, in_stock=True, url="http://example.com/2"),
            Product(title="MGSD 飛翼鋼彈", price=1350, in_stock=True, url="http://example.com/3"),
            Product(title="HG 命運鋼彈", price=500, in_stock=True, url="http://example.com/4"),
            Product(title="MGSD 命運鋼彈", price=1400, in_stock=False, url="http://example.com/5"),
        ]
        self.checker = ProductChecker()

    def test_find_product_successfully(self):
        """Test finding a product that exists and is in stock."""
        params = {
            "keywords": ["MGSD", "飛翼鋼彈"],
            "exclude_keywords": ["水貼"],
        }
        found_product = self.checker.check(self.products, params)
        self.assertIsNotNone(found_product)
        self.assertEqual(found_product.title, "MGSD 飛翼鋼彈")

    def test_product_not_found_due_to_keyword(self):
        """Test that a product is not found if keywords don't match."""
        params = {"keywords": ["不存在"]}
        found_product = self.checker.check(self.products, params)
        self.assertIsNone(found_product)

    def test_product_not_found_due_to_exclude_keyword(self):
        """Test that a product is not found if it contains excluded keywords."""
        params = {
            "keywords": ["MGSD", "飛翼鋼彈"],
            "exclude_keywords": ["飛翼"], # Exclude itself
        }
        found_product = self.checker.check(self.products, params)
        self.assertIsNone(found_product)

    def test_product_not_found_due_to_price(self):
        """Test that a product is not found if the price is too low."""
        params = {
            "keywords": ["MGSD", "飛翼鋼彈"],
            "exclude_keywords": ["水貼"],
            "min_price": 1500,
        }
        found_product = self.checker.check(self.products, params)
        self.assertIsNone(found_product)

    def test_product_not_found_due_to_out_of_stock(self):
        """Test that a product is not found if it is out of stock."""
        params = {
            "keywords": ["MGSD", "命運鋼彈"],
        }
        found_product = self.checker.check(self.products, params)
        self.assertIsNone(found_product)

if __name__ == '__main__':
    unittest.main()