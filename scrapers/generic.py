# scrapers/generic.py
from typing import List
from models import Product
from scrapers.base import BaseScraper

class GenericScraper(BaseScraper):
    """A generic scraper to simply get a webdriver session."""

    def scrape(self, params: dict) -> List[Product]:
        """
        This method is required by the abstract base class, but we only need the
        driver instance from BaseScraper, so it returns an empty list.
        """
        return []
