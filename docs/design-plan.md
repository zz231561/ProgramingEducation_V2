# 介面設計借鑑計畫

> 參考來源：getdesign.md 收錄之 6 份 DESIGN.md（cursor / warp / linear.app / claude / vercel / raycast），原文存於 `docs/design-references/`。
> 本計畫的核心：**借鑑「結構模式」，不借鑑「視覺基本元素」**。確保 6 份來源不會讓 UI 產生 Frankenstein 違和感。

---

## 0. 視覺統一協議（最高位階，不可違反）

### 0.1 唯一視覺基本元素：GitHub Dark
所有 **color / font / shadow / border / radius / spacing** 一律來自 `.claude/rules/frontend.md`。任何借鑑來源的「色值、字體名稱、陰影 stack、邊框技法、radius 數字」**禁止直接挪用**。

### 0.2 參考來源只貢獻「結構模式」
| 結構模式 | 來源 | 我們渲染用的視覺基本元素 |
|----------|------|--------------------------|
| 多次執行的 block-based 輸出 | Warp | GitHub Dark `#161B22` 實心面 + `#30363D` 實線邊框 |
| AI 操作步驟 timeline | Cursor | GitHub Dark 5 色 accent（blue/green/orange/purple/red） |
| 列表密度 + 命令面板 | Linear | GitHub Dark 實心面 + 實線邊框 |
| 訊息氣泡角色區分 | Claude | GitHub Dark 既有 accent（purple `#BC8CFF`） |
| Metric 數字卡排版 | Vercel | GitHub Dark `#161B22` 實心面 + `#30363D` 邊框 |
| 鍵盤鍵帽形狀 | Raycast | GitHub Dark `#21262D → #161B22` 漸層 |

### 0.3 七條統一規則（檢核違和感的硬標準）

| 規則 | 規格 | 違反信號 |
|------|------|----------|
| **R1 顏色** | 僅用 `frontend.md` 的 GitHub Dark token | 出現 `#f2f1ed` / `#c96442` / `#5e6ad2` / `#FF6363` |
| **R2 字體** | Inter（UI）+ Noto Sans TC（中文）+ JetBrains Mono（Code）三家 | 出現 CursorGothic / Matter / Geist / Anthropic Serif |
| **R3 邊框** | 一律 `1px solid` + GitHub Dark border token | 出現 `box-shadow 0 0 0 1px`（Vercel shadow-as-border）、`rgba(255,255,255,0.08)` 半透明邊（Linear） |
| **R4 陰影** | 僅 3 階：flat / card / modal（見 §3.2） | 出現 4 層以上 stack、inset 高光（Raycast 風格只允許在「鍵帽」單一元件） |
| **R5 Radius** | 僅 5 階：4 / 6 / 8 / 12 / 9999（pill） | 出現 32px、86px、22px、3px、1.5px |
| **R6 Hover** | Surface 元件：背景升一階；Button：背景升一階；Link：文字色轉 `#58A6FF` | 出現 opacity 0.6、文字轉暖紅 `#cf2d56` |
| **R7 字距** | Display ≥40px → -0.02em；Body 維持預設 0；UI label → `font-feature-settings: "cv01", "ss03"` | 出現 -2.4px / -2.88px 極端壓縮、+0.4px 大正字距 |

> **檢驗法**：任一新元件實作完成後，逐條對 R1-R7 自檢。若違反 → 退回，用 GitHub Dark 重新渲染。

---

## 1. 各區塊借鑑對照表（簡版）

| 區塊 | 借鑑「結構」 | Phase |
|------|--------------|-------|
| Workspace 三欄佈局 | Cursor — Editor + AI Chat 並列 | 已完成 |
| EDF Pipeline 視覺化 | Cursor — AI 操作 timeline | 1-6 |
| Editor 包覆框 | Cursor — screenshot framing 結構 | 1-6 |
| Output Panel Run Block | Warp — 每次執行為獨立 block | 1-6 P0 |
| Chat 訊息氣泡 | Claude — ring 區分 user/AI | 1-6 P0 |
| Toolbar | Linear — 緊湊 nav + tab | 1-6 |
| Learn / Quiz 列表 | Linear — 高密度 row + chip filter | 2-2 |
| Dashboard 數據卡 | Vercel — metric 大數字排版 | 2-3 |
| Landing / Login | Vercel — gallery emptiness 大留白 | 2-4 |
| Cmd+K 命令面板 | Raycast — 浮動面板 + 多層陰影 | 2-5 |
| 鍵盤鍵帽 `.kbd` | Raycast — 漸層鍵帽 | 2-5 |

