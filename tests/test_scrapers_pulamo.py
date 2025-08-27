# tests/test_scrapers_pulamo.py
import pytest
import logging
import config
from scrapers.pulamo import PulamoScraper
from models import Product # To ensure Product is correctly imported and used

# Use pytest-asyncio for async tests
@pytest.mark.asyncio
@pytest.mark.docker # Add this marker
async def test_pulamo_scraper_functional():
    """
    Functional test for PulamoScraper to verify web scraping and element extraction.
    """
    logging.info("--- 開始功能測試: Pulamo 爬蟲 ---")

    try:
        # Instantiate PulamoScraper
        # This will connect to the Selenium Grid defined in config.SELENIUM_GRID_URL
        scraper = PulamoScraper(config.SELENIUM_GRID_URL)
        with scraper:
            # Use the search URL for Wing Gundam as an example
            params = {'search_url': 'https://www.pulamo.com.tw/products?search=MGSD'}
            products = scraper.scrape(params)

            # Assertions to verify the scraper's functionality
            assert products is not None, "Scraper should return a list of products."
            assert len(products) > 0, "Should have scraped at least one product."

            # Optional: Further assertions on specific product data if known and stable
            # For example, check if a specific product title or price is present
            # This might be brittle if the website changes frequently.
            # For now, just check if the basic structure is correct.
            for product in products:
                assert isinstance(product, Product)
                assert isinstance(product.title, str) and len(product.title) > 0
                assert isinstance(product.price, int) and product.price >= 0
                assert isinstance(product.in_stock, bool)
                assert isinstance(product.url, str) and len(product.url) > 0
                logging.info(f"  - 驗證商品: {product.title}")

    except Exception as e:
        logging.error(f"Pulamo 爬蟲功能測試失敗: {e}", exc_info=True)
        pytest.fail(f"Pulamo 爬蟲功能測試中發生未預期的錯誤: {e}")
    finally:
        logging.info("--- Pulamo 爬蟲功能測試結束 ---")