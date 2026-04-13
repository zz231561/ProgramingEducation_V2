#!/bin/sh
# 容器啟動腳本：先跑 DB migration，再啟動 uvicorn

set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting uvicorn..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
