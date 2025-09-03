# tests/test_ruten_unit.py
import pytest
from unittest.mock import patch
from bs4 import BeautifulSoup
from models import Product
from scrapers.ruten import RutenSearchScraper, RutenProductPageScraper
from checkers.keyword import KeywordChecker
from checkers.stock import StockChecker, PaymentMethod

# --- Test Data ---
@pytest.fixture
def ruten_search_scraper():
    # We don't need a real grid_url for unit testing parsing logic
    with patch('scrapers.base.BaseScraper._initialize_driver', return_value=None):
        return RutenSearchScraper(grid_url="", browser='chrome')

@pytest.fixture
def ruten_page_scraper():
    with patch('scrapers.base.BaseScraper._initialize_driver', return_value=None):
        return RutenProductPageScraper(grid_url="", browser='chrome')

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
def sample_product_page_with_payment_methods_html():
    return '''
    <table>
        <tr>
            <td class="title">付款方式：</td>
            <td>
                <ul class="detail-list">
                    <li class="PW_SEVEN_COD">7-11取貨付款</li>
                    <li class="PW_FAMILY_COD">全家取貨付款</li>
                    <li>面交取貨付款</li>
                </ul>
            </td>
        </tr>
    </table>
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
        Product(title="Product A", price=100, url="", in_stock=False, seller="seller_A"),
        Product(title="Product B", price=200, url="", in_stock=True, seller="seller_B"),
        Product(title="Product C", price=300, url="", in_stock=True, seller="blacklisted_seller"),
        Product(title="Product D", price=50, url="", in_stock=True, seller="seller_D"),
    ]

@pytest.fixture
def sample_products_for_payment_check():
    return [
        Product(title="Product A", price=100, in_stock=True, seller="seller_A", url="http://example.com/a", payment_methods=['PW_SEVEN_COD']),
        Product(title="Product B", price=200, in_stock=True, seller="seller_B", url="http://example.com/b", payment_methods=['PW_FAMILY_COD']),
        Product(title="Product C", price=300, in_stock=True, seller="seller_C", url="http://example.com/c", payment_methods=['PChomePay支付連 信用卡']),
        Product(title="Product D", price=400, in_stock=True, seller="seller_D", url="http://example.com/d", payment_methods=['PW_SEVEN_COD', 'PChomePay支付連 信用卡']),
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

def test_parse_payment_methods(ruten_page_scraper, sample_product_page_with_payment_methods_html):
    """Test parsing payment methods from product page."""
    soup = BeautifulSoup(sample_product_page_with_payment_methods_html, 'html.parser')
    payment_methods = ruten_page_scraper._parse_payment_methods(soup)
    assert len(payment_methods) == 3
    assert "PW_SEVEN_COD" in payment_methods
    assert "PW_FAMILY_COD" in payment_methods
    assert "面交取貨付款" in payment_methods

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

def test_stock_checker_payment_method_rejection(sample_products_for_payment_check):
    """Test that the checker rejects products with unacceptable payment methods."""
    checker = StockChecker()
    params = {
        "acceptable_payment_methods": [PaymentMethod.SEVEN_ELEVEN_COD]
    }
    found_products, stats = checker.check(sample_products_for_payment_check, params)
    assert len(found_products) == 2
    assert "Product A" in [p.title for p in found_products]
    assert "Product D" in [p.title for p in found_products]
    assert len(stats["rejected_due_to_payment_method"]) == 2
    assert "Product B" in stats["rejected_due_to_payment_method"]
    assert "Product C" in stats["rejected_due_to_payment_method"]

def test_stock_checker_payment_method_acceptance(sample_products_for_payment_check):
    """Test that the checker accepts products with acceptable payment methods."""
    checker = StockChecker()
    params = {
        "acceptable_payment_methods": [PaymentMethod.SEVEN_ELEVEN_COD, PaymentMethod.FAMILY_MART_COD]
    }
    found_products, stats = checker.check(sample_products_for_payment_check, params)
    assert len(found_products) == 3
    assert "Product A" in [p.title for p in found_products]
    assert "Product B" in [p.title for p in found_products]
    assert "Product D" in [p.title for p in found_products]
    assert len(stats["rejected_due_to_payment_method"]) == 1
    assert "Product C" in stats["rejected_due_to_payment_method"]

def test_stock_checker_no_payment_method_filter(sample_products_for_payment_check):
    """Test that the checker does not filter by payment method if no acceptable payment methods are provided."""
    checker = StockChecker()
    params = {}
    found_products, stats = checker.check(sample_products_for_payment_check, params)
    assert len(found_products) == 4
    assert len(stats["rejected_due_to_payment_method"]) == 0
