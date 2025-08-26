
# test_checker.py

import unittest
from scraper import Product
from checker import find_target_product

class TestChecker(unittest.TestCase):

    def setUp(self):
        """Set up some sample products for testing."""
        self.products = [
            Product(title="MGSD 自由鋼彈", price=1200, in_stock=True),
            Product(title="MGSD 飛翼鋼彈 水貼", price=150, in_stock=True),
            Product(title="MGSD 飛翼鋼彈", price=1350, in_stock=True),
            Product(title="HG 命運鋼彈", price=500, in_stock=True),
            Product(title="MGSD 命運鋼彈", price=1400, in_stock=False),
        ]

    def test_find_product_successfully(self):
        """Test finding a product that exists and is in stock."""
        spec = {
            "name": "飛翼鋼彈",
            "keywords": ["MGSD", "飛翼鋼彈"],
            "exclude_keywords": ["水貼"],
        }
        found_product = find_target_product(self.products, spec)
        self.assertIsNotNone(found_product)
        self.assertEqual(found_product.title, "MGSD 飛翼鋼彈")

    def test_product_not_found_due_to_keyword(self):
        """Test that a product is not found if keywords don't match."""
        spec = {"name": "不存在的鋼彈", "keywords": ["不存在"]}
        found_product = find_target_product(self.products, spec)
        self.assertIsNone(found_product)

    def test_product_not_found_due_to_exclude_keyword(self):
        """Test that a product is not found if it contains excluded keywords."""
        spec = {
            "name": "飛翼鋼彈",
            "keywords": ["MGSD", "飛翼鋼彈"],
            "exclude_keywords": ["飛翼"], # Exclude itself
        }
        found_product = find_target_product(self.products, spec)
        self.assertIsNone(found_product)

    def test_product_not_found_due_to_price(self):
        """Test that a product is not found if the price is too low."""
        spec = {
            "name": "飛翼鋼彈",
            "keywords": ["MGSD", "飛翼鋼彈"],
            "exclude_keywords": ["水貼"],
            "min_price": 1500,
        }
        found_product = find_target_product(self.products, spec)
        self.assertIsNone(found_product)

    def test_product_not_found_due_to_out_of_stock(self):
        """Test that a product is not found if it is out of stock."""
        spec = {
            "name": "命運鋼彈",
            "keywords": ["MGSD", "命運鋼彈"],
        }
        found_product = find_target_product(self.products, spec)
        self.assertIsNone(found_product)

if __name__ == '__main__':
    unittest.main()
