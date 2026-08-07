# ProgramingEducation V2 — 開發指揮中心

## 執行守則 (STRICT RULES)
1. **小步快跑**：每次對話僅限執行 Roadmap 中的「單一最小 Checkbox 任務」。
2. **強制中斷**：完成代碼修改後立即停止，提示使用者手動測試。
3. **禁止擅自推進**：等待使用者回覆「測試通過」才可勾選 Checkbox 並開始下一任務。
4. **狀態同步**：任務確認後優先更新對應文件的 Checkbox `[x]`。
5. **專業匯報**：簡述修改對架構的影響，確認是否符合工程規範。
6. **強制文檔同步**：每次指令完成後**必須**更新：
   - `docs/changelog.md` — 新增變更記錄行
   - `docs/roadmap.md` — 勾選 Checkbox（**僅一行摘要**，細節歸 changelog）
   - `CLAUDE.md` 當前狀態 — 反映最新進度
   - `docs/tech-debt.md` — 若產生或消除技術債
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

## 當前狀態
> 詳細 sub-task 進度見 `docs/roadmap.md`；已完成細節見 `docs/roadmap-archive.md` / `docs/changelog.md`。
> **每次 session 開頭先讀 `docs/dev-setup.md` §1**（Colima + docker-compose 啟動 SOP）。
> ⚠ **環境前置**：`web/.env.local` `AUTH_SECRET` 必須與 `backend/.env` `NEXTAUTH_SECRET` 同值。

**已完成（細節一律查 roadmap-archive / changelog，禁止回填此處）**
Phase 1-4 全數 ✅｜Phase 5 教師端 ✅（5-3/5-4 除外，等真實資料）｜Phase 6 教學內容建構 ✅｜
Phase 6-K K-Graph 自適應引擎 ✅｜Phase 6-U 學生端修正 ✅｜DEV 開發者模式 ✅｜
Phase 7-R 自建互動執行引擎 ✅（生產終端已上線）｜Phase 7-U 上線後體驗優化 ✅ 六項｜
**Phase 7-C Coddy 教學品質 ✅ 全數完成**（C1/C1'/C2a/C2a'/C2a''/C2b/C3/C4，2026-08-06）——
核心成果：揭露階梯由「追問次數」改為 **need 需求量估計**（施壓不再有效）、
2-6 Comprehension 前端補齊（後端從此有流量）、七型模擬驗收全數通過

**🎯 進行中 — 7-D 技術債清償**（功能已全部完成；定序：功能 → **技術債** → 驗收）
- ✅ 7-D1 前端 Vitest（2026-08-07，`cd web && npm test`，31 it）
- ✅ 7-D2 Code Health 規則改版（2026-08-07）：門檻 250/400 + 舉證豁免 + jscpd 重複偵測；
  7 檔逐案處置＝1 拆分 6 豁免，🚫/⚠ 歸零。工作流見 `.claude/skills/code-health/`
- ✅ 7-D2b 後端 lint 首次落地（2026-08-07）：ruff 宣告了卻沒裝，437 findings → **0**；
  rule set 擴充 B/C4/SIM/PERF/ERA/RUF 並校準 6900+ 中文與 FastAPI 誤判
- 待辦：7-D3 changelog 拆檔（近 5000 行）｜ 7-D4 R6 收尾 ｜ 7-D5 文件稽核 ｜
  7-D6 全站 429/5xx toast ｜ **7-D7 無意義註解清查**（需 LLM 語意判斷，linter 做不到）
- ⏳ **待使用者裁決**：comprehension 觸發頻率——修掉吸收態後，弱學生連答 10 題會被驗 10 次
  （每次 2 呼叫）。屬教學取捨不是 bug，建議 7-E 實際點過再定
- **7-E 使用者驗收在 7-D 之後**；本 session 新做的 UI（理解驗證 Modal / AI 鎖 / NZEC 說明 /
  揭露階梯）全部留到那輪驗，清單項已寫入 `docs/acceptance-checklist.md` 4-6~4-9 與 5-5a~g
- 之後：Phase 8 / 7-2 監控 / 7-3 效能 / 5-3·5-4

**排在驗收之後**：Phase 8 專案健檢（8-0 討論已完成）／6-4b 教材局部重跑（依操作回饋）／K1d·K4d·K5d 使用者自測

**工具**：`python3 scripts/doc_selfcheck.py` — 文件自檢（超門檻檔案／失效路徑／測試數）；session 結束前跑一次
**健檢**：`.claude/skills/code-health/` — 檔案大小與重複的**決策**工作流（門檻 250/400、
三問判斷、舉證豁免、jscpd 重複偵測）。改完一個邏輯變更後跑，**不在每次 Edit 後跑**
**驗收機制**：`backend/scripts/eval_coddy/` — 七型學生模擬（真實 LLM + debug_sink/DB 白盒探針），改完 Coddy 重跑對照

**部署與營運**：見 `docs/deployment.md`。要點＝**push 即自動部署**、migration 自動跑；
**唯獨改環境變數必須手動重啟 service**；OAuth 測試模式 100 人上限（Step 6 與已知限制節）。

## 文件索引
> 本文件目標 ≤ 60 行。新增內容先判斷歸屬，禁止回填 roadmap/日誌/UI 參數/Schema。

**`.claude/rules/`**（編輯對應檔案時自動注入，無需手動查閱）
- `frontend.md` — Design Tokens、元件規格、響應式斷點（glob: `web/**`）
- `backend.md` — 錯誤處理、安全規範、環境變數（glob: `backend/**`）
- `edf-pipeline.md` — EDF 三層管線、ConceptTag、出題流程（glob: `backend/services/edf/**`）

**`docs/`**（按需查閱，預設不主動讀）
- [dev-setup.md](docs/dev-setup.md) — **本機環境啟動 SOP（每次 session 必讀 §1）**
- [acceptance-checklist.md](docs/acceptance-checklist.md) — **真人驗收清單（依操作動線分 0~9 段；2026-08-06 全面重寫）**
- [roadmap.md](docs/roadmap.md) — 任務追蹤（精簡）/ [roadmap-archive.md](docs/roadmap-archive.md) — 完成細節（凍結）
- [changelog.md](docs/changelog.md) — 變更日誌（時間序）
- [architecture.md](docs/architecture.md) / [modules.md](docs/modules.md) / [db-schema.md](docs/db-schema.md)
- [ui-ux-spec.md](docs/ui-ux-spec.md) / [ui-wireframes.md](docs/ui-wireframes.md)（實作該頁時才讀）
- [api-spec.md](docs/api-spec.md) / [deployment.md](docs/deployment.md)（§E = Runner 部署 SOP）/ [server-plan.md](docs/server-plan.md) — A 機 + B 機 Runner 專用機（2026-08-05 改版）
- [design-plan.md](docs/design-plan.md) — 統一視覺協議（實作 UI 前才讀）
- [tech-debt.md](docs/tech-debt.md) / [references.md](docs/references.md)
