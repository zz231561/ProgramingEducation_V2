# 變更日誌

## [2026-04-29] — OSS 重用策略落地 + Roadmap 重排（功能優先、部署延後）

### 新增
- `docs/references.md` §1 **OSS 重用決策矩陣**（4 Tier 分級）：
  - **Tier 1 立即依賴**：pyBKT、LlamaIndex、Cytoscape.js、Vercel AI SDK、prefixspan
  - **Tier 2 Schema 採用**：ProgSnap2 EventType、StudyChat dialogue act
  - **Tier 3 Clone 研讀**：DeepTutor、Mr. Ranedeer、JetBrains Edu Plugin
  - **Tier 4 不採用**：PM4Py（AGPL 風險）、OATutor BKT port、EduAdapt-AI RL、BloomBERT、Socratic-LLM
- `docs/references.md` §2 **授權白名單／黑名單**：嚴禁 AGPL-3.0 / GPL-3.0；MIT / Apache-2.0 / BSD-3 / ISC 直接採用
- `CLAUDE.md` 執行守則 #7 **避免重複造輪子（OSS 優先）**：開發前必查決策矩陣，新增 dependency 必須 PR 列出 license

### 變更
- `docs/roadmap.md` **重排執行順序**：
  - 移除原 Phase 1-7（部署）→ 新增 **Phase 4：部署上線**（4-1 容器化 / 4-2 Zeabur / 4-3 上線驗證）
  - 原 Phase 4 教師端 → **Phase 5**（5-1 ~ 5-5 全數重編）
  - 執行順序：Phase 2 智慧功能 → Phase 3 學習體驗 → Phase 4 部署 → Phase 5 教師端
  - **理由**：API 串接 + Zeabur 反覆卡關，先把學生端做完一次性處理部署
- `docs/roadmap.md` 各 Phase 任務加註 **OSS 標記**：
  - 2-1 RAG → LlamaIndex `PGVectorStore`
  - 2-2 知識圖譜 → Cytoscape.js + fcose
  - 2-3 精熟度 → **pyBKT，禁止 port OATutor**
  - 3-1 學習路徑 → 拓撲排序，**不採用 EduAdapt-AI RL**
  - 5-2 行為事件 → ProgSnap2 + StudyChat schema
  - 5-3 行為分析 → pyBKT + prefixspan，**禁止用 PM4Py**
- `CLAUDE.md` 當前狀態區塊壓縮為摘要（Phase 1 全完成 + 下一步 Phase 2 任務清單）

### 已確認決策（roadmap.md）
- 新增「OSS 重用」與「執行順序」兩條長期決策

## [2026-04-29] — Login hero 移除主標 `Code with Edge`，避免與 h1 `Codedge` 重複

### Changed
- `web/app/login/page.tsx` — 移除中間的「Code with Edge」副 slogan 行：h1 `Codedge` 已等同於拆解後的字面，再放等於重複。保留唯一副標「會思考的學習，從會提問的 AI 開始」（mt-2 text-sm secondary）

### Kept
- `web/app/layout.tsx` `<title>` 仍保留「Codedge — Code with Edge」：browser tab / SEO 場景單獨出現，「Code with Edge」首次接觸者揭示品牌雙關，無視覺重複

## [2026-04-29] — Slogan 改版：雙標題式 hero（Code with Edge）

### 命名邏輯
- **主標 `Code with Edge`** — 直接拆解 `Codedge` 字母，三層意義同步：cutting-edge / edge case / have the edge
- **副標「會思考的學習，從會提問的 AI 開始」** — 點出 EDF Pipeline 蘇格拉底式提問教學差異化（vs ChatGPT 直接給答案）
- 取代原 slogan「Coddy 陪你寫 C++，磨穿每個 edge case」（受苦感、未體現品牌雙關）

### Changed
- `web/app/login/page.tsx` — login hero 由單行改為雙標題：`Code with Edge`（text-base font-medium）+「會思考的學習，從會提問的 AI 開始」（text-sm secondary）
- `web/app/layout.tsx` — `<title>` "Codedge" → "Codedge — Code with Edge"；description 更新為中文價值主張，強調蘇格拉底式提問與不直接給答案

## [2026-04-29] — 品牌命名：**Codedge** 平台 + **Coddy** AI 助教

### 命名邏輯
- **Codedge** = `Code` + `Edge` 字母融合（共享 `e`）。三層意義：(1) Cutting-edge 程式前沿、(2) Edge case 邊界案例（CS 核心術語）、(3) "have the edge" 取得競爭優勢
- **Coddy** = AI 助教名，承襲 `Cod-` 字頭與品牌 `Codedge` 兄妹呼應

### Changed — 全站 rename
- `web/components/layout/global-nav.tsx` — Logo "C++ Tutor" → **Codedge**；chat toggle title/aria "AI 導師" → "Coddy"
- `web/components/layout/chat-panel.tsx` — header "AI 導師" → "Coddy"
- `web/components/layout/tablet-header.tsx` — "C++ Tutor" → "Codedge"
- `web/components/chat/message-list.tsx` — "AI 導師隨時為你解答" → "Coddy 隨時為你解答"；"AI 導師思考中…" → "Coddy 思考中…"
- `web/components/chat/run-result-card.tsx` — "AI 導師已取得..." → "Coddy 已取得..."（含註解）
- `web/components/workspace/run-block.tsx` — 「💬 詢問 AI 導師」按鈕 title/aria → "詢問 Coddy"
- `web/app/login/page.tsx` — `<h1>` "C++ Tutor" → "Codedge"；副標 "AI 驅動的 C++ 程式教學平台" → "Coddy 陪你寫 C++，磨穿每個 edge case"
- `web/app/layout.tsx` — `<title>` "ProgramingEducation" → "Codedge"；description 更新為「Codedge — AI-powered C++ programming education with Coddy」
- `backend/core/config.py` — `APP_NAME` "ProgramingEducation API" → "Codedge API"
- `docs/ui-ux-spec.md` + `docs/ui-wireframes.md` — wireframe ASCII / 文案同步更新

### Verified
- `grep` 全 `web/` `backend/` 殘留 "C++ Tutor" 0 處、"AI 導師" 0 處（生產代碼）
- TypeScript `tsc --noEmit` exit 0
- changelog 歷史紀錄保留「C++ Tutor」原貌不修改

