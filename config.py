# config.py
import os
from checkers.stock import PaymentMethod

# --- General Settings ---
SELENIUM_GRID_URL = "http://selenium:4444/wd/hub"
RETRY_DELAY_SECONDS = 5
CHECK_INTERVAL_SECONDS = 30
MAX_RETRIES = 10

# --- Telegram Settings ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Blacklist ---
BLACKLISTED_SELLERS = [
    'lana20110406',
]

# --- Task Definitions ---
TASKS = [
    {
        'name': 'Pulamo - Wing Gundam',
        'scraper': 'pulamo.PulamoScraper',
        'scraper_params': {
            'search_url': 'https://www.pulamo.com.tw/products?search=MGSD',
        },
        'checker': 'product.ProductChecker',
        'checker_params': {
            'name': '飛翼鋼彈',
            'store_name': 'Pulamo',
            'keywords': ['MGSD', '飛翼鋼彈'],
            'exclude_keywords': ['水貼', '遮蓋膠帶'],
        },
        'notifier': 'telegram.TelegramNotifier',
        'notifier_params': {
            'name': '飛翼鋼彈',
            'store_name': 'Pulamo',
        },
    },
    {
        'name': 'Pulamo - Destiny Gundam',
        'scraper': 'pulamo.PulamoScraper',
        'scraper_params': {
            'search_url': 'https://www.pulamo.com.tw/products?search=MGSD',
        },
        'checker': 'product.ProductChecker',
        'checker_params': {
            'name': '命運鋼彈',
            'store_name': 'Pulamo',
            'keywords': ['命運鋼彈'],
            'exclude_keywords': [],
            'min_price': 500,
        },
        'notifier': 'telegram.TelegramNotifier',
        'notifier_params': {
            'name': '命運鋼彈',
            'store_name': 'Pulamo',
        },
    },
    {
        'name': 'Ruten - Destiny Gundam',
        'type': 'ruten',
        'search_scraper': 'ruten.RutenSearchScraper',
        'search_scraper_params': {
            'search_url': 'https://www.ruten.com.tw/find/?q=mgsd+%E5%91%BD%E9%81%8B&prc.now=900-1400',
        },
        'keyword_checker': 'keyword.KeywordChecker',
        'keyword_checker_params': {
            'keywords': ['mgsd', '命運鋼彈'],
            'exclude_keywords': ['魔物語', 'ps5', 'ns2', '非'] # Exclude game pre-orders
        },
        'page_scraper': 'ruten.RutenProductPageScraper',
        'stock_checker': 'stock.StockChecker',
        'stock_checker_params': {
            'max_price': 2000,
            'blacklisted_sellers': BLACKLISTED_SELLERS,
            'acceptable_payment_methods': [
                PaymentMethod.SEVEN_ELEVEN_COD,
                PaymentMethod.FAMILY_MART_COD,
                PaymentMethod.HILIFE_COD,
            ],
        },
        'notifier': 'telegram.TelegramNotifier',
        'notifier_params': {
            'name': 'MGSD 命運鋼彈',
            'store_name': '露天拍賣',
        },
    },
]

# --- Test Task Definitions ---
TEST_TASKS = [
    {
        'name': 'Pulamo - Barbatos Gundam (Test)',
        'type': 'simple', # Add type for test tasks
        'scraper': 'pulamo.PulamoScraper',
        'scraper_params': {
            'search_url': 'https://www.pulamo.com.tw/products?search=MGSD',
        },
        'checker': 'product.ProductChecker',
        'checker_params': {
            'name': '獵魔鋼彈',
            'store_name': 'Pulamo',
            'keywords': ['MGSD', '獵魔'],
            'exclude_keywords': ['擴充', '水貼'],
        },
        'notifier': 'telegram.TelegramNotifier',
        'notifier_params': {
            'name': '獵魔鋼彈 (測試案例)',
            'store_name': 'Pulamo',
        },
    }
]
