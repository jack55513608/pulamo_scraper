# factory.py
from typing import Type, Tuple, Dict, Any

# Import all concrete classes
from scrapers.pulamo import PulamoScraper
from checkers.product import ProductChecker
from notifiers.telegram import TelegramNotifier

# Import new Ruten components
from scrapers.ruten import RutenSearchScraper, RutenProductPageScraper
from scrapers.ruten_api import RutenProductPageAPIScraper, RutenSearchAPIScraper
from checkers.keyword import KeywordChecker
from checkers.stock import StockChecker

from scrapers.base import BaseScraper
from checkers.base import BaseChecker
from notifiers.base import BaseNotifier

# --- Registry of available classes ---
SCRAPERS = {
    'pulamo.PulamoScraper': PulamoScraper,
    'ruten.RutenSearchScraper': RutenSearchScraper,
    'ruten_api.RutenSearchAPIScraper': RutenSearchAPIScraper, # <--- 新增的 API Scraper
    'ruten.RutenProductPageScraper': RutenProductPageScraper,
    'ruten_api.RutenProductPageAPIScraper': RutenProductPageAPIScraper,
}

CHECKERS = {
    'product.ProductChecker': ProductChecker,
    'keyword.KeywordChecker': KeywordChecker,
    'stock.StockChecker': StockChecker,
}

NOTIFIERS = {
    'telegram.TelegramNotifier': TelegramNotifier,
}

# --- Factory Functions ---
def get_scraper(name: str, *args, **kwargs) -> BaseScraper:
    """Factory function to get a scraper instance."""
    scraper_class = SCRAPERS.get(name)
    if not scraper_class:
        raise ValueError(f"未知的 Scraper: {name}")
    return scraper_class(*args, **kwargs)

def get_checker(name: str, *args, **kwargs) -> BaseChecker:
    """Factory function to get a checker instance."""
    checker_class = CHECKERS.get(name)
    if not checker_class:
        raise ValueError(f"未知的 Checker: {name}")
    return checker_class(*args, **kwargs)

def get_notifier(name: str, *args, **kwargs) -> BaseNotifier:
    """Factory function to get a notifier instance."""
    notifier_class = NOTIFIERS.get(name)
    if not notifier_class:
        raise ValueError(f"未知的 Notifier: {name}")
    return notifier_class(*args, **kwargs)
