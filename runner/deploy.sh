#!/usr/bin/env bash
# B 機部署／更新 runner。冪等，可重複執行。
# 用法（在 B 機的 runner/ 目錄下）：bash deploy.sh
set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -f .env ]]; then
  echo "缺少 .env — 請先 cp .env.example .env 並填入 RUNNER_TOKEN" >&2
  exit 1
fi
if ! grep -q '^RUNNER_TOKEN=.\+' .env; then
  echo "RUNNER_TOKEN 未設定（產生：openssl rand -hex 32）" >&2
  exit 1
fi

echo "== build =="
docker compose build

echo "== up =="
docker compose up -d

echo "== 等待 healthy =="
for i in $(seq 1 30); do
  status=$(docker inspect -f '{{.State.Health.Status}}' codedge-runner 2>/dev/null || echo starting)
  [[ "$status" == "healthy" ]] && break
  sleep 2
done
echo "health: ${status:-unknown}"

echo "== 冒煙測試（本機直打，需帶 token）=="
TOKEN=$(grep '^RUNNER_TOKEN=' .env | cut -d= -f2-)
curl -s -X POST http://127.0.0.1:8080/run \
  -H "Content-Type: application/json" \
  -H "X-Runner-Token: $TOKEN" \
  -d '{"code":"#include <iostream>\nint main(){std::cout<<\"runner ok\";}"}' \
  | head -c 400
echo