## [2026-04-29] — Chat toggle 改為「僅收合時顯示」

### Changed
- `web/components/layout/global-nav.tsx` — chat toggle 按鈕從「總是顯示」改為「`!chatOpen` 時才渲染」：chat 開啟時隱藏（避免與 ChatPanel 內收合按鈕重複），chat 收合時顯示 `MessageSquare` icon 提供視覺 affordance 重新開啟
- `web/components/layout/app-shell.tsx` — 恢復傳遞 `chatOpen` / `toggleChat` props 至 `<GlobalNav />`

### UX
- Chat 開啟：右上只見 Avatar 下拉（極簡）
- Chat 收合：右上出現訊息 icon（一鍵展開）+ Avatar 下拉
- Ctrl+B 仍可全狀態切換

## [2026-04-29] — 移除 GlobalNav chat toggle 與 ChatPanel header 訊息 icon

### Removed
- `web/components/layout/global-nav.tsx` — 移除右上角 chat toggle 按鈕（`MessageSquare` / `PanelRightOpen` icon）；連帶移除已 orphan 的 `chatOpen` / `onToggleChat` props
- `web/components/layout/chat-panel.tsx` — 移除 ChatPanel header「AI 導師」文字左側的 `MessageSquare` icon，header 僅保留純文字 + 右側 SessionList + 收合按鈕

### Changed
- `web/components/layout/app-shell.tsx` — `<GlobalNav />` 不再傳 props（簽名簡化）

### Notes
- Chat 開關現只能透過 **Ctrl+B 全域快捷鍵** 或 **ChatPanel 內收合按鈕** 觸發
- Chat 關閉時無視覺按鈕重新開啟（依使用者要求保持極簡）；若日後需要視覺後備可加回浮動按鈕
- TypeScript `tsc --noEmit` exit 0；其他用到 `MessageSquare` 的場景保留（session-list / message-list 空狀態 / run-block 詢問 AI 按鈕）

## [2026-04-29] — R8 反 AI 感視覺修正（Phase 1-6 follow-up）

> 觸發：使用者指出截圖中右上 chat icon 半透明 halo + 紫色圓 bot 頭像 + `⚠` emoji = 廉價 AI 感。專業工具（Linear/Stripe/Vercel）皆無此風格。

### Added — R8 規則
- `.claude/rules/frontend.md` — 新增 R8 反 AI 感規則（5 條）：禁半透明色背景 / 禁 emoji 符號字 / 禁圓形彩色 halo 頭像 / 禁裝飾性彩色 / active 狀態用 border 不用色背景
- `docs/design-plan.md` §0.3 違和感檢核表新增 R8.1-R8.5
- 例外白名單：`text-text-muted/N` 灰階淡化、`shadcn/ui` 基礎元件、`lucide-react` 線條 icon、實線 border-accent-X

### Changed — 9 處違規修正
- `web/components/chat/message-bubble.tsx` — Avatar 從圓形彩色 halo（`rounded-full + bg-accent-X/20`）改為圓角方型 + border（`rounded-md + bg-surface-1 + border-border-default`），icon 顏色改為 `text-text-secondary` 去除彩色填充
- `web/components/layout/global-nav.tsx` — Logo 從 `◇ C++ Tutor`（Unicode 幾何字 + 藍色 hover）改為純文字「C++ Tutor」；chat toggle active 從 `bg-accent-blue/15 text-accent-blue` 改為 `bg-surface-2 text-text-primary`
- `web/components/workspace/run-block.tsx` — `STATUS_META` 重構：加入 `Icon: LucideIcon` 欄位（Check/AlertOctagon/X/Clock/Minus）；移除標籤中的 `✓`；badge 從半透明色填充（`bg-accent-X/10`）改為實線 border + 純文字色（`border-accent-X text-accent-X`）；export STATUS_META 供 output-panel 復用
- `web/components/workspace/output-panel.tsx` — 將 `collapsedStatusText()` 字串函式改為 `<CollapsedStatusContent />` React 元件，用 lucide icon 取代 `✓` `✗` 符號字
- `web/hooks/use-chat.ts` — 錯誤訊息 `⚠ 無法取得 AI 回應` → `無法取得 AI 回應`
- `web/components/layout/tablet-header.tsx` — hamburger `☰` 字符 → lucide `<Menu />` icon；avatar 占位由 `rounded-full` 改 `rounded-md`
- `web/app/login/page.tsx` — Logo 容器 `bg-accent-blue/10 text-accent-blue` → `bg-bg-canvas border-border-default text-text-secondary`

### Verified
- `grep -rE 'bg-(accent|btn|primary|destructive)[a-z-]*/[0-9]+'` 全程式碼 0 命中（排除 shadcn ui/button.tsx 白名單）
- `grep -rE '✓|✗|⚠|◇|☰|✕'` 全程式碼 0 命中
- TypeScript `tsc --noEmit` exit 0

## [2026-04-29] — Phase 1-6f EDF Pipeline mini timeline + Phase 1-6 全部完成 ✅

### Added
- `web/components/chat/edf-timeline.tsx` — 新建 EDF Pipeline mini timeline：4 步（Evidence orange / Decision purple / Feedback green / RAG blue）8px 圓點 + 連接線；每步附 hint tooltip 解說；前 3 步永遠 active（Phase 1 必經）；RAG 在 Phase 2-1 啟用後才會 active

### Changed
- `web/components/chat/message-bubble.tsx` — AI 訊息有 `evidence` 時，於氣泡上方渲染 `<EdfTimeline />`；max-w-[80%] 容器內排列：timeline + bubble（Bloom badge 仍在 bubble 底部）

### 🎉 Phase 1-6「介面精修」全部完成
- 1-6a Surface / Shadow / Border / Radius token ✅
- 1-6b Inter OpenType + 三權重檢核 ✅
- 1-6c Output Panel Run Block 化 ✅
- 1-6d Chat 訊息氣泡 ring + Bloom badge ✅
- 1-6e GlobalNav 取代 ActivityBar ✅
- 1-6f EDF Pipeline mini timeline ✅

### Verified
- TypeScript `tsc --noEmit` exit 0
- design-plan §0.3 七條視覺統一規則皆遵守（R1 顏色 / R2 字體 / R3 邊框 / R4 陰影 / R5 Radius / R6 Hover / R7 字距）
- 兩處唯一視覺例外：AI 訊息氣泡 ring（border-ai purple alpha）、`.kbd` 鍵帽（待 Phase 2-5 Cmd+K 實作時建立）

