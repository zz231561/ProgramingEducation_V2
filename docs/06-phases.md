# 實作階段

## Phase 1：基礎建設（MVP）

**目標：** 可部署到 Zeabur 的最小可用版本

| # | 任務 | 涉及模組 |
|---|------|---------|
| 1 | 專案初始化（Next.js + FastAPI + PostgreSQL + Redis） | 全域 |
| 2 | Auth 模組（Google OAuth + JWT） | Module 1 |
| 3 | 程式碼編輯器 + Judge0 執行 | Module 2 |
| 4 | EDF 教學管線（保留 V1 核心邏輯） | Module 3 |
| 5 | 基礎對話介面（AI Chat） | Module 3 |
| 6 | Zeabur 部署配置 | 全域 |

**完成標準：** 學生可以登入、寫 C++ 程式碼、執行、與 AI 對話學習

**對應 UI 頁面：** Workspace（Page 1）

---

## Phase 2：智慧功能

**目標：** 加入差異化的智慧學習功能

| # | 任務 | 涉及模組 |
|---|------|---------|
| 7 | RAG 知識檢索（pgvector + LlamaIndex） | Module 4 |
| 8 | 知識圖譜（概念關係 + 視覺化） | Module 5 |
| 9 | 學生精熟度追蹤 + 視覺化 | Module 5 |
| 10 | 智慧出題（4 階段管線） | Module 6 |

**完成標準：** RAG 檢索可用、知識圖譜可視覺化、弱項概念可自動出題

**對應 UI 頁面：** Knowledge（Page 4）、Quiz 基礎版

---

## Phase 3：學習體驗

**目標：** 完整的結構化學習體驗

| # | 任務 | 涉及模組 |
|---|------|---------|
| 11 | 結構化學習路徑 | Module 7 |
| 12 | Quiz 系統（選擇題 + 程式撰寫題） | Module 6 |
| 13 | 學習進度 Dashboard | Module 5, 7 |

**完成標準：** 學生可從頭到尾跟隨學習路徑，完成測驗，查看進度

**對應 UI 頁面：** Learn（Page 2）、Quiz（Page 3）、Dashboard（Page 5）

---

## Phase 4：教師端（未來）

| # | 任務 | 涉及模組 |
|---|------|---------|
| 14 | 教師 Dashboard | Module 8 |
| 15 | 班級管理 + 作業指派 | Module 8 |
| 16 | 學習數據分析 | Module 8 |

---

## 已確認決策

- **Terminal 模式**：Batch 模式即可（送出程式碼 → 等結果），不需即時互動式 terminal
- **介面語言**：繁體中文為主，暫不做多語系
- **UI 風格**：GitHub Dark + VS Code 風格，純 Dark Mode
- **Judge0 部署策略**：
  - 開發期：使用 Judge0 官方 hosted API（RapidAPI 免費 50 次/天）
  - 上線後：現有 Tencent Tokyo VPS（2C/2GB）升級後自架，或加第二台 VPS
- **目標平台**：Zeabur（現有 Tencent Tokyo VPS 節點）
- **使用者規模**：初期 < 100 人，架構保留擴充彈性
