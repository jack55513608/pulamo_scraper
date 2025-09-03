"""# Pulamo 商品監控爬蟲

## 1. 專案目標

本專案旨在監控 [弘德模型 (Pulamo)](https://www.pulamo.com.tw/) 及 [露天拍賣 (Ruten)](https://www.ruten.com.tw/) 網站，自動化地檢查特定商品的庫存狀態。在一次檢查週期中，若找到多個符合條件的商品，系統會對所有商品逐一發出通知。

目前監控的目標商品為：
1.  **MGSD 飛翼鋼彈**: 監控模型本體是否有貨。
2.  **MGSD 命運鋼彈**: 監控此未來商品是否上架且有貨。

專案中也包含一個「MGSD 獵魔鋼彈」的測試案例，用以驗證爬蟲的抓取與判斷邏輯是否正常運作。

---

## 2. 技術棧

- **Python**: 主要的程式語言。
- **Selenium & Selenium Grid**: 用於建立分散式的瀏覽器驅動環境，抓取動態加載的網頁內容。
- **requests**: 用於直接對網站 API 發出 HTTP 請求，實現更高效的資料抓取。
- **BeautifulSoup4**: 用於解析 HTML，提取所需資訊。
- **Docker & Docker Compose**: 用於建立一個獨立、可重複的執行環境，簡化部署與執行流程。
- **Pytest**: 用於執行單元測試。

---

## 3. 如何使用

### 步驟 1: 環境需求

- 請確保你的電腦已安裝最新版的 Docker 與 Docker Compose。
- 本專案現在使用 **Selenium Grid** 架構，包含一個 Hub (主控中心) 和多個可擴展的 Node (瀏覽器節點)。這允許更穩定且可平行處理的監控任務。
- `docker-compose.yml` 使用官方的 `selenium/` 映像檔，支援多種平台。
- `docker-compose.test.yml` 為了 ARM64 架構 (如 Apple Silicon) 的相容性，使用了 `seleniarm/` 系列的映像檔。

### 步驟 2: 設定環境變數 (.env)

若要使用 Telegram 通知功能，您需要設定必要的環境變數。

請先將 `env.example` 檔案複製一份並重新命名為 `.env`：

```bash
cp env.example .env
```

接著，編輯 `.env` 檔案並填入您的個人資訊：

```ini
TELEGRAM_BOT_TOKEN="在此填入您的 Bot Token"
TELEGRAM_CHAT_ID="在此填入您的 Chat ID"
```

- `TELEGRAM_BOT_TOKEN`: 您從 BotFather 取得的 Telegram Bot Token。
- `TELEGRAM_CHAT_ID`: 您希望接收通知的 Telegram 使用者或群組 ID。

**注意**: 這個 `.env` 檔案已被加入 `.gitignore`，不會被上傳到 Git 儲存庫，以確保您的敏感資訊安全。

### 步驟 3: 設定監控目標 (可選)

所有監控的商品都定義在 `config.py` 檔案中。你可以修改此檔案來新增或變更監控目標。

一個商品的設定規格如下：

**Pulamo 任務:**
```python
# config.py
{
    'name': 'Pulamo - Wing Gundam',
    'type': 'pulamo',
    'browser': 'chrome', # 可選 'chrome' 或 'firefox'
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
}
```

**多步驟任務 (例如 Ruten):**

露天拍賣的搜尋爬蟲現在使用 **API** 方式，不再需要啟動瀏覽器，大幅提升了效率和穩定性。

您也可以在 `config.py` 中定義 `BLACKLISTED_SELLERS` 列表，來過濾掉特定賣家的商品 (此功能目前僅支援 Ruten)。

```python
# config.py
{
    'name': 'Ruten - Destiny Gundam',
    'type': 'ruten',
    'browser': 'firefox', # 此瀏覽器僅供後續的 page_scraper 使用
    # search_scraper 已改用高效的 API 版本
    'search_scraper': 'ruten_api.RutenSearchAPIScraper',
    'search_scraper_params': {
        'search_url': 'https://www.ruten.com.tw/find/?q=mgsd+%E5%91%BD%E9%81%8B&prc.now=900-1400',
    },
    'keyword_checker': 'keyword.KeywordChecker',
    'keyword_checker_params': {
        'keywords': ['mgsd', '命運鋼彈'],
        'exclude_keywords': ['魔物語', 'ps5', 'ns2'] # Exclude game pre-orders
    },
    'page_scraper': 'ruten_api.RutenProductPageAPIScraper',
    'stock_checker': 'stock.StockChecker',
    'stock_checker_params': {
        'max_price': 2000,
        'blacklisted_sellers': ['seller_id_to_block_1', 'seller_id_to_block_2'],
    },
    'notifier': 'telegram.TelegramNotifier',
    'notifier_params': {
        'name': 'MGSD 命運鋼彈',
        'store_name': '露天拍賣',
    },
}
```

### 步驟 4: 啟動主要監控程式

此指令會啟動預設的服務，包含 Selenium Hub、Firefox 節點以及應用程式本身。

```bash
# 建立 Docker 映像檔並啟動所有預設服務 (背景執行)
docker-compose up --build -d
```

若要停止服務：
```bash
docker-compose down
```

#### 啟動 Chrome 瀏覽器節點 (可選)

`Chrome` 節點被設定為一個獨立的 `profile`，預設不會啟動。如果您需要使用 Chrome 進行測試或爬取，可以使用以下指令來啟動它：

```bash
# 啟動預設服務外，再加上 profile 為 chrome 的服務
docker-compose up --profile chrome -d
```

#### 擴展瀏覽器節點

如果需要同時執行更多爬蟲任務，可以輕易地增加瀏覽器節點的數量。`docker-compose.yml` 中已預設包含 `chrome` 和 `firefox` 兩種瀏覽器節點。

```bash
# 將 Chrome 節點擴展到 3 個
docker-compose up --scale chrome=3 -d

# 將 Firefox 節點擴展到 2 個
docker-compose up --scale firefox=2 -d
```

### 步驟 5: 其他指令

#### Demo Dumpers

`demo_dumpers` 資料夾中提供了一些腳本，用於手動抓取網頁內容或 API 回應，非常適合用於臨時的分析或除錯。

**1. Selenium Dumper (抓取動態網頁)**

此腳本使用 Selenium 瀏覽器來抓取指定網址的 **最終 HTML** 內容。

**使用方式：**

```bash
# 請先確保 Selenium Grid 正在運行
docker-compose run --rm dumper python3 demo_dumpers/selenium_dumper.py <您要抓取的網址>
```

**範例：**

```bash
docker-compose run --rm dumper python3 demo_dumpers/selenium_dumper.py https://www.pulamo.com.tw/
```

**2. Requests Dumper (抓取 API)**

此腳本使用 `requests` 直接請求指定的 URL，適合用來測試 API 或抓取靜態網頁的 JSON/HTML 回應。

**使用方式：**

```bash
# 此腳本不需 Selenium Grid
docker-compose run --rm dumper python3 demo_dumpers/requests_dumper.py <您要抓取的網址>
```

**範例：**

```bash
docker-compose run --rm dumper python3 demo_dumpers/requests_dumper.py https://rtapi.ruten.com.tw/api/search/v3/index.php/core/prod?q=mgsd
```

---

## 4. 如何測試

本專案包含兩種主要測試方式：

### 1. 純單元測試 (不需 Docker 環境)

這些測試用於快速驗證獨立的函式邏輯，不依賴於 Docker 或 Selenium Grid。

```bash
# 執行所有不需 Docker 環境的單元測試
pytest -m "not docker"
```

### 2. 功能測試與整合測試 (需 Docker 環境)

這些測試用於驗證應用程式在實際環境中的行為，需要 Selenium Grid 運行。

#### 啟動測試環境

在執行以下測試前，請確保您的 Selenium Grid 服務已啟動。您可以選擇啟動主要環境的 Grid，或專門為測試啟動一個獨立的 Grid。

```bash
# 啟動主要環境的 Selenium Grid (如果尚未運行)
docker-compose up -d selenium chrome
```

#### 執行所有需要 Docker 的測試

這會執行所有標記為 `docker` 的測試案例，例如 Pulamo 爬蟲的功能測試。

```bash
# 在 Docker 容器內部執行所有需要 Docker 環境的測試
docker-compose run --rm scraper pytest -m docker
```

#### 整合測試 (獵魔鋼彈測試案例)

這會使用獨立的測試用 Selenium Grid 來模擬一次性的完整爬蟲流程，檢查「MGSD 獵魔鋼彈」。

```bash
# 啟動測試環境並執行測試
docker-compose -f docker-compose.test.yml up --build -d

# 查看 debugger 服務的日誌來確認結果
docker-compose -f docker-compose.test.yml logs -f debugger

# 測試完畢後關閉測試環境
docker-compose -f docker-compose.test.yml down
```

預期結果範例 (若商品未上架):
'''
INFO - --- 開始檢查商品狀態 (測試案例) ---
INFO - 未找到符合條件的 獵魔鋼彈 (測試案例) 已售完或未上架
INFO - --- 商品狀態檢查結束 (測試案例) ---
'''

#### 露天拍賣功能測試

此測試用於驗證 `RutenSearchScraper` 是否能正確抓取露天拍賣搜尋頁面上的所有商品。

```bash
# 在 Docker 容器內部執行露天拍賣功能測試
docker-compose run --rm scraper pytest -m docker tests/test_ruten_functional.py
```

---

## 5. 專案結構

- `main.py`: 主要監控程式的進入點，負責初始化和執行任務迴圈。
- `main_debug.py`: 「獵魔鋼彈」測試案例的進入點。
- `config.py`: 存放所有可變的設定，例如 URL 和商品規格。
- `models.py`: 定義專案中使用的資料模型，例如 `Product`。
- `factory.py`: 負責動態載入和實例化各種插件 (Scraper, Checker, Notifier)。
- `processors/`: 存放所有任務處理邏輯的插件。
    - `pulamo.py`: 處理 Pulamo 網站的任務邏輯。
    - `ruten.py`: 處理露天拍賣網站的任務邏輯，並包含通知冷卻管理器。
- `scrapers/`: 存放所有網站的爬蟲插件。
    - `base.py`: 所有爬蟲插件的抽象基礎類別。
    - `api_scraper.py`: 基於 `requests` 的爬蟲基礎類別。
    - `selenium_scraper.py`: 基於 `Selenium` 的爬蟲基礎類別。
    - `pulamo.py`: 針對 Pulamo 網站的爬蟲實作。
    - `ruten.py`: 針對露天拍賣網站的 **Selenium** 爬蟲實作。
    - `ruten_api.py`: 針對露天拍賣網站的 **API** 爬蟲實作，效率更高。
- `checkers/`: 存放所有商品檢查邏輯的插件。
    - `base.py`: 檢查邏輯插件的抽象基礎類別。
    - `product.py`: 針對商品關鍵字和價格的檢查實作。
    - `keyword.py`: 根據關鍵字篩選商品的檢查器。
    - `stock.py`: 檢查商品庫存狀態的檢查器。
- `notifiers/`: 存放所有通知模組的插件。
    - `base.py`: 通知模組插件的抽象基礎類別。
    - `telegram.py`: 針對 Telegram 的通知實作。
- `demo_dumpers/`: 包含用於手動分析和除錯的腳本。
    - `selenium_dumper.py`: 使用 Selenium 抓取動態網頁的 HTML。
    - `requests_dumper.py`: 使用 requests 抓取靜態網頁或 API 回應。
- `docker-compose.yml`: 定義和管理**主要監控服務**的 Docker 設定 (包含 Selenium Hub, Chrome Node, 和 Firefox Node)。
- `docker-compose.test.yml`: 定義和管理**整合測試**的 Docker 設定 (使用 Selenium Grid)。
- `Dockerfile`: 建立 Python 應用程式 Docker 映像檔的說明書。
- `requirements.txt`: Python 依賴套件列表。
- `tests/`: 存放所有單元測試和功能測試檔案。
- `README.md`: 本說明文件。

---

## 6. 日誌 (Logging)

本專案的日誌系統經過簡化，以更好地與 Docker 整合。

- **應用程式日誌**: 程式本身產生的日誌只包含**日誌等級**和**訊息** (例如 `INFO - --- 開始新一輪檢查 ---`)。
- **時間戳**: 所有日誌的時間戳都由 Docker 的日誌驅動程式統一提供，以確保在多個服務中格式一致。

當您使用 `docker-compose logs` 查看日誌時，會看到如下格式：

```
scraper  | YYYY-MM-DDTHH:MM:SS.sssssssssZ INFO - --- 開始新一輪檢查 ---
```
""
