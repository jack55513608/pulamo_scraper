# scrapers/base.py
from abc import ABC, abstractmethod
from typing import List, Optional
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options
import logging
import time
import config
from models import Product

class BaseScraper(ABC):
    """Abstract base class for all scrapers."""

    def __init__(self, grid_url: str):
        self.grid_url = grid_url
        self.driver = self._initialize_driver()
        if self.driver:
            self.driver.set_page_load_timeout(120)
            self.driver.implicitly_wait(10)

    def _initialize_driver(self) -> Optional[WebDriver]:
        """Sets up and connects to the Selenium Grid."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )

        # Assuming MAX_RETRIES is defined in config.py
        for attempt in range(getattr(config, 'MAX_RETRIES', 10)):
            try:
                driver = webdriver.Remote(
                    command_executor=self.grid_url, options=chrome_options
                )
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