## [2026-04-29] — Phase 1-6e GlobalNav 取代 ActivityBar（VSCode sidebar → GitHub top nav）

### Added
- `web/components/layout/global-nav.tsx` — 新建頂部全域導覽（48px 高 / `bg-canvas` / `border-muted` 底）：Logo + 5 頁籤（Workspace / Learn / Quiz / Knowledge / Dashboard）+ Chat Toggle + Avatar 下拉選單（學習總覽 / 通知 / 設定 / 登出）；Tab active 採 `border-bottom: 2px solid #F78166`；click-outside + Escape 關閉下拉

### Changed
- `web/components/layout/app-shell.tsx` — laptop / desktop 將 `ActivityBar` 換為 `GlobalNav` 置於頂部；移除 floating `ChatToggle`（GlobalNav 已含 toggle，避免重複）；laptop chat overlay shadow 改用 `shadow-modal` token
- `web/components/workspace/toolbar.tsx` — 移除 AI 切換按鈕（已上移至 GlobalNav）；新增「未執行版本」橘色 dot（`isDirty` prop）；改用 `border-muted` 底線、`body-ui` 行高、`rounded-pill` 語言 badge
- `web/app/(app)/workspace/page.tsx` — 新增 `isDirty` state：editor 變更時 true、Run 成功後 false；傳給 Toolbar

### Removed
- `web/components/layout/activity-bar.tsx` — 完全刪除（GlobalNav 取代所有功能）

### Layout 哲學變更
- 從 VSCode 風 left sidebar（180px）改為 GitHub 風 top horizontal nav（48px）
- 釋出更多水平空間給 Editor + Chat
- Tablet/Mobile 維持原本 TabletHeader / MobileNav，未來再統一

### Notes
- `global-nav.tsx` 203 行（介於 150 警告與 250 停止之間，可選擇性拆出 AvatarMenu 至獨立檔）
- TypeScript `tsc --noEmit` exit 0

## [2026-04-29] — Phase 1-6d Chat 訊息氣泡 ring + Bloom badge

### Added
- `web/components/chat/bloom-badge.tsx` — 新建 Bloom 6 級 pill badge：6 色取自 GitHub Dark accent token（L1 muted / L2 blue / L3 green / L4 orange / L5 purple / L6 red）+ `extractBloomLevel(evidence)` 防禦性 parse helper

### Changed
- `web/components/chat/message-bubble.tsx` — User / AI 訊息同 `bg-surface-1` 背景；以 border 顏色區分角色（User: `border-default`、AI: `border-ai` GitHub Dark purple 25% alpha ring，符合 R3 邊框唯一例外）；radius 12px (`rounded-xl`)；line-height 1.6 (`body-reading`)；AI 訊息底部顯示 BloomBadge（讀 `evidence.bloom_level`）；Avatar 從 green 改為 purple（與 ring 色呼應）
- `web/lib/chat-types.ts` — `MessageItem` 新增 `evidence?: Record<string, unknown>` 選用欄位
- `web/hooks/use-chat.ts` — `toMessageItem` 將 `msg.evidence` 透傳至 MessageItem，使 BloomBadge 可讀取
- `web/components/chat/message-list.tsx` — 訊息間距從 `space-y-4` (16px) 改為 `space-y-3` (12px) 符合 design-plan §2.4

### Verified
- TypeScript `tsc --noEmit` exit 0
- 5 個檔案皆 ≤ 150 行（bloom-badge 48 / message-bubble 59 / message-list 66 / chat-types 46 / use-chat 122）

## [2026-04-29] — Phase 1-6c Output Panel Run Block 化

### Added
- `web/components/workspace/run-block.tsx` — 新建單一 Run Block 元件：32px header（折疊 chevron / Run #N / 時間 / status badge / runtime / 記憶體 / 📋 複製 / 💬 詢問 AI）+ 可折疊 body（compile / stdout / stderr 分區）+ 5 種狀態分類（accepted / compile-error / runtime-error / limit-exceeded / unknown）

### Changed
- `web/components/workspace/output-panel.tsx` 重寫 — 從單次輸出 tab UI 改為 block list：訂閱 `onExecutionComplete`、新 block 置頂自動收合舊 block（仿 Warp）、panel header 含「清空」按鈕與 block 計數、保留收合單行 status bar 顯示最新 block 摘要
- `web/components/workspace/workspace-context.tsx` — `ExecutionResult` 新增 `time / memory` 選用欄位；新增 `requestChatInjection` + `onChatInjectionRequest` queued listener pattern（chat 收合時點擊 block 「💬」會 queue，等 chat 掛載時 drain）
- `web/components/layout/chat-panel.tsx` — 新增訂閱 `onChatInjectionRequest`，與 auto-inject 共用 `injectExecutionResult`
- `web/app/(app)/workspace/page.tsx` — 移除本地 `output` state（OutputPanel 自管理）、`setExecutionResult` 補傳 `time / memory`、移除 `statusText` 由 OutputPanel 內部生成

### Verified
- TypeScript `tsc --noEmit` exit 0，無錯誤
- `RunResultCard`（chat 內既有執行結果卡片）保持不變，與 RunBlock 各司其職

## [2026-04-29] — Phase 1-6b Inter OpenType + 三權重檢核

### Added
- `web/app/globals.css` — `body` 套用 `font-feature-settings: "cv01", "ss03"`（Inter 單層 'a' + 幾何字形，全站生效）
- `web/app/globals.css` — Typography helper classes：`.display`（≥40px 字級用，-0.02em 字距 + 1.1 行高）、`.body-reading`（chat/段落用，1.6 行高）、`.body-ui`（按鈕/nav 用，1.4 行高）

### Changed
- `web/components/layout/activity-bar.tsx` — Logo `◇` 從 `font-bold` (700) 改為 `font-semibold` (600)，遵守 R7 三權重系統

### Verified
- `grep` 全 `web/` 確認無剩餘 `font-bold` / `font-extrabold` / `font-black` / `font-weight: 700+`
- 既有元件已使用 `font-medium` (500) / `font-semibold` (600) / 預設 (400)，全數符合 R7

## [2026-04-29] — Phase 1-6a Surface/Shadow/Border/Radius token 增補

