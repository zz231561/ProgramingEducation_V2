# 技術債追蹤

> 記錄已知的技術債項目，每次消除後標記 ✅ 並註明日期。

## ⚠ 待處理

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
- [ ] **`concept_edges` seed 的 23 條邊為 AI 暫定值**
  - **影響**：知識圖譜佈局聚類、Detail Panel 的「先修/進階」清單、未來路徑生成 (3-1) 都會用到
  - **內容**：20 prerequisite + 3 related，依常見 C++ 教學順序；其中 `function-design → oop-encapsulation` 與 `oop-polymorphism → template-meta` 屬可爭議選擇
  - **如何處理**：實際使用後依教師回饋調整；可發 patch migration 增刪邊或建管理介面
- [ ] **`concepts` seed 的 `category` / `difficulty_level` / `name_zh` 為暫定值**
  - **影響**：知識圖譜 (2-2c) 的分類聚合、出題 (2-4) 的難度過濾、Learn 頁面 (3-1) 的學習路徑生成都會吃這些值
  - **暫定來源**：AI 在 2-2a 依 C++ 教學常見譯名 + 經驗判斷填入；20 個 ConceptTag 本身是 authoritative（來自 `.claude/rules/edf-pipeline.md`），但 enrichment 欄位非
  - **如何處理**：等 2-2c 圖譜可視化後校準（視覺上判斷 category 聚合是否協調）；之後可能要 patch migration 或建管理介面修改

### 程式碼層
- [ ] **`backend/requirements.lock` 過時**
  - 缺少 `cryptography`、`PyJWT`、`authlib`、`openai`、`pgvector`、`alembic` 等實際使用的套件
  - **2-1b 新增**：`llama-index`、`llama-index-vector-stores-postgres`、`llama-index-embeddings-openai`、`psycopg2-binary`、`tiktoken`（共 28+ 個 transitive deps）也未進入 `pyproject.toml`
  - 目前 dev 依賴從 `pyproject.toml` 抽出後直接 `uv pip install`，未使用 lock
  - **如何處理**：Phase 4-1a 容器化前用 `uv pip compile pyproject.toml -o requirements.lock` 重產（並先把 2-1b 新增的 LlamaIndex 套件補進 `pyproject.toml`）
- [ ] **`backend/pyproject.toml` 沒設 hatchling packages**
  - 直接 `pip install -e .` 會失敗（hatchling 找不到 wheel target）
  - 目前繞過：直接列依賴而非 install self
  - **如何處理**：因 backend 是 application 不是 library，可加 `[tool.hatch.build.targets.wheel] packages = [...]` 或改用 `uv sync`（需要重組為 src/ layout）

## ✅ 已消除

（無）