---

## 2. 各區塊借鑑細節

### 2.1 EDF Pipeline 視覺化（結構：Cursor AI Timeline）

學生在 Chat 收到 AI 回覆前，先看一條極簡 timeline 顯示 AI 的教學決策過程。**這是把 EDF 三層管線變成可教學的 UI 元素**，是借鑑 Cursor 最有價值的單點。

```
[●] Evidence  →  [●] Decision  →  [●] Feedback   ← 完成的步驟用 accent 色實心
[○] RAG（若觸發）                                   ← 未觸發用空心
```

| EDF 階段 | 用 GitHub Dark token |
|----------|---------------------|
| Evidence | `#D29922`（orange） |
| Decision | `#BC8CFF`（purple） |
| Feedback | `#3FB950`（green） |
| RAG | `#58A6FF`（blue，僅在觸發時點亮） |

點 size：8px 實心圓；連接線：`1px solid #30363D`；背景：`#161B22`；高度：32px。

### 2.2 Editor 包覆框（結構：Cursor）

CodeMirror 外加 `1px solid #30363D` + 8px radius。Editor toolbar（檔名 / Run）背景 `#161B22`，主體 `#0D1117`。

### 2.3 Output Panel Run Blocks（結構：Warp，視覺：GitHub Dark）

每次 Run 為獨立 block，可摺疊、複製、加註，已實作的「Run 結果注入 Chat」改用 block 內按鈕觸發。

```
┌─ Block Header ──────────────────────────────────┐
│ ▼ Run #3   14:32  ✓ Accepted  124ms   [📋][💬]   │
├─────────────────────────────────────────────────┤
│ stdout: ...                                      │
│ stderr: ...                                      │
└─────────────────────────────────────────────────┘
```

| 元素 | 規格 |
|------|------|
| Block 背景 | `#161B22` |
| Block border | `1px solid #30363D`，radius 6px |
| Block 間距 | 8px gap，新 block 從頂部插入 |
| Header 高度 | 32px（摺疊狀態僅顯示 header） |
| Status badge | Accepted → `#3FB950` text on `rgba(63,185,80,0.1)` bg；Error → `#F85149`；CE → `#D29922`；TLE/MLE → `#8B949E` |

> 不借鑑 Warp 的半透明邊框（違反 R3）、Matter 字體（違反 R2）。

### 2.4 Chat 訊息氣泡（結構：Claude，視覺：GitHub Dark）

借 Claude「用邊框區分角色」的單一概念。**這是全站唯一可使用 ring shadow 的位置**。

| 角色 | 規格 |
|------|------|
| User 訊息 | 背景 `#161B22`，`1px solid #30363D`，radius 12px |
| AI 訊息 | 背景 `#161B22`，`1px solid rgba(188,140,255,0.25)`（GitHub Dark purple 25% alpha），radius 12px |
| 訊息間距 | 12px gap |
| Line-height | 1.6（中文可讀性） |

**Bloom 等級指示器（每則 AI 訊息底部）：** pill 形 12px Inter 500，padding 2px 8px，border `1px solid #30363D`，radius 9999px。配色：

| Bloom 等級 | 色（pill text） |
|-----------|----------------|
| L1 REMEMBER | `#8B949E` |
| L2 UNDERSTAND | `#58A6FF` |
| L3 APPLY | `#3FB950` |
| L4 ANALYZE | `#D29922` |
| L5 EVALUATE | `#BC8CFF` |
| L6 CREATE | `#F85149` |

> 不借鑑 Claude Anthropic Serif（R2）、Parchment 背景（R1）、Terracotta 主色（R1）。

### 2.5 Toolbar（結構：Linear，視覺：GitHub Dark）

- 高度 48px，背景 `#0D1117`，底部 `1px solid #21262D`
- Tab active：`border-bottom: 2px solid #F78166`（已是 frontend.md 規範）
- 左：Logo + 5 個頁籤；中：當前檔名 + 儲存狀態 dot；右：Run + Chat Toggle + Avatar
- **全站套用 Inter OpenType `cv01, ss03`** — 一行 CSS，提升 Inter 的工程化字感

