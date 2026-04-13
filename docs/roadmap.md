# Roadmap

## Phase 1：基礎建設（MVP）
> 完成標準：學生可登入、寫 C++ 程式碼、執行、與 AI 對話學習
> 對應頁面：Workspace (Page 1)

- [ ] 1-1 專案初始化（Next.js + FastAPI + PostgreSQL + Redis）
- [ ] 1-2 Auth 模組（Google OAuth + JWT）
- [ ] 1-3 程式碼編輯器 + Judge0 執行
- [ ] 1-4 EDF 教學管線（保留 V1 核心邏輯）
- [ ] 1-5 基礎對話介面（AI Chat）
- [ ] 1-6 Zeabur 部署配置

## Phase 2：智慧功能
> 完成標準：RAG 檢索可用、知識圖譜可視覺化、弱項可自動出題
> 對應頁面：Knowledge (Page 4)、Quiz 基礎版

- [ ] 2-1 RAG 知識檢索（pgvector + LlamaIndex）
- [ ] 2-2 知識圖譜（概念關係 + 視覺化）
- [ ] 2-3 學生精熟度追蹤 + 視覺化
- [ ] 2-4 智慧出題（4 階段管線）

## Phase 3：學習體驗
> 完成標準：學生可從頭到尾跟隨學習路徑，完成測驗，查看進度
> 對應頁面：Learn (Page 2)、Quiz (Page 3)、Dashboard (Page 5)

- [ ] 3-1 結構化學習路徑
- [ ] 3-2 Quiz 系統（選擇題 + 程式撰寫題）
- [ ] 3-3 學習進度 Dashboard

## Phase 4：教師端（未來）

- [ ] 4-1 教師 Dashboard
- [ ] 4-2 班級管理 + 作業指派
- [ ] 4-3 學習數據分析

## 已確認決策

- Terminal：Batch 模式，不需即時互動式 terminal
- 介面語言：繁體中文為主，暫不做多語系
- UI：GitHub Dark + VS Code 風格，純 Dark Mode
- Judge0：開發期 RapidAPI (免費 50 次/天) → 上線後自架
- 部署：Zeabur (Tencent Tokyo VPS) | 使用者規模：初期 < 100 人
