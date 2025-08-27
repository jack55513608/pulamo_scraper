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

    @patch('scrapers.base.webdriver.Remote') # Patch the Remote constructor where it's used
    @patch('scrapers.base.webdriver.ChromeOptions') # Patch the ChromeOptions class where it's used
    def test_initialize_driver_success_on_first_attempt(self, MockChromeOptions, MockRemote):
        MockRemote.return_value = MagicMock() # Mock Remote to return a WebDriver instance
        
        scraper = MockConcreteScraper(grid_url="http://test_grid:4444/wd/hub") # Use mock concrete class
        
        MockRemote.assert_called_once() # Should try to connect once
        self.assertIsNotNone(scraper.driver) # Driver should be initialized

    @patch('scrapers.base.webdriver.Remote', side_effect=Exception("Connection failed"))
    @patch('scrapers.base.webdriver.ChromeOptions')
    def test_initialize_driver_failure_after_max_retries(self, MockChromeOptions, MockRemote):
        # Suppress logging output for expected errors during test
        with self.assertLogs('root', level='ERROR') as cm:
            scraper = MockConcreteScraper(grid_url="http://test_grid:4444/wd/hub") # Use mock concrete class
            
            self.assertEqual(MockRemote.call_count, config.MAX_RETRIES) # Should try MAX_RETRIES times
            self.assertIsNone(scraper.driver) # Driver should not be initialized
            self.assertIn("Could not connect to Selenium Grid after 3 attempts", cm.output[0])

    @patch('scrapers.base.webdriver.Remote') # Patch the Remote constructor
    @patch('scrapers.base.webdriver.ChromeOptions')
    def test_initialize_driver_success_after_retries(self, MockChromeOptions, MockRemote):
        # Set side_effect here, using a MagicMock for the WebDriver instance
        MockRemote.side_effect = [Exception("Fail"), Exception("Fail"), MagicMock()]
        
        # Suppress logging output for expected warnings during test
        with self.assertLogs('root', level='WARNING') as cm:
            scraper = MockConcreteScraper(grid_url="http://test_grid:4444/wd/hub") # Use mock concrete class
            
            self.assertEqual(MockRemote.call_count, 3) # Should try 3 times (2 fails + 1 success)
            self.assertIsNotNone(scraper.driver) # Driver should be initialized
            self.assertEqual(len(cm.output), 2) # Should log 2 warnings for failed attempts

if __name__ == '__main__':
    unittest.main()
