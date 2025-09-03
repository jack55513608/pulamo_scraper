# tests/test_ruten_functional.py
import pytest
from scrapers.ruten import RutenSearchScraper
import config

@pytest.mark.docker
def test_ruten_search_scraper_finds_all_products():
    """Functional test to ensure the Ruten search scraper finds all products."""
    scraper = RutenSearchScraper(grid_url=config.SELENIUM_GRID_URL, browser='firefox')
    params = {
        'search_url': 'https://www.ruten.com.tw/find/?q=mgsd+%E5%91%BD%E9%81%8B&prc.now=900-1800'
    }
    with scraper:
        products = scraper.scrape(params)
        assert len(products) >= 14
