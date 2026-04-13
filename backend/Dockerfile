FROM python:3.12-slim

WORKDIR /app

# 安裝依賴
COPY requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock

# 複製原始碼
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
