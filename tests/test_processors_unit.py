import asyncio
import unittest
from unittest.mock import MagicMock, AsyncMock

from processors.ruten import process_ruten_task
from models import Product

class TestRutenProcessor(unittest.IsolatedAsyncioTestCase):

    async def test_process_ruten_task_happy_path(self):
        """Test the full, successful execution flow of a Ruten task."""
        # Arrange
        mock_search_scraper = MagicMock()
        mock_search_scraper.scrape.return_value = [Product(title="found_product", price=100, url="http://a.com", in_stock=True)]

        mock_keyword_checker = MagicMock()
        mock_keyword_checker.check.return_value = ([Product(title="filtered_product", price=120, url="http://b.com", in_stock=True)], {'rejected_keyword_mismatch': [], 'rejected_excluded_keyword': []})

        mock_page_scraper = MagicMock()
        mock_page_scraper.scrape.return_value = ([Product(title="detailed_product", price=150, url="http://c.com", in_stock=True, seller='good_seller')], {'failed_to_scrape': []})

        mock_stock_checker = MagicMock()
        mock_stock_checker.check.return_value = ([Product(title="final_product", price=180, url="http://d.com", in_stock=True)], {'out_of_stock_titles': [], 'rejected_due_to_price': [], 'rejected_due_to_seller': [], 'rejected_due_to_payment_method': []})

        mock_notifier = AsyncMock()

        # Mock factory functions
        mock_get_scraper = MagicMock()
        mock_get_scraper.side_effect = [mock_search_scraper, mock_page_scraper]
        mock_get_checker = MagicMock()
        mock_get_checker.side_effect = [mock_keyword_checker, mock_stock_checker]
        mock_get_notifier = MagicMock(return_value=mock_notifier)

        task_config = {
            'name': 'Test Ruten Task',
            'search_scraper': '...',
            'search_scraper_params': {},
            'keyword_checker': '...',
            'keyword_checker_params': {},
            'page_scraper': '...',
            'stock_checker': '...',
            'stock_checker_params': {},
            'notifier': '...',
            'notifier_params': {}
        }

        # Act
        await process_ruten_task(
            task_config,
            mock_get_scraper,
            mock_get_checker,
            mock_get_notifier
        )

        # Assert
        mock_search_scraper.scrape.assert_called_once()
        mock_keyword_checker.check.assert_called_once()
        mock_page_scraper.scrape.assert_called_once()
        mock_stock_checker.check.assert_called_once()
        mock_notifier.notify.assert_called_once()

if __name__ == '__main__':
    unittest.main()
