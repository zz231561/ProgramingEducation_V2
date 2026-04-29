---
description: 前端開發規範 — Design Tokens、元件規格、響應式斷點
globs: web/**
---

# 前端開發規範

## Design Tokens（GitHub Dark）

背景: `--bg-canvas: #0D1117` | `--bg-default: #161B22` | `--bg-subtle: #1C2128` | `--bg-inset: #010409`
邊框: `--border-default: #30363D` | `--border-muted: #21262D` | `--border-emphasis: #6E7681`
文字: `--text-primary: #E6EDF3` | `--text-secondary: #8B949E` | `--text-muted: #6E7681` | `--text-link: #58A6FF`
強調: `blue: #58A6FF` | `green: #3FB950` | `red: #F85149` | `orange: #D29922` | `purple: #BC8CFF`
按鈕: `primary-bg: #238636` | `primary-hover: #2EA043` | `default-bg: #21262D` | `default-border: #363B42`

圓角: 4/6/8/12/9999(pill) | 間距: 4px 基礎單位
字型: Inter (UI) + Noto Sans TC (中文) + JetBrains Mono (程式碼)
元件庫: shadcn/ui (dark preset, 基於 Radix UI)

### Phase 1-6 統一協議 token（design-plan §3）
Surface 語義別名: `--surface-0` (=bg-canvas) | `--surface-1` (=bg-default) | `--surface-2` (=bg-subtle) | `--surface-inset` (=bg-inset)
Shadow（僅 3 階）: flat | `--shadow-card`: `0 1px 3px rgba(0,0,0,0.3)` | `--shadow-modal`: `0 16px 48px rgba(0,0,0,0.5), 0 0 0 1px var(--border-default)`
Border AI 例外: `--border-ai`: `rgba(188, 140, 255, 0.25)` — 僅 Chat AI 訊息氣泡可用
Tailwind utility: `bg-surface-1`、`shadow-card`、`shadow-modal`、`border-ai`、`rounded-pill`

## 元件規格

| 元件 | 規格 |
|------|------|
| Button Primary | bg: #238636, hover: #2EA043, text: #FFF, radius: 6px, h: 32px |
| Button Default | bg: #21262D, border: #363B42, text: #C9D1D9, hover-bg: #30363D |
| Button Danger | bg: transparent, border: #F85149, text: #F85149, hover-bg: #F8514922 |
| Card | bg: #161B22, border: 1px #30363D, radius: 6px, padding: 16px |
| Input | bg: #0D1117, border: #30363D, focus-border: #58A6FF, text: #E6EDF3, h: 32px |
| Badge | radius: 12px, padding: 2px 8px, font-size: 12px |
| Tab active | border-bottom: 2px #F78166, text: #E6EDF3 |
| Tab inactive | text: #8B949E, hover-text: #E6EDF3 |
| Code Block | bg: #010409, border: #30363D, font: JetBrains Mono 14px |
| Toast | bg: #161B22, border-left: 3px accent color, radius: 6px |

## 響應式斷點

| 斷點 | 寬度 | 佈局 |
|------|------|------|
| Desktop | >= 1280px | Editor + Chat side-by-side |
| Laptop | 1024-1279px | Chat 改為 overlay drawer |
| Tablet | 768-1023px | 單欄，Chat 為 bottom sheet |
| Mobile | < 768px | 全螢幕單欄，Header tab → hamburger |

## 導覽

Top Navigation Bar（GitHub 風格頂部 tab），非 Sidebar。
Tab: Workspace(預設) | Learn | Quiz | Knowledge | Dashboard
Active tab: `border-bottom: 2px solid #F78166`

## 測試策略

- **Component**: Vitest + React Testing Library → 各 UI 元件
- **E2E**: Playwright → 登入 → 寫程式 → 執行 → AI 對話（golden path）
- Phase 1 優先：Workspace 頁面 E2E test

## API 呼叫

前端統一用 `fetch('/api/...')` 打 Next.js API Routes（proxy 至 FastAPI），不直接打後端。
統一錯誤攔截：401 → 重導登入、429 → 冷卻倒數 toast、5xx → 錯誤 toast

## 統一視覺協議（Phase 1-6 借鑑計畫）

**詳見 [docs/design-plan.md](../../docs/design-plan.md)。** 6 份外部借鑑來源（Cursor / Warp / Linear / Claude / Vercel / Raycast）僅貢獻結構模式，**所有 color / font / shadow / border / radius / spacing 一律來自本檔上方既有 GitHub Dark token**。

### 違和感檢核 7 條（每元件實作後逐條對照）
| 規則 | 規格 |
|------|------|
| R1 顏色 | 僅 GitHub Dark token，禁外來 hex |
| R2 字體 | 僅 Inter / Noto Sans TC / JetBrains Mono |
| R3 邊框 | 一律 `1px solid` + 既有 border token，禁 shadow-as-border / 半透明邊 |
| R4 陰影 | 僅 3 階：flat / `--shadow-card` / `--shadow-modal`；`.kbd` 鍵帽為唯一例外 |
| R5 Radius | 僅 5 階：4 / 6 / 8 / 12 / 9999 |
| R6 Hover | Surface 升一階 / Button bg 變化；禁 `opacity 0.6` / 暖紅文字 |
| R7 字距 | Display ≥40px → -0.02em；Body 預設 0；UI 全站 `font-feature-settings: "cv01", "ss03"` |

### 兩處唯一視覺例外
1. **AI 訊息氣泡** ring：`border: 1px solid var(--border-ai)`（已建立 token，1-6d 套用）
2. **`.kbd` 鍵帽**：多層 inset 陰影（1-6e 實作時建立 `.kbd` class，規格見 design-plan §2.10）