### Added
- `web/app/globals.css` — `:root` 新增 8 個 token：
  - Surface 語義別名 4 個（`--surface-0/1/2/inset`）疊加既有 `--bg-*`，不破壞 backward compatibility
  - Shadow stack 2 個（`--shadow-card`、`--shadow-modal`）
  - Border AI ring 例外 1 個（`--border-ai`）
  - Pill radius 1 個（`--radius-pill: 9999px`）
- `web/app/globals.css` — `@theme inline` 對應新增 9 條 Tailwind utility 映射，解鎖 `bg-surface-1` / `shadow-card` / `shadow-modal` / `border-ai` / `rounded-pill`
- `.claude/rules/frontend.md` — Design Tokens 區塊新增「Phase 1-6 統一協議 token」說明列；移除底部 placeholder 註記

### Notes
- 純 additive 變更，所有既有元件與 `--bg-*` 引用 0 影響
- 為 1-6c (Output Run Block) / 1-6d (Chat ring + Bloom badge) / 1-6e (Toolbar + .kbd) 鋪設 token 基礎

## [2026-04-29] — Phase 1-2 Google OAuth 本機端到端驗證通過

### Verified
- `web/.env.local` 建立完成（`AUTH_SECRET` 由 `openssl rand -base64 33` 產生；`AUTH_GOOGLE_ID` / `AUTH_GOOGLE_SECRET` 已填入 Google Cloud Console 取得的憑證）
- Google OAuth 登入流程實測通過：`/login` → Google 同意畫面 → 重導 `/workspace`
- NextAuth v5 `MissingSecret` 錯誤已排除，`/api/auth/session` 不再回 500

### Notes
- Google Cloud Console OAuth 用戶端設定：Authorized redirect URI = `http://localhost:3000/api/auth/callback/google`；測試使用者已加入 `abbyabby41@gmail.com`
- `.env.local` 受 `web/.gitignore` 保護（`.env*` 規則），不會被 commit
- Phase 1-2 Auth 模組 4 子任務（1-2a~d）roadmap 早已勾選，本次為首次完整本機 dev 環境驗證

## [2026-04-29] — Phase 1-6 介面精修計畫產出 + Roadmap 重排

### Added
- `docs/design-plan.md` — 統一視覺協議與 6 份借鑑來源映射計畫；§0.3 七條違和感檢核硬規則；§2 各區塊借鑑細節（含 EDF Pipeline timeline、Output Run Block、Chat ring、Bloom badge）；§3 Token 增補規格
- `docs/design-references/` — 6 份原版 DESIGN.md 收錄（cursor / warp / linear.app / claude / vercel / raycast，共 1819 行原文，自 voltagent/awesome-design-md repo 首次 commit 提取）
- `.claude/rules/frontend.md` — 新增「統一視覺協議」章節，含 R1-R7 違和感檢核 7 條 + 兩處唯一視覺例外

### Changed
- `docs/roadmap.md` — **新增 Phase 1-6「介面精修」**（6 子任務 a-f），對應 design-plan §2-3；**原 Phase 1-6 部署改為 Phase 1-7**，3 子任務全部回退為未完成（上次卡關於 API 串接，1-7c golden path 未通過）
- `CLAUDE.md` — 當前狀態同步：Phase 1-6 改為「介面精修 🔧」、Phase 1-7「部署 ⏸」；新增「介面借鑑：6 份來源僅貢獻結構模式」於已確認決策

### Decision
- **唯一視覺基本元素**：GitHub Dark token，外部 6 份來源不貢獻 color/font/shadow/border/radius/spacing
- **兩處唯一視覺例外**：AI 訊息氣泡 ring（GitHub Dark purple alpha）、`.kbd` 鍵帽多層 inset 陰影
- **執行順序變更**：UI 統一精修先於部署，避免上線後再大幅改 UI

## [2026-04-13] — Phase 1-6a/b 部署配置（Dockerfile + Zeabur）
### Added
- `zeabur.json` — Zeabur Template 定義（web + backend + PostgreSQL + Redis 四服務）
- `backend/start.sh` — 容器啟動腳本：先跑 Alembic migration 再啟動 uvicorn
- `docs/deployment.md` — Zeabur 部署指南（環境變數、service 串接、驗證步驟）

### Changed
- `backend/Dockerfile` — CMD 改為 `start.sh`，啟動時自動執行 DB migration

## [2026-04-13] — Phase 1-5d Chat Panel 收合/展開 toggle
### Added
- `web/components/workspace/toolbar.tsx` — Toolbar 新增 [AI] 按鈕，顯示 Chat Panel 展開/收合狀態（藍色 active / 灰色 inactive）

### Changed
- `web/components/workspace/workspace-context.tsx` — 新增 `chatOpen` / `toggleChat` props，從 AppShell 傳入
- `web/components/layout/app-shell.tsx` — 將 chatOpen/toggleChat 傳入 WorkspaceProvider

### 4 種 toggle 方式
| 方式 | 位置 |
|------|------|
| Toolbar [AI] 按鈕 | Workspace 頂部工具列 |
| ChatPanel 收合按鈕 | Chat 面板 header |
| Ctrl+B 快捷鍵 | 全域 |
| 浮動 ChatToggle | Chat 收合時右上角 |

## [2026-04-13] — Phase 1-5c Run 結果自動注入 Chat context
### Added
- `web/components/chat/run-result-card.tsx` — 執行結果摘要卡片：通過/編譯失敗/執行錯誤狀態 badge + stdout/stderr 預覽
- `web/lib/chat-types.ts` — Chat 型別定義：`MessageItem | ExecutionItem` union type

### Changed
- `web/components/workspace/workspace-context.tsx` — 新增 `onExecutionComplete` 事件訂閱機制（subscribe/notify pattern）
- `web/hooks/use-chat.ts` — 新增 `injectExecutionResult()` 注入執行結果卡片至訊息列表
- `web/components/layout/chat-panel.tsx` — 訂閱執行事件，Run 完成後自動在 Chat 中顯示結果卡片
- `web/components/chat/message-list.tsx` — 支援 `ChatItem` union type 渲染（message / execution）

## [2026-04-13] — Phase 1-5b 對話歷史持久化（session 管理 + 歷史載入）
### Added
- `web/hooks/use-sessions.ts` — session 列表管理 hook：串接 GET/DELETE /chat/sessions API，自動載入歷史 session
- `web/components/chat/session-list.tsx` — session 歷史下拉選單：新對話、切換 session、刪除 session

