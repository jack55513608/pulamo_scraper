# scrapers/base.py
from abc import ABC, abstractmethod
from typing import List, Optional
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
import logging
import time
import config
from models import Product

class BaseScraper(ABC):
    """Abstract base class for all scrapers."""

    def __init__(self, grid_url: str, browser: str = 'chrome'):
        self.grid_url = grid_url
        self.browser = browser
        self.driver = self._initialize_driver()
        if self.driver:
            self.driver.set_page_load_timeout(120)
            self.driver.implicitly_wait(10)

    def _initialize_driver(self) -> Optional[WebDriver]:
        """Sets up and connects to the Selenium Grid."""
        if self.browser == 'firefox':
            options = FirefoxOptions()
            options.set_preference('permissions.default.image', 2)
            options.set_preference('permissions.default.stylesheet', 2)
        else: # Default to chrome
            options = ChromeOptions()
            options.add_experimental_option("prefs", {
                "profile.managed_default_content_settings.images": 2,
                "profile.managed_default_content_settings.stylesheets": 2,
            })

        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )

        # Assuming MAX_RETRIES is defined in config.py
        for attempt in range(getattr(config, 'MAX_RETRIES', 10)):
            try:
                driver = webdriver.Remote(
                    command_executor=self.grid_url, options=options
                )

                # Block third-party tracking scripts for performance (Chrome-specific)
                if self.browser == 'chrome':
                    blocked_urls = [
                        "*://*.google-analytics.com/*",
                        "*://*.googletagmanager.com/*",
                        "*://*.facebook.net/*",
                        "*://*.fbcdn.net/*",
                        "*://*.connect.facebook.net/*",
                    ]
                    driver.execute_cdp_cmd("Network.setBlockedURLs", {"urls": blocked_urls})
                    driver.execute_cdp_cmd("Network.enable", {})

                return driver
            except Exception as e:
                if attempt < getattr(config, 'MAX_RETRIES', 10) - 1:
                    logging.warning(f"Connection failed. Retrying in {config.RETRY_DELAY_SECONDS} seconds...")
                    time.sleep(config.RETRY_DELAY_SECONDS)
                else:
                    logging.error(f"Could not connect to Selenium Grid after {getattr(config, 'MAX_RETRIES', 10)} attempts: {e}", exc_info=True)
                    return None
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logging.error(f"Error while closing WebDriver: {e}", exc_info=True)

    @abstractmethod
    def scrape(self, params: dict) -> List[Product]:
        """
        The main method to scrape a website.
        It should be implemented by each concrete scraper.
        """
        pass
