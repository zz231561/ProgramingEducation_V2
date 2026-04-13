# ProgramingEducation V2 — 重寫計畫總覽

## 背景

ProgramingEducation V1 是一個 C++ 互動式學習平台，具備 Socratic 教學（EDF Pipeline）、Docker 沙箱執行、Bloom 認知分類等功能。但因架構限制（Docker socket 依賴、無身份驗證、原生 JS 前端、Redis-only 儲存），無法部署至 Zeabur 供眾多學生使用。

V2 將完整重寫實作程式碼，保留 V1 已驗證的教學設計理念，並新增 RAG、知識圖譜、智慧出題、結構化學習等功能。

---

## 文檔索引

| 文件 | 內容 |
|------|------|
| [01-tech-stack.md](01-tech-stack.md) | 技術棧、系統架構圖、專案目錄結構 |
| [02-modules.md](02-modules.md) | 8 個模組規劃 + DB Schema |
| [03-ui-design.md](03-ui-design.md) | UI/UX 設計、Design Tokens、5 頁 Wireframe、元件規格 |
| [04-api-spec.md](04-api-spec.md) | 完整 API 端點規格 |
| [05-engineering.md](05-engineering.md) | 環境變數、錯誤處理、安全規範、測試策略、第三方依賴 |
| [06-phases.md](06-phases.md) | 4 個實作階段 + 已確認決策 |

---

## 已確認決策（摘要）

- **技術棧**：Next.js 15 + TypeScript + Tailwind / FastAPI + PostgreSQL + Redis
- **UI 風格**：GitHub Dark + VS Code 風格，純 Dark Mode
- **程式碼執行**：Judge0 hosted API（開發期）→ 自架（上線後）
- **Terminal**：Batch 模式
- **介面語言**：繁體中文為主
- **Auth**：Google OAuth + JWT
- **知識圖譜**：PostgreSQL 鄰接表
- **RAG**：LlamaIndex + pgvector
- **部署**：Zeabur（Tencent Tokyo VPS 節點）
- **使用者規模**：初期 < 100 人，保留擴充彈性