### Changed
- `web/hooks/use-chat.ts` — 新增 `loadSession(id)` 載入既有對話、`startNewSession()` 開始新對話、`onSessionCreated` 回呼
- `web/components/layout/chat-panel.tsx` — 整合 useSessions + SessionList，header 加入對話歷史按鈕

## [2026-04-13] — Phase 1-5a Chat Panel 元件（訊息氣泡 + 輸入框 + Context 共享）
### Added
- `web/hooks/use-chat.ts` — 聊天狀態管理 hook：訊息列表、session 追蹤、發送訊息（串接 `/chat/interact` REST API）
- `web/components/chat/message-bubble.tsx` — 訊息氣泡元件：user 靠右藍底、assistant 靠左灰底，含頭像
- `web/components/chat/message-list.tsx` — 可捲動訊息列表：自動捲到底部、空狀態提示、loading 動畫
- `web/components/chat/chat-input.tsx` — 聊天輸入框：textarea + Enter 發送、Shift+Enter 換行
- `web/components/workspace/workspace-context.tsx` — WorkspaceContext：用 ref 共享編輯器程式碼與執行結果，不觸發額外 re-render

### Changed
- `web/components/layout/chat-panel.tsx` — 從 placeholder 重構為功能完整的 Chat Panel，整合 MessageList + ChatInput + useChat
- `web/components/layout/app-shell.tsx` — 包裹 WorkspaceProvider、提取 ShellLayout 子元件
- `web/app/(app)/workspace/page.tsx` — 同步程式碼變更與執行結果至 WorkspaceContext

## [2026-04-13] — Phase 1-4e 安全防護：輸入三層防護 + 輸出驗證
### Added
- `backend/services/security/sanitizer.py` — 輸入安全防護 service：
  - Regex 層：12 個 prompt injection 偵測模式（中英文，含角色覆寫、資訊洩漏、直接要求答案）
  - XML 標籤隔離：`<student_input>` / `<student_code>` 包裝使用者輸入
  - `sanitize_input()` — 偵測到 injection 時拋出 422
- `backend/tests/test_sanitizer.py` — 18 個安全防護測試

### Changed
- `backend/services/chat.py` — interact 前先 `sanitize_input()` 過濾使用者提問
- `backend/services/edf/evidence.py` — user prompt 用 `<student_code>` XML 標籤包裝程式碼
- `backend/services/edf/feedback.py` — user message 用 `<student_input>` XML 標籤包裝

### 三層防護完整對照
| 層 | 位置 | 功能 |
|---|---|---|
| 1. Regex | sanitizer.py | 偵測已知 prompt injection 模式 |
| 2. XML 隔離 | evidence.py + feedback.py | 防止 LLM 混淆使用者輸入與系統指令 |
| 3. System Preamble | feedback.py PREAMBLE | 5 條不可覆寫規則 |
| 輸出驗證 | feedback.py validate_output() | 阻擋 >8 行無 TODO 的完整程式碼 |

## [2026-04-13] — Phase 1-4d Chat API 端點
### Added
- `backend/models/chat.py` — ChatSession + ChatMessage SQLAlchemy models（JSON 欄位存 execution_result/evidence）
- `backend/alembic/versions/a1b2c3d4e5f6_create_chat_tables.py` — migration：chat_sessions + chat_messages 表
- `backend/services/chat.py` — Chat service（interact 串接 EDF 三層管線、session CRUD、對話歷史管理）
- `backend/api/routes/chat.py` — 4 個 API 端點：POST /chat/interact、GET /chat/sessions、GET /chat/sessions/{sid}、DELETE /chat/sessions/{sid}
- `backend/tests/test_chat.py` — 4 個 Chat service 測試（建立 session、復用 session、列表、刪除）

### Changed
- `backend/models/__init__.py` — 匯入 ChatSession、ChatMessage
- `backend/main.py` — 註冊 chat router
- `backend/tests/conftest.py` — pytest_configure 改為 drop+create 確保 schema 最新

## [2026-04-13] — Phase 1-4c Feedback 層 prompt 組裝 + 輸出驗證
### Added
- `backend/services/edf/feedback.py` — Feedback 層 service：
  - 分層 prompt 組裝（preamble 5 條不可違反規則 → persona → strategy 指令 → evidence context）
  - LLM 呼叫（GPT-4o, temperature=0.7），支援對話歷史（最近 10 輪）
  - 輸出驗證：不允許程式碼時移除 code block、允許時超過 8 行且無 TODO/FIXME 自動截斷
- `backend/tests/test_feedback.py` — 11 個 Feedback 層測試（prompt 組裝 3 個、輸出驗證 5 個、LLM 呼叫 3 個）

## [2026-04-13] — Phase 1-4b Decision 層策略矩陣
### Added
- `backend/services/edf/decision.py` — Decision 層：6×6 Bloom × Hint Ladder 策略矩陣（36 格教學指令），RAG 觸發條件（hint≥2 且 bloom≥ANALYZE），回傳 TeachingStrategy（instruction + allow_code_snippet + use_rag）
- `backend/tests/test_decision.py` — 10 個 Decision 層測試（低/高 Bloom×Hint 組合、RAG 觸發/不觸發、邊界值 clamp、36 格完整性驗證）

## [2026-04-13] — Phase 1-4a Evidence 層 LLM 結構化分析
### Added
- `backend/services/edf/models.py` — EDF 共用模型（BloomLevel 6 級 enum、ErrorType 6 類 enum、20 個 ConceptTag 常數、EvidenceResult schema）
- `backend/services/edf/evidence.py` — Evidence 層 service：呼叫 OpenAI GPT-4o（JSON mode），分析學生程式碼回傳錯誤分類、ConceptTag、Bloom 認知等級
- `backend/tests/test_evidence.py` — 8 個 Evidence 層測試（prompt 組裝、model 解析、LLM 成功/失敗/JSON 異常）
- `backend/pyproject.toml` — 新增 openai、httpx 依賴

## [2026-04-13] — Phase 1-3f resize handle UX 改善
### Changed
- `web/app/(app)/workspace/page.tsx` — 垂直 resize handle 從 1px 改為 4px hit area + 1px 視覺線條（before pseudo-element）
- `web/components/layout/app-shell.tsx` — 水平 resize handle 同樣改善，更容易拖曳

