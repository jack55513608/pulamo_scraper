# tests/test_ruten_unit.py
import pytest
from bs4 import BeautifulSoup
from models import Product
from scrapers.ruten import RutenSearchScraper, RutenProductPageScraper
from checkers.keyword import KeywordChecker
from checkers.stock import StockChecker

# --- Test Data ---
@pytest.fixture
def ruten_search_scraper():
    # We don't need a real grid_url for unit testing parsing logic
    return RutenSearchScraper(grid_url="")

@pytest.fixture
def ruten_page_scraper():
    return RutenProductPageScraper(grid_url="")

@pytest.fixture
def sample_product_item_html():
    return """
    <div class="product-item">
        <div class="rt-product-card">
            <a href="https://www.ruten.com.tw/item/show?22535685934686" title="【高雄冠軍】26年2月預購 萬代 組裝模型 MGSD 鋼彈SEED 命運鋼彈" class="rt-product-card-name-wrap">
                <p class="rt-product-card-name">
                    <svg></svg>
                    【高雄冠軍】26年2月預購 萬代 組裝模型 MGSD 鋼彈SEED 命運鋼彈
                </p>
            </a>
            <div class="rt-product-card-price-wrap">
                <div class="price-range-container">
                    <span class="rt-text-price rt-text-bold text-price-dollar">1,350</span>
                </div>
            </div>
        </div>
    </div>
    """

@pytest.fixture
def sample_product_page_html_instock():
    return '''
    <html><head>
    <meta name="description" content="直購價: 1260 - 1260, 已賣數量: 120, 庫存: 10, 物品狀況: 全新">
    </head></html>
    '''

@pytest.fixture
def sample_product_page_html_outofstock():
    return '''
    <html><head>
    <meta name="description" content="直購價: 1260 - 1260, 已賣數量: 120, 庫存: 0, 物品狀況: 全新">
    </head></html>
    '''

@pytest.fixture
def sample_products_for_filtering():
    return [
        Product(title="MGSD 命運鋼彈", price=1300, url="", in_stock=False),
        Product(title="[預購] MGSD 命運鋼彈", price=1300, url="", in_stock=False),
        Product(title="MG 命運鋼彈", price=1000, url="", in_stock=False), # Missing 'MGSD'
        Product(title="MGSD 自由鋼彈", price=1200, url="", in_stock=False), # Wrong gundam
        Product(title="MGSD 命運鋼彈 PS5遊戲片", price=1800, url="", in_stock=True), # Excluded keyword
    ]

@pytest.fixture
def sample_products_for_stock_check():
    return [
        Product(title="Product A", price=100, url="", in_stock=False),
        Product(title="Product B", price=200, url="", in_stock=True), # First in stock
        Product(title="Product C", price=300, url="", in_stock=True), # Should not be returned
    ]

# --- Unit Tests ---

def test_parse_product_item_successfully(ruten_search_scraper, sample_product_item_html):
    """ Test that a single product item is parsed correctly."""
    soup = BeautifulSoup(sample_product_item_html, 'html.parser')
    item = soup.find('div', class_='product-item')
    product = ruten_search_scraper._parse_product_item(item)

    assert product is not None
    assert product.title == "【高雄冠軍】26年2月預購 萬代 組裝模型 MGSD 鋼彈SEED 命運鋼彈"
    assert product.url == "https://www.ruten.com.tw/item/show?22535685934686"
    assert product.price == 1350
    assert product.in_stock is False # Default value

def test_parse_stock_status_in_stock(ruten_page_scraper, sample_product_page_html_instock):
    """Test parsing stock status when item is in stock."""
    soup = BeautifulSoup(sample_product_page_html_instock, 'html.parser')
    in_stock = ruten_page_scraper._parse_stock_status(soup)
    assert in_stock is True

def test_parse_stock_status_out_of_stock(ruten_page_scraper, sample_product_page_html_outofstock):
    """Test parsing stock status when item is out of stock."""
    soup = BeautifulSoup(sample_product_page_html_outofstock, 'html.parser')
    in_stock = ruten_page_scraper._parse_stock_status(soup)
    assert in_stock is False

def test_keyword_checker(sample_products_for_filtering):
    """Test the keyword checker filters correctly."""
    checker = KeywordChecker()
    params = {
        'keywords': ['mgsd', '命運鋼彈'],
        'exclude_keywords': ['ps5']
    }
    filtered_products, stats = checker.check(sample_products_for_filtering, params)
    assert len(filtered_products) == 2
    assert filtered_products[0].title == "MGSD 命運鋼彈"
    assert filtered_products[1].title == "[預購] MGSD 命運鋼彈"

def test_stock_checker_found(sample_products_for_stock_check):
    """Test the stock checker finds the first available product."""
    checker = StockChecker()
    product, stats = checker.check(sample_products_for_stock_check, {})
    assert product is not None
    assert product.title == "Product B"

def test_stock_checker_not_found(sample_products_for_stock_check):
    """Test the stock checker returns None when no product is available."""
    checker = StockChecker()
    all_out_of_stock = [p for p in sample_products_for_stock_check if not p.in_stock]
    product, _ = checker.check(all_out_of_stock, {})
    assert product is None

def test_stock_checker_price_rejection(sample_products_for_stock_check):
    """Test the stock checker rejects items if their price is too high."""
    checker = StockChecker()
    params = {'max_price': 150}
    product, stats = checker.check(sample_products_for_stock_check, params)
    
    # All in-stock products (B and C) are over the max_price, so none should be found.
    assert product is None 
    
    # Both B and C should be rejected due to price.
    assert len(stats['rejected_due_to_price']) == 2
    assert "Product B" in stats['rejected_due_to_price']
    assert "Product C" in stats['rejected_due_to_price']