### 2.6 Learn / Quiz 列表（結構：Linear，視覺：GitHub Dark）

| 元素 | 規格 |
|------|------|
| Row 高度 | 48px，padding 12px 16px |
| Row 背景 | `#161B22` |
| Row hover | 升一階至 `#1C2128` |
| Row 邊框 | 底部 `1px solid #21262D`（連續清單共用底線） |
| 篩選 chip | radius 9999px，padding 2px 10px，`1px solid #30363D`，12px Inter 500，active 改 `1px solid #6E7681` |
| Card radius | 8px |

> 不借鑑 Linear 的 `rgba(255,255,255,0.02)` 半透明面（R3 違反）、Brand indigo（R1）、weight 510（R2 — Tailwind 無此字重）。

### 2.7 Dashboard 數據卡（結構：Vercel，視覺：GitHub Dark）

| 元素 | 規格 |
|------|------|
| Card 背景 | `#161B22` |
| Card border | `1px solid #30363D`，radius 8px |
| Card 陰影 | Level 1（見 §3.2） |
| Metric 數字 | 48px Inter weight 600，line-height 1.0，letter-spacing -0.96px |
| Metric 描述 | 14px Inter weight 400，`#8B949E`，line-height 1.5 |
| Metric trend | 12px JetBrains Mono，up: `#3FB950`，down: `#F85149` |

> 不借鑑 Vercel shadow-as-border（R3 違反）、Geist 字體（R2）、Workflow 三色（R1）。

### 2.8 Landing / Login（結構：Vercel）

- 背景 `#0D1117`，section 垂直 padding 80px（mobile 48px）
- Hero 標題 48px Inter weight 600，line-height 1.1，letter-spacing -0.96px
- CTA 兩個並排：primary `#238636`（綠）+ secondary `#21262D` border `#363B42`
- 不採 Vercel 純白背景。

### 2.9 Cmd+K 命令面板（結構：Raycast，視覺：GitHub Dark）— Phase 2-5

> Phase 1 不實作，僅預留設計。

| 元素 | 規格 |
|------|------|
| 面板尺寸 | 600 × 400px，置中浮動 |
| 背景 | `#161B22` |
| Border | `1px solid #30363D`，radius 12px |
| 陰影 | Level 2 modal（見 §3.2） |
| Result row hover | 背景升至 `#1C2128` |

### 2.10 鍵盤鍵帽 `.kbd`（結構：Raycast，視覺：GitHub Dark）

**全站套用**（tooltip、選單項、Cmd+K 結果列）。**這是全站唯一可使用多層陰影的元件**。

```css
.kbd {
  background: linear-gradient(180deg, #21262D 0%, #161B22 100%);
  border-radius: 4px;
  padding: 2px 6px;
  font: 11px JetBrains Mono;
  color: #C9D1D9;
  box-shadow:
    rgba(255, 255, 255, 0.04) 0 1px 0 0 inset,
    rgba(0, 0, 0, 0.3) 0 1px 2px 0,
    rgba(0, 0, 0, 0.2) 0 -1px 0 0 inset;
}
```

> 此元件是 R4 的合法例外。其他元件不可使用 inset 高光。

---

## 3. Design Token 增補（寫入 `frontend.md`）

### 3.1 Surface Stack（純 GitHub Dark hex，無 rgba）

| Token | 值 | 用途 |
|-------|-----|------|
| `--surface-0` | `#0D1117` | Page canvas、Toolbar |
| `--surface-1` | `#161B22` | Card、Output block、Chat 氣泡、Modal |
| `--surface-2` | `#1C2128` | Hover / Active row |
| `--surface-inset` | `#010409` | Code editor 主體 |

### 3.2 Shadow Stack（僅 3 階）

| Token | 值 | 用途 |
|-------|-----|------|
| Level 0 | none | 預設 flat |
| `--shadow-card` | `0 1px 3px rgba(0,0,0,0.3)` | Card 提升 |
| `--shadow-modal` | `0 16px 48px rgba(0,0,0,0.5), 0 0 0 1px #30363D` | Modal / Cmd+K |
| `.kbd` 多層陰影 | 見 §2.10 | 鍵帽唯一例外 |

### 3.3 Border（單一技法：實線）

