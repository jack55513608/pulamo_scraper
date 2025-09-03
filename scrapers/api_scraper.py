# scrapers/api_scraper.py
from scrapers.base import BaseScraper

class APIScraper(BaseScraper):
    """Base class for scrapers that use APIs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
