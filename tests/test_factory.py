# tests/test_factory.py
import unittest
from factory import get_scraper, get_checker, get_notifier
from scrapers.pulamo import PulamoScraper
from checkers.product import ProductChecker
from notifiers.telegram import TelegramNotifier

class TestFactory(unittest.TestCase):

    def test_get_scraper_returns_correct_class(self):
        scraper_instance = get_scraper('pulamo.PulamoScraper', grid_url="http://test_grid")
        self.assertIsInstance(scraper_instance, PulamoScraper)

    def test_get_scraper_raises_error_for_unknown_name(self):
        with self.assertRaises(ValueError):
            get_scraper('unknown.UnknownScraper', grid_url="http://test_grid")

    def test_get_checker_returns_correct_class(self):
        checker_instance = get_checker('product.ProductChecker')
        self.assertIsInstance(checker_instance, ProductChecker)

    def test_get_checker_raises_error_for_unknown_name(self):
        with self.assertRaises(ValueError):
            get_checker('unknown.UnknownChecker')

    def test_get_notifier_returns_correct_class(self):
        # Mock the Bot to avoid actual Telegram API calls and token issues
        with unittest.mock.patch('notifiers.telegram.Bot'):
            notifier_instance = get_notifier('telegram.TelegramNotifier')
            self.assertIsInstance(notifier_instance, TelegramNotifier)

    def test_get_notifier_raises_error_for_unknown_name(self):
        with self.assertRaises(ValueError):
            get_notifier('unknown.UnknownNotifier')

if __name__ == '__main__':
    unittest.main()