## [2026-04-13] — 移除 stdin 前端 UI
### Removed
- `web/components/workspace/stdin-panel.tsx` — Phase 1 不需要前端 stdin 面板，後端 API 仍保留 stdin 參數供未來 test case 機制使用

### Changed
- `web/components/workspace/toolbar.tsx` — 移除 stdin 按鈕及相關 props
- `web/app/(app)/workspace/page.tsx` — 移除 stdin state 和 StdinPanel 引用

## [2026-04-13] — Phase 1-3d 前端 Run 按鈕串接 + Output Panel
### Changed
- `web/app/(app)/workspace/page.tsx` — 串接 Run 按鈕：點擊呼叫 `POST /api/code/execute`，管理 isRunning/output state，自動展開 Output Panel，顯示執行狀態（Running → Passed/Error）
- `web/components/editor/code-editor.tsx` — mount 時通知父層初始程式碼內容，確保 Run 可取得程式碼

## [2026-04-13] — Phase 1-3c Judge0 API client
### Added
- `backend/services/judge0.py` — Judge0 async client（submit + polling），支援 RapidAPI 和自架模式，base64 編碼，逾時/限流/不可用錯誤處理
- `backend/api/routes/code.py` — `POST /code/execute` 端點（需登入），接收 code/language_id/stdin，回傳 stdout/stderr/compile_output
- `backend/tests/test_judge0.py` — 7 個 Judge0 service 測試（b64 解碼、submit+poll 成功、編譯錯誤、429 限流、503 不可用）

### Changed
- `backend/main.py` — 註冊 code router

## [2026-04-13] — Phase 1-3b Workspace 頁面基礎佈局
### Added
- `web/components/workspace/toolbar.tsx` — Toolbar 元件（檔名顯示、C++ 語言標籤、stdin 按鈕、▶ Run 按鈕）
- `web/components/workspace/output-panel.tsx` — Output Panel 元件（stdout/stderr/compile tabs、stderr 紅點指示、可收合為單行 status bar）

### Changed
- `web/app/(app)/workspace/page.tsx` — 重構為三區佈局：Toolbar (40px) + Editor (70%) + Output Panel (30%)，使用 react-resizable-panels 垂直拖曳調整

## [2026-04-13] — Phase 1-3a CodeMirror 6 整合
### Added
- `web/components/editor/code-editor.tsx` — CodeMirror 6 編輯器元件（C++ 語法高亮、One Dark 主題、行號、括號配對、fold gutter、歷史紀錄）
- CodeMirror 6 相關套件：codemirror、@codemirror/lang-cpp、@codemirror/theme-one-dark、@codemirror/state、@codemirror/view

### Changed
- `web/app/(app)/workspace/page.tsx` — 替換 placeholder 為 CodeEditor 元件，佔滿可用空間

## [2026-04-13] — Phase 1-2e Role-based 權限 middleware
### Added
- `backend/api/deps.py` — `require_roles(*roles)` 依賴工廠，檢查使用者角色，不符合回傳 403 FORBIDDEN
- `backend/tests/test_roles.py` — 5 個 role-based 權限測試（student 可/不可存取、teacher 升級、admin 全通、多角色允許）
- `backend/tests/helpers.py` — 共用測試工具（DB engine、session factory、token 加密），修復 conftest 雙重載入問題
- `backend/tests/conftest.py` — 重構為純 fixtures（DB 初始化/清理、client、secret 設定）

### Changed
- 測試基礎設施全面重構：pytest-asyncio 升級至 1.3，SQLite file-based DB 取代 in-memory（解決事件迴圈綁定），27 個測試全數通過

## [2026-04-13] — Phase 1-2d 前端登入/登出頁面 + 未登入重導
### Added
- 確認先前實作的登入頁面、登出按鈕、middleware 重導功能完整可用，正式標記 1-2d 完成

## [2026-04-13] — Phase 1-2c 使用者首次登入自動建立 DB 記錄
### Added
- `backend/services/user.py` — `get_or_create_user()` 依 google_id 查找/建立使用者，每次登入更新 name、avatar、last_login_at
- `backend/tests/test_user_service.py` — 5 個使用者 service 測試（首次建立、重複登入、profile 更新、fallback google_id）

### Changed
- `backend/api/deps.py` — 新增 `get_current_db_user` 依賴注入（token 解析 + DB upsert）
- `backend/api/routes/auth.py` — `/auth/me` 改用 `get_current_db_user`，回傳完整 DB 使用者資訊（含 UUID、role）
- `backend/tests/test_auth.py` — 整合測試改用 SQLite in-memory 覆蓋 DB 依賴，新增重複呼叫測試

## [2026-04-13] — Phase 1-2b 後端 JWT 驗證 middleware
### Added
- `backend/core/auth.py` — NextAuth v5 JWE token 解密（HKDF-SHA256 金鑰衍生 + authlib 解密 + `TokenPayload` model）
- `backend/api/routes/auth.py` — `GET /auth/me` 端點，回傳當前登入使用者資訊
- `backend/tests/test_auth.py` — 6 個 auth 測試（金鑰衍生、token 解碼、401 保護、/auth/me 整合測試）
- `backend/Dockerfile` + `web/Dockerfile` — 前後端 Docker 建構設定
- `backend/tests/test_cors.py` / `test_errors.py` / `test_models.py` — 補齊先前功能的 unit tests

### Changed
- `backend/api/deps.py` — 匯出 `get_current_user` + `TokenPayload` 供路由依賴注入
- `backend/main.py` — 註冊 auth router
- `backend/pyproject.toml` — 新增 `authlib`、`cryptography`、`PyJWT` 依賴

## [2026-04-13] — Phase 1-2a 前端 Auth 完善
### Added
- `web/app/login/page.tsx` — Google OAuth 登入頁面
- `web/middleware.ts` — NextAuth v5 middleware，未登入重導至 /login
- `web/app/(app)/` — 路由群組，所有需認證頁面移入此群組

### Changed
- `web/auth.ts` — 新增 `authorized` callback 控制存取 + `jwt`/`session` callbacks 傳遞 Google profile
- `web/app/layout.tsx` — 移除 `(app)` 群組外的 SessionProvider（改由群組內 layout 處理）

