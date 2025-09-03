# tests/test_scrapers_base.py
import unittest
from unittest.mock import patch, MagicMock
import logging
import time
import config # Import config to mock its values
from abc import ABC, abstractmethod # Import ABC for the mock class

from scrapers.selenium_scraper import SeleniumScraper


class TestBaseScraper(unittest.TestCase):

    @patch('scrapers.selenium_scraper.webdriver.Remote')
    def test_initialize_driver_success_on_first_attempt(self, mock_remote):
        scraper = SeleniumScraper(grid_url="http://fake-url")
        self.assertIsNotNone(scraper.driver)
        mock_remote.assert_called_once()

    @patch('scrapers.selenium_scraper.webdriver.Remote')
    @patch('scrapers.selenium_scraper.time.sleep', return_value=None)
    def test_initialize_driver_success_after_retries(self, mock_sleep, mock_remote):
        mock_remote.side_effect = [Exception("Connection failed"), MagicMock()]
        scraper = SeleniumScraper(grid_url="http://fake-url")
        self.assertIsNotNone(scraper.driver)
        self.assertEqual(mock_remote.call_count, 2)

    @patch('scrapers.selenium_scraper.logging.error')
    @patch('scrapers.selenium_scraper.time.sleep', return_value=None)
    @patch('scrapers.selenium_scraper.webdriver.Remote')
    def test_initialize_driver_failure_after_max_retries(self, mock_remote, mock_sleep, mock_log_error):
        mock_remote.side_effect = Exception("Connection failed")
        scraper = SeleniumScraper(grid_url="http://fake-url")
        self.assertIsNone(scraper.driver)
        self.assertEqual(mock_remote.call_count, 10)
        # Check that the error was logged
        mock_log_error.assert_called_once()
        self.assertIn("Could not connect to Selenium Grid", mock_log_error.call_args[0][0])

    @patch('scrapers.selenium_scraper.webdriver.Remote')
    @patch('scrapers.selenium_scraper.FirefoxOptions')
    def test_initialize_driver_uses_firefox_options(self, mock_firefox_options, mock_remote):
        SeleniumScraper(grid_url="http://fake-url", browser='firefox')
        mock_firefox_options.assert_called_once()

    @patch('scrapers.selenium_scraper.webdriver.Remote')
    @patch('scrapers.selenium_scraper.ChromeOptions')
    def test_firefox_preferences_are_set(self, mock_chrome_options, mock_remote):
        mock_driver = MagicMock()
        mock_remote.return_value = mock_driver
        mock_options = MagicMock()
        mock_chrome_options.return_value = mock_options

        scraper = SeleniumScraper(grid_url="http://fake-url", browser='chrome')
        scraper.close()

if __name__ == '__main__':
    unittest.main()
