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
def sample_product_page_with_seller_html():
    return """
    <html><body>
        <div data-v-1e217fce>
            <a data-v-1e217fce href="https://www.ruten.com.tw/store/good_seller_id"></a>
        </div>
    </body></html>
    """

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
        Product(title="Product A", price=100, url="", in_stock=False, seller="seller_A"),
        Product(title="Product B", price=200, url="", in_stock=True, seller="seller_B"),
        Product(title="Product C", price=300, url="", in_stock=True, seller="blacklisted_seller"),
        Product(title="Product D", price=50, url="", in_stock=True, seller="seller_D"),
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

def test_parse_seller_id(ruten_page_scraper, sample_product_page_with_seller_html):
    """Test parsing seller ID from product page."""
    soup = BeautifulSoup(sample_product_page_with_seller_html, 'html.parser')
    seller_id = ruten_page_scraper._parse_seller_id(soup)
    assert seller_id == "good_seller_id"

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

def test_stock_checker_found_all_valid(sample_products_for_stock_check):
    """Test the stock checker finds all available products when no filters are applied."""
    checker = StockChecker()
    products, stats = checker.check(sample_products_for_stock_check, {})
    
    assert len(products) == 3
    found_titles = [p.title for p in products]
    assert "Product B" in found_titles
    assert "Product C" in found_titles
    assert "Product D" in found_titles
    assert len(stats['out_of_stock_titles']) == 1

def test_stock_checker_not_found(sample_products_for_stock_check):
    """Test the stock checker returns an empty list when no product is available."""
    checker = StockChecker()
    all_out_of_stock = [p for p in sample_products_for_stock_check if not p.in_stock]
    products, _ = checker.check(all_out_of_stock, {})
    assert products == []

def test_stock_checker_price_rejection(sample_products_for_stock_check):
    """Test the stock checker rejects items if their price is too high."""
    checker = StockChecker()
    params = {'max_price': 150}
    products, stats = checker.check(sample_products_for_stock_check, params)
    
    # Only Product D (price 50) should be found.
    assert len(products) == 1
    assert products[0].title == "Product D"
    
    # Both B and C should be rejected due to price.
    assert len(stats['rejected_due_to_price']) == 2
    assert "Product B" in stats['rejected_due_to_price']
    assert "Product C" in stats['rejected_due_to_price']

def test_stock_checker_seller_rejection(sample_products_for_stock_check):
    """Test the stock checker rejects an item if the seller is blacklisted."""
    checker = StockChecker()
    params = {'blacklisted_sellers': ['blacklisted_seller']}
    # We expect Product B and D to be found, as Product C's seller is blacklisted
    products, stats = checker.check(sample_products_for_stock_check, params)
    
    assert len(products) == 2
    found_titles = [p.title for p in products]
    assert "Product B" in found_titles
    assert "Product D" in found_titles

    assert len(stats['rejected_due_to_seller']) == 1
    assert stats['rejected_due_to_seller'][0] == "Product C"
