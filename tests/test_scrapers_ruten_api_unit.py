import unittest
from unittest.mock import MagicMock, patch
import requests

from scrapers.ruten_api import RutenSearchAPIScraper, RutenProductPageAPIScraper
from models import Product

class TestRutenAPIScrapers(unittest.TestCase):

    def setUp(self):
        """Set up a mock session for all tests."""
        self.mock_session = MagicMock(spec=requests.Session)

    def test_search_scraper_success(self):
        """Test the RutenSearchAPIScraper's happy path."""
        # Arrange
        mock_search_response = MagicMock()
        mock_search_response.json.return_value = {
            "Rows": [
                {"Id": "111"},
                {"Id": "222"}
            ]
        }

        mock_details_response = MagicMock()
        mock_details_response.json.return_value = [
            {
                "ProdId": "111",
                "ProdName": "Test Product 1",
                "PriceRange": [10000, 20000],
                "StockStatus": 1,
                "SellerId": "seller1",
                "Payment": "CREDIT_CARD,SEVEN_COD"
            },
            {
                "ProdId": "222",
                "ProdName": "Test Product 2",
                "PriceRange": [30000, 40000],
                "StockStatus": 0,
                "SellerId": "seller2",
                "Payment": "FAMI_COD"
            }
        ]
        self.mock_session.get.side_effect = [mock_search_response, mock_details_response]

        scraper = RutenSearchAPIScraper(session=self.mock_session)
        params = {'search_url': 'https://www.ruten.com.tw/find/?q=test'}

        # Act
        products = scraper.scrape(params)

        # Assert
        self.assertEqual(len(products), 2)
        
        self.assertEqual(products[0].title, "Test Product 1")
        self.assertEqual(products[0].price, 100)
        self.assertTrue(products[0].in_stock)
        self.assertEqual(products[0].url, "https://www.ruten.com.tw/item/show?111")
        self.assertEqual(products[0].seller, "seller1")
        self.assertIn("SEVEN_COD", products[0].payment_methods)

        self.assertEqual(products[1].title, "Test Product 2")
        self.assertEqual(products[1].price, 300)
        self.assertFalse(products[1].in_stock)

    def test_page_scraper_success(self):
        """Test the RutenProductPageAPIScraper's happy path."""
        # Arrange
        initial_product = Product(title="Initial Title", price=100, url="https://www.ruten.com.tw/item/show?22536771547054", in_stock=True)

        mock_html_response = MagicMock()
        mock_html_response.text = '''
            <html><body>
            <script>RT.context = {
                "item": {
                    "no": "22536771547054",
                    "name": "Updated Title",
                    "remainNum": 5,
                    "payment": ["SEVEN_COD", "FAMI_COD"]
                },
                "seller": {
                    "nick": "test_seller"
                }
            };</script>
            </body></html>
        '''

        mock_price_api_response = MagicMock()
        mock_price_api_response.json.return_value = {
            "data": [
                {
                    "goods_price_range": {"min": 999, "max": 2000}
                }
            ]
        }

        self.mock_session.get.side_effect = [mock_html_response, mock_price_api_response]

        scraper = RutenProductPageAPIScraper(session=self.mock_session)

        # Act
        updated_products, stats = scraper.scrape([initial_product], {})

        # Assert
        self.assertEqual(len(updated_products), 1)
        product = updated_products[0]

        self.assertEqual(product.title, "Updated Title")
        self.assertEqual(product.price, 999) # Price should be updated from the accurate price API
        self.assertTrue(product.in_stock)
        self.assertEqual(product.seller, "test_seller")
        self.assertIn("SEVEN_COD", product.payment_methods)
        self.assertEqual(len(stats['failed_to_scrape']), 0)

    def test_search_scraper_api_failure(self):
        """Test that the search scraper handles a request exception."""
        # Arrange
        self.mock_session.get.side_effect = requests.exceptions.RequestException("API is down")
        scraper = RutenSearchAPIScraper(session=self.mock_session)
        params = {'search_url': 'https://www.ruten.com.tw/find/?q=test'}

        # Act
        products = scraper.scrape(params)

        # Assert
        self.assertEqual(len(products), 0)

    def test_page_scraper_html_fetch_failure(self):
        """Test that the page scraper handles an exception when fetching HTML."""
        # Arrange
        initial_product = Product(title="Initial Title", price=100, url="http://test.com/1", in_stock=True)
        self.mock_session.get.side_effect = requests.exceptions.RequestException("Page is down")
        scraper = RutenProductPageAPIScraper(session=self.mock_session)

        # Act
        updated_products, stats = scraper.scrape([initial_product], {})

        # Assert
        self.assertEqual(len(updated_products), 1)
        self.assertFalse(updated_products[0].in_stock) # Should be marked as out of stock
        self.assertEqual(len(stats['failed_to_scrape']), 1)

    def test_page_scraper_price_api_failure(self):
        """Test that the page scraper handles a failure in the price API gracefully."""
        # Arrange
        initial_product = Product(title="Initial Title", price=100, url="http://test.com/1", in_stock=True)

        mock_html_response = MagicMock()
        mock_html_response.text = '''
            <html><body>
            <script>RT.context = {
                "item": {
                    "no": "123",
                    "name": "Updated Title",
                    "remainNum": 5,
                    "directPrice": 12345
                },
                "seller": {"nick": "test_seller"}
            };</script>
            </body></html>
        '''
        # Price API fails
        self.mock_session.get.side_effect = [mock_html_response, requests.exceptions.RequestException("Price API down")]

        scraper = RutenProductPageAPIScraper(session=self.mock_session)

        # Act
        updated_products, stats = scraper.scrape([initial_product], {})

        # Assert
        self.assertEqual(len(updated_products), 1)
        # Price should fallback to the one from RT.context
        self.assertEqual(updated_products[0].price, 12345)
        self.assertTrue(updated_products[0].in_stock)

if __name__ == '__main__':
    unittest.main()
