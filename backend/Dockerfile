FROM python:3.12-slim

WORKDIR /app

# 安裝依賴
COPY requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock

# 複製原始碼
COPY . .

# 啟動腳本需要執行權限
RUN chmod +x start.sh

EXPOSE 8000

# 啟動時先跑 Alembic migration 再啟動 uvicorn
CMD ["./start.sh"]
