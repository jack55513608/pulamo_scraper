import asyncio
import unittest
from unittest.mock import MagicMock, AsyncMock, patch

from processors.pulamo import process_pulamo_task
from processors.ruten import process_ruten_task, notification_manager
from models import Product

# A sample task config that can be reused across tests
SAMPLE_TASK_CONFIG = {
    'name': 'Test Task',
    'type': 'pulamo', # Default type
    'browser': 'chrome',
    'scraper': 'scrapers.pulamo.PulamoScraper',
    'scraper_params': {},
    'checker': 'checkers.product.ProductChecker',
    'checker_params': {},
    'notifier': 'notifiers.telegram.TelegramNotifier',
    'notifier_params': {},
    # Ruten-specific keys
    'search_scraper': 'scrapers.ruten_api.RutenSearchAPIScraper',
    'search_scraper_params': {},
    'keyword_checker': 'checkers.keyword.KeywordChecker',
    'keyword_checker_params': {},
    'page_scraper': 'scrapers.ruten_api.RutenProductPageAPIScraper',
    'stock_checker': 'checkers.stock.StockChecker',
    'stock_checker_params': {},
}

class TestPulamoProcessor(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        """Set up a standard mock environment for Pulamo processor tests."""
        self.mock_scraper = MagicMock()
        self.mock_checker = MagicMock()
        self.mock_notifier = AsyncMock()

        self.mock_get_scraper = MagicMock(return_value=self.mock_scraper)
        self.mock_get_checker = MagicMock(return_value=self.mock_checker)
        self.mock_get_notifier = MagicMock(return_value=self.mock_notifier)

    async def test_happy_path(self):
        """Test the full, successful execution flow."""
        # Arrange
        self.mock_scraper.scrape.return_value = [Product(title="found", price=100, url="http://a.com", in_stock=True)]
        self.mock_checker.check.return_value = [Product(title="final", price=150, url="http://b.com", in_stock=True)]

        # Act
        await process_pulamo_task(SAMPLE_TASK_CONFIG, self.mock_get_scraper, self.mock_get_checker, self.mock_get_notifier)

        # Assert
        self.mock_scraper.scrape.assert_called_once()
        self.mock_checker.check.assert_called_once()
        self.mock_notifier.notify.assert_called_once()

    async def test_exits_early_if_scraper_finds_nothing(self):
        """Test that the process exits early if the scraper finds no products."""
        # Arrange
        self.mock_scraper.scrape.return_value = []  # No products found

        # Act
        await process_pulamo_task(SAMPLE_TASK_CONFIG, self.mock_get_scraper, self.mock_get_checker, self.mock_get_notifier)

        # Assert
        self.mock_scraper.scrape.assert_called_once()
        self.mock_checker.check.assert_not_called()
        self.mock_notifier.notify.assert_not_called()

    async def test_no_notification_if_checker_finds_nothing(self):
        """Test that the notifier is not called if the checker filters all products."""
        # Arrange
        self.mock_scraper.scrape.return_value = [Product(title="found", price=100, url="http://a.com", in_stock=True)]
        self.mock_checker.check.return_value = []  # Checker finds nothing

        # Act
        await process_pulamo_task(SAMPLE_TASK_CONFIG, self.mock_get_scraper, self.mock_get_checker, self.mock_get_notifier)

        # Assert
        self.mock_scraper.scrape.assert_called_once()
        self.mock_checker.check.assert_called_once()
        self.mock_notifier.notify.assert_not_called()

    @patch('processors.pulamo.logging')
    async def test_handles_component_instantiation_failure(self, mock_logging):
        """Test that exceptions during component creation are caught and logged."""
        # Arrange
        self.mock_get_scraper.side_effect = ValueError("Unknown Scraper")

        # Act
        await process_pulamo_task(SAMPLE_TASK_CONFIG, self.mock_get_scraper, self.mock_get_checker, self.mock_get_notifier)

        # Assert
        mock_logging.error.assert_called_once()
        self.assertIn("在處理任務 'Test Task' 時發生錯誤", mock_logging.error.call_args[0][0])


class TestRutenProcessor(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        """Set up a standard mock environment for Ruten processor tests."""
        notification_manager._last_notified.clear()

        self.mock_search_scraper = MagicMock()
        self.mock_keyword_checker = MagicMock()
        self.mock_page_scraper = MagicMock()
        self.mock_stock_checker = MagicMock()
        self.mock_notifier = AsyncMock()

        self.mock_get_scraper = MagicMock(side_effect=[self.mock_search_scraper, self.mock_page_scraper])
        self.mock_get_checker = MagicMock(side_effect=[self.mock_keyword_checker, self.mock_stock_checker])
        self.mock_get_notifier = MagicMock(return_value=self.mock_notifier)

    async def test_happy_path(self):
        """Test the full, successful execution flow of a Ruten task."""
        # Arrange
        self.mock_search_scraper.scrape.return_value = [Product(title="p1", price=100, url="http://a.com", in_stock=True)]
        self.mock_keyword_checker.check.return_value = ([Product(title="p2", price=120, url="http://b.com", in_stock=True)], {'rejected_keyword_mismatch': [], 'rejected_excluded_keyword': []})
        self.mock_page_scraper.scrape.return_value = ([Product(title="p3", price=150, url="http://c.com", in_stock=True)], {'failed_to_scrape': []})
        self.mock_stock_checker.check.return_value = ([Product(title="p4", price=180, url="http://d.com", in_stock=True)], {'out_of_stock_titles': []})

        # Act
        await process_ruten_task(SAMPLE_TASK_CONFIG, self.mock_get_scraper, self.mock_get_checker, self.mock_get_notifier)

        # Assert
        self.mock_search_scraper.scrape.assert_called_once()
        self.mock_keyword_checker.check.assert_called_once()
        self.mock_page_scraper.scrape.assert_called_once()
        self.mock_stock_checker.check.assert_called_once()
        self.mock_notifier.notify.assert_called_once()

    async def test_exits_early_if_no_search_results(self):
        """Test that the process exits early if the search scraper finds nothing."""
        # Arrange
        self.mock_search_scraper.scrape.return_value = []

        # Act
        await process_ruten_task(SAMPLE_TASK_CONFIG, self.mock_get_scraper, self.mock_get_checker, self.mock_get_notifier)

        # Assert
        self.mock_search_scraper.scrape.assert_called_once()
        self.mock_keyword_checker.check.assert_not_called()
        self.mock_page_scraper.scrape.assert_not_called()
        self.mock_stock_checker.check.assert_not_called()

    async def test_cooldown_prevents_notification(self):
        """Test that the notifier is not called if the product is on cooldown."""
        # Arrange
        product_url = "http://d.com/on-cooldown"
        notification_manager.record_notification(product_url)

        self.mock_search_scraper.scrape.return_value = [Product(title="p1", price=100, url="http://a.com", in_stock=True)]
        self.mock_keyword_checker.check.return_value = ([Product(title="p2", price=120, url="http://b.com", in_stock=True)], {'rejected_keyword_mismatch': [], 'rejected_excluded_keyword': []})
        self.mock_page_scraper.scrape.return_value = ([Product(title="p3", price=150, url="http://c.com", in_stock=True)], {'failed_to_scrape': []})
        self.mock_stock_checker.check.return_value = ([Product(title="final", price=180, url=product_url, in_stock=True)], {'out_of_stock_titles': []})

        # Act
        await process_ruten_task(SAMPLE_TASK_CONFIG, self.mock_get_scraper, self.mock_get_checker, self.mock_get_notifier)

        # Assert
        self.mock_stock_checker.check.assert_called_once()
        self.mock_notifier.notify.assert_not_called()

if __name__ == '__main__':
    unittest.main()
