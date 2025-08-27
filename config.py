# config.py
import os

# --- General Settings ---
SELENIUM_GRID_URL = "http://selenium:4444/wd/hub"
RETRY_DELAY_SECONDS = 5
CHECK_INTERVAL_SECONDS = 30
MAX_RETRIES = 10

# --- Telegram Settings ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

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
]

# --- Test Task Definitions ---
TEST_TASKS = [
    {
        'name': 'Pulamo - Barbatos Gundam (Test)',
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
