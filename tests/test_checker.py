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
            Product(title="ANOTHER MGSD 飛翼鋼彈", price=1400, in_stock=True, url="http://example.com/6"),
        ]
        self.checker = ProductChecker()

    def test_find_product_successfully(self):
        """Test finding a single product that exists and is in stock."""
        params = {
            "keywords": ["自由鋼彈"],
            "exclude_keywords": [],
        }
        found_products = self.checker.check(self.products, params)
        self.assertEqual(len(found_products), 1)
        self.assertEqual(found_products[0].title, "MGSD 自由鋼彈")

    def test_find_multiple_products_successfully(self):
        """Test finding multiple products that match the criteria."""
        params = {
            "keywords": ["MGSD", "飛翼鋼彈"],
            "exclude_keywords": ["水貼"],
        }
        found_products = self.checker.check(self.products, params)
        self.assertEqual(len(found_products), 2)
        self.assertIn("MGSD 飛翼鋼彈", [p.title for p in found_products])
        self.assertIn("ANOTHER MGSD 飛翼鋼彈", [p.title for p in found_products])

    def test_product_not_found_due_to_keyword(self):
        """Test that an empty list is returned if keywords don't match."""
        params = {"keywords": ["不存在"]}
        found_products = self.checker.check(self.products, params)
        self.assertEqual(found_products, [])

    def test_product_not_found_due_to_exclude_keyword(self):
        """Test that an empty list is returned if it contains excluded keywords."""
        params = {
            "keywords": ["MGSD", "飛翼鋼彈"],
            "exclude_keywords": ["飛翼"], # Exclude itself
        }
        found_products = self.checker.check(self.products, params)
        self.assertEqual(found_products, [])

    def test_product_not_found_due_to_price(self):
        """Test that an empty list is returned if the price is too low."""
        params = {
            "keywords": ["MGSD", "飛翼鋼彈"],
            "exclude_keywords": ["水貼"],
            "min_price": 1500,
        }
        found_products = self.checker.check(self.products, params)
        self.assertEqual(found_products, [])

    def test_product_not_found_due_to_out_of_stock(self):
        """Test that an empty list is returned if it is out of stock."""
        params = {
            "keywords": ["MGSD", "命運鋼彈"],
        }
        found_products = self.checker.check(self.products, params)
        self.assertEqual(found_products, [])

if __name__ == '__main__':
    unittest.main()