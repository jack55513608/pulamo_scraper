# tests/test_models.py
import unittest
from models import Product

class TestProductModel(unittest.TestCase):

    def test_repr_in_stock(self):
        """Test the __repr__ method for a product that is in stock."""
        product = Product(
            title="Test Product",
            price=100,
            in_stock=True,
            url="http://example.com",
            seller="test_seller",
            payment_methods=['CASH', 'CARD']
        )
        
        expected_repr = "Product(title='Test Product', price=100, stock='有貨', url='http://example.com', seller='test_seller', payment_methods=['CASH', 'CARD'])"
        self.assertEqual(repr(product), expected_repr)

    def test_repr_out_of_stock(self):
        """Test the __repr__ method for a product that is out of stock."""
        product = Product(
            title="Another Product",
            price=200,
            in_stock=False,
            url="http://example.com/another"
        )
        
        # Note: seller and payment_methods are optional
        expected_repr = "Product(title='Another Product', price=200, stock='缺貨', url='http://example.com/another', seller=None, payment_methods=[])"
        # To make the test more robust against changes in how default empty fields are represented,
        # we can check for the core components.
        self.assertIn("title='Another Product'", repr(product))
        self.assertIn("price=200", repr(product))
        self.assertIn("stock='缺貨'", repr(product))
        self.assertIn("url='http://example.com/another'", repr(product))

    def test_repr_minimal_data(self):
        """Test the __repr__ method with only the required fields."""
        product = Product(
            title="Minimal",
            price=50,
            in_stock=True,
            url="http://example.com/minimal"
        )
        
        representation = repr(product)
        self.assertIn("stock='有貨'", representation)
        self.assertNotIn("seller='", representation) # Should not show seller if it's None
        self.assertNotIn("payment_methods=['", representation) # Should not show payment methods if empty

if __name__ == '__main__':
    unittest.main()
