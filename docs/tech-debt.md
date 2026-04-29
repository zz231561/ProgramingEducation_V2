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

### 程式碼層
- [ ] **`backend/requirements.lock` 過時**
  - 缺少 `cryptography`、`PyJWT`、`authlib`、`openai`、`pgvector`、`alembic` 等實際使用的套件
  - 目前 dev 依賴從 `pyproject.toml` 抽出後直接 `uv pip install`，未使用 lock
  - **如何處理**：Phase 4-1a 容器化前用 `uv pip compile pyproject.toml -o requirements.lock` 重產
- [ ] **`backend/pyproject.toml` 沒設 hatchling packages**
  - 直接 `pip install -e .` 會失敗（hatchling 找不到 wheel target）
  - 目前繞過：直接列依賴而非 install self
  - **如何處理**：因 backend 是 application 不是 library，可加 `[tool.hatch.build.targets.wheel] packages = [...]` 或改用 `uv sync`（需要重組為 src/ layout）

## ✅ 已消除

（無）
