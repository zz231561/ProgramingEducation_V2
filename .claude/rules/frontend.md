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

圓角: 4/6/8/12px | 間距: 4px 基礎單位 | 陰影: 極少，以 border 分隔層級
字型: Inter (UI) + Noto Sans TC (中文) + JetBrains Mono (程式碼)
元件庫: shadcn/ui (dark preset, 基於 Radix UI)

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
