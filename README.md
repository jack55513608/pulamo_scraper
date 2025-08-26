
# Pulamo 商品監控爬蟲

## 1. 專案目標

本專案旨在監控 [弘德模型 (Pulamo)](https://www.pulamo.com.tw/) 網站，自動化地檢查特定商品的庫存狀態。

目前監控的目標商品為：
1.  **MGSD 飛翼鋼彈**: 監控模型本體是否有貨。
2.  **MGSD 命運鋼彈**: 監控此未來商品是否上架且有貨。

專案中也包含一個「MGSD 獵魔鋼彈」的測試案例，用以驗證爬蟲的抓取與判斷邏輯是否正常運作。

---

## 2. 技術棧

- **Python**: 主要的程式語言。
- **Selenium**: 用於驅動瀏覽器，抓取動態加載的網頁內容。
- **BeautifulSoup4**: 用於解析 HTML，提取所需資訊。
- **Docker & Docker Compose**: 用於建立一個獨立、可重複的執行環境，簡化部署與執行流程。
- **Pytest**: 用於執行單元測試。

---

## 3. 如何使用

### 步驟 1: 環境需求

- 請確保你的電腦已安裝最新版的 Docker 與 Docker Compose。
- **Apple Silicon (ARM64) 用戶請注意**: 本專案的 `docker-compose.yml` 預設使用 x86/amd64 架構的 Selenium 映像檔。為了解決在 ARM64 架構下的相容性問題，測試環境已改用 `seleniarm/standalone-chromium` 映像檔。如果您需要在 ARM64 架構下執行主程式，請參考 `docker-compose.test.yml` 的設定來修改 `docker-compose.yml`。

### 步驟 2: 設定監控目標 (可選)

所有監控的商品都定義在 `config.py` 檔案中。你可以修改此檔案來新增或變更監控目標。

一個商品的設定規格如下：
```python
# config.py
WING_GUNDAM_SPEC = {
    "name": "飛翼鋼彈",
    "keywords": ["MGSD", "飛翼鋼彈"],
    "exclude_keywords": ["水貼", "遮蓋膠帶"],
    "search_url": "https://www.pulamo.com.tw/products?search=MGSD",
}
```

### 步驟 3: 啟動主要監控程式

此指令會啟動持續監控服務，檢查 `config.py` 中定義的主要目標商品（飛翼、命運鋼彈）。

```bash
# 此指令會建立 Docker 映像檔並啟動所有服務
docker-compose up --build
```

---

## 4. 如何測試

本專案包含兩種測試方式：

### 整合測試 (獵魔鋼彈測試案例)

這會模擬一次性的完整爬蟲流程，用來檢查「MGSD 獵魔鋼彈」。它會建立獨立的測試環境，執行完畢後自動清理，並且會發送真實的 Telegram 通知。

```bash
# 執行此指令來啟動整合測試
docker-compose -f docker-compose.test.yml down --remove-orphans && docker-compose -f docker-compose.test.yml run --build --rm debugger && docker-compose -f docker-compose.test.yml down --remove-orphans
```

預期結果範例 (若商品未上架):
```
--- 開始檢查商品狀態 (測試案例) ---
未找到符合條件的 獵魔鋼彈 (測試案例) 已售完或未上架
--- 商品狀態檢查結束 (測試案例) ---
```

### 單元測試 (Pytest)

這會執行所有位於 `test_*.py` 中的單元測試，用來快速驗證獨立的函式邏輯是否正確。

```bash
# 1. 安裝 pytest
pip install pytest

# 2. 執行測試
pytest
```

---

## 5. 專案結構

- `main.py`: 主要監控程式的進入點。
- `main_debug.py`: 「獵魔鋼彈」測試案例的進入點。
- `config.py`: 存放所有可變的設定，例如 URL 和商品規格。
- `scraper.py`: 包含 `PulamoScraper` 類別，專門負責抓取和解析網頁資料。
- `checker.py`: 包含所有檢查商品是否符合條件的商業邏輯。
- `notifier.py`: 負責發送 Telegram 通知的模組。
- `docker-compose.yml`: 定義和管理**主要監控服務**的 Docker 設定。
- `docker-compose.test.yml`: 定義和管理**整合測試**的 Docker 設定。
- `Dockerfile`: 建立 Python 應用程式 Docker 映像檔的說明書。
- `requirements.txt`: Python 依賴套件列表。
- `test_*.py`: Pytest 單元測試檔案。
- `README.md`: 本說明文件。