## [2026-04-13] — Phase 1-2a NextAuth.js Google OAuth 設定
### Added
- `web/auth.ts` — NextAuth v5 核心設定（Google OAuth provider + JWT/session callbacks）
- `web/app/api/auth/[...nextauth]/route.ts` — Auth API route handler（`/api/auth/*`）
- `web/components/providers/session-provider.tsx` — Client-side SessionProvider wrapper
- `web/.env.example` — 前端環境變數範本（AUTH_SECRET、AUTH_GOOGLE_ID、AUTH_GOOGLE_SECRET）

### Changed
- `web/app/layout.tsx` — 加入 SessionProvider 包裹全域
- `web/.gitignore` — 排除 `.env.example` 使其可被追蹤

## [2026-04-13] — Phase 1-1f Health check + 前端連線狀態顯示
### Added
- `hooks/use-health-check.ts` — 定期 poll `/api/health`（30 秒），回傳 DB/Redis 連線狀態
- StatusBar 即時顯示：連線成功綠點 `Connected` / 斷線紅點 `Disconnected`

### Changed
- Phase 1-1 專案骨架全部完成（1-1a ~ 1-1g 共 7 個子任務）

## [2026-04-13] — Phase 1-1e 前後端通訊串接
### Added
- `web/app/api/[...path]/route.ts` — catch-all API proxy，將 `/api/*` 轉發至 FastAPI backend
- `web/lib/api.ts` — 前端統一 API client（`api<T>(path)` 函式 + 錯誤攔截 + `ApiRequestError` 類別）
- 支援所有 HTTP method（GET/POST/PUT/PATCH/DELETE）、query string 保留、body 轉發
- 後端不可用時回傳 502 + 標準錯誤格式

## [2026-04-13] — Phase 1-1d Alembic 初始化 + users 表
### Added
- Alembic async migration 環境（`alembic/env.py` 改寫為 asyncio + asyncpg）
- `models/user.py` — User SQLAlchemy model（UUID PK、email、name、role enum、google_id、timestamps）
- 第一次 migration `29ec153bbf77_create_users_table`：建立 `users` 表 + `user_role` enum + email/google_id unique index

## [2026-04-13] — Phase 1-1c PostgreSQL + Redis 連線
### Added
- `core/database.py` — SQLAlchemy async engine + sessionmaker + `Base` 宣告式基底 + `get_db` 依賴注入
- `core/redis.py` — Redis async client 初始化/關閉 + `get_redis` 依賴注入
- `main.py` 新增 `lifespan` context manager 管理 DB engine dispose + Redis 連線生命週期
- `api/routes/health.py` 升級為完整健康檢查：回傳 DB + Redis 連線狀態（`connected` / `disconnected`）
- `api/deps.py` 匯出 `get_db`、`get_redis` 供路由依賴注入使用

## [2026-04-13] — Phase 1-1b FastAPI 專案建立
### Added
- `backend/` 目錄結構：`api/routes/`、`api/middleware/`、`models/`、`services/`、`core/`
- `pyproject.toml` + `requirements.lock` 依賴管理（FastAPI 0.135 + Pydantic 2.13 + SQLAlchemy 2.0 + asyncpg）
- `core/config.py` — Pydantic Settings 管理環境變數（DB、Redis、Auth、OpenAI、Judge0）
- `core/errors.py` — 標準錯誤回應模型 `ErrorResponse` + 全域例外處理（`AppError` → JSON）
- `main.py` — FastAPI 進入點 + CORS middleware（僅允許 NEXTAUTH_URL）+ health route
- `api/routes/health.py` — `GET /health` 端點
- `.env.example` — 環境變數範本

## [2026-04-13] — Activity Bar 放大並加入文字標籤
### Changed
- Activity Bar 從 48px icon-only 改為 180px icon + 文字標籤（英文名稱 + 中文說明）
- Chat Panel 預設寬度改為 350px（pixel-based），修正原本過窄的問題

## [2026-04-13] — Phase 1-1g 前端 UI 基礎建設
### Added
- 安裝 shadcn/ui（base-nova style, dark preset）+ lucide-react + react-resizable-panels v4
- Activity Bar 元件（48px 左側導覽，9 項 icon 導覽 + Avatar + Tooltip）
- AI Chat Panel 空殼（Header + 訊息佔位 + 輸入區，支援收合/展開）
- Status Bar 元件（24px 底部，連線狀態 + 語言 + 編碼 + 游標位置 + 精熟度）
- AppShell 全域骨架整合 react-resizable-panels 拖曳調整 Content / Chat 寬度
- 響應式佈局：Desktop 三欄 / Laptop Chat overlay / Tablet 漢堡選單頂部 bar / Mobile 底部 tab bar
- 8 個路由佔位頁面（workspace / learn / quiz / knowledge / overview / notifications / dashboard / settings）
- `useBreakpoint` hook（4 斷點偵測）
- Ctrl+B 快捷鍵收合/展開 Chat Panel

## [2026-04-13] — 新增 UI/UX 介面規格書
### Added
- `docs/ui-ux-spec.md` — 完整 UI/UX 介面規格書（13 章節）
- VSCode 風格 IDE 佈局：Activity Bar + Content Area + AI Chat Panel
- 7 個頁面規格：Workspace、Learn、Quiz、Knowledge、Overview、Dashboard、Settings
- Workspace 檔案樹（多檔案管理）、學生 Overview 獨立頁面、通知系統鈴鐺
- 響應式設計（Desktop / Laptop / Tablet / Mobile 四斷點）
- 動效、快捷鍵、狀態列、Pre-Coding Reflection / Post-Solution 互動流程

## [2026-04-13] — Phase 1-1a Next.js 專案初始化
### Added
- `web/` 目錄：Next.js 16 + App Router + TypeScript + Tailwind CSS v4
- Design Tokens（GitHub Dark）套用為 CSS 變數，Tailwind `@theme` 映射為 utility class
- 字型載入：Inter（UI）+ Noto Sans TC（中文）+ JetBrains Mono（程式碼）
- Dark mode 預設啟用（`<html class="dark">`）
- `lang="zh-TW"` 設定

## [2026-04-13] — Roadmap 新增前端 UI 基礎建設任務
### Changed
- `roadmap.md` Phase 1-1 新增 1-1g：shadcn/ui 安裝 + 全域 Layout + Header Navigation + 響應式骨架，確保後續功能開發時已有成熟 UI 框架

