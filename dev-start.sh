#!/bin/zsh
set -e

PROJECT="$(cd "$(dirname "$0")" && pwd)"

echo "▶ 啟動 Colima..."
colima start

echo "▶ 啟動 Docker 容器..."
cd "$PROJECT"
docker-compose -f docker-compose.dev.yml up -d

echo "▶ 等待 Postgres 就緒..."
sleep 3
docker exec codedge-postgres-dev pg_isready -U postgres -d programing_education

echo "▶ 確認 Alembic migration..."
cd "$PROJECT/backend"
.venv/bin/alembic current

echo "▶ 啟動後端 API (port 8000)..."
.venv/bin/uvicorn main:app --reload --port 8000
