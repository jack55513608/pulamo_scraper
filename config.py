
# config.py
import os

# --- Scraper Settings ---
SELENIUM_GRID_URL = "http://selenium:4444/wd/hub"
RETRY_DELAY_SECONDS = 5 # 新增此行

# --- Telegram Settings ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Product Specifications ---
WING_GUNDAM_SPEC = {
    "name": "飛翼鋼彈",
    "keywords": ["MGSD", "飛翼鋼彈"],
    "exclude_keywords": ["水貼", "遮蓋膠帶"],
    "search_url": "https://www.pulamo.com.tw/products?search=MGSD",
}

DESTINY_GUNDAM_SPEC = {
    "name": "命運鋼彈",
    "keywords": ["命運鋼彈"],
    "exclude_keywords": [],
    "min_price": 500,
    "search_url": "https://www.pulamo.com.tw/products?search=MGSD",
}

BARBATOS_GUNDAM_SPEC = {
    "name": "獵魔鋼彈",
    "keywords": ["MGSD", "獵魔"],
    "exclude_keywords": ["擴充", "水貼"],
    "search_url": "https://www.pulamo.com.tw/products?search=MGSD",
}