| Token | 值 | 用途 |
|-------|-----|------|
| `--border-muted` | `1px solid #21262D` | 連續行底線、toolbar 底 |
| `--border-default` | `1px solid #30363D` | Card / block 預設 |
| `--border-emphasis` | `1px solid #6E7681` | Focus / Selected |
| `--border-ai` | `1px solid rgba(188,140,255,0.25)` | AI 訊息氣泡（唯一例外，Bloom purple） |

### 3.4 Typography 全站設定

```css
/* 全站 Inter OpenType（提升工程感） */
body { font-feature-settings: "cv01", "ss03"; }

/* 顯示字級字距（≥40px） */
.display { letter-spacing: -0.02em; line-height: 1.1; }

/* Body 中文閱讀（chat、editorial） */
.body-reading { line-height: 1.6; }

/* UI 緊湊（按鈕、navlink） */
.body-ui { line-height: 1.4; }
```

三權重：400 / 500 / 600。**禁用 700。**

### 3.5 Radius Scale（5 階）

| 用途 | 值 |
|------|-----|
| Inline / micro | 4px |
| Button / input | 6px |
| Card / block | 8px |
| Hero / modal / chat 氣泡 | 12px |
| Pill / badge | 9999px |

### 3.6 Hover 統一（單一規則）

| 元素類型 | 規則 |
|----------|------|
| Surface（card、row） | 背景升一階：`--surface-1` → `--surface-2` |
| Button primary | `#238636` → `#2EA043`（已是 frontend.md） |
| Button default | `#21262D` → `#30363D` |
| Link | 文字色轉 `#58A6FF` |
| Icon button | 背景由 transparent → `rgba(255,255,255,0.04)` |

> 禁用 `opacity: 0.6`（Raycast 風）、文字轉暖紅 `#cf2d56`（Cursor 風）。

---

## 4. 實作優先序（合併為 Phase 1-6「介面精修」）

| # | 子任務 | 規格出處 | 預估工 |
|---|--------|----------|--------|
| 1-6a | Surface / Shadow / Border / Radius token 增補 | §3.1-3.5 | 極小 |
| 1-6b | Inter `cv01, ss03` 全站套用 + 三權重檢核 | §3.4 | 極小 |
| 1-6c | Output Panel Run Block 化 + status badge | §2.3 | 中 |
| 1-6d | Chat 訊息氣泡 ring + Bloom badge | §2.4 | 小 |
| 1-6e | Toolbar Linear 風格化 | §2.5 | 小 |
| 1-6f | EDF Pipeline mini timeline（在 Chat 訊息上方） | §2.1 | 中 |

> 完成 1-6 後再進 1-7c 上線驗證，避免上線後再大幅改 UI。

---

## 5. 違和感檢查清單（每個元件實作後逐條檢核）

```
□ R1 顏色：所有色值來自 frontend.md token？無外來 hex？
□ R2 字體：僅 Inter / Noto Sans TC / JetBrains Mono？
□ R3 邊框：實線 1px + GitHub Dark border？無 shadow-as-border？無半透明邊？
□ R4 陰影：屬於 §3.2 三階之一？或為 .kbd 例外？
□ R5 Radius：4 / 6 / 8 / 12 / 9999 之一？
□ R6 Hover：surface 升一階？或符合 §3.6？
□ R7 字距：display -0.02em？body 預設 0？
□ AI 角色信號：僅 Chat AI 氣泡使用 purple ring？
□ Bloom badge：6 色僅用於 Bloom 等級？
□ EDF timeline：4 色僅用於 EDF 階段？
```

任一條 ✗ → 退回該元件，用統一規格重做。

---

## 6. 後續動作

1. **此計畫經確認後**：
   - 在 `docs/roadmap.md` 新增 **Phase 1-6：介面精修**（6 個子任務）
   - 在 `.claude/rules/frontend.md` 增補 §3 全部 token
   - 在 `docs/changelog.md` 記錄計畫產出
   - git commit + push
2. **每完成一個 1-6 子任務**：跑 §5 檢查清單，確認後請使用者驗收。
3. **Phase 2 預留任務**：1-6 完成後，Cmd+K + Landing/Login + Dashboard 進入 Phase 2 實作。

---

> **參考檔案：** `docs/design-references/{cursor,warp,linear.app,claude,vercel,raycast}.md`（共 1819 行原文，留作後續查閱）
