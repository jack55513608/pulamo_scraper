# scrapers/base.py
from abc import ABC, abstractmethod
from typing import List
from models import Product

class BaseScraper(ABC):
    """Abstract base class for all scrapers."""

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Close any resources used by the scraper."""
        pass

    @abstractmethod
    def scrape(self, params: dict) -> List[Product]:
        """
        The main method to scrape a website.
        It should be implemented by each concrete scraper.
        """
        pass