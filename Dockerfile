# 使用 Selenium 官方維護的、包含 Chrome 和 WebDriver 的映像檔
FROM --platform=linux/amd64 selenium/standalone-chrome:latest

# Selenium 映像檔預設的使用者是 'seluser'，我們先切換到 root 來安裝 Python
USER root

# 安裝 Python 和 pip
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# 設定工作目錄
WORKDIR /app

# 複製我們的爬蟲腳本
COPY . .

# 切換回非 root 使用者
USER seluser

# 複製依賴文件並安裝
# 使用 --chown 來確保 seluser 擁有這些檔案
COPY --chown=seluser:seluser requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# 複製我們的爬蟲腳本
COPY --chown=seluser:seluser . .

