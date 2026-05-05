# 技術債追蹤

> 記錄已知的技術債項目，每次消除後標記 ✅ 並註明日期。

## ⚠ 待處理

### 部署相關（待實測）
- [ ] **Zeabur PREBUILT + source.type=IMAGE schema 未實測**
  - 4-1b 將 `zeabur.json` 的 postgres 從 marketplace `postgresql`（不含 pgvector）改為 `template: PREBUILT` + `source: {type: "IMAGE", image: "pgvector/pgvector:pg16"}`
  - 此 schema 細節依 Zeabur template.json 規範撰寫，但**未經實際部署驗證**
  - **如何處理**：4-2 實際 Zeabur 部署時若 schema 被拒，依 deployment.md §A 的 fallback 改用 marketplace pgvector 或 GIT + 一行 Dockerfile
- [ ] **Judge0 自架 docker-compose 未在生產驗證**
  - 4-1c 新增 `docker-compose.judge0.yml` + `judge0.conf.example`，僅在規格層面撰寫
  - **限制**：Zeabur 等雲平台禁用 `privileged: true` → 自架 Judge0 只能在自己的 VPS 跑
  - **如何處理**：self-host VPS 部署時實測 stack 啟動 → workers 成功 register languages → backend 能透過 `/about` 與 `/submissions` 對話；若 worker fail 多半是 cgroups / privileged 問題

### 環境設定（使用者手動）
- [ ] **`backend/.env` 的 `OPENAI_API_KEY` 未填**
  - **影響**：2-1b 跑 LlamaIndex 索引、EDF Chat 互動會 401
  - **如何處理**：使用者手動填入；不可由 AI 寫入（敏感資訊）
- [ ] **git user.name / user.email 未設定**
  - **影響**：commit `3f702be` 與後續 commits 會用系統預設身分顯示在 GitHub
  - **如何處理**：
    ```bash
    git config --global user.name "你的名字"
    git config --global user.email "你的 email"
    ```

### 內容層（教學課綱）
- ✅ ~~`concept_edges` seed 的 23 條邊為 AI 暫定值~~ — 2026-05-05 完全替換為 58 條線性 PREREQUISITE（隨 e1f2a3b4c5d6 重 seed）
- ✅ ~~`concepts` seed 的 `category` / `difficulty_level` / `name_zh` 為暫定值~~ — 2026-05-05 完全替換為 59 影片 concept

### 內容層（教學課綱）— 新一批待補
- [ ] **YT video metadata 未補**（59 個影片 concept 全部 `video_youtube_id` / `video_duration_seconds` 為 NULL）
  - **影響**：3-1d 學習單元頁的概念說明 tab 無法 embed YT player；只能顯示影片標題與「待補」placeholder
  - **如何處理**：教授整理 59 個影片的 YT URL + 時長 → AI 寫 PATCH script 一次匯入（不需新 migration）
  - **建議格式**：CSV 或 JSON，欄位 `video_order, youtube_id, duration_seconds`
- [ ] **跨章節 PREREQUISITE 邊未標**（目前只有線性 04→05→...→62 共 58 條）
  - **影響**：拓撲排序生成路徑時，學生 confidence 高跳過某 unit 後不會牽連解鎖實際依賴的後續 unit
  - **範例**：47 遞迴函式真正依賴 36 函式 + 29 for 迴圈；52 指標與陣列依賴 48 陣列 + 51 指標；目前圖譜只有 N→N+1 線性鏈
  - **如何處理**：教授標關鍵跨章依賴（< 30 條）→ AI 加 patch migration
- [ ] **學習單元 content 為空骨架**（`{summary: "", examples: [], exercise_question_ids: []}`）
  - **影響**：3-1d 學習單元頁的「範例程式」「摘要」tab 無實質內容
  - **如何處理**：兩種策略可選 —
    - (a) LLM 依 concept name + difficulty 自動生成 summary + examples（成本低）
    - (b) 教授/助教手動填寫（品質高，工時大）
  - **建議**：先 (a) MVP，看品質再決定是否人工校對

### Learn 頁面視覺化升級
- [ ] **3-1c 卡片版 ≠ ui-wireframes.md 期望的「節點+箭頭」graph 版**
  - **影響**：與知識圖譜頁 (`/knowledge`) 風格不統一；無法直觀顯示 PREREQUISITE 依賴的分支
  - **如何處理**：3-1d/e 完成後，回頭把 detail 頁從 ordered list 升級為 reactflow / d3 graph（可復用 knowledge 頁的元件）

### EDF Mastery 連動暫時退場
- [ ] **EDF chat 評估的 ConceptTag 不再寫入 BKT mastery**
  - **背景**：3-1c+ 把 concepts 表完全替換為 59 影片 concept；EDF 的 20 粗 tag 只留在 `services/edf/models.py` enum 給 LLM 提示用；`update_mastery` 找不到 concept 自動跳過
  - **影響**：學生在 Workspace 與 AI Tutor 對話時的 mastery 不再上下調；只有 quiz 答題 + comprehension 驗證會驅動 BKT
  - **如何處理**：兩種策略可選 —
    - (a) 接受現狀（chat 評估本來噪音多，quiz/comprehension 是更可信信號）
    - (b) 在 concepts 表加 `edf_parent_tag` 欄位，建立粗 tag → 多影片 concept 的 mapping，讓 EDF 評估平均更新到對應影片 concept

### 程式碼層
- ✅ ~~`backend/requirements.lock` 過時~~ — 2026-05-05（4-1a）已透過 `uv pip compile pyproject.toml -o requirements.lock` 重產（38 行 → 272 行，含全部 transitive）；pyproject.toml 補完 LlamaIndex 三套件 + psycopg2-binary。pyBKT 註解確認**未實際 import**（updater.py 註解保留為未來演算法升級線索），無需安裝
- [ ] **`backend/pyproject.toml` 沒設 hatchling packages**
  - 直接 `pip install -e .` 會失敗（hatchling 找不到 wheel target）
  - 目前繞過：直接列依賴而非 install self
  - **如何處理**：因 backend 是 application 不是 library，可加 `[tool.hatch.build.targets.wheel] packages = [...]` 或改用 `uv sync`（需要重組為 src/ layout）

## ✅ 已消除

（無）
