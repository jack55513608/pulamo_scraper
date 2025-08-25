
# config.py

# --- Scraper Settings ---
BASE_URL = "https://www.pulamo.com.tw/products"
SEARCH_TERM = "Mgsd"
SELENIUM_GRID_URL = "http://selenium:4444/wd/hub"

# --- Product Specifications ---
WING_GUNDAM_SPEC = {
    "name": "飛翼鋼彈",
    "keywords": ["MGSD", "飛翼鋼彈"],
    "exclude_keywords": ["水貼", "遮蓋膠帶"],
}

DESTINY_GUNDAM_SPEC = {
    "name": "命運鋼彈",
    "keywords": ["命運鋼彈"],
    "exclude_keywords": [],
    "min_price": 500,
}

# --- Test Cases ---
BARBATOS_GUNDAM_TEST_SPEC = {
    "name": "獵魔鋼彈 (測試案例)",
    "keywords": ["MGSD", "獵魔鋼彈"],
    "exclude_keywords": ["水貼"],
}
