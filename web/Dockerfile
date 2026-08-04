FROM node:20-alpine AS base

# --- 安裝依賴 ---
FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# --- Build ---
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# --- Production ---
FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production

RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# --- 容器內 Node 網路行為（2026-08-05 上線實測，缺少會讓整站慢到無法使用）---
# ipv4first：容器內 Node 18+ 預設 IPv6 優先，而雲平台容器的 IPv6 常無法路由外網，
#   每次 DNS 解析都要等逾時才 fallback（實測 /api/auth/session 首次卡 2.2 分鐘）
# UV_THREADPOOL_SIZE：Node 的 DNS 查詢走 libuv threadpool，預設僅 4 執行緒，
#   上述逾時會佔滿它 → 同 process 的所有請求一起排隊（含 proxy 轉發至 backend）
ENV NODE_OPTIONS="--dns-result-order=ipv4first"
ENV UV_THREADPOOL_SIZE=32

CMD ["node", "server.js"]
