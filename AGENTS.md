# ProgramingEducation V2 — 開發指揮中心

> ⚠ **本檔會被 hook 原樣複製為 `AGENTS.md`（給 Codex 讀）。改規則一律改本檔——
> 直接編輯 `AGENTS.md` 會在下次同步時被覆蓋。**

## 執行守則 (STRICT RULES)
1. **小步快跑**：每次對話僅限執行 Roadmap 中的「單一最小 Checkbox 任務」。
2. **強制中斷**：完成代碼修改後立即停止，提示使用者手動測試。
3. **禁止擅自推進**：等待使用者回覆「測試通過」才可勾選 Checkbox 並開始下一任務。
4. **狀態同步**：任務確認後優先更新對應文件的 Checkbox `[x]`。
5. **專業匯報**：簡述修改對架構的影響，確認是否符合工程規範。
6. **文檔同步（依變更類型決定，不是每次都四處寫）**：
   - **變更明細不寫進任何文檔**——那在 git log：`git log --grep=<關鍵字>` / `git log -p -- <path>`。
     因此 commit message 必須寫清楚 what & why，它是唯一的變更記錄
   - `docs/roadmap.md` — 完成 sub-task 就打勾 + **一行**摘要（**進度的唯一真相來源**）
   - `docs/decisions.md` — **有設計取捨才寫**：決策理由／否決方案／實測數據；純執行的變更不寫
   - `docs/tech-debt.md` — 產生或消除技術債時
   - **禁止手抄機械事實**（行數／測試數）→ 一律以 `doc_selfcheck.py` 產出為準
   - 各文檔「怎麼寫」寫在**該檔自己的檔頭**，不另立格式規範
7. **改檔案一律用 Edit/Write 工具**：**禁止**用 `python3 - <<EOF` / `sed -i` / `cat >` 等 shell 手法改動專案檔案——那是任意程式碼執行、diff 不可見、且會繞過權限確認。批次改動就多呼叫幾次 Edit。
8. **避免重複造輪子（OSS 優先）**：開發新功能前必先查 `docs/references.md` §1 決策矩陣。**禁止移植已有對應套件的演算法**（例：BKT 必用 pyBKT）。**禁止引入 AGPL/GPL 授權套件**（見 references.md §2 黑名單）。
9. **當場修小問題**：發現的問題若**範圍小、根因明確、不需設計裁決**（過時文案、失效路徑、錯誤敘述、明顯 bug），**當輪直接修**，不要只記錄或延後、也不必先問。需要討論的只有三種：改動會擴散到其他模組、涉及架構或教學設計取捨、根因尚未確定。修完照守則 6 同步文檔。

## 技術棧（已鎖定）
- **前端**：Next.js 15 + TypeScript + Tailwind CSS（`web/`）
- **後端**：FastAPI + Python 3.12 + SQLAlchemy 2.0 async（`backend/`）
- **資料庫**：PostgreSQL + pgvector | **快取**：Redis
- **程式碼執行**：自建 runner（nsjail + PTY 互動終端，B 機）| fallback：Judge0
- **LLM**：OpenAI gpt-5.6（`luna` 對話/分析/生成、`terra` 審查/內容）| **RAG**：LlamaIndex + pgvector
- **Auth**：NextAuth.js (Google OAuth) + JWT | **編輯器**：CodeMirror 6
- **部署**：Zeabur（Tencent Tokyo VPS）

## 常駐須知
> **進度一律見 `docs/roadmap.md`（唯一真相來源）——本檔不重複、禁止回填進度。**
> **每次 session 開頭先讀 `docs/dev-setup.md` §1**（Colima + docker-compose 啟動 SOP）。
> ⚠ **環境前置**：`web/.env.local` `AUTH_SECRET` 必須與 `backend/.env` `NEXTAUTH_SECRET` 同值。

**工具**：`python3 scripts/doc_selfcheck.py` — 文件自檢（超門檻／失效路徑／失效章節）；session 結束前跑
**部署與營運**：見 `docs/deployment.md`。**push 即自動部署**、migration 自動跑；
**唯獨改環境變數必須手動重啟 service**；OAuth 測試模式 100 人上限。

## 文件索引
> 本文件 ≤ 62 行（`doc_selfcheck.py` 會驗）。禁止回填進度/日誌/UI 參數/Schema。
> **狀態標記**：🔵 活躍｜⚪ 穩定（需維持正確）｜⚫ 凍結（不維護）。稽核只查 🔵⚪。

**`.claude/rules/`**（Claude Code 依 glob 自動注入；**Codex 等其他 agent 必須自己開來讀**）
- `frontend.md` — Design Tokens、元件規格、響應式斷點（glob: `web/**`）
- `backend.md` — 錯誤處理、安全規範、環境變數（glob: `backend/**`）
- `edf-pipeline.md` — EDF 三層管線、ConceptTag、出題流程（glob: `backend/services/edf/**`）

**`.claude/skills/`**（Claude Code 依 description 自動選用；**Codex 請當一般文件直接讀**）
- `code-health/` — 檔案大小與重複的**決策**工作流；改完一個邏輯變更後跑，不在每次 Edit 後跑

**`docs/`**（按需查閱，預設不主動讀）
- 🔵 [roadmap.md](docs/roadmap.md) 進度唯一真相 / [decisions.md](docs/decisions.md) 決策記錄
  （理由／否決方案／實測數據；**變更明細查 git log**）/ [tech-debt.md](docs/tech-debt.md)
- ⚪ [dev-setup.md](docs/dev-setup.md) **本機啟動 SOP（每次 session 必讀 §1）** / [acceptance-checklist.md](docs/acceptance-checklist.md) 真人驗收清單
- ⚪ [architecture.md](docs/architecture.md) / [modules.md](docs/modules.md) / [db-schema.md](docs/db-schema.md) / [api-spec.md](docs/api-spec.md) / [references.md](docs/references.md)（OSS 決策矩陣，守則 8）
- ⚪ [deployment.md](docs/deployment.md)（§E = Runner 部署 SOP）/ [server-plan.md](docs/server-plan.md) A 機 + B 機
- ⚫ [roadmap-archive.md](docs/roadmap-archive.md) 完成細節快照｜UI 規格全數收斂於 `frontend.md`
- **驗收機制**：`backend/scripts/eval_coddy/` — 七型學生模擬（真實 LLM + 白盒探針），改完 Coddy 重跑對照
