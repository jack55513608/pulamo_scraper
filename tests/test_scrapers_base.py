# tests/test_scrapers_base.py
import unittest
from unittest.mock import patch, MagicMock
import logging
import time
import config # Import config to mock its values
from abc import ABC, abstractmethod # Import ABC for the mock class

from scrapers.base import BaseScraper

# Create a concrete mock class for testing BaseScraper
class MockConcreteScraper(BaseScraper):
    def scrape(self, params: dict):
        # This method is not tested here, just needs to be implemented to allow instantiation
        pass

class TestBaseScraper(unittest.TestCase):

    def setUp(self):
        # Store original config values to restore them later
        self._original_max_retries = getattr(config, 'MAX_RETRIES', 10)
        self._original_retry_delay_seconds = getattr(config, 'RETRY_DELAY_SECONDS', 5)

        # Set mock config values for testing retries
        config.MAX_RETRIES = 3
        config.RETRY_DELAY_SECONDS = 0.01 # Small delay for faster tests

    def tearDown(self):
        # Restore original config values
        config.MAX_RETRIES = self._original_max_retries
        config.RETRY_DELAY_SECONDS = self._original_retry_delay_seconds

    @patch('scrapers.base.webdriver.Remote')
    @patch('scrapers.base.FirefoxOptions')
    @patch('scrapers.base.ChromeOptions')
    def test_initialize_driver_success_on_first_attempt(self, MockChromeOptions, MockFirefoxOptions, MockRemote):
        MockRemote.return_value = MagicMock()
        
        scraper = MockConcreteScraper(grid_url="http://test_grid:4444/wd/hub", browser='chrome')
        
        MockRemote.assert_called_once()
        MockChromeOptions.assert_called_once()
        MockFirefoxOptions.assert_not_called()
        self.assertIsNotNone(scraper.driver)

    @patch('scrapers.base.webdriver.Remote')
    @patch('scrapers.base.FirefoxOptions')
    @patch('scrapers.base.ChromeOptions')
    def test_initialize_driver_uses_firefox_options(self, MockChromeOptions, MockFirefoxOptions, MockRemote):
        MockRemote.return_value = MagicMock()

        scraper = MockConcreteScraper(grid_url="http://test_grid:4444/wd/hub", browser='firefox')

        MockRemote.assert_called_once()
        MockFirefoxOptions.assert_called_once()
        MockChromeOptions.assert_not_called()
        self.assertIsNotNone(scraper.driver)

    @patch('scrapers.base.webdriver.Remote')
    @patch('scrapers.base.FirefoxOptions')
    @patch('scrapers.base.ChromeOptions')
    def test_firefox_preferences_are_set(self, MockChromeOptions, MockFirefoxOptions, MockRemote):
        mock_options_instance = MagicMock()
        MockFirefoxOptions.return_value = mock_options_instance
        MockRemote.return_value = MagicMock()

        scraper = MockConcreteScraper(grid_url="http://test_grid:4444/wd/hub", browser='firefox')

        mock_options_instance.set_preference.assert_any_call('permissions.default.image', 2)
        mock_options_instance.set_preference.assert_any_call('permissions.default.stylesheet', 2)

    @patch('scrapers.base.webdriver.Remote', side_effect=Exception("Connection failed"))
    @patch('scrapers.base.FirefoxOptions')
    @patch('scrapers.base.ChromeOptions')
    def test_initialize_driver_failure_after_max_retries(self, MockChromeOptions, MockFirefoxOptions, MockRemote):
        with self.assertLogs('root', level='ERROR') as cm:
            scraper = MockConcreteScraper(grid_url="http://test_grid:4444/wd/hub", browser='chrome')
            
            self.assertEqual(MockRemote.call_count, config.MAX_RETRIES)
            self.assertIsNone(scraper.driver)
            self.assertIn("Could not connect to Selenium Grid after 3 attempts", cm.output[0])

    @patch('scrapers.base.webdriver.Remote')
    @patch('scrapers.base.FirefoxOptions')
    @patch('scrapers.base.ChromeOptions')
    def test_initialize_driver_success_after_retries(self, MockChromeOptions, MockFirefoxOptions, MockRemote):
        MockRemote.side_effect = [Exception("Fail"), Exception("Fail"), MagicMock()]
        
        with self.assertLogs('root', level='WARNING') as cm:
            scraper = MockConcreteScraper(grid_url="http://test_grid:4444/wd/hub", browser='chrome')
            
            self.assertEqual(MockRemote.call_count, 3)
            self.assertIsNotNone(scraper.driver)
            self.assertEqual(len(cm.output), 2)

if __name__ == '__main__':
    unittest.main()