## [2026-04-13] — 文檔交叉引用修正
### Fixed
- `architecture.md` routes 註解補齊 `dashboard, analytics, reflection` 端點
- `changelog.md` Module 9 參考專案計數修正（7→6）
- `db-schema.md` Module 6 `student_answers` 加入 comprehension 擴充欄位交叉引用
- `roadmap.md` Phase 2 header 補齊影響頁面（Workspace Pre-Coding Reflection 側邊欄）
- `roadmap.md` Phase 4-2c `dialogue_act` enum 補漏 `acknowledgment`

## [2026-04-13] — 新增 Pre-Coding Reflection 反認知外包機制
### Added
- 跨模組機制：Pre-Coding Reflection（解題前反思閘門，方案 B 一次追問機會）
- 跨模組機制：Post-Solution Comprehension Check（EPL / 預測輸出 / 變體挑戰）
- DB Schema：`reflections` 表 + `student_answers` 擴充 comprehension 欄位
- API：Reflection 端點（create + update + get）+ Quiz comprehension 端點
- Roadmap：Phase 2 新增 2-5（反思閘門）+ 2-6（理解驗證）、Phase 3-1 新增 3-1e
- 學術參考：7 篇新增至 references.md（CodeAid、PRIMM、EPL、Self-explanation 等）

### Changed
- modules.md Module 6/7 加入反思觸發點、Module 9 加入反認知外包指標
- edf-pipeline.md Evidence 層加入反思內容注入、Feedback 層加入反思引用
- references.md 新增 Pre-Coding Reflection 參考區塊

## [2026-04-13] — 新增 Module 9 學習行為分析模組
### Added
- Module 9：學習行為分析（教師專屬，Phase 4）— 中粒度追蹤 coding 行為與 AI 互動
- DB Schema：`coding_events` 事件紀錄表 + `behavior_aggregates` 預聚合表
- `chat_messages` 擴充 `dialogue_act` 欄位（Phase 4-2c）
- API：Behavior Analytics 端點（班級總覽/散佈圖/熱力圖/個人時序/摘要）
- Roadmap Phase 4 拆分為 5 子階段（4-1 班級管理 → 4-2 資料收集 → 4-3 分析演算法 → 4-4 視覺化 → 4-5 作業指派）
- 參考專案：ProgSnap2、KOALA、StudyChat、pyBKT、PM4Py、OpenLAP 等 6 個新增至 references.md
- 目錄結構新增 `backend/services/analytics/`

### Changed
- modules.md 擴充為 9 模組
- CLAUDE.md 更新模組數量

## [2026-04-13] — 新增開源參考專案文檔
### Added
- `docs/references.md` — 8 個開源參考專案對照表（DeepTutor、OATutor、Mr. Ranedeer、EduAdapt-AI 等）
- 各功能最佳參考來源對照（EDF、RAG、Knowledge Tracing、智慧出題、學習路徑）
- 學術資源連結（論文、awesome list）

### Changed
- `docs/modules.md` — Module 3/4/6/7 加入對應開源參考來源
- `docs/roadmap.md` — Phase 1-4、2-1、2-3、2-4、3-1 加入參考專案指引
- `.claude/rules/edf-pipeline.md` — 加入開源參考區塊
- `CLAUDE.md` — 文件索引新增 references.md

## [2026-04-13] — 文檔一致性修正
### Fixed
- 將 `CHANGELOG.md` 搬移至 `docs/changelog.md`，與 CLAUDE.md 文件索引一致
- 修正 changelog 格式：每次變更使用獨立日期標頭，移除非標準的 `Previous` 區塊
- 統一導覽 Tab 命名：wireframe Header 的 `Graph` → `Knowledge`，並補上 `Dashboard` tab
- api-spec.md 新增 Dashboard API 端點（`/api/dashboard/summary` + `/api/dashboard/activity`）

## [2026-04-13] — Phase 0 規劃文檔完善
### Changed
- Roadmap 拆分為原子級子任務（每個 checkbox = 一次對話可完成）
- DB Schema 補齊 index/constraint 標記（unique、GIN、HNSW、複合索引）
- EDF pipeline 補完 Bloom 6 級定義 + Hint Ladder 6 級策略表
- architecture.md 新增前後端通訊模式（Next.js API proxy）+ 標準錯誤 JSON 格式
- API spec 更新 Chat 端點（SSE streaming + session CRUD）
- rules/frontend.md 補入測試策略 + API 呼叫規範

### Added
- `.env.example` — 環境變數範本
- `db-schema.md` Module 3 Chat Session 表（chat_sessions + chat_messages）

## [2026-04-12] — 文檔架構重構
### Changed
- 重構全部文檔架構，最佳化 Claude Code 上下文效率
- 新增 `.claude/rules/` 自動注入規則（frontend、backend、edf-pipeline）
- 拆分大檔案：modules + db-schema、ui-wireframes + rules/frontend
- 合併冗餘文件：06-phases → roadmap、00-overview → CLAUDE.md
- 刪除 7 個舊文件，重組為 8 個 docs + 3 個 rules

### Added
- `.claude/rules/frontend.md` — 前端 Design Tokens、元件規格、響應式（自動注入 web/**）
- `.claude/rules/backend.md` — 錯誤處理、安全規範、環境變數（自動注入 backend/**）
- `.claude/rules/edf-pipeline.md` — EDF 管線規範（自動注入 backend/services/edf/**）
- `docs/architecture.md` — 系統架構圖 + 目錄結構
- `docs/modules.md` — 8 模組功能摘要
- `docs/db-schema.md` — 全部 DB Schema
- `docs/ui-wireframes.md` — 5 頁 wireframe

### Removed
- `docs/00-overview.md` — 內容已涵蓋在 CLAUDE.md
- `docs/01-tech-stack.md` — 拆分至 architecture.md + CLAUDE.md
- `docs/02-modules.md` — 拆分至 modules.md + db-schema.md + edf-pipeline.md
- `docs/03-ui-design.md` — 拆分至 ui-wireframes.md + rules/frontend.md
- `docs/04-api-spec.md` — 重命名為 api-spec.md
- `docs/05-engineering.md` — 拆分至 rules/backend.md
- `docs/06-phases.md` — 合併至 roadmap.md

## [2026-04-11] — 專案初始化
### Added
- 新增 `CLAUDE.md` 專案級開發指揮中心
- 專案初始化，建立 Git repository
- 新增 .gitignore
