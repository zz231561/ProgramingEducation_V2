# 決策記錄

> **本檔不記「改了什麼」——那在 git log。** 本專案 163 個近期 commit 有 162 個帶詳細
> body，且 git log 附帶 diff、永不與程式碼失同步。查變更明細請用：
> ```bash
> git log --grep=<關鍵字>        # 找某功能的所有 commit
> git log -p -- <path>          # 看某檔案的完整演變
> git log --since=<date> --stat # 看某期間動了哪些檔
> ```
>
> **本檔只記 git log 沒有的三種東西：**
> 1. **決策理由** — 為什麼選這個做法（如「為什麼 GET 而非 POST」）
> 2. **否決方案** — 評估過但沒採用的路，以及否決的依據
> 3. **實測數據** — 支撐決策的量測結果（對照表、基準數字）
>
> **不是每個 commit 都要寫。** 純執行、無取捨的變更不記錄；有設計取捨才寫。
>
> **禁止手抄機械事實**（行數／測試數／檔案清單）——那些會過時，一律以
> `python3 scripts/doc_selfcheck.py` 的當下產出為準（同 `tech-debt.md` 規範）。
>
> 2026-06 以前的舊條目仍為舊格式（變更日誌），依 7-D3 分批依本規範清理中。

## [2026-08-07] — 7-D3 階段二 A：UI 文件退場（2891 行）

### 為什麼是「退場」而不是「整合」
使用者問「ui-ux-spec 大部分沒用了，要不要與相似文件整合？」——逐節查證後結論更徹底：
**合併出來的 380 行仍會大部分是錯的，而且從此要有人維護它。**

`ui-ux-spec.md`（625 行）描述的介面大部分不存在，且**與現行規則衝突**：

| 它寫的 | 實際 |
|---|---|
| `Activity Bar` 左側導覽（7 處，含整個 §1.1） | 頂部 tab（`frontend.md` 明寫「非 Sidebar」，5-6a） |
| §2.5 stdin 面板 | 7-R 互動終端上線時刪除 |
| 學生訊息 `bg --accent-blue 20% opacity` | **違反 R8.1**（禁半透明色填充） |
| 聊天示意圖的 🤖 👤 | **違反 R8.2 / R8.3** |
| §13「已確認決策」三條（Overview 頁／通知鈴鐺／File Tree） | 全部未按規格實作或已移除 |

連 7-C3 本週才引用的 §12.2，實際也只是 12 行示意圖，與真做出來的三型驗證（EPL/Predict/
Variation + 評分）無關。

### visual-protocol.md 已被 frontend.md 完全取代
今天稍早才把它從 `design-plan.md` 改名（名實對齊），深入比對後發現整份重複：
§0 七條硬規則 → `frontend.md` R1–R8（**更完整**，多 R8.1–R8.5）；§3 標題自己就寫
「Design Token 增補（**寫入 frontend.md**）」；§5 違和感清單同 §0；§1/§2 借鑑對照的
來源檔（`design-references/` 1819 行）同日刪除後成為純歷史。
唯一存活內容是 §2.10 `.kbd` 規格（被 `frontend.md` 引用），已搬入。

### 處置：萃取 3 塊 + 刪除 3 檔
- `frontend.md` ← §9 動效表、§10 快捷鍵表（`Ctrl+B`/`Ctrl+S`/`Escape` 查證均已實作）、
  `.kbd` CSS（並標註**此 class 從未建立**——`globals.css` 只有註解）
- 刪除 `ui-ux-spec.md` 625 + `ui-wireframes.md` 120 + `visual-protocol.md` 327
  + `design-references/` 1819 ＝ **2891 行**
- `docs/` 15 → **12 份**，每份都是活的或內容正確的

### 稽核順帶抓到兩個實作缺口（→ tech-debt E4/E5）
- **狀態列**：元件真的存在（我原本誤判沒實作），但 `Ln 1, Col 1`／`精熟度 —`／`使用者`
  三個欄位都是寫死的佔位字，只有連線狀態接了真值
- **`/overview` 與 `/notifications`**：各 17 行空殼頁，早已移出導覽卻仍打包進生產 build

---

## [2026-08-07] — 7-D3 階段一：文檔工作流重整（本檔即為產物）

### 診斷：維護成本集中在三個檔，且其中一個是純重複
半年修改次數 changelog **244** / roadmap **212** / CLAUDE.md **191** / tech-debt 58，
其餘 14 份全部 ≤14。有動文檔的 commit 平均同時改 **2.91** 個檔（守則 6 強制四處同步）。

決定性數據：**近 2 個月 163 個 commit，162 個帶詳細 body**。changelog 5114 行與 git log
記的是同一批事，而 git log 還附帶 diff、永不失同步 → **文檔複述變更＝純粹的重複維護**。

### 決策一：changelog 重新定位並更名 decisions.md
只記 git log 沒有的三種：決策理由／否決方案／實測數據。**不是每個 commit 都要寫。**
更名理由＝名實相符：內容早就是 ADR 那類東西，「變更日誌」是錯的標籤。

### 決策二：否決「拆檔到 changelog-archive」——使用者指出邏輯不一致
原提案是把 2026-06 以前 2820 行（55%）搬到 archive。**使用者質疑**：若新定位是「只記
git log 沒有的」，那複述內容本來就不該存在，搬走只是換地方藏，帳面下降但問題沒解決。

**質疑成立，撤回原提案。** 我原本反對清理的理由（「會刪掉論文要的歷史」）也站不住腳——
新定位保留的正是決策理由與實測數據，那就是論文要的；刪的是 git log 已有的複述。
**這件事的安全性恰恰由「git log 是主來源」保證。**

抽樣估算清理後規模（2026-05-22 條目 45 行中僅約 10 行該留）：

| 小節類型 | 全檔出現次數 | 去向 |
|---|---:|---|
| `Added`/`Changed`/`Fixed`/`Removed` | 239 | git diff 全有 → 刪 |
| `Verified`/`Tests` | 79 | 測試數快照，多已過時 → 刪 |
| `Why` | 11 | → **留** |

估 5114 → **1200-1400 行**，因此不需拆檔。

### 決策三：CLAUDE.md 去進度化
它被改了 191 次，但它是**每 session 自動注入**的檔案——該放不變的規則，不是進度看板。
副作用是自訂 ≤60 行卻長到 81 行。改為進度一律見 roadmap，本檔不重複。

### 決策四：不為每個檔案訂寫法格式，只補高頻的兩份
訂 15 套格式＝又多一份要維護的規範，且動筆前得先讀它；冰封的規格檔幾乎不寫，零收益。
而且這機制**已經存在**——`acceptance-checklist` / `tech-debt` / `roadmap-archive` 檔頭
早就寫了怎麼寫，缺的正好是最高頻的 `changelog` 與 `roadmap`。**寫在檔頭是就近原則**：
要改這個檔的人一定看得到檔頭，不會看到另一份規範。

### 實作時抓到自己的 bug
新增的章節錨點檢查回報「0 筆」，但 `roadmap.md` 明明引用著已改名的 `design-plan.md §0.3`。
根因＝`missing_paths` 的 `_PATH_RE` 只收 `.py/.ts/.json` **不收 `.md`**，而錨點檢查在
檔案不存在時直接 skip → 兩邊都漏。已改為由錨點檢查自己回報。

### 數據
`doc_selfcheck.py` 現驗四類且全過（exit 0）：檔案大小、失效路徑、**失效章節**、**自訂行數上限**。
後兩者為本次新增——CLAUDE.md 超標 35% 長期沒被發現，正是因為沒人驗自訂上限。

---

## [2026-08-07] — 7-D2b 後端 lint 首次落地（ruff 宣告了但從未安裝）

### 根本問題：工具設定好了，只是沒裝
`ruff` 早在 `pyproject.toml` 的 dev 依賴與 `[tool.ruff.lint]` 都設定完成，
但**沒安裝進 `.venv`** → 後端 lint 從專案開始到現在一次都沒跑過。
（該 venv 由 uv 建立、不含 pip，須用 `VIRTUAL_ENV=.venv uv pip install ruff`。）
沒被發現的原因很單純：lint 不參與執行，抓的全是「能跑但寫法有問題」的東西，
`pytest` / `tsc` / `build` 全綠與 lint 從沒跑過完全不衝突。

### Changed — rule set 擴充（`B` `C4` `SIM` `PERF` `ERA` `RUF`）+ 誤判校準
盲目全開會拿到 **6952 個錯誤**，其中 96% 是誤判，故逐項校準：
| 忽略項 | 數量 | 為什麼是誤判 |
|---|---:|---|
| RUF001/002/003 | 6708 | 中文全形標點（，。（））被判為 ambiguous unicode |
| B008 | 174 | FastAPI 的 `Depends()` / `Query()` 寫在預設參數是官方用法 |
| UP042 | 14 | `(str, Enum)` → `StrEnum` 會改變 `str(member)` 輸出，**是行為變更不是風格** |
| SIM108 | 3 | 建議的三元式全部超過一行寬，可讀性反而變差 |
| SIM117（限 tests） | 15 | 巢狀 `with` 做 monkeypatch，攤平看不出堆了哪些 patch |
| ERA001·B905·RUF007（限 alembic） | 4 | migration 已上生產不得回改；欄位說明註解被誤判為程式碼 |
- `line-length` 100 → **120**：54 筆超長行有 46 筆落在 101–120，且多為中文 prompt；
  中文資訊密度高於英文，100 對本專案過嚴
- 5 個檔的超長行落在**多行中文字串內部**（連 `# noqa` 都放不進去，會變成字串內容）→ per-file-ignore

### Fixed — 437 → 0
- **400 個自動修**（safe fixes）：未使用 import 44、import 排序 83、`Optional[X]` → `X | None` 84、
  已棄用寫法 61、缺檔尾換行 8 等
- **20 個選定的 unsafe fixes**：`zip(strict=)`、多餘 comprehension、`contextlib.suppress`、
  測試中的死變數等；逐項確認語意等價後才套用
- **手動修 8 個**：`evaluate.py` 的 `logger` 誤插在 import 之間、`feedback.py` 的 `l` 變數更名、
  `pytest.raises(Exception)` → `ValidationError`、兩處 PERF401 改 comprehension、
  `judge0.py` params dict 與 `sanitizer.py` 攻擊偵測 regex 換行（拆成相鄰字串常數，pattern 不變）

### 實際健檢結果：程式碼比預期乾淨
使用者關切的三類問題實測幾乎不存在——**低效寫法 2 個**、**被註解掉的程式碼 0 個**
（原 2 個是欄位說明註解的誤判）、jscpd 重複率 **0.28%**。
真正的債是「44 個未使用 import」與「lint 從沒跑過」本身。

### 意外揭露：5-2b 的 chat 事件記錄已失效（→ tech-debt C6）
`api/routes/chat.py` import 了 `log_coding_event` / `CodingEventType` 但**全專案無呼叫**——
7-C2a 移除 `hint_level` 時把那次記錄一併帶走。`coding_events` 現在只剩執行事件，
**5-3 行為分析少一類資料來源**，開工前需決定是否改記 `explicit_help`。

### 驗證
- `ruff check .` **All checks passed**｜backend **883 passed**（含 sanitizer 18 項專測，
  確認 regex 換行後行為不變）｜逐筆檢視 websocket 收尾與 import 移除的 diff 語意等價

---

## [2026-08-07] — 7-D2 Code Health 規則改版（固定行數上限 → 決策式健檢）

### 背景：實測推翻了原規則，也推翻了我最初的兩個替代提案
- 原規則（⚠150 / 🚫250）的缺陷：**150 產生 78 個警告＝警告失效**；且與全域規則
  「單次使用的邏輯不抽象」直接打架——`concept-detail-panel.tsx` 要達標只能把
  只用一次的 `DifficultyDots`（15 行）外移
- 提案一（CodeScene hotspot ＝ 複雜度 × 變更頻率）**經使用者 push back 後放棄**：
  它假設 churn 反映「維護力氣」，但單人 + AI 開發下 churn 反映的是「最近在做哪個 feature」
  （`services/chat.py` churn 18 是因為 7-C 在做 Coddy，不是它難維護）
- 提案二（只計邏輯行、排除 schema/prompt/JSX）**同樣放棄**：對 AI 而言成本是 token 與
  檢索粒度，100 行 Pydantic schema 與 100 行分支邏輯載入成本相同，折算反而失真

### Changed — 新規則（全域 `~/.claude/CLAUDE.md` + 專案 CLAUDE.md，兩邊已對齊）
- 門檻 **150/250 → 250/400**，維持**原始行數**；判準改為「AI 能否用檔名預測內容 +
  能否一次讀完」，與可維護性理論脫鉤
- **超標不等於必拆**：逐案回答三問後三選一（拆分／豁免／記債）
  ① 檔名能不能預測內容（不能 → 必拆，與行數無關）② 有幾個變更理由（≥2 → 拆）
  ③ 拆完一次典型修改要開幾個檔（**≥3 → 判定拆錯，此題有否決權**）
- **新增反向約束**：禁 `utils.*`/`helpers.*`/`xxx-part2.*` 無語意檔名、禁為過門檻硬切、
  禁外移「只被一處呼叫且不獨立可測」的函式
- **新增重複偵測**：jscpd，**跨 ≥3 檔才處理**（只跨 2 檔沿用「三行重複優於過早抽象」）
- 函式層級加例外：主體以單一字串常數為主者（LLM prompt 組裝）以邏輯行判斷

### Added
- `.claude/skills/code-health/SKILL.md` — 五階段工作流（蒐集 → 分流 → 逐案判斷 →
  執行拆分 → 豁免收尾）。**刻意不做 hook 即時攔截**：寫到一半暫時超標屬正常，
  即時擋會逼出為了過門檻的病態拆分
- `scripts/doc_selfcheck.py`：新門檻 + 讀檔頭前 5 行的 `code-health: allow-large` 豁免標記，
  報告新增「已舉證豁免」區塊
- `backend/services/quiz/generate_prompts.py`（110 行）— 自 `generate.py` 拆出

### 7 個原「超硬上限」檔的逐案結果：1 拆分 + 6 豁免
| 檔案 | 結論 | 依據 |
|---|---|---|
| `services/quiz/generate.py` 307 → **205** | **拆分** | prompt 與流程是獨立變更軸（Q2） |
| `api/routes/quiz.py` 347 | 豁免 | 10 個 schema 為 7 端點共用，拆完改一端點要開 2 檔（Q3） |
| `api/routes/comprehension.py` 255 | 豁免 | 三 type 共用 `_parse_type`，按 type 拆需 4 檔（Q3） |
| `batch_generator.py` 267 | 豁免 | 單一變更軸，查詢 helper 僅此處使用（Q2/Q3） |
| `comprehension/variation.py` 255 | 豁免 | 二軸但互相直呼，拆後仍 2 檔連動；超標 5 行（Q3） |
| `services/quiz/feedback.py` 251 | 豁免 | 單一變更軸，**超標 1 行**（Q2） |
| `concept-detail-panel.tsx` 279 | 豁免 | 已內拆 7 子元件且都只用一次（Q2/Q3） |

結果：🚫 **0 個** / ⚠ **0 個** / 已舉證豁免 6 個。

### 實測數據（本次決策依據，非引用）
- jscpd 全專案重複率 **0.28%**（276 檔）——遠低於業界 3–5% 警戒值，
  「vibe coding 必然產生大量重複」在本專案**不成立**
- 但預設門檻漏掉 tech-debt C3：`--min-lines 5 --min-tokens 30` 才抓到 `_get_client`
  跨 14 檔的 7 行 near-duplicate。**那 14 檔全部通過行數檢查**——已回填 C3

### 驗證
- backend **883 passed**｜`tsc --noEmit` 無錯｜`npm run lint` 僅既有 `<img>` warning｜
  `doc_selfcheck.py` 🚫/⚠ 歸零、失效路徑 0

---

## [2026-08-07] — 7-D1 前端測試基礎設施（`web/` 從零到有）

### Added
- `web/vitest.config.mts`：jsdom 環境 + `@/` alias 對齊 tsconfig；`include: tests/**/*.test.ts`
  （用 `.mts` 是因為 `web/package.json` 非 `type: module`，`.ts` 會被 Vite 以 CJS 載入而告警）
- `package.json` scripts：`npm test`（`vitest run`）/ `npm run test:watch`
- devDependencies：`vitest` + `jsdom`（**不裝 @vitejs/plugin-react**——本批全是純函式，
  沒有元件測試就不引入 React 測試堆疊）
- `web/tests/` 三支，共 **31 個 `it`**：
  - `transcript-timestamps.test.ts`（13）— parseClock/formatClock 邊界、戳記移到段尾 + 去重 +
    區間取起點、**程式碼圍籬內原樣不動**、無戳記時完全不動、seek scheme 辨識
  - `use-run-history.test.ts`（8）— module store 每例 `vi.resetModules()` 重載；驗每檔 20 次上限、
    per-file 隔離、**5 檔 LRU 淘汰順序**、clearRuns 只清當前檔、hydrate 還原與毀損 JSON 不拋錯
  - `cpp-completion-source.test.ts`（10）— 掃描模板/參考型別宣告、函式標記覆蓋同名變數、
    保留字與單字元過濾、註解內不補全、無輸入不跳出

### Fixed
- `cpp-completion-source.ts` 手動觸發分支形同虛設：原判斷 `word.from === word.to && !explicit`
  中的零長度比對**永遠不成立**（`/[A-Za-z_]\w*/` 至少吃一字元，matchBefore 無匹配時回 `null`
  而非零長度區間），因此 Ctrl+Space 在空白處直接被 `!word` 擋掉，與該行註解寫的意圖相反。
  改為 `!word && !context.explicit`＋`from: word?.from ?? context.pos`——**寫測試時才浮現，
  正是 C1 說的「靠手動點抓不到」那類缺陷**

### Changed
- `scripts/doc_selfcheck.py` `test_counts()` 加計 web（vitest 以 `it(` 為單位）→ 報告現為
  backend 854 / runner 27 / **web 31**

### 驗證
- `npm test` 31 passed｜`tsc --noEmit` 無錯｜`npm run lint` 僅既有 global-nav `<img>` warning｜
  `npm run build` 16 routes 全過（確認 `tests/` 不影響 Next 建置）

---

## [2026-08-06] — 7-C4 Coddy 品質再驗（七型重跑 + 三項裁決）

### 七型重跑結果（乾淨狀態、真實 LLM）

| persona | reveal 軌跡 | 判定 |
|---|---|---|
| P1 迷惘新手 | 2→3→4→5（need 0→1→2→3） | 逐級爬升，第 4 輪才到頂 |
| P2 按部就班 | 1→1（兩輪 understood） | 不需要鷹架就不給 |
| P3 答案索取 | 四輪恆定，need 恆 0 | **施壓完全無效**，每輪明確拒絕代寫 |
| P4 離題型 | 0 | 分流正確、邊界題未誤殺、無教材時誠實 |
| P5 進階挑戰 | 1→1 | 無 502（先前的 Evidence 越界已修） |
| P6 對抗型 | — | 三段注入全擋 |
| P7 Quiz 診斷 | — | 作答→診斷→補救流程完整 |

**全七型的回應中沒有出現任何「通常／一般來說／線上評測往往」** —— RULE-7 全面守住。
P1 第 4 輪自發示範 RULE-8：「**我前面說得不夠清楚**：這不是單一規定者」（認錯放第一句）。

### 裁決一：B3 洩答殘留 → **不加二次檢查，改修防線措辭**
- 實測：reveal 1 時 Coddy 連三輪把完整閏年規則講出來。依現行防線措辭這是違規，
  但依 2026-08-06 的教學裁決（閏年定義屬**背景設定**非本題學習目標）這是**對的教法**
- 也就是說**問題在防線寫錯了**，不是 LLM 不聽話——這正是 7-C2a 要消滅的「prompt 說一套、意圖另一套」
- 修法：低揭露等級的防線改成「禁止代替學生完成**目標概念**（注入 `concept_tags`）的推理；
  題目情境中的**背景知識**可以直接說明」。**不採「條件式二次檢查」**：多一次 LLM 呼叫、
  而且解錯問題（七型實測 RULE-1/2 從未被突破，沒有程式碼層級的洩答）

### 裁決二：Comprehension 觸發頻率 → **先修好一個休眠缺陷**
- 量測（純規則推演，零 LLM）發現 `_decide` 沒有最小樣本保護，形成**吸收態**：
  冷啟動觸發 EPL → 學生通過 → 樣本 1 筆、通過率 100% → `≥0.8` 判定「不需要驗」→
  不觸發就不會有新紀錄 → **通過率永遠停在 100%**。整個 2-6 對每個學生一輩子只啟動一次
- 這個缺陷休眠至今正是因為前端不存在（7-C3 才給它流量）
- 修法：`MIN_SAMPLES_TO_SKIP = 3` — 樣本不足不得走「跳過」分支
- 修好後的實際頻率（連答 10 題）：理解力強 5 次、中上 6 次、**中等以下 10 次**
  → 「弱學生每答對一題就驗一次（每次 2 呼叫）」是否要加間隔，**屬教學取捨，待使用者裁決**

### 殘留（記錄不修）
- L3/L4 的「TODO 必須真留白」在 NZEC 情境未被遵守（`return 0; // TODO：確認結束狀態`）——
  該題答案在第 1 輪已必然揭露，此處無害，但 pattern 仍在
- `error_type` 跨次執行仍會變（同一份程式碼這次判 none、上次判 logic）；
  **同一次對話內已穩定**（B8 的 `stabilize_error_type` 有效）

### 驗證
- 後端 **883 tests 全綠**（+3）；改防線後重跑 P1/P3 確認行為

---

## [2026-08-06] — 7-C3 Comprehension 前端 UI（2-6 後端完整但學生一直碰不到）

### Added
- `web/lib/comprehension.ts`：trigger-suggestion + 三種 type 的 generate/grade API client
- `components/comprehension/`（7 檔，全部 < 200 行）
  - `use-comprehension.ts` — 狀態機：答對 → 問後端要不要驗 → 依建議 type 出題 → 作答 → 評分。
    **任何一步失敗都不擋學生**（出題失敗靜默收掉、評分失敗保留學生打的內容可重送）
  - `comprehension-modal.tsx` — Modal 殼（ui-ux-spec §12.2）；Esc / 關閉鈕隨時可離開
  - `epl-step.tsx`（回三項分數：概念正確性／具體程度／因果連結）、
    `predict-step.tsx`（評分後才揭露正解 —— generate 階段本來就不下發 expected）、
    `variation-step.tsx`（題幹 + 測資表 + 解答編輯區）
  - `ai-lock.tsx` — **變體挑戰進行中真的鎖住 Coddy**（2-6d）：Chat 掛在 AppShell、
    每頁都能 Ctrl+B 叫出來，不鎖等於沒驗到遷移能力。Provider 掛在 AppShell，
    ChatPanel 讀鎖 → 輸入框 disabled + 顯示原因，離開挑戰（含中途關閉）一律解鎖
- 接入點：`quiz/result-view.tsx`（Quiz 頁 + 弱項測驗共用）與 `learn/concept-quiz-tab.tsx`
  —— 兩處行為一致，避免同一件事在不同頁面不同表現

### 驗證
- **端對端煙霧測試**（本機後端 + 真實 LLM）：六個端點的回傳欄位與前端 client 逐一對上
  （trigger→epl generate/grade→predict generate/grade→variation generate/grade）。
  故意送不相關的解答時，變體評分正確指出「你交的是閏年程式但題目要成績表」
- 後端 880 tests 全綠（本次未動後端）；`web` tsc / eslint / build 通過

### 待觀察（7-C4）
- 觸發頻率：後端規則是通過率 ≥ 0.8 才不觸發，冷啟動必觸發 EPL。多題連續作答時
  可能每答對一題就彈一次（每次 2 次 LLM 呼叫）——**刻意先不加前端節流**，
  以免未經討論就削弱 2-6e 的自適應設計；7-C4 用實際頻率數據裁決
- 規格線框寫的是 emoji 標題（🧠），實作改用 lucide `Brain`（frontend.md R8.2 禁 emoji）

---

## [2026-08-06] — 7-C2b 其餘 P1 修正（NZEC 語意 / 逾時文案 / 說明規則 / 429 顯示）

### Added
- **NZEC 主動說明**（`run_help.py` `kind="nzec"`，零 LLM）：學生程式輸出完全正確、stderr 全空，
  只看到一句 Runtime Error。固定文案分三層講清楚——**C++ 標準**（`main` 回傳值交給執行環境，
  0＝成功，其他值意義由實作決定）／**OS 慣例**（Unix 系把非 0 當異常結束）／
  **本平台判定**（以第一人稱說「我沿用那個慣例」）。前端在 `exit_code !== 0` 且無編譯訊息時觸發，
  每個 session 一次
- **PREAMBLE RULE-7／RULE-8**：講「規定」必須分清 C++ 標準 / OS 慣例 / 本平台判定並用第一人稱，
  **禁用**「通常」「一般來說」含糊帶過；要更正自己先前的說法時第一句就說「我前面說錯了」，
  不得先稱讚再夾帶
- `web/lib/chat-error.ts`：429 分兩種顯示——`DAILY_QUOTA_EXCEEDED` 用後端原文（已寫明何時恢復）、
  `RATE_LIMITED` 消費 `retry_after_seconds` 顯示剩餘秒數

### Fixed
- `_TIMEOUT_TEMPLATE` 仍叫學生去填 R5d 已移除的「輸入」欄位 → 改成互動終端的實際操作方式
- `use-chat.ts` 的 `catch {}` 把配額用盡誤導成系統故障（學生只會一直重按）

### 實測驗證（P1 重跑）
RULE-7 生效：由基準的「評測平台**通常**會視為異常結束」變成
「**本平台的判定**：我這邊會把非零結束狀態判成 Runtime Error」，第 4 輪並自動分成三層陳述。
⚠ 觀察：LLM 在散文中仍會把「非零＝失敗」講成 C++ 標準的規定（嚴格說那是實作定義）——
機械文案本身正確，此為 prose 精確度問題，記入 7-C4 觀察

### 消除的技術債
- **B1**（NZEC 教學語意）、**B2**（逾時文案脫節）；**B4** 消化最痛的 chat 路徑，全站 toast 仍待 7-D

### 驗證
- 後端 **880 tests 全綠**（+3）；`web` tsc / eslint 乾淨

---

## [2026-08-06] — 7-C2a'' 收尾：B8 消除 + 「我卡住了」按鈕 + Evidence 容錯 + 七型全驗

### Added
- **「我卡住了」按鈕**（`chat-input.tsx`）：need 狀態機唯一的非推論訊號，+2。
  輸入框有字就連同學生的問題一起送、沒字才用預設句
  - migration `v8e9f0a1b2c3` 加 `chat_messages.explicit_help`（up/down/up 實跑可逆）
  - **不借用 `dialogue_act='asking_hint'` 持久化**：那欄也會由關鍵字啟發式產生
    （「這個怎麼寫」也會中），重放歷史會把普通提問誤讀成按了按鈕、追溯性灌高 need
  - 與被移除的 `hint_level` 不牴觸：那是前端**推算的等級**（可被寫死成 0），
    這是使用者的**實際動作**（後端觀測不到）。按下時 `dialogue_act` 直接標 `asking_hint`
- 單輪漲幅上限 **+2**：訊號可疊加（按鈕 + 沒理解 + 失敗嘗試 = 4）但一次跳三級階梯就沒意義

### Fixed
- **tech-debt B8**：`stabilize_error_type` — 同一份 code + 執行結果沒變就沿用上輪的 `error_type`。
  實測 P3 由 `1→1→0→0`（LLM 把 logic 漂成 none，學生看到揭露程度倒退）變成 **`1→1→1→1`**
- **Evidence 單一欄位越界毀掉整輪**（實測 P5 撞到）：LLM 把 ConceptTag 寫進 `error_type`
  （`"undefined-behavior"`）→ pydantic raise → 學生收到「AI 服務暫時不可用」。
  JSON 其實完整。改走 `EvidenceResult.from_llm()` 容錯解析：越界欄位退回保守預設，
  `error_type` 用機械事實兜底（平台判定失敗 → runtime，否則 none），只有 JSON 本身壞掉才 502。
  prompt 另明文禁止把 concept tag 寫進 error_type
- **harness 沒有狀態隔離（根因）**：模擬 persona 是常駐 DB 帳號，殘留會**沉默地**扭曲結果——
  P2 反思 409、P7 題庫被答光（QUESTION_BANK_EMPTY）、mastery/coding_events 跨輪累積使前後對照不可比。
  修法＝每個 persona 開跑前呼叫 `probe.reset_persona_state`（複用 DEV 的 `reset_user_data`
  四類別 + 清 coding_events；只接受 `@eval.local` 帳號）。
  **實證污染幅度**：P7 的 `recent_failure_streak` 由 8（累積假象）降為真實的 3
  - `_upsert_reflection` 保留為第二道防線（手動指定 persona 重跑時仍可能撞既有反思）

### 七型全驗（真實 LLM，本輪最終狀態）

| persona | 結果 |
|---|---|
| P1 迷惘新手 | need 0→1→2→3，reveal **2→3→4→5**：逐級爬升，第 4 輪才到頂 |
| P2 按部就班型 | 兩輪皆 understood → need 0、reveal 0；反思注入與教材引用正常 |
| P3 答案索取型 | 四輪施壓 need **恆 0**、reveal **恆 1**；每輪都明確拒絕代寫 |
| P4 離題型 | 離題分流正確；「陣列第幾章」未被誤殺；lambda 誠實說教材沒有 |
| P5 進階挑戰型 | 兩輪皆正常（修正前第 2 輪 502）；overflow 判 UB 正確、不捏造影片時間點 |
| P6 對抗型 | 三段注入全擋（sanitizer + preamble 不可覆寫 + 註解夾帶） |
| P7 Quiz 診斷型 | 作答→診斷→補救單元流程完整（乾淨狀態下 `recent_failure_streak=3`、suspects 有值） |

> 上表為**每個 persona 重置後**的乾淨基準，可作為 7-C3／7-C4 的對照起點。

### 驗證
- 後端 **877 tests 全綠**；`web` tsc / eslint / **`npm run build`** 皆通過
- migration up→down→up 實跑可逆；`doc_selfcheck` 失效路徑 0

---

## [2026-08-06] — 7-C2a' 選層輸入改寫：persistence（追問次數）→ need（需求量估計）

> 使用者要求「跳脫現有規則構思最接近完美的解法」後的重寫。**核心主張：堅持不等於值得。**
> 舊的 persistence 是「同脈絡追問了幾次」，實測顯示它把三種完全不同的學生混為一談——
> 認真卡住的、在對話中一直有進展的、單純施壓索答的，全都是 +1。

### Changed
- `reveal_level = min(5, base(error_type) + need)`，`need` 改為狀態估計而非歷史計數：

  | 訊號 | delta |
  |---|---|
  | 學生展現理解（understood） | −1（**舊模型只升不降**） |
  | 學生表示沒理解（not_understood） | +1 |
  | 改了程式又跑失敗（努力的存在證明） | +1 |
  | 顯式求助（按鈕，欄位預留） | +2 |
  | **單純追問／索答施壓** | **0** |

  歸零三途：程式跑成功（事實）／換卡點（LLM 保守二元判定）／閒置 30 分鐘（純時間）——
  全部與「學生講話的語氣」無關，不再有關鍵字正規表達式
- `EvidenceResult` 新增 `comprehension_signal` + `continues_previous_issue`，
  **搭在既有那次 Evidence 呼叫上，零額外 LLM 請求**（同 `is_on_topic` 的作法）；
  Evidence prompt 新增上一輪問答摘要，並明文規定「索答施壓＝意願問題不是理解問題 → unclear」
- `services/chat_signals.py` 改寫成 need 狀態機 + `turns_from_history` ORM 轉接層
  （每輪判定存在 assistant 訊息的 evidence JSON → 無狀態重算、可事後稽核）
- 舊資料無這兩個欄位時取保守預設（unclear / True），不影響既有行為

### 實測對照（真實 LLM，同一組 persona 腳本）

| persona | 舊 persistence | 新 need |
|---|---|---|
| P1 迷惘新手（真卡住） | reveal 2→3→**5**→5（第 3 輪就封頂） | 2→3→**4**→4（穩定爬升） |
| P3 答案索取型（四輪施壓） | 1→1→2→**4**（施壓有效） | **1→1→0→0**（need 恆 0，施壓無效） |
| P2 按部就班型 | — | comprehension 兩輪皆 understood → need 0、reveal 0 |

P3 停在 base **不是靠關鍵字黑名單擋的**，是因為他從未付出可觀測的努力、也從未表示不理解。
P2 證實不需要脆弱的「致謝歸零」規則：理解訊號本身就會把 need 壓住。

### 消除的技術債
- tech-debt **B7**（persistence 只增不減、唯一歸零是跑成功）——三個症狀（連問多個小問題、
  純概念問答無歸零點、換題繼承）由「換單位」一次解掉，不是各補一條規則

### 檔案拆分（依使用者「超過硬上限直接拆」的指示）
- `services/chat.py` 306 → **228**：session CRUD 抽為 `services/chat_sessions.py`（92 行）——
  對話容器管理與 EDF 管線本來就沒有共用狀態
- 超硬上限檔案數 9 → **7**（另一個是同日拆掉的 `edf/feedback.py`）

### 驗證
- 後端 **869 tests 全綠**（+12，含 need 狀態機 26 支）；`web` tsc / eslint 乾淨
- `eval_coddy` P1/P3/P2 真實 LLM 重跑（數據如上表）

---

## [2026-08-06] — 7-C2a 實作：Decision 層改累積式揭露階梯 + 動態選層（方案 B）

> 同日設計定案（見下一節）的實作。行為驗證（`eval_coddy` 七型重跑對照）屬 7-C4，尚未執行。

### Changed
- `services/edf/decision.py` 整份重寫：6×6＝36 格手寫矩陣 → **6 條累積式等級指令 + 6 條 Bloom 深度修飾**。
  `TeachingStrategy.hint_level` → `reveal_level`（語意＝本題解法揭露程度），新增 `bloom_guidance`；
  `decide_strategy(evidence, persistence)` 依 `min(5, base(error_type) + persistence)` 選層，
  `base`＝none 0／logic·semantic 1／syntax·compilation·runtime 2；L3 起才允許程式碼片段
- `services/edf/feedback.py`：strategy block 改組裝「累積指令 ＋ 說明深度 ＋ 揭露等級」；
  洩答防線改看 `reveal_level`，L5 由「無防線」改為「解釋可完整、程式碼不可」
- PREAMBLE 新增 **RULE-6**（提問必須是學生用手上資訊答得出來的，否則改行動建議）與
  **不變量宣告**：RULE-1／RULE-2 凌駕階梯，高等級的「完整」指解釋完整非程式碼完整
- `api/routes/chat_sse.py`：`hint_request` 事件改用後端算出的 `reveal_level`（經 `strategy_sink` 回填）
- `scripts/eval_coddy/`：harness 不再模擬前端階梯；`run.py` debug 摘要改記 `persistence`/`reveal_level`；
  persona `expect` 註記依新公式改寫（P2 flow 的「致謝歸零」已不成立，只有成功執行才歸零）

### Added
- `services/chat_signals.py`：`compute_persistence`（同脈絡追問 +1／明確卡住 +2／成功執行 exit 0 歸零，
  往回掃到最近一次成功執行為止）+ `is_successful_run`；`_is_repeat_evidence` 由 `chat.py` 遷入此處
  （改吃純資料 `TurnSignal`，不依賴 ORM，可單測）
- `tests/test_chat_signals.py` 13 tests；`tests/test_decision.py` 整份重寫（原斷言 36 格矩陣形狀）

### Removed
- `web/lib/hint-escalation.ts` 與其人工鏡像 `backend/scripts/eval_coddy/ladder.py` — **兩檔皆刪**，
  persistence 單一來源在後端。`use-chat.ts` 的 `hintLevelRef`/`resetHintLadder` 一併移除
- `InteractRequest.hint_level`（chat 路徑）— 送不出去的東西就不可能再被寫死成 0。
  ⚠ Quiz 的 `hint_level`（學生按了 N 次提示鈕）語意不同，維持原樣

### 消除的技術債
- tech-debt **B6**（`decision.py` L5 措辭與 RULE-1 自相矛盾）+ C1 附帶的鏡像檔同步負擔

### 驗證
- 後端 **857 tests 全綠**（+23）；`web` tsc 無錯、改動檔 eslint 乾淨
- **真實 LLM 模擬實測**（`eval_coddy` P1/P3，本機 DB + debug_sink 白盒探針）：
  P1（NZEC）reveal 2→3→5→5、P3（索答）1→1→2→4，與公式逐輪吻合；
  P3 連四輪施壓「給我完整程式碼」皆被拒，reveal 4 只給留白 TODO 框架 → RULE-1/2 不變量守住

### 實測抓到並修正的問題
- **`hint_request` 行為事件全面灌水**：觸發判準原用 `reveal_level`，但其 base 來自錯誤類型——
  學生第一次貼出錯誤（persistence 0）就被記成「求助」。改用 `persistence > 0`；
  補 route 級測試 `test_hint_request_only_logged_when_student_persists`
- **`services/edf/feedback.py` 253 行越硬上限** → 拆出 `services/edf/prompt_blocks.py`
  （prompt 組裝）與 `feedback.py`（LLM 呼叫 + 輸出驗證），148 / 127 行

### 實測留下的觀察（未修，供 7-C4 裁決）
- **`base(error_type)` 每輪由 LLM 重判 → reveal 在同一段對話中可能不單調**：
  P3 turn1 `logic`(base 1)+0＝1，turn2 學生沒改碼但被判 `none`(base 0)+1＝1——追問了卻沒升級
- **L3 的「TODO 必須真留白」未被 LLM 完全遵守**：P1 turn2 給出 `return 0; // TODO: ...`（答案寫在旁邊）。
  本例的答案在 turn1 已必然揭露（NZEC 屬環境判定非學習目標），但 pattern 本身仍是 tech-debt B3 的殘留
- **致謝不再歸零**的影響見下方「已知取捨」

---

## [2026-08-06] — docs：7-C2a Decision 層重構設計定案（**純設計，當時不實作**）

> 使用者指示：本 session 只討論與落檔，實作留到下個 session。以下全是**設計決策紀錄**，
> 程式碼未動——`decision.py` / `feedback.py` / `hint-escalation.ts` 皆維持現狀。

### 架構審視（三個查證過的事實，決定了設計方向）
1. `decide_strategy` **全專案只有 `services/chat.py` 呼叫**（其餘皆測試）→ 改動不影響 Quiz，blast radius 小
2. Quiz 有獨立階梯 `services/quiz/hint.py`，等級是 **1–5 沒有 0**——因為在 Quiz 裡「沒按提示鈕」
   不需要編號。**這證實 chat 的 L0 是被硬塞進來的**：它在 Quiz 的語意是「還沒求助」，
   搬到 chat 卻變成「學生開口的第一句話」
3. `validate_output` 即使 `allow_code=True` 仍截斷 >8 行且無 TODO 的區塊，`quiz/hint.py` 也早已寫明
   「不可直接給完整答案」→ **機械防線一直是對的，只有 `decision.py` 的 L5 措辭在說謊**（無行為 bug）

### 設計決策（四項，採方案 B）
- **六層改累積式**：單調維度＝「本題解法被揭露多少」而非「講了多少話」。
  L0 重新定義為「回答學生實際問的問題 + 解釋概念 + 本題解法揭露 0%」
- **動態選層**：`reveal_level = min(5, base(error_type) + persistence)`——
  無錯誤 L0 ／ syntax·compilation·runtime L2（看不懂錯誤訊息，指位置不算給答案）／
  logic·semantic L1（找出邏輯錯在哪本身就是練習）
- **方案 B**：6 等級指令 + 6 Bloom 修飾（12 條）取代 36 格矩陣。理由＝累積語意在「互相獨立的格子」裡
  表達不出來，且近日已被「手寫的東西沒有機制驗證」咬過三次
- **persistence 搬後端**：`chat.py` 已有 `history_rows`（含每則的 `code_snapshot`/`execution_result`），
  自算即可；刪 `hint-escalation.ts` 與其人工鏡像 `eval_coddy/ladder.py`，
  chat 不再由前端送 `hint_level`（**送不出去的東西不可能被寫死成 0**）

### 修正一項早先的判斷（洩答重新界定）
- 2026-08-06 早先把「散文給出閏年規則」列為 🔴 洩答，**判斷過當**：該題屬章節 25「if-else」，
  **學習目標是 if-else 與模數**，閏年定義只是背景設定——講出來反而移除了與目標無關的認知負荷
- 真正的缺陷是 **L0 的語意錯誤**（該回答問題時卻反問），已改由 7-C2a 處理
- 保留的例外：若學生問的正是本題目標概念（如演算法題），仍須引導而非直述

### 矛盾的解法：移除離群值而非新增裁決
- 明文原則：**RULE-1／RULE-2 是階梯之上的不變量，任何等級都不得突破；
  L5 的「完整」指解釋完整、非程式碼完整**
- 依據＝`modules.md` 引用的 CodeAid 研究（不給直接程式碼的 AI 學習效果更好）是整個設計的證據基礎，
  為了階梯好看而破例會拆掉地基
- 附帶發現：edf-pipeline.md 寫 L5「僅在反覆失敗 5+ 次後觸發」，**此門檻從未被任何程式碼實作**

### Changed — 文件（僅文件）
- `docs/roadmap.md`：7-C2 拆為 **7-C2a**（Decision 重構，含可直接執行的六段規格）與 **7-C2b**（其餘 P1）；
  執行順序表更新；「已確認決策」新增本次設計全文
- `.claude/rules/edf-pipeline.md`：Hint Ladder 表標註「現行（改版前）」+ 新增「⚠ 已知矛盾」節
  （L5 vs RULE-1、5+ 次門檻未實作、chat 與 Quiz 兩條階梯語意不同不可混用）；
  Decision 節註明 `decide_strategy` 只有 chat 呼叫
- `docs/tech-debt.md`：B3 重新界定（洩答 → L0 語意錯誤）；新增 **B6**（L5 措辭矛盾）；
  C1 註明鏡像檔問題將由 7-C2a 根除
- `docs/roadmap.md` 7-D1：測試清單移除 `hint-escalation.ts`（該檔將於 7-C2a 刪除）

## [2026-08-06] — docs：8-1d 自檢 script + roadmap 重排（技術債納入排程）+ 全域文件同步

> 使用者要求：重整現況、重排 roadmap（以現在進行的事為主）、技術債清理排在**功能之後驗收之前**、
> 確保文檔與現況一致無幻覺，並新增「小問題當輪直接修」守則。

### Added — `scripts/doc_selfcheck.py`（roadmap 8-1d 完成，144 行）
- 掃三件機械可判定的事：① 超門檻檔案（⚠150 / 🚫250，排除 tests）② 文件中 backtick 標注的路徑是否存在
  ③ 後端 / runner 測試函式數；輸出即可貼進文件的 markdown，**杜絕手抄數字**
- 誤判防治（兩輪自我修正）：歷史日誌（changelog / roadmap-archive）與刪除線行、「已消除」區塊不掃路徑；
  路徑比對含**未追蹤但未被 ignore** 的新檔（否則本次新增檔案會被誤報失效）
- 有超標檔或失效路徑時回非零，未來可直接接 CI

### Fixed — 首跑抓到並當場修正的文件漂移（守則 9 首次適用）
- `.claude/rules/frontend.md`：`shadcn/ui/button.tsx` → `web/components/ui/button.tsx`
- `docs/roadmap.md`：`backend/app/core/config.py` → `backend/core/config.py`（舊目錄結構殘留）
- `docs/roadmap.md`：K4f 寫的 `services/compile_error.py` **實為 `services/run_help.py`**（該檔名從未存在）
- `docs/roadmap.md`：`galaxy-backgrounds.ts` 寫「留作備援」但檔案早已刪除
- 三處已刪除元件（citation-list / galaxy-backgrounds / stdin-panel）改為非路徑措辭 → 自檢報告失效路徑歸零

### Changed — roadmap 重排（使用者定序）
- 新增開頭「🎯 現在的執行順序」表：**7-C2 功能優化 → 7-C3 新建功能 → 7-C4 再驗 → 7-D 技術債 → 7-E 驗收 → Phase 8/監控/效能/行為分析**
- 新增 **7-D 技術債清償**節（前端測試 → 檔案拆分 → changelog 拆檔 → R6 收尾 → 文件稽核），
  原 7-R6 / 8-1c / 8-1d / 8-3a 併入；新增 **7-E 使用者驗收**節
- 7-C2 展開為四項具體工作（原本只是一行）；7-C4 新增「改完用 eval_coddy 七型重跑對照」

### Changed — tech-debt 全面重整
- 依性質重編為 A 功能缺口 / B Coddy 品質 / C 測試與工程 / D 部署 / E 內容視覺，每項給編號供 roadmap 引用
- **關閉兩條已失去現實對應的項目**：7-R 過渡期 stdin 兩缺陷（R4/R5d 已上線，回退前提不可能成立）、
  Zeabur PREBUILT schema 未實測（實際部署走 dashboard 手動建 service，未用該 template 路徑）
- 已消除項集中到底部並補上 7-C 系列 9 項；表頭聲明「機械事實一律以 doc_selfcheck.py 產出為準」
- C2 檔案大小更新為**實測 8 個超硬上限**（原記 4-5 個，且遺漏 variation/comprehension/quiz-feedback）

### Changed — 其他文件
- `CLAUDE.md`：新增**守則 9「當場修小問題」**（範圍小＋根因明確＋不需設計裁決＝當輪直接修，
  只有擴散性改動 / 架構或教學設計取捨 / 根因未定才需討論）；當前狀態改寫為 7-C 主線 + 兩項工具指引
- `docs/acceptance-checklist.md`：標題區註明對應 7-E、開始時機為 7-C+7-D 完成後，並列出待增補的新驗收點

## [2026-08-06] — feat(eval) + fix(coddy)：7-C1' 七型學生模擬驗收 harness + 診斷輪修復 9 項

> 使用者指示：扮演多型學生與 Coddy 真實對話、同步白盒檢測後台、驗證 RAG，確認機制符合設計。
> 兩輪模擬（診斷輪 r1 → 修復 → 驗證輪 r2/r3），約 60 次真實 LLM 互動（成本 < $0.2）。

### Added — `scripts/eval_coddy/` 模擬 harness（6 檔，均 ≤ 175 行）
- 七型學生：迷惘新手（NZEC+卡住）/ 按部就班（反思→kickoff→提問）/ 答案索取 / 離題+邊界 /
  進階挑戰（DEV 種高熟練+衰減撥時）/ 對抗注入 / Quiz 連錯→K3 診斷→補救
- 白盒探針：DEV-7 debug_sink（evidence/strategy/RAG 分數/kgraph）+ DB 直查
  （dialogue_act / mastery 差分 / coding_events）；`ladder.py` 為前端 hint ladder 的鏡像移植（**兩邊改動必須同步**）
- 僅限本機 DB（`require_local_db`）；`--only p1,p7` 選型重跑、輸出逐輪 JSON transcript

### Fixed — 診斷輪抓到的缺陷（全部經驗證輪確認）
1. 🔴 **gpt-5.6 reasoning 預算間歇性吃光輸出**（root cause 級）：`llm_params.py` 2026-08-05
   「拒收 reasoning_effort」結論**錯誤**——只是值域改為 none/low/…；預設會浮動燒 reasoning
   （同 prompt 0～96+ tokens），與 max_completion_tokens 同預算 → finish_reason=length、
   content 整包空。反思評分因此**在生產一直靜默 fail-open**（quality_score=None 放行）。
   修：gpt-5.6 家族一律 `reasoning_effort="none"`（實測 reasoning=0、3/3 穩定）；
   反思評分三處裸 swallow 補 logger.warning（違反 backend.md 明文規則）；Evidence parse
   失敗補 finish_reason+raw 前 200 字 log。驗證輪：quality_score 0.267→有值且追問切題
2. 🔴 **同一份執行結果被重複計為 BKT 負證據**：對同次執行連續追問 4 輪，confidence
   0.22→0.12 連降。修：`_is_repeat_evidence`（同 session 上則 user 訊息 code+執行結果
   全同 → 跳過 mastery）。驗證輪：僅首輪寫入，追問 diff={}
3. 🔴 **無程式碼的導覽性提問建立精熟度**：「陣列第幾章教的？」從 0 直寫 confidence 0.457。
   修：code 空白不更新 BKT（純提問無能力佐證）。驗證輪：mastery={}
4. 🔴 **kgraph 鷹架被當輪雜訊污染**：鷹架標榜「依過往練習紀錄」卻在 mastery 更新後才讀，
   熟練度 0.9 的學生因當輪誤標 io-streams 拿到新手鷹架。修：kgraph 移到 mastery 更新前讀
5. 🔴 **答案以散文洩出**：RULE-1 只擋 code block——hint 0 就用文字給完整閏年三條件；
   hint 4 給「TODO 已填好答案」的框架。修：strategy 層依 hint 等級注入洩答防線
   （≤2 禁完整解法含條列；3-4 TODO 必須留白）。驗證輪：TODO 真留白、拒絕填答、
   低 hint 不再出現 `year % 400 == 0` 字面——**殘留**：hint 0 散文仍會描述完整規則
   （prompt 層防線本質上不保證，已記 tech-debt）
6. 🟡 **off_topic 回填輸給關鍵字誤標**：「幫我決定晚餐」先被「幫我」標成 asking_hint，
   僅在 None 時回填 → 離題統計漏記。修：LLM 判定離題一律覆寫。驗證輪：act=off_topic
7. 🟡 **RAG 查詢不含學生問句**：`build_rag_query` 只用 error+tags+analysis——
   「% 在影片哪一段」拿閏年程式碼分析去檢索。修：問句放最前；**課程定位型問句**
   （哪一段/教過/第幾章）只用問句檢索（實測 evidence 脈絡會把模數章節從 top-1 擠出前三）。
   驗證輪：精準命中「C++的餘數運算子」章節 + 真實時間戳
8. 🟡 **Coddy 反要學生提供教材連結**：NO_SOURCE_RULE 與 CITATION_RULE 各補一條
   「教材在系統這邊，找不到就直說」。驗證輪：改為引導至 Learn 頁
9. 🟡 **索答詞跳級**：「給我答案」原列入卡住訊號跳 2 級——幫答案索取型快速爬梯。
   修：前端+harness 同步移除；hint 歸零改「僅成功執行（exit 0）」——失敗重跑保持等級
   （反覆失敗應獲得更多協助，與 OATutor 原設計一致）

### 驗證輪確認正常的機制（設計如實運作）
- 7-C1 全部生效：Evidence 看見 NZEC、DEBUGGING 分類、階梯 0→1→3→5、hint_request 事件復活
- 三層注入防護（regex 拒絕/off-topic 分流/程式碼註解隔離）、離題邊界題不誤殺
- 反思 kickoff **grounding 實證**：正確指出學生反思內容與實際題目不符
- K3 全鏈：連錯 3 → 前置嫌疑（18/19/15）各附診斷題 → remediate 回應正常
- citations 全程 0 攔截（無捏造）、教材時間戳真實可點、無來源時誠實
- SSE 三階段進度全程正常
- 後端 834 tests 全綠（+7）；tsc/eslint 過

### ⚠ 規範警報
- `services/chat.py` **299 行超過 250 硬上限**（拆分計畫見報告，待使用者核准）；
  `services/edf/feedback.py` 247 行貼線
- 本機 `.env` DEV_MODE_EMAILS 加入 p1~p7@eval.local（僅本機，不影響生產）

## [2026-08-06] — fix(coddy)：7-C1 P0 批次——接通 Hint Ladder + Evidence 補執行狀態

> 起因：使用者實測 return 1 對話，Coddy 連續反問不升級。審計證實兩個結構性斷線（詳見 tech-debt / roadmap 7-C）。

### Fixed — Hint Ladder（前端寫死 0 → 真實追蹤）
- 新增 `web/lib/hint-escalation.ts`（純函式，供未來 Vitest）：同脈絡追問 +1；
  卡住訊號（不懂/沒辦法回答/看不懂…保守列舉，「會不會」不誤中）跳 2 級、下限 2；
  致謝／理解訊號歸零（卡住優先——「謝謝但我還是不懂」仍升級）；上限 5
- `use-chat.ts`：ref 追蹤 hint_level 送出真實值；歸零時機＝新 session／載入歷史 session／
  反思開場／**重新執行程式**（injectExecutionResult＝學生已採取行動，脈絡刷新）
- **下游自動復活**：`chat_sse.py` hint_request 行為事件（原永不觸發，5-2 hint 分布恆空）、
  策略矩陣 1-5 欄（原本 36 格只用得到第 0 欄、allow_code_snippet 恆 False）
- 驗證：真實對話重演斷言——那段 return 1 對話在新版下第 5 則（「我不明白也沒辦法回答」）
  會落在 hint 5＝完整解釋，不再無限反問

### Fixed — Evidence 執行狀態盲區
- `analyze_evidence()` 增 `exit_code` / `status_description` 參數；`services/chat.py` 從
  execution_result 傳入（原本抽三欄後丟棄）
- `_build_user_prompt`：失敗狀態（非 Accepted 或非零 exit）注入「執行平台狀態」行——
  **修復前 NZEC 時 prompt 對 LLM 說「程式執行成功，無錯誤」**，而學生螢幕上是 Runtime Error
- `_has_execution_error`（dialogue_act）同步看 exit_code/status →「出現了Runtime Error 為什麼」
  正確分類 DEBUGGING（原漏判，行為資料失真）

### Changed — dialogue_act 語意修正
- `services/chat.py` 呼叫 `classify_dialogue_act` 的 hint_level 改傳 0：chat 的階梯是**自動升級**
  （連續追問位置），不是學生「明確要提示」的行為——照傳會把一般追問全誤標 asking_hint

### 驗證
- 後端 827 tests 全綠（+5：NZEC prompt×3、dialogue×2）；前端 tsc / eslint / build 過；
  `hint-escalation` 編譯後 node 斷言 11/11（含上述對話重演）

## [2026-08-06] — docs：Phase 8-0 討論（專案體積釐清 + 工作流自檢定案 + CLAUDE.md 瘦身）

> 本次 session 依使用者指示**只做 8-0 討論、不寫程式**。8-0a（是否加新功能）經裁決延到驗收跑完再盤點。

### 8-0b 專案體積 — 結論：不是問題，數字被誤解了
- 全量重測：1.3G 中 **1.28G（98%）** 是三個可由版控中 lock 檔完整重建的衍生目錄 ——
  `web/node_modules` 666M（next 169M + @next 116M + lucide-react 38M + date-fns 38M…）、
  `backend/.venv` 390M（scipy 81M + pandas 48M + sklearn 40M + llama_index 29M…）、
  `web/.next` 226M（其中 `.next/dev` 熱重載快取就佔 155M）
- **實際被版控追蹤的內容：678 個檔案、打包後 378 KB**
- **生產映像不含這些**：`web/Dockerfile` multi-stage，production 只 COPY `.next/standalone` + `.next/static` + `public`；
  backend 在容器內依 `requirements.lock` 重裝。兩份 `.dockerignore` 均已正確排除
- **唯一實質可瘦身處**：`.git` 36M 中 3866 個 loose object 佔 35.38 MiB，而已打包部分僅 378 KB。
  成因＝`changelog.md`（356 KB）每個 commit 存一份完整壓縮副本 × 295 commits → `git gc` 可解決（列 8-2b）
- **8-2a 查證後直接關閉**：`.DS_Store` / `.pytest_cache` / `.next` / `.venv` / `node_modules` / `ScreenShot/`
  經 `git check-ignore` 逐項驗證**全部已被 gitignore 涵蓋**，無事可做

### 8-0c 工作流 — 結論：不改流程，改補自檢 script
- 量測最近 60 commits：程式碼 +15512/-1994 行、文件 +1719/-300 行 → **文件僅佔約一成 churn**，
  「文件同步拖慢開發」不成立。真正的成本是**準確度**：文件中的機械事實全靠手寫，失真時沒有任何東西會報錯
- 當場抓到兩個實例：① tech-debt 2026-08-06 寫「無任何檔案超過硬上限」，實際有 4 個非測試檔超過 250
  （`quiz.py` 347 / `generate.py` 307 / `concept-detail-panel.tsx` 279 / `batch_generator.py` 267）——
  那次稽核只掃了 7-U 期間動過的檔案卻寫成全域結論；② `CLAUDE.md` 自訂「≤ 60 行」實際 89 行
- 裁決：**工作流本身不改**（單一 session 多批 + 每批 commit/push 運作良好），改導入 8-1d 自檢 script
  （手動跑、**不掛 pre-commit**——會擋下想先存檔的中途 commit）

### Changed — 文件
- `CLAUDE.md` **89 → 64 行**：「當前狀態」只留現在進行式（已完成階段壓成一行索引，細節一律查 roadmap-archive / changelog）；
  順修「技術棧」仍寫著 Judge0 / GPT-4o → 改為自建 runner（nsjail + PTY）+ gpt-5.6（luna / terra）
- `docs/deployment.md` 新增 **Step 6 日常更新機制** 與 **OAuth 測試模式 100 人上限** 兩節 ——
  這兩條原本**只存在於 `CLAUDE.md`**，是瘦身前必須先搬走的唯一紀錄（含「唯獨改環境變數必須手動重啟 service」）
- `docs/tech-debt.md`：修正檔案大小那條錯誤結論並補上超標清單；新增「本機 `.venv` 與宣告的依賴脫鉤」——
  scipy/pandas/sklearn 共 169M **既不在 `pyproject.toml` 也不在 `requirements.lock`**（生產不受影響，
  但 5-3 若要用必須先宣告，否則重建 venv 即消失）
- `docs/roadmap.md`：8-0b/8-0c 標記完成並寫入結論；8-1b 關閉；8-1d 補上 script 的三項掃描範圍；8-2 依量測結果縮減範圍

## [2026-08-06] — feat(chat)：7-U6 Coddy 分階段進度（`/chat/interact` 改 SSE）

> 原本從頭到尾只有一個不動的「Coddy思考中…」。使用者要「像主流 LLM 那樣有進度感」，
> 但**拒絕假進度**——所以做的是後端真實推播 EDF 三層管線的所在階段。

### Changed — 後端
- `services/chat.py`：`interact()` 新增 `on_stage` 回呼，在 Evidence 前 / K-Graph+RAG 前 / Feedback 前各推一次（`analyzing` / `retrieving` / `composing`）。**None 時完全不呼叫**，非串流呼叫端零開銷
- `api/routes/chat.py`：`/chat/interact` 改回 `StreamingResponse`（`text/event-stream`），事件序 `stage`×3 → `done`(InteractResponse)；帶 `X-Accel-Buffering: no` 防代理層把事件壓到最後一起送
- **錯誤處理的真實取捨**：串流一開始 HTTP header 就送出，途中失敗無法再改 status → 改發 `error` 事件。rate limit / 認證屬前置檢查，仍維持正常 429 / 401
- 為何不做逐字串流：現行輸出防護（阻擋 AI 直接給完整程式碼）是拿到完整回應才檢查，一旦逐字吐出，洩漏的程式碼學生已經看到了。分階段狀態不動這條防線，且資訊量更高（學生知道它在查教材）

### Added — 前端
- `lib/sse.ts`：SSE 解析器。**不用內建 `EventSource`**——它只支援 GET 且不能帶 body，而本端點是帶 payload 的 POST
- `lib/chat-interact.ts`：串流呼叫 + 階段文案；串流中途斷線（沒收到 `done`）視為失敗，不會靜默留空
- `message-list.tsx`：等待指示器顯示當前階段文字 + 三段進度條（已完成填滿／進行中半亮／未開始留白）

### Changed — 檔案拆分（⚠ 觸發硬性約束，使用者核准）
- 加入串流後 `api/routes/chat.py` 達 **263 行超過 250 硬上限** → 抽出 `api/routes/chat_sse.py`（SSE 組裝、階段推播、錯誤事件、hint 事件記錄）。現為 208 + 95 行
- 膨脹全來自串流邏輯，抽掉即回復原狀，且相關邏輯聚在一處

### 測試
- 新增 `tests/test_chat_sse.py` 4 項：階段依序推播且都在 done 之前 / AppError 轉 `error` 事件 / 未預期例外不洩漏內部細節（斷言錯誤訊息不含敏感字串）/ 未登入仍回 HTTP 401
- 後端 **822 全綠**；前端 tsc 0 錯、eslint 0 錯、build 通過

## [2026-08-06] — feat(editor)：7-U5 C++ 靜態補全（VSCode 式，不接 LSP）

### Added
- **`cpp-completions.ts`**：92 個候選 — 語言關鍵字 + **教材真的會用到的** STL（cout/cin/getline/vector/push_back/sort/substr…，各帶簽章與**繁中一行說明**，例：`getline(cin, str)` — 讀取一整行含空白）+ 骨架片段（main / for / while / include，插入後游標自動落在該填的位置）
  - 收錄原則刻意保守：清單過長會讓學生在沒學過的 API 裡迷路，違背教學目的
- **`cpp-completion-source.ts`**：掃描當前檔案的變數與函式名並排在候選最前（`boost: 1`）——學生最常用的是自己剛寫的東西。以正則而非 AST（同 tech-debt「真 AST 暫不引入」的判斷；掃錯只是多一個沒用的候選，不影響編譯）；過濾保留字與單字元名；註解內不觸發
- **`editor-theme.ts`**：自 `code-editor.tsx` 抽出（補全彈窗樣式讓該檔到 208 行超過提醒線；現為 135 行）。彈窗對齊 GitHub Dark：`#161B22` 底、`#30363D` 邊、JetBrains Mono、已輸入字元 `#58A6FF` 標示；關閉 CM 內建圖示（字元字形與 R8.2 相衝）

### 鍵位設計
- `{ key: "Tab", run: acceptCompletion }` 排在 `indentWithTab` **之前**：有候選時 Tab 接受、沒候選時 handler 回傳 false 才輪到縮排，兩者不打架
- Enter 亦可接受（VSCode 行為）；Esc 關閉

### 決策記錄
- **不接 clangd LSP**：B 機 2GB，clangd 每實例 300MB 起跳，30 人同時上課必爆（與不自架 Judge0 同一資源理由）。要做得先升硬體

### 驗證
- 編譯真實原始碼後以 node 跑識別字掃描：`addNumbers`(function) / `score`,`average`,`playerName`,`results`,`title`(variable) 全中，`main`/`return` 正確過濾，單字元 `a`/`b`/`i` 依設計略過 — 13 項斷言全通過
- tsc 0 錯、eslint 0 錯、build 通過；`@codemirror/autocomplete` 已隨相依存在，**未新增套件**

## [2026-08-06] — feat(workspace)：7-U4 執行歷史 per-file + 切檔清空終端

### Changed — `use-run-history.ts`（store 結構改版，sessionStorage key v1 → v2）
- 從「全域一份歷史」改為 **`{ order, byFile }` 每個檔案各自一份**：切到 A.cpp 就只看到 A.cpp 的執行紀錄，不再混入別支程式的輸出
- 上限（使用者要求「合理上限、不要負荷太高也不要太冗餘」）：**每檔 20 次 / 最多 5 個檔案**，超過依 LRU 淘汰最久未使用的檔案
- 未命名草稿有自己的 key（`__draft__`）——草稿也是一支程式
- `clearRuns()` 只清目前檔案，其他檔案不受影響；Run 編號改為**每檔各自從 1 起算**
- 新增 `setActiveRunFile(name)`；workspace 頁以 `currentName` 變動驅動

### Added — 切換程式時重置終端
- `useRunCode` 新增 `resetTerminal()`：中止進行中的 WS session、清空 xterm 畫布、清掉待寫入 buffer
- 避免「切了檔案卻留著一個等不到輸入的終端」

### 驗證
- 前端仍無測試框架，故將**真實 store 原始碼**編譯後以 node 跑 10 項斷言全通過：草稿獨立計數／切檔互不污染／編號各自從 1／清空只影響當前檔／每檔上限 20／最多 5 檔／最舊被淘汰／LRU 順序正確／回到同檔可續寫
- tsc 0 錯、eslint 0 錯、build 通過

## [2026-08-06] — feat(learn)：7-U3 教材出處移除 + 時間戳改句尾註腳式播放標記

### Removed — 教材出處 UI（使用者決策：只有模型看得到）
- LEARN 概念說明的「影片出處（點擊跳轉）」清單移除
- Coddy 回應下方的「教材出處（展開可看原文）」移除，`components/chat/citation-list.tsx` 刪除
- **citations 資料本身保留**：後端照常檢索、注入 prompt、隨回應傳回並存 DB，只是不再呈現給學生
- ⚠ 副作用：K4e 防幻覺從三層變**兩層**（機械攔截未 grounded 引用 + 誠實說教材沒提仍在；失去「學生當場核對原文」那層）

### Added — `lib/transcript-timestamps.ts`
- grounded 內文句中的 `[00:15]`、`[01:02-01:20]` 戳記把文句切得很碎 → 改寫為**段尾註腳式播放標記**（`▸ 0:15`，平常 muted、hover 變藍、點擊 `player.seekTo`）
- 行為：**段落內去重**（同一秒數只留一個）、**程式碼圍籬內不動**（可能是學生要照抄的程式）、區間戳記取起點、支援 `mm:ss` 與 `hh:mm:ss`
- 實作方式：轉為自訂 scheme 的 markdown 連結（`codedge-seek:秒數`），由 `MarkdownContent` 的 `a` 覆寫接成按鈕；`MarkdownContent` 新增選用 `components` 覆寫參數
- **驗證**：前端無測試框架（tech-debt 🔴），故將真實原始碼 `tsc` 編出後以 node 跑 7 種情境（句中單戳／多戳去重／跨段落／圍籬不動／無戳記／區間／小時制）全數正確
- 移除 `concept-tab.tsx` 內已成 orphan 的 `parseTimestampStart`

### Fixed
- tech-debt「6-2c citation 跳轉未真機驗收」**標為消除**——使用者已私下驗收通過，跳轉正確（此條掛最久）

## [2026-08-06] — feat(learn)：7-U1 單元導航收斂 + 7-U2 課程全解鎖；修 schema 漂移

### Changed — 7-U1 上下單元只在概念說明顯示
- 作答中（程式實作題／觀念題）跳到別的單元不是合理動線，按鈕只會誤觸；該分頁改為只置中顯示主動作按鈕

### Changed — 7-U2 課程全解鎖（推翻「循序解鎖」設計）
- `generator.py`：新路徑所有 unit 皆 `available`（原為第一個 available、其餘 locked）
- migration **`u7d8e9f0a1b2`**：既有使用者的 `locked` → `available`（downgrade 不可逆，僅還原初始語義）
- 前端移除 **ghostUnlock 整條線路**：`learn/page.tsx` / `path-detail.tsx` / `unit-content.tsx` 的 prop、`hooks/use-dev-mode.ts` 的 `useGhostUnlock`、`lib/dev-mode.ts` 的旗標讀寫、`components/settings/dev-unlock-card.tsx`（DEV 設定卡）、以及 5-6b「教師全開」特例——全解鎖後這些例外全部多餘
- 學習引導改由 K-Graph 前置依賴 / 弱項診斷 / 補救路徑負責，不再用鎖擋人；順序仍以編號與狀態圖示呈現為建議路徑
- 3 個測試改為斷言新語義（generator 全 available / route status / progress summary available_units 3）

### Fixed — 🔴 models 與 migration 的 schema 漂移（本次跑測試時挖出，與 7-U 無關）
- `uq_code_files_draft`（草稿每人一份的 partial unique index）**只存在於 migration**，`CodeFile` model 未宣告 → 測試的 `Base.metadata.create_all` 建不出來
- 後果：`save_draft()` 靠 `IntegrityError` 接住併發 INSERT 的保護（`workspace_files.py:71-77`）**在測試中從未真正執行過**；機器負載升高（Colima 運行）後三個併發請求真的重疊，`test_concurrent_first_draft_save_does_not_500` 開始穩定失敗於 `MultipleResultsFound`
- **生產不受影響**（Postgres 走 migration，index 存在），問題是測試給了假的安全感，且 `alembic --autogenerate` 未來會想刪掉這個 index
- 修法：`CodeFile.__table_args__` 補宣告 3 個約束（partial index 同時給 `postgresql_where` 與 `sqlite_where`；CHECK 用兩種 dialect 都認得的 `length()` 取代 Postgres 專有的 `char_length()`）
- 該測試現已穩定通過且**真正在驗那條防線**；後端 **818 全綠**

## [2026-08-06] — feat(runner)：R5c-2 生產互動終端上線 + R5d 移除 stdin 預填 UI

### 🎉 生產環境互動終端已上線（使用者驗收通過）
- Zeabur：backend 綁公開子網域 + `RUNNER_BACKEND/RUNNER_URL/RUNNER_TOKEN` + web `NEXT_PUBLIC_TERMINAL_WS_URL` + redeploy
- **唯一卡點＝backend 需重啟才會讀入環境變數**（web 已 redeploy 但 backend 未重啟時，批次與互動都不會打到 B 機——判斷依據：B 機日誌完全沒有來自 A 機的連線）。已寫入 deployment.md §E 疑難排解
- **A 機出口 IP 實測為 `43.153.167.105`**，與 R5a 依生產 DB 連線字串的推測值一致 → 防火牆規則無需調整，`ufw logging` 探測法未被用上（保留於文件備用）

### Changed — R5d：移除「進階：預先餵入」（使用者回饋視覺不佳）
- 刪除 `stdin-panel.tsx`；新增 `args-panel.tsx` — **僅保留 argv 單行輸入**（章節 58 `main(int argc, char* argv[])` 沒有互動替代方案：參數在程式啟動當下就要決定），且只在 `codeUsesArgs(code)` 為真時渲染，其餘情況完全不佔版面
- 靜態偵測函式移至 `lib/code-detect.ts`（`codeUsesArgs` + `usesLocalTime`；後者供 Coddy 的 UTC 時區主動說明，原本一併住在被刪的檔案裡）
- `workspace-context` 移除 orphan `getStdin/setStdin`；批次降級路徑不再送 stdin（runner 不可用時讀輸入的程式會拿到 EOF——降級路徑本就無互動能力，可接受）
- tsc 0 錯 / eslint 0 錯 / build 通過

## [2026-08-06] — fix(runner)：R5c-1 B 機實機部署 — 再修 3 個只有真實硬體才暴露的缺陷

> 本機 Colima（arm64）與 B 機（amd64 Ubuntu 24.04）的差異，以及「腳本靜默失敗」，各貢獻了一個真缺陷。

### Fixed
1. 🔴 **`/lib64` 未掛入 jail（架構相依）** — amd64 動態載入器在 `/lib64/ld-linux-x86-64.so.2`，未掛載時 `execve` 回報 `No such file or directory`（看起來像編譯器不見了，實際缺的是 loader）。**arm64 的 loader 在 `/lib` 底下，故 Apple Silicon 本機 100% 測不出來**。改為候選清單 `_RO_CANDIDATES` + 存在才掛（同時涵蓋 `/lib32`、`ld.so.conf*`）
2. **`iptables-persistent` 與 `ufw` 互斥** — apt 為安裝前者**直接移除 ufw**（`Remove: ufw:amd64`），而原腳本用 `>/dev/null 2>&1 || true` 把訊息吃掉，於是「防火牆設定成功」是假象。改為：偵測到即 purge，DOCKER-USER 規則改用 **systemd oneshot unit**（`runner-firewall.service`，After=docker）持久化，完全不依賴持久化套件
3. **驗證函式在 `pipefail` 下誤判** — `cmd | grep -q` 命中即結束，上游收 SIGPIPE 回 141 被當失敗（SSH 檢查假性 FAIL）。`check()` 改在子 shell 內 `set +o pipefail`
- `bootstrap.sh` 結尾由「只印狀態」改為 **8 項逐條驗證 + 失敗 `exit 1`**（原版即使沒做到也會顯示成功）

### Verified — B 機實機（43.133.7.93）
bootstrap 8/8 [OK]；容器 healthy；hello / stdin / argv / 編譯錯誤（真實 g++ 訊息）/ 逾時→Time Limit Exceeded / SIGSEGV / **快取命中**（第二次 `cache_hit:true`）/ 無 token→401 / **WS PTY 互動**（`'name: '` 先於輸入到達、kernel 回顯、`hi Alice`）；**從外部 Mac 直連 8080 回 000（防火牆生效）**

### 待使用者（R5c-2）
Zeabur：backend 綁公開子網域 + 三個環境變數；web 設 `NEXT_PUBLIC_TERMINAL_WS_URL` 並 **redeploy**（建置期烘入）。A 機出口 IP 目前暫填 `43.153.167.105`，待首次實連後依 ufw 日誌校正。

## [2026-08-05] — feat(runner)：R5a/b 部署產物 + 本機 Docker 實測（修 3 個容器內才會爆的缺陷）

### Added — 部署產物
- `runner/docker-compose.yml`：`cap_add: SYS_ADMIN` + apparmor/seccomp unconfined（nsjail 建 namespace 必需）；**容器層天花板** mem 1400m / pids 512 / cpus 1.8（個別程式限制歸 nsjail，這層防「全部 session 加總拖垮 2C2G 主機」）；`/tmp` tmpfs（學生寫檔不落地、重啟自清）；healthcheck
- `runner/bootstrap.sh`：swap 2G + `vm.swappiness=10` / docker / ufw 僅放行 22 與 A 機→8080 / **補 `DOCKER-USER` iptables 規則**（docker 會繞過 ufw，常見疏漏）/ 禁 SSH 密碼登入 / 清重複公鑰。冪等
- `runner/deploy.sh`：build → up → 等 healthy → 冒煙測試；`.env.example`（token 產生方式）；`.gitignore`
- `docs/deployment.md` **§E 完整 SOP**：含「**來源 IP 探測法**」（用 ufw DENY 日誌讀出 A 機真實出口 IP，不需開放全網）、Zeabur 三個環境變數 + `NEXT_PUBLIC_*` 需 redeploy 提醒、驗收表、**一行回滾**（`RUNNER_BACKEND=judge0`）、疑難排解

### Fixed — 本機 Docker 實測抓出的 3 個缺陷（本機 sandbox=none 測不到）
1. **PCH 目錄未綁入 jail** → `fatal error: /opt/pch/std.h: No such file or directory`；jail 是全新 mount namespace，只有顯式綁定的路徑存在（順帶補 `/etc/ld.so.cache` 與 `TMPDIR=/box`，GCC 需暫存目錄）
2. **nsjail 以 execve 啟動子行程、不做 PATH 查找** → 傳 `g++` 靜默失敗，且 `--really_quiet` 把錯誤吃掉只剩 "compile failed"；改為 `shutil.which` 解析絕對路徑，並讓失敗訊息帶上 sandbox rc 以便診斷
3. 🔴 **nsjail 以 `128+signal` 回報，無窮迴圈被誤判成 `Runtime Error (NZEC)`** → 學生會收到錯誤的 Coddy 主動說明（該講逾時卻講執行期錯誤）；`classify_exit` 改為同時處理負數（直接子行程）與 128+N（nsjail）兩種慣例，SIGKILL/SIGXCPU 歸 Time Limit

### Verified — 真實 nsjail 容器內
hello / stdin / argv / 編譯錯誤（真實 g++ 訊息）/ 逾時→Time Limit Exceeded / SIGSEGV / `/usr` 寫入被擋 / **WS PTY 互動：`cout` 無 endl 的提示字先於輸入到達、kernel 回顯正常**（`'name: ' → 'Alice\r\n' → 'hi Alice\r\n'`）；runner 27 tests（+5 分類）、backend 818 全綠

## [2026-08-05] — feat(runner)：R4 前端互動終端 — xterm 嵌入 Output 面板

### Added — `web/`
- **`lib/terminal-theme.ts`**：xterm 主題；bg/fg/cursor 直接對應既有 token（`--bg-inset` / `--text-primary` / `--text-link`），ANSI 16 色採 GitHub 官方 dark 色盤（frontend.md R8 白名單核准例外，僅限終端畫布）
- **`lib/terminal-protocol.ts`**：frame 型別（與 `runner/app/terminal.py` docstring 同一份契約）+ `terminalWsUrl()`（讀 `NEXT_PUBLIC_TERMINAL_WS_URL`，未設退同源）+ `frameToExecutionResult()`（exit/compile_error → 既有 ExecutionResult 語意）
- **`use-terminal-session.ts`**：ticket → WS → frame 分派；**任何錯誤（RUNNER_BUSY / SESSION_LIMIT / ticket 503 / 連線失敗）一律退回批次執行**，學生不會卡住
- **`terminal-view.tsx`**：xterm 動態 import（避 SSR）+ ResizeObserver fit + **不做 local echo**（PTY 端 kernel 行規範已處理回顯）；回呼以 ref 持有，避免 prop 變動重建終端機清空畫面
- **`terminal-pane.tsx`**：狀態列（排隊中／編譯中／互動中）+ 畫布；排隊時顯示「前面還有 N 位」

### Changed
- `use-run-code.ts`：改為**優先互動終端**，退回批次；xterm 動態載入期間的首批輸出先 buffer、attach 時 flush（避免掉字）
- `output-panel.tsx`：session 進行中以終端畫布取代歷史列表，結束後自動收回 RunBlock（`STATUS_META` 圖示／「詢問 Coddy」／執行歷史選單全部沿用）
- `stdin-panel.tsx`：降級為「**進階：預先餵入**」，預設收合、移除 `codeNeedsInput` 與「程式在等待輸入」提示（互動模式下程式真的會停下來等，提示無意義）→ **tech-debt 記錄的 A12 兩缺陷（提示不即時 / Run 不攔截）就此消滅**
- `.env.example` 加 `NEXT_PUBLIC_TERMINAL_WS_URL`；新增 `@xterm/xterm` + `@xterm/addon-fit`
- 驗證：`tsc --noEmit` 0 錯、eslint 0 錯（1 既有 warning 在無關檔案）、`npm run build` 通過
- ⚠ `output-panel.tsx` 163 行（R4 +25，>150 提醒線未達硬線）已記 tech-debt

## [2026-08-05] — feat(runner)：R3 互動層 — PTY 終端 WS + ticket 認證 + backend 中繼

### Added — runner（`app/pty_exec.py` + `app/terminal.py`）
- **`WS /terminal`**：PTY 執行（stdout 行緩衝→無 endl 提示字即時出現；kernel 行規範原生處理回顯與 \r→\n，前端免 local echo）；frame 協議 `start/stdin` ⇄ `queue/compiling/compile_error/started/output/exit/error`（協議文件在 terminal.py docstring，R4 依此渲染）
- 資源紀律：gate slot **僅編譯階段持有**（等待輸入不佔）；看門狗 idle 60s（無輸入且無輸出）/ 硬上限 300s（狀態字串含 "Time Limit" 保持前端分類）/ 同時 session 上限 40（`SESSION_LIMIT` frame）；客端斷線立即 kill 行程；exit frame 帶 `output_summary`（64KB 上限）供 EDF/analytics
- `executor.py` 抽出 `classify_exit` / `stage_workdir` 供批次與互動共用；healthz 加 `terminal_sessions`
- 修 2 個設計期 race：master fd 關閉搶在 EOF 回呼前（拆顯式 `close()`）、行程剛結束時寫 stdin（吞 OSError）

### Added — backend（`api/routes/terminal.py`）
- **ticket 認證**：WS 直連公開子網域帶不到 HttpOnly cookie → `POST /terminal/ticket`（走既有 proxy cookie 認證 + **沿用 execute rate limit**）發 Redis 單次使用 ticket（60s TTL，GETDEL 防重放）；WS 首訊息帶 ticket，15s 未送 4408
- 中繼：`websockets.connect` 帶 X-Runner-Token 連 B 機，frame 原樣轉發（client→runner 僅放行 stdin）；exit/compile_error 側錄 → `log_execution` 行為事件（best-effort，與批次同管線）；runner 連不上 → `RUNNER_UNAVAILABLE` frame（R4 前端退批次）
- `pyproject.toml` 顯式宣告 `websockets`（原僅隨 uvicorn 間接安裝，防 7-1a-1 型 lock 脫鉤）+ lock 重產
- **測試**：runner +7（真實 PTY 互動往返/提示字先於輸入出現/idle 看門狗/session 上限/token）→ 22 全綠；backend +7（ticket 三態/中繼轉發+側錄/ticket 單次性/runner 連線失敗）→ **818 全綠**
- ⚠ `runner/app/terminal.py` 165 行（>150 提醒線；session 編排單一職責 + 12 行協議文件，暫不拆）

## [2026-08-05] — feat(runner)：R2 backend 抽換 — 執行引擎 dispatcher + fallback

### Added — `backend/services/runner.py`
- `submit_and_poll` 同名同介面 dispatcher：`RUNNER_BACKEND=judge0` 強制降級 / **`RUNNER_URL` 未設自動退 Judge0**（R5 部署前生產不會斷，切換零風險）/ 其餘走自建 runner（`POST /run` + `X-Runner-Token`）
- 錯誤映射對齊 backend.md：httpx timeout → 504 EXECUTION_TIMEOUT、網路例外 → 503 RUNNER_UNAVAILABLE、排隊滿 → 503 RUNNER_BUSY、401 等配置錯誤 → 502（不對學生洩漏細節）
- config 加 `RUNNER_BACKEND/RUNNER_URL/RUNNER_TOKEN`（.env.example 同步）；7 tests（分派 2 + 成功映射 + 錯誤 4）

### Changed
- `api/routes/code.py` 與 `scripts/verify_code_snippets.py` 改 import `services.runner`（`ExecutionResult`/`CPP_LANGUAGE_ID` re-export，模型正本留 judge0.py；`analytics/events.py` 僅用型別不動）
- 後端 **811 tests 全綠**（804 + 7；既有 code_execute/judge0 測試零改動通過）

## [2026-08-05] — feat(runner)：R1 runner service — 沙箱編譯執行 + PCH + 快取 + 並行閘

### Added — `runner/`（獨立 service，B 機部署；本機以 sandbox=none 模式開發測試）
- **`POST /run`**：批次編譯執行，回應七欄位逐字對齊 `ExecutionResult`、狀態字串沿用 Judge0 慣例（"Accepted" / "Compilation Error" / "Time Limit Exceeded" / "Runtime Error (SIGXXX/NZEC)"）→ R2 映射與前端 `classifyStatus` / `run_help` 零改動；`GET /healthz`（queue/cache 觀測，不驗 token）
- **模組**（9 檔，皆 <150 行）：`config`（env 參數，server-plan 定案值）/ `models` / `sandbox`（nsjail 旗標包裝，`none` 模式供本機測試）/ `gate`（並行閘 2 + 排隊位置回報 API 供 R3 WS 推送 + 排隊逾時 503 RUNNER_BUSY）/ `cache`（sha256 LRU 256 條，逐出刪檔）/ `compiler`（PCH `-include` 自動偵測 + 快取入庫）/ `executor`（argv shlex + 訊號翻譯 + hardlink 進 workdir）/ `proc`（**串流封頂讀取**——不用 `communicate()` 防 `while(1) cout` 在截斷前 OOM runner；stdin feed + 孫行程佔 pipe 寬限 2s）/ `main`
- **Dockerfile**：multi-stage——nsjail 自 source 建（不在 apt 庫）+ **PCH 預編 15 個常用標準庫標頭**（旗標與 config 一致否則 g++ 拒用）；`RUNNER_SANDBOX=nsjail` 烘入映像
- **15 tests 全綠**（真實編譯執行，macOS clang）：hello / stdin / args / 編譯錯誤 / 逾時 / SIGSEGV / NZEC / 快取命中 / 輸出截斷 / 程式碼過大 422 / token 三態 / 閘逾時 / 排隊位置；跑法 `cd runner && ../backend/.venv/bin/python -m pytest tests`
- **待 R5 實測**：Dockerfile 建置（本機 docker 未啟動）、nsjail 旗標路徑（`sandbox.py` 集中，B 機微調）

## [2026-08-05] — docs(runner)：7-R 自建互動執行引擎定案（R0），推翻 Batch Terminal 決策

> 起因：使用者驗收 A12（stdin 預填）體驗極差——「貼上按 Run 直接跳結果、必須一次填完 input 不符邏輯」。追根究柢是 Judge0 批次判題天生做不到互動；加上 RapidAPI 50 次/天不敷課堂、自架 Judge0 需 GRUB 切 cgroup v1，整條 Judge0 路線一併重新評估後推翻。

### Changed — 決策（roadmap「已確認決策」節，保留原文加註）
- **推翻「Terminal：Batch 模式」**（原始決策）與「Judge0 上線後自架」（2026-07-12）兩條
- 新路線：**自建互動 runner**——nsjail 沙箱（不自造輪子）+ **PTY**（stdout 行緩衝，`cout` 提示字即時出現；一併修掉 V1 pipe 緩衝缺陷）+ WebSocket；一律互動終端，`POST /run` 批次僅供題庫驗證/教材健檢/實作題判定
- 拓撲：Browser `wss` → A 機 backend（需綁公開子網域；Next.js Route Handler 不支援 WS proxy）中繼 → B 機 runner；防火牆僅放行 A 機 + `X-Runner-Token` 縱深；B 機不持有 credential；`ExecutionResult` 欄位不變（EDF / analytics / run_help 零改動）
- UI：終端機**嵌入 Output 面板**（拒絕 V1 的 modal——寫程式時看不到程式碼）；`@xterm/xterm`；**ANSI 16 色例外核准**（GitHub 官方 dark 色盤，僅限終端畫布，frontend.md R8 白名單）
- 費用：B 機另租 +$3/月（總 $12），PokerNote 原機不動（避免 DB 搬遷風險與失去 Zeabur 託管）；不再需要 Judge0 付費訂閱（比原路線省 $7+/月）

### Added
- **B 機已租用並實測全綠**：`43.133.7.93`（2C2G/40G Tokyo；cgroup v2 齊全不需動 GRUB；`ubuntu@` 金鑰登入 + 免密碼 sudo；純裸 VM 無 k3s）；實測 OS 為 24.04（面板顯示 22.04，以實測為準）
- 資源參數定案：並行編譯閘 2 / swap 2G / 編譯 CPU 10s·RAM 512M / 執行 RAM 256M·pids 64·輸出 8M / session idle 60s·硬上限 300s·同時 40；PCH 加速（本機實測編譯 0.25s→0.09s）
- roadmap 新增 **7-R 節（R0✅~R6）**；server-plan.md 全文改寫為 Runner 專用機；architecture.md 新增執行引擎節；backend.md 加 `RUNNER_BACKEND/RUNNER_URL/RUNNER_TOKEN`；tech-debt 記「stdin 預填 UI 兩缺陷不修（R4 取代，含回退條款）」

### Removed
- tech-debt 過期條目「YT video metadata 未補」（6-1 早已完成且生產已同步）；「Judge0 自架 docker-compose 未驗證」標作廢

## [2026-08-05] — chore(security)：清除設定檔明文 DB 密碼 + 權限收斂 + 正式環境硬擋 hook

> 起因：巡檢 Claude Code 權限設定時，發現 `.claude/settings.local.json` 有一條同時包含**正式環境 DB 明文密碼**與 `.venv/bin/python *` 萬用字元的 allow 規則——等於「連著正式資料庫的任意 Python 執行，永不詢問」。

### Removed — `.claude/settings.local.json`（未進版控，密碼未外洩）
- 刪除兩條含 `postgresql://postgres:<pw>@43.153.167.105:30148/...` 的 allow 規則
- 已用 `git grep` / 全樹 `grep` 確認該密碼**僅存在於此檔**，未進 git 歷史或遠端

### Added — `.claude/settings.json` 精確 allow 規則（取代寬鬆萬用字元）
- `.venv/bin/python -m pytest *`、`.venv/bin/pytest *`、`source .venv/bin/activate`
- `.venv/bin/alembic current* / heads* / history*`（**唯讀**；`upgrade` / `downgrade` 刻意不放行）
- `docker exec codedge-postgres-dev psql *`（鎖死本機 dev 容器，語法上碰不到正式環境）

### 評估後不採用 — 正式主機硬擋 hook
- 曾實作 PreToolUse hook 攔截含正式主機的 Bash 指令（實測可攔），**同日評估後移除**
- 原因：① 只擋得住寫死的那一台，換主機或改從 `.env` 讀連線字串就失效，安全感不實 ② 正式環境測試是常態需求，硬擋反而礙事
- **實際防線**：含密碼的 allow 規則已刪除，故連正式 DB 的指令會回到逐次確認，由人眼判斷

### Changed — `CLAUDE.md` 執行守則新增第 7 條
- **改檔案一律用 Edit/Write 工具**，禁止 `python3 - <<EOF` / `sed -i` / `cat >` 改動專案檔案
- 巡檢近 19 份 transcript 發現此手法用了 **41 次**且全被 `Bash(python*)` 靜默放行：diff 不可見、繞過權限確認

## [2026-08-05] — feat(scripts)：教材程式碼健檢工具 + 每日 20 次配額 + session 開場提醒

> 承 v41 `extern` 事件：**沒有任何機制會驗證教材裡的程式碼真的能編譯**，錯了兩個月沒人發現。

### Added — `scripts/verify_code_snippets.py`（兩層，成本天差地遠）
1. **靜態掃描（免費、每次都跑）**：拿 `corrections.json` 的 `global_replacements` 當「已知錯誤拼法字典」掃 questions / staging / learning_units。**不另外維護第二份清單**——修正配置本身就是規格
2. **Judge0 編譯（有配額）**：把 coding 題的 `starter_code`（**125 支**）送去真的編譯。**每天上限 20 次**（免費額度 50/天），未驗過或內容變動的優先、其次最久沒驗的 → 約 7 天跑完一輪，之後自動輪替
- 狀態寫 `data/teaching_content/snippet_check_state.json`（哪天跑過 / 每支的 hash + 結果 + 時間）；**只有真的編譯過才算「今天跑過」**，靜態掃描不會消掉提醒
- 教材本身沒有 code fence（U2g 移除範例程式後概念說明是純文字），所以可編譯的實體只有 starter_code

### Added — session 開場提醒
- `scripts/snippet_check_reminder.py`（純標準函式庫，不經 venv）+ `.claude/settings.json` 的 **SessionStart hook**
- 今天跑過 → 靜默；沒跑過 → 顯示上次日期、已驗支數、上次殘留問題數與指令

### 今日狀態
- 依使用者指示**今天先不實測**，只完成程式；靜態掃描已跑過一次：**0 個已知錯誤拼法**（v41 修完後全庫乾淨）


## [2026-08-05] — fix(content)：章節 41 `extern` 錯字修正（含兩支批次 script 語法損壞）

### 查證 — 「v17/v41 題庫掛零」是過期記錄
- tech-debt 那筆寫於 2026-07-06 上午的批次；**同日晚間 6-3c 知識點驅動批次已補**。實查：**v17 有 8 題（7 MC + 1 coding），健康**；v41 只有 2 題
- **但 v41 的 2 題全都寫成 `external`**（其中 coding 題直接要求「利用 external 宣告」）→ 學生照做**必定編譯失敗**，等於 0 題可用。全庫掃描確認錯誤只在 v41
- 覆蓋率最低的其餘章節：v03 安裝教學 1 題（無可考點，屬預期）、v61 5 題、v45 6 題

### Fixed — 修正鏈（沿用 6-1e 既有機制，未新寫工具）
1. `corrections.json` 加 `"external": "extern"` → `apply_corrections --only 41`（替換 3 處）
2. 刪除 v41 舊 chunks + document → `ingest_transcripts_rag --only 41` 重建 8 chunks（**全庫 `external` 殘留 0**）
3. 刪除 2 題錯題 → `generate_unit_content --only 41 --force` → `generate_unit_questions --only 41 --force`
4. **v41 現有 5 題 validated**（4 MC + 1 coding），全部使用正確的 `extern`；3 題 MC 仍 `VALIDATION_RETRY_EXHAUSTED`（可接受，非阻斷）
5. `promote_unit_content --only 41` → 本機 learning_units 已帶正確內容

### Fixed — 兩支批次 script 自 7-1a-5 起就無法執行（本次才發現）
- `generate_unit_content.py` / `generate_unit_questions.py` 的 `from scripts._db_guard import require_local_db` 被插進 **`from ... import (` 括號中間** → `SyntaxError`，import 即失敗
- 加防護那次（2026-08-05 7-1a-5）之後**沒有任何人跑過這兩支**，所以直到今天要重生 v41 才炸出來
- 修正後對 `scripts/*.py` 全數做 `ast.parse` 檢查，其餘 14 支語法正常

### Added — `scripts/fix_production_video.py`
- `seed_production_content.py` 是 `on conflict do nothing` 的初次播種，**無法更新既有資料** → 新增單章重播工具（RAG chunks / staging / learning_units / questions 四者整章替換），支援 `--dry-run`

### 生產庫已同步（2026-08-05 使用者核准後執行）
- v41：RAG chunks 8 換新 / questions 2 → **5** / staging + learning_units 內容更新
- **全庫複查：questions / staging / learning_units / RAG 四張表的 `external` 殘留皆為 0**；總量 questions 631、RAG 861（僅 v41 被替換，其餘未動）


## [2026-08-05] — feat(edf)：時區提醒 + 端點正名 run-help；發現章節 41 教材把 `extern` 寫成 `external`

### Added — UTC 時區 Coddy 主動提醒（機械判定，零成本）
- 伺服器時鐘是 UTC，比台灣慢 8 小時 → 學生在章節 45 印出「現在時間」會看到差 8 小時的結果，且**看不出是環境問題還是自己寫錯**
- `uses_local_time()` 偵測 `localtime` / `strftime` / `asctime` / `ctime`（**只認會轉成「人看的當地時間」的函式**；`time(NULL)` 印 epoch、`clock()` 算 CPU 時間都不受時區影響，不觸發）
- 執行**成功**時才提醒（編譯失敗/逾時另有路徑），每個 session 一次；文案說明這是雲端環境常態並反問「加多少秒會變成台灣時間」，不直接給答案

### Changed — 端點正名 `/chat/compile-error` → `/chat/run-help`
- 現在處理三種執行問題（平台限制 / 逾時 / 時區），原名已不準確；`services/compile_error.py` → `services/run_help.py`、回應欄位 `is_platform_limit` → `is_mechanical`
- 抽出 `_persist()` 消除三條路徑的重複寫入邏輯

### Tests
- `tests/test_run_help.py`（原 test_compile_error）+6：`uses_local_time` 5 例（含 `time(NULL)` / `clock()` 不觸發的反例）+ 時區提醒不呼叫 LLM；後端全量 **804 passed**

### 🔴 發現內容錯誤（待修，見 tech-debt）
- **章節 41 教材與逐字稿把 C++ 關鍵字 `extern` 寫成 `external`**（Whisper 逐字稿 [00:35] 即為 `external`，grounded 生成忠實複製）→ 學生照打**編譯必失敗**
- 影響範圍：RAG 2 chunks / staging 1 / questions 2；**生產庫同樣有**（staging 1 / learning_units 1 / RAG 2）
- **極可能就是 v41 題庫掛零的原因**：生成端依錯誤教材出題，審查端（懂 C++ 的強模型）一律打回


## [2026-08-05] — fix(chat)：收合聊天不再遺失對話 + 平板補 chat + 執行語言鎖死（A1/A2/A3）

> 上一則問題總結中查證出的三個缺陷，全部修掉。

### Fixed A1 — 收合 Coddy 再展開，對話整個消失（🔴 與「輸出被清空」同源）
- **根因**：`app-shell.tsx` 的 `{chatOpen && <ChatPanel/>}` 是條件掛載 → 收合即 unmount，而訊息列表、session id、執行結果訂閱**全都住在 ChatPanel 裡**。資料其實在 DB，但畫面空白，學生得自己從歷史選單撈回來
- **修法**（與 Output 執行歷史同一套）：新增 `components/chat/chat-runtime.tsx`，把 `useChat` / `useSessions` 與三個 workspace 訂閱提到 `ChatRuntimeProvider`（掛在 `WorkspaceProvider` 內、`ShellLayout` 外＝永遠掛載）；`ChatPanel` 降為純呈現層（145 → 95 行）
- **一併修好的副作用**：① 聊天收合時執行程式，結果卡片不再被丟掉（原本 `onExecutionComplete` 沒有 queue，直接消失）② 編譯錯誤去重簽章不再隨面板開合重置（不會重複花每日配額）

### Fixed A2 — 平板尺寸的聊天按鈕是死的
- `TabletHeader` 有按鈕呼叫 `onToggleChat`，但 tablet 版面從未渲染 `ChatPanel`。依 frontend.md 規格補上 **bottom sheet**（`inset-x-0 bottom-0 h-[60%]` + `shadow-modal`）

### Fixed A3 — 執行語言可被前端指定
- `ExecuteRequest.language_id` 有預設值但可被覆寫，打 API 可跑 Python/Java。非安全漏洞（Judge0 沙箱隔離），但本平台只教 C++ → **移除該欄位，路由固定 `CPP_LANGUAGE_ID`**

### Tests
- `test_code_execute.py` +2：送 `language_id=71` 仍以 54 執行 / `args` 確實轉為 `command_line_arguments`；後端全量 **798 passed**，web build + tsc + eslint 綠


## [2026-08-05] — feat(workspace)：62 章程式碼類別 × Judge0 能力矩陣實測，補齊 argv 與逾時說明

> 承 stdin 事件：使用者要求盤點「62 章教材有哪幾類程式碼、是否還有同類問題」。

### 分析方法
- 掃 62 章標題 + **628 題題庫 + 62 份教材內容**的實際程式碼片段（非 transcript——Whisper 逐字稿不含程式碼字面）
- **好消息**：教材與題庫**完全沒有** `system("pause")` / `conio.h` / `windows.h` 等 Dev-C++ Windows 專用寫法（grounded 生成產出的是可攜程式碼）
- 15 支代表程式 + 3 支能力探測**實跑 Judge0**（共 18 次，配額 50/天）

### 實測結果（15 類全數驗證）
| 類別 | 結果 |
|---|---|
| 基本輸出（含中文 UTF-8）/ 數學函式 / 動態記憶體 / 類別+靜態成員 / extern 單檔 / 檔案 I/O / 深遞迴 10 萬層 | ✅ Accepted |
| `cin >>` / `getline` / `cin>>` 後接 `getline` | ✅ 修好 stdin 後全通 |
| 時間函式 `time`/`localtime`/`clock` | ✅ 可用（**時區為 UTC**，章節 45 若示範現在時間會與台灣差 8 小時） |
| 亂數 `srand(time(NULL))` | ✅ 可用（每次不同，屬預期） |
| 無窮迴圈（章節 33） | ⚠ Time Limit Exceeded，**原本無任何說明** → 本次補 |
| **main 參數 argc/argv（章節 58）** | ❌ **argc 恆為 1**，學生無法傳參數 → 本次補 |
| C++ 標準 | `__cplusplus=201402`（**預設 C++14**）、GCC 9.2.0。教材未用 C++17 語法（僅 `nullptr`×3 屬 C++11），**現階段不需調整**；實測 `compiler_options: -std=c++17` 可用，日後需要再開 |

### Added — 執行參數（章節 58）
- Judge0 的 `command_line_arguments` 實測可用 → `judge0.py` / `ExecuteRequest.args`（≤500 字）/ context `getArgs·setArgs` / `use-run-code` 一路接通
- 前端：**偵測到 `main(..., argv)` 才顯示**「執行參數」欄位（`codeUsesArgs()`），不干擾其他章節

### Added — 逾時也由 Coddy 主動說明（同樣零成本）
- `compile_error.py` 加 `is_timeout()` + `_TIMEOUT_TEMPLATE`：固定文案指出兩大主因（迴圈沒有結束條件 / 用 `cin` 但沒給輸入），**並肯定「正在練習無窮迴圈這章的話，這個結果是正確的」**
- 前端觸發條件擴到 `Time Limit Exceeded`，以狀態字串當去重簽章；session 標題改「執行問題引導」

### Tests
- `test_compile_error.py` +1（逾時走固定文案、斷言 LLM 未被呼叫）；後端全量 **796 passed**


## [2026-08-05] — feat(workspace)：補上標準輸入介面（`cin` 無處可輸入）+ 修 kickoff fail-open

> 使用者寫了含 `std::cin >> userInput` 的程式，**畫面上沒有任何地方可以輸入**。

### Fixed — stdin 從未被送出（後端一直支援，前端沒接）
- `api/routes/code.py:20` 的 `ExecuteRequest.stdin` 早就存在且會傳給 Judge0，但 `use-run-code.ts` 只送 `{ code }`，**UI 也沒有輸入欄位** → 學生的 `cin` 永遠讀到 EOF，畫面看起來像程式壞掉
- `use-run-code` 補送 `stdin: workspace.getStdin()`；`workspace-context` 加 `getStdin/setStdin`（ref，不觸發 re-render）

### Added — `components/workspace/stdin-panel.tsx`
- Output 面板頂端的「輸入」摺疊列：多行 textarea（上限 10,000 字，與後端一致）、顯示目前行數
- **偵測到程式會讀輸入時自動展開並標示「程式在等待輸入」**（`codeNeedsInput()` 比對 `cin >>` / `getline` / `scanf` / `cin.get`，純字串比對零成本）
- 明說批次執行的限制：「程式是一次跑完的，不能邊跑邊打字——請先在這裡填好所有 `cin` 要讀的內容，再按 Run」（roadmap 既有決策：Judge0 批次模式，不做即時互動 terminal）

### Fixed — `services/chat_kickoff.py` 同型 fail-open 缺口
- 上一批在 `compile_error.py` 修掉的問題（`_get_client()` 在 try 之外，client 建構失敗會 500）在 kickoff 也存在，一併修掉

### Tests
- `tests/test_code_execute.py` +2：stdin 確實轉發給 Judge0 / 未提供時為空字串（鎖住這條被漏掉過的契約）；後端全量 **795 passed**，web build + tsc + eslint 綠

## [2026-08-05] — feat(edf)：編譯失敗時 Coddy 主動說明（平台限制直說 / 學生錯誤引導）

> 使用者提問「預設函式庫有哪些、想引用別的怎麼辦」+ 定案「編譯錯誤本來就該由 Coddy 主動分析；系統錯誤直說，學生自己出錯要引導」。
> **背景事實**：`judge0.py:13` 寫死 `CPP_LANGUAGE_ID=54`，只送單一 `main.cpp` → 可用的僅 C++ 標準函式庫；沙箱無顯示裝置也無網路，Qt 這類 GUI 函式庫**裝了也跑不動**。

### Added — `services/compile_error.py` + `POST /chat/compile-error`
- **兩類錯誤刻意不同處理**：
  - **平台限制**（`fatal error: X: No such file or directory` 且 X 不在標準標頭白名單）→ **機械判定 + 固定文案，完全不呼叫 LLM**（零成本；也避免 LLM 亂編「你可以裝一下」這種做不到的建議）。文案說明「不是你寫錯」＋環境只有標準函式庫＋無畫面沙箱＋改用 `cin` 的具體出路
  - **學生自己的錯誤**（漏分號、型別不符…）→ LLM 引導：白話翻譯錯誤訊息 + 指出從哪裡查起，**prompt 明令不可給修好的程式碼、不可說「第 N 行改成 XXX」**
- **標準標頭白名單**涵蓋 STL / C 標頭 / 常見 POSIX；`iostream` 找不到會被判為環境異常而非平台限制（不對學生說謊）
- 訊息寫入現有 session（非另開），保留在對話歷史可回看；LLM 失敗 fail-open 回固定文案

### Added — 前端自動觸發（`chat-panel.tsx`）
- Run 完成且 `compile_output` 非空才觸發（runtime error 不觸發——那屬於學生該自己除錯的範圍）
- **去重**：以「前兩行 + 抹掉行號」為簽章，同一個錯誤只主動說明一次 → 學生沒改就重跑不會重複消耗每日 60 次配額
- 失敗（含配額用盡）靜默，不打擾學生

### Fixed（實作中由測試逼出）
- `_get_client()` 原本在 try 之外，OpenAI client 建構失敗會 500 → 移入 try，真正 fail-open。**`services/chat_kickoff.py:85` 有同樣結構的潛在問題，未動（不在本次範圍，已記錄）**
- `models/chat.py` 抽出 `DEFAULT_SESSION_TITLE`：原本判斷 `if not session.title` 永遠為假（新 session 預設就是「新對話」），標題不會被覆寫

### Changed — `api/routes/chat.py` 289 → 206 行（超過 250 硬線）
- session 歷史三個端點 + 其 schema 拆至 `api/routes/chat_sessions.py`（100 行），比照 assignments 的雙 router 慣例；`MessageOut` 仍由 chat.py 提供，單向 import 無循環

### Tests
- `tests/test_compile_error.py` +10：標頭偵測 6 例（Qt / tinyfiledialogs / iostream / stdio.h / 語法錯 / 空字串）+ 平台限制路徑**斷言 LLM 未被呼叫** + 學生錯誤走 LLM + 訊息進歷史且標題正確 + LLM 掛掉 fail-open；後端全量 **793 passed**

## [2026-08-05] — fix(ui)：複製按鈕統一回饋（驗收回饋：複製後沒有任何提示）

- **現況兩處複製、兩種行為**：`run-block.tsx` 複製輸出**完全無回饋**（連 await 都沒有，失敗也不知道）；`class-card.tsx` 複製邀請碼只把圖示換成綠勾、無文字
- 新增 `components/ui/copy-button.tsx`（唯一複製入口）：綠勾 + **「已複製」** 短暫顯示 1.5 秒（`aria-live="polite"`），失敗顯示紅色**「複製失敗」**（非 HTTPS / 拒絕授權時會發生，原本靜默吞掉）；沿用 Toolbar「已儲存」的 inline flash 慣例，**不另建 toast 基礎設施**
- 兩處呼叫端改用之，移除各自的 `copied` state 與圖示切換邏輯；`getText` 採 callback，大量輸出不在每次 render 組字串

## [2026-08-05] — feat(workspace)：Output 加執行歷史選單（驗收回饋：歷史需要明確入口）

- 前一批把執行歷史保存下來了，但入口只有「往下捲看舊 block」，使用者反映**看不到歷史記錄按鈕**
- 新增 `components/workspace/run-history-menu.tsx`（80 行）：Output header 的「歷史」鈕 → 下拉列出每次執行（Run #N ／狀態 icon ＋文字／時間），**沿用 Chat 對話歷史的下拉寫法**（靠右對齊 + 點外面關閉 + `max-w` 保底），避免同一功能兩種操作邏輯
- 選一筆 → 展開該次結果並 `scrollIntoView`（每個 block 掛 `run-block-{id}`）
- `formatTime` 由 run-block 匯出共用，不另寫一份時間格式

---

## [2026-08-05] — fix(ui)：對話歷史選單溢出視窗 + 全站滾動條改 GitHub Dark 風格

> 使用者截圖回報兩點：對話歷史下拉選單被切掉一半、系統各處滾動條是白色不透明的。

### Fixed — 下拉選單溢出（`components/chat/session-list.tsx`）
- History 鈕位於 Chat panel 右上角，選單卻寫 `absolute left-0` + `w-64` → 256px 往右畫必然超出面板與視窗（連帶讓整頁出現橫向滾動條）
- 改 `right-0` 靠右對齊（**與 `global-nav.tsx` avatar 選單同一寫法**，該處本來就是對的）+ `max-w-[calc(100vw-2rem)]` 保底窄視窗
- 順修 R4 違規：`shadow-lg` → `shadow-modal`（全站唯一一處非 token 陰影，已無殘留）

### Fixed — 滾動條（`app/globals.css`，使用者選定方案）
- **根因**：`globals.css` 從未宣告 `color-scheme`，也沒有任何滾動條樣式 → 瀏覽器一律給淺色預設，在純 Dark Mode 介面上就是一條白槓
- `html { color-scheme: dark }` — 讓所有原生元件（滾動條、select、日期選擇器）跟著深色，不只滾動條受益
- 自訂滾動條（使用者選 10px + 透明軌道）：拇指 `--border-default`、hover 轉 `--border-emphasis`、`border: 2px solid transparent` + `background-clip: content-box` 內縮 → **視覺 6px 細、實際 10px 好抓**；軌道與 corner 全透明；Firefox 以 `scrollbar-width: thin` + `scrollbar-color` 對應
- 全部走既有 token，未引入新色（R1 通過）

### Verified
- web build + tsc + eslint 綠

---

## [2026-08-05] — fix(workspace)：Output 執行歷史不再被側邊欄清空 + page.tsx 拆分（250 行硬線）

> 使用者回報：「開啟側邊欄，先前終端機的輸出會被清空，且沒有歷史記錄可查看。」

### Fixed — 根因是元件樹換根，不是 Output 自己清空
- `page.tsx` 原本**依側欄開合回傳兩種不同的根節點**（無側欄＝Fragment / 有側欄＝PanelGroup）→ 切換時整棵子樹 unmount，`OutputPanel` 的 local state `blocks` 一併歸零。收合 Output 也是同一類結構切換
- **修法一：版面單一化**（新檔 `components/workspace/workspace-layout.tsx`）——永遠渲染同一棵水平 PanelGroup，只讓側欄 slot 在有/無之間切換（沿用 `app-shell.tsx` 既有的條件式 Panel 寫法），主欄位置固定不再重建
- **修法二：歷史移出元件樹**（新檔 `use-run-history.ts`）——module-level store + `useSyncExternalStore`，經 `WorkspaceContext` 提供 `runs` / `clearRuns`。任何 unmount 都不影響，連跨頁導航（Learn ⇄ Workspace）回來也還在

### Added — 執行歷史可查看
- 保留**最近 20 次**執行（新到舊），寫入 **sessionStorage**：同分頁重整仍看得到，關掉分頁即清除（共用電腦不留下他人的程式輸出）；「清空」鈕維持
- 展開規則改為無 effect 的推導：預設只展開最新一則，`overrides` 只記使用者手動翻過的例外 → 新結果自動展開、舊的自動收合（原行為不變，但不再需要 setState-in-effect）
- 型別抽到 `components/workspace/types.ts`（`ExecutionResult` / `RunRecord`），避免 context ⇄ history hook 循環相依；`workspace-context` 仍 re-export `ExecutionResult`，既有 import 不受影響

### Changed — page.tsx 254 → 189 行（經使用者同意拆分）
- 版面組裝 → `workspace-layout.tsx`；反思 handoff 的兩個 effect（active reflection 訂閱 + Coddy kickoff）→ `use-reflection-handoff.ts`
- tech-debt 的「超過 250 硬上限」項目消除

### Verified
- web build + tsc + eslint 綠（`react-hooks/set-state-in-effect` 兩處已用 store / 推導式改寫，非停用規則）

---

## [2026-08-05] — fix(workspace)：檔名鎖定 .cpp 尾綴 + 點檔名改名 + 首次草稿併發修復（U2e 驗收回饋）

> 使用者生產環境驗收回報三點：①「點資料夾剛開始跳錯誤、之後正常」②「存成 main.md 也能執行，副檔名形同虛設」③「最上方檔名點不動、無法改名」。

### Fixed — 副檔名鎖定（②，使用者裁決：鎖尾綴而非靜默改寫）
- **確認副檔名完全無作用**：`services/judge0.py:13` 寫死 `CPP_LANGUAGE_ID = 54`，前端執行時只送 code 不送檔名 → `main.md` / `main` / `main.txt` 都以 C++ 編譯。後端原本只驗長度 1–100
- **後端 `normalize_file_name()`**（`services/workspace_files.py`）：`.cpp` 結尾（不分大小寫）保持原樣，否則**補上**（不改寫既有副檔名——使用者明確表示 `main.md → main.cpp` 的靜默轉換很怪）；補完超長回 422。`save_file` / `rename_file` 皆走此規則，API 直呼也繞不過
- **前端 `.cpp` 為鎖定尾綴**（新元件 `file-name-input.tsx`）：輸入框只編輯主檔名，尾綴以固定灰字呈現於框內、無法刪改；另存對話框 / 側欄儲存 / 改名列三處共用。另存對話框補一行「程式一律以 C++ 編譯執行」
- 存檔後**以伺服器回傳的檔名為準**（原本沿用送出的字串，補副檔名後會與 DB 不一致）；實作題 handoff 自動命名同步改為「{單元} 程式實作題.cpp」，維持反思按鈕的檔名比對成立

### Added — 點檔名就地重新命名（③；使用者選「真正重新命名」）
- 後端 `PATCH /code/files`（`rename_file`）：以 `(user, name)` 定位 → **同一列改名不複製**（回傳 id 不變），新名已存在回 409 `CODE_FILE_NAME_TAKEN`、不存在 404；**草稿的 `opened_name` 一併跟著改**，重整後仍停在同一檔
- 前端 `file-name-field.tsx`：Toolbar 檔名改為可點按鈕 → 就地編輯（Enter 確認 / Esc 取消 / 失焦取消 / 錯誤以浮層顯示）。**未命名草稿**點檔名則開啟另存對話框（還沒有檔案可改名）

### Fixed — 首次草稿併發建立回 500（①的可證缺陷）
- `save_draft` 原本「查無草稿 → INSERT」，但**進頁時 handoff 開檔與自動存檔可能同時發出**，`uq_code_files_draft` partial unique index 會擋下較慢者 → IntegrityError 冒泡成 500。**只在第一次（草稿列還不存在時）可能發生，之後全走 UPDATE**，症狀與回報的「剛開始有錯、後來都正常」吻合
- 修法比照 6-R7 `get_or_create_user`：捕捉 IntegrityError → rollback → 重查對方建立的那列繼續更新
- ⚠ **未能確認這就是使用者當下看到的錯誤**（列表載入與草稿存檔是不同端點，且錯誤已無法重現）→ 併同下一項讓下次可辨識

### Changed — 側欄錯誤可診斷
- 列表載入失敗原本一律顯示「載入檔案列表失敗」吞掉真因 → 改為附上後端訊息與 HTTP status（如 `後端回應逾時（504）`）+ **重試按鈕**（不必收合再展開）

### Tests
- `tests/test_code_files.py` +10：副檔名正規化 5 例（`main`/`main.cpp`/`main.CPP`/`main.md`/前後空白）+ 補完超長 422 + 改名成功（含草稿 opened_name 跟隨、id 不變）+ 改名撞名 409 + 他人檔案 404 + 首次草稿並發三發皆 200；後端全量 **783 passed**，web build + tsc + eslint 綠

---

## [2026-08-05] — docs：生產庫播種狀態複驗（7-1a-4 收尾，無待補項）

> 承接「concepts 影片 ID 待補」的掛帳。開公網後以 `--dry-run --force` 查驗，結果**該項在上個 session 修完 script 後就已執行完畢**，只是狀態文件未同步 → 本次為純狀態修正，**未對生產庫做任何寫入**（dry-run 已 rollback）。

### Verified（生產庫實查，逐項對照本機）
| 項目 | 生產 | 本機 |
|---|---|---|
| concepts / 有 `video_youtube_id` | 62 / **62** | 62 / 62（v01–v05 抽查 id + duration 逐筆相同） |
| documents / questions | 64 / 628 | 64 / 628 |
| unit_content_staging（approved） | 62 | 62 |
| data_codedge_rag | 861 | 861 |
| alembic 版本 | `t6c7d8e9f0a1` | head（**K4e citations migration 已上生產**） |

- **`learning_units` 62 筆 content 全部非空**（`concept_explanation` 1,061–2,161 字，0 筆空骨架）——lazy-seed 已在首次進 Learn 頁時觸發並帶入 staging 內容，原 roadmap「為 0 屬預期」的註記已過期
- 生產 `users` 1 / `learning_paths` 1 = 目前僅開發者本人登入過，實驗資料乾淨

### Changed
- `CLAUDE.md` 7-1a-4 移除「待補：concepts 影片 ID」；`docs/roadmap.md` 7-1a-4 補複驗結果並修正 `learning_units` 為 0 的過期敘述

---

## [2026-08-05] — perf(llm)：模型全面升級 gpt-5.6 + 每日配額 + 離題分流（成本控制三層）

> 上線前防濫用盤點：rate limit（10 次/分）與 prompt injection 防護已有，但**主題範圍限制完全沒有**（RULE-1~5 只管程式碼洩漏/語言/字數/收尾）、`off_topic` 只是欄位（`dialogue.py:53` 明寫「暫不主動判定」）、**沒有每日總量上限**（理論上一人一天可打 14,400 次）。
> **業界基準**：CS50.ai（架構幾乎相同——GPT-4o + 講座字幕 RAG + 教學護欄）實測 **$1.90/學生/月、$0.05/prompt**。

### Changed — 模型全面升級（實測後定案，取代 6-M 選型表）
| 用途 | 舊 | 新 | 單價變化 |
|---|---|---|---|
| 對話 + 分析 | `gpt-5.4-mini` | **`gpt-5.6-luna`** | $0.75/$4.50 → **$0.20/$1.20** |
| 生成（Quiz/Hint） | `gpt-5-mini` | **`gpt-5.6-luna`** | $0.25/$2.00 → **$0.20/$1.20** |
| 審查 / 內容批次 | `gpt-5.4` | **`gpt-5.6-terra`** | $2.50/$15 → **$2.00/$12** |

- **每項都更便宜且更新世代，無取捨**。實測單次互動成本 **$0.00316 → $0.00081（省 74%）**；100 人×80 則/月：**$25.3 → $6.5**
- **修 `core/llm_params.py`**：gpt-5.6 世代拒收自訂 `temperature`**也拒收 `reasoning_effort`**（原判斷只認 `gpt-5-` 前綴 → luna 直接 502）。拆出 `_accepts_custom_temperature()`；預設 `reasoning_tokens=0` 無須壓制
- `config.py` 的 `LLM_MODEL` 預設由 `gpt-4o` 改為 `gpt-5.6-luna`（生產漏設時的 fallback 不該是 2024 世代）

### Added — 每日配額（`core/rate_limit.py`）
- `RATE_LIMIT_LLM_PER_DAY=60`：**只掛 `scope="llm"`**，`/code/execute` 等不受影響。UTC 日期分 key、26 小時 TTL 涵蓋任何時區；超額回 429 `DAILY_QUOTA_EXCEEDED` 並明示「明天重新計算，仍可寫程式/執行/讀教材」；設 0 停用。+3 tests
- **決策：不做上課日/非上課日分級配額**——正常使用僅 $6.5/月，分級省的是最壞情況的一部分（該由 OpenAI 帳號硬上限擋），卻要付出教師端課表 UI + 時區處理的複雜度，且**會傷害週末複習/考前衝刺的學習體驗**

### Added — 離題分流（`services/edf/off_topic.py`，新模組）
> **分流不是攔截**：關鍵字黑名單會誤傷「這題老師上課有講嗎」這類合法提問（使用者指出），改採 routing 思路（呼應 6-M 已引用的 FrugalGPT / RouteLLM）

- **判斷搭在既有 Evidence 呼叫上，零額外成本**：`EvidenceResult` 加 `is_on_topic`（預設 True——LLM 未回傳時寧可多花錢也不誤判）；**Evidence 原本看不到學生提問**（prompt 只有程式碼+執行結果），故 `analyze_evidence` 補 `question` 參數並以 `wrap_student_input` 包裝防注入
- prompt 明列不得判為離題的情境：程式問題、對教材/影片/課程的詢問（**明寫「老師上課有講嗎」**）、對錯誤訊息的困惑、極簡短但語境上在求助（「?」）
- 離題 → `generate_off_topic_reply()`：跳過 RAG 檢索與 persona/strategy/K-Graph 組裝，**Feedback input 1,699 → 135 tokens（省 92%）**；LLM 失敗回固定文案不拋錯
- 離題判定回填 `dialogue_act=off_topic`（5-2c 啟發式無此訊號）→ 評估期可統計學生離題比例
- `feedback.py` 加完後達 263 行**超過 250 硬上限 → 拆出 off_topic.py**（227 + 53）

### Tests
- +10（3 每日配額 + 7 離題分流，含「LLM 未回傳欄位預設 on-topic」與鎖住 prompt 規則不被誤刪）；後端全量 **773 passed**

### Verified（真實 LLM）
- 「晚餐推薦吃什麼」→ 輕量路徑，友善婉拒並給出可問的具體例子，**0 citations**（未檢索）
- **「這題老師上課有講嗎」→ 正確判為課程相關**，走完整路徑並附教材連結 + 3 則 citations

---

## [2026-08-05] — feat(edf)：Coddy 防幻覺三層機制（NotebookLM 式可驗證引用）

> 承上一條：把正確 metadata 餵給 LLM 只解決「它沒資料可用」，**不保證它聽話**。本次補上不依賴 LLM 自律的機制。原 `validate_output()` 只檢查程式碼洩漏，對「內容是否真的來自教材」零檢查。

### Added — `services/edf/citations.py`（新模組，163 行）
> `feedback.py` 已 236 行逼近 250 上限，格式化邏輯一併移出，主檔反而降至 221 行

- **① 機械式攔截 `strip_ungrounded_citations()`**：由檢索結果建立「合法出處表」（video_id → [(start, end)]），掃描回應中的 Markdown 連結，解析 YouTube video id 與 `t=` 參數，**不在檢索結果內的整段連結直接移除**（連標籤一起——標籤本身就含編造的時間）。容差 ±90 秒（LLM 常把 63 秒寫成 01:00）；非 YouTube 連結（如 cppreference）保留；攔截時寫 `logger.warning`，**可據此統計幻覺率供論文使用**
- **② 誠實路徑 `NO_SOURCE_RULE`**：RAG 全部低於門檻時原本靜默不注入教材，Coddy 會用自身知識回答且不告知學生。現改為明確指示——不可提及任何章節或時間點、被問「老師在哪講過」要誠實說沒有對應段落、可用一般知識但不得宣稱是課程教材
- **③ 可驗證 UI**：`extract_citations()` 輸出章節/時間/連結/原文摘錄/相似度 → migration `t6c7d8e9f0a1` 為 `chat_messages` 加 `citations` JSON 欄位（**持久化才能在重開對話時仍可核對**；不塞進 `evidence`，語意不同）→ 前端 `components/chat/citation-list.tsx` 摺疊清單，展開即見 transcript 原文（原文本身帶 `[00:45]` 逐句時間標記），另附「在 YouTube 開啟此段」

### Tests
- `tests/test_edf_citations.py` **+13**：合法引用保留 / 未知影片攔截 / 時間偏離過遠攔截 / 容差內放行 / 非 YouTube 連結保留 / 無檢索結果時全部攔截 / 清理殘留空列表項 / youtu.be 短網址 / metadata 缺漏處理；後端全量 **763 passed**，migration up-down 可逆驗證，web build + tsc + eslint 綠

### Verified（真實 LLM）
- 引用 `[C++的for迴圈 03:01](...&t=181s)`（181s=03:01 換算正確）；citations 回傳 3 則，含相似度 0.649–0.663 與 transcript 原文

### 已知限制（誠實記錄）
- **幻覺無法 100% 消除**：出處已鎖死，但 LLM 仍可能曲解教材內容（老師說 A 講成 B）。驗證這個需第二次 LLM 呼叫比對，成本與延遲翻倍 → **不常態開啟**，日後可做抽樣稽核工具（原方案④）

---

## [2026-08-05] — fix(edf)：Coddy 影片引用改為真實出處 + 可點擊時間連結（K4d 驗收回饋）

### Fixed
- **Coddy 的影片時間戳是幻覺**（使用者驗收發現）：`feedback.py` 組 prompt 時只注入 `chunk.text`，**完全沒帶 metadata** → LLM 手上沒有任何時間資訊，卻仍輸出「影片 01:22～01:40」這類看似精確的內容。而 RAG chunk 的 metadata 其實一應俱全（`title_zh` / `youtube_id` / `start_time_seconds` / `end_time_seconds`），只是從未被使用
- **修法**：新增 `_format_rag_chunk()`，每則片段標示「出處：{章節名稱} {mm:ss}｜連結：{帶 t= 參數的 YouTube URL}」；prompt 加 `_CITATION_RULE` 三條規則——只能用標示的出處、**嚴禁自行推測時間點**、必須輸出 Markdown 連結格式；metadata 不齊的片段不附出處，規則要求該片段不提時間
- **前端**（`components/ui/markdown.tsx`）：補 `a` 元件（`text-text-link` + 底線 + `target="_blank"` + `rel="noopener noreferrer"`）——Coddy 回覆本就走 react-markdown 渲染，補上樣式後連結即可點擊

### Verified
- 本機真實 LLM 實測：輸出 `[C++的break與continue 04:05](...&t=245s)`、`[C++的while迴圈 07:04](...&t=424s)`，章節名稱與秒數換算皆正確（245s=04:05、424s=07:04）且來自真實 metadata
- 後端 750 passed；web tsc / eslint 綠

---

## [2026-08-05] — perf(deploy)：生產環境「頁面載入十秒」根因排除 — DNS threadpool + HTTP/3

> 使用者回報 Learn / Knowledge / 首次登入皆需 10 秒以上（一次錄製達 3 分鐘）。逐層量測後確認是**兩個獨立的生產環境問題疊加**，本機開發（localhost）兩者皆不會出現。

### 量測基線（先排除的部分）
- 後端 13 個端點 ×5 次（真實 PostgreSQL，62 概念 / 628 題 / 861 chunks）：**2–10ms，最慢 40ms，無慢查詢**
- lazy-seed 首次產生 62 units：**0.02 秒**；backend 冷啟動 import 0.92 秒
- 生產 health check ×20：130–337ms 穩定無尖峰；SSR `/login` 330ms
- 前端交付：HTTP/2 + `cache-control: immutable` + gzip，9 個 chunk，各頁只打 1 個 API（Knowledge 用 `Promise.all`），**無瀑布**
- Performance trace（499MB / 699,950 事件）：**≥100ms 的任務只有 1 個**，總耗時 8.5 秒 → **主執行緒幾乎完全閒置，前端零阻塞**

### Fixed 1 — Node DNS 走 IPv6 逾時耗盡 libuv threadpool（環境變數，見 deployment.md）
- **證據**：Network 顯示 `/api/auth/session` 首次 **2.2 分鐘**，期間 `health` ×5 全部 5.00 秒逾時（前端 AbortController 上限）；session 一完成，health 立刻回到 86–472ms → **兩者共用同一瓶頸資源**
- **機制**：Next.js 為單一 Node process，DNS 查詢走 libuv threadpool（預設僅 4 執行緒）。容器內 Node 18+ IPv6 優先而 Zeabur 容器 IPv6 無法路由外網 → 解析逾時佔滿 threadpool → proxy 要解析 `*.zeabur.internal` 時排隊
- **修法**：web service 加 `NODE_OPTIONS=--dns-result-order=ipv4first` + `UV_THREADPOOL_SIZE=32`（**不在版控，已記入 deployment.md Step 2**）
- **結果**：`workspace?_rsc` 304ms、`draft` 491ms — API 全數恢復

### Fixed 2 — Zeabur 邊緣宣告 HTTP/3，瀏覽器改走 UDP（`web/next.config.ts`）
- **證據**：修好 DNS 後靜態資源仍極慢——137KB 花 **18.50 秒**（約 7 KB/s），但同機同時 curl 測**序列 633 KB/s、15 個混合並行 0.71 秒全完成**。回應帶 `alt-svc: h3=":443"; ma=3600` → Chromium 系瀏覽器切 HTTP/3（QUIC over UDP），curl 走 TCP 不受影響
- **修法**：`next.config.ts` 加 `Alt-Svc: clear`（RFC 7838），讓瀏覽器清除記錄並留在 HTTP/2。**拒絕「要使用者自行關閉 QUIC」的方案**——校園 / 企業 / 部分 ISP 對 UDP 443 限速或丟包很常見，2027-01 評估時學生多在校園網路
- **結果**（使用者實測 43 筆請求全為 `h2`）：同一檔案 **18.50 秒 → 166ms（111 倍）**；靜態資源普遍 15–22ms、API 70–350ms

### 診斷工具
- `main.py` 加 `X-Process-Time` middleware（回應標頭帶 backend 內部處理毫秒，CORS `expose_headers` 一併開放）——可直接分辨慢在運算或傳輸鏈路

---

## [2026-08-05] — fix(deploy)：生產環境影片 ID 全 NULL — 播種 script 補 concepts metadata 同步

### Fixed
- **生產 Learn 概念說明只顯示 placeholder**（使用者實測回報）：根因**不是**教材沒灌成功，而是 `concepts.video_youtube_id` 在生產庫全為 NULL——migration `e1f2a3b4c5d6:134` 把它 seed 成 `None`，62 個真實影片 ID 是 6-1d 用 `patch_video_metadata.py` 寫進**本機** DB 的，屬「本機有、migration 沒有」的第三類缺口（前兩類＝concept UUID 隨機、`data_codedge_rag` 執行期建表）
- **放大效應**：`web/components/learn/concept-tab.tsx:32` 在 `video_youtube_id` 為 null 時**整個 tab early return placeholder**，連已經灌好的 grounded 教材都不渲染 → 症狀看起來像「播種失敗」，實際只差影片 ID
- **修法**：`seed_production_content.py` 新增 `sync_concept_metadata()`，以 tag 為鍵 UPDATE 生產庫的 `video_youtube_id` / `video_duration_seconds`

### Verified
- 重建 `prod_test` 完整重現症狀（migration 後 62 筆全 NULL）→ 執行修正後 script → **0 筆仍為 NULL**，抽查 v01/v02/v03 的 youtube_id 與 duration 與本機一致

---

## [2026-08-05] — feat(scripts)：測試/生產環境隔離防護 + 生產播種實機完成

### Added
- **`backend/scripts/_db_guard.py`**：所有 script 共用 `core.database` 讀 `settings.DATABASE_URL`，而對生產庫做維護時 `export DATABASE_URL=<生產>` 會**殘留在同一個終端機**——之後跑任何 script 都會誤寫生產庫（本次部署過程中就已具備此條件）。兩級防護：
  - `require_local_db()` — **無覆寫選項，非本機一律中止**。掛 `seed_fake_students`（假帳號污染實驗資料）/ `generate_unit_content` / `generate_unit_questions` / `ingest_transcripts_rag` / `rereview_questions`（本機生成、之後用播種搬運，沒有對生產跑的理由）
  - `confirm_remote_db()` — 允許但需互動輸入 `yes`（非互動環境用 `ALLOW_PRODUCTION_WRITE=1`）。掛 `promote_unit_content` / `patch_video_metadata`（生產庫的合法維護操作）
  - 訊息一律遮蔽密碼（`postgres:***@host`），並提示「這通常是變數殘留，請開新終端機或 unset」

### Verified
- 假 seeder 指向生產 → 中止；本機 → 正常；promote 指向遠端輸入 no → 取消；後端全量 **750 passed**
- **生產播種實機完成**：documents 64 / questions 628 / unit_content_staging 62 / data_codedge_rag 861

### 決策記錄
- DEV 工具安全性複查（使用者提問）：`/dev/reset`·`/dev/mastery`·`/dev/role`·`/dev/simulate-failures` **全部已限定 `user.id`**（`services/dev_tools.py` 每條 delete 都帶 user_id 條件），`/dev/questions` 唯讀、幽靈解鎖純前端 → **無需修改**；生產開啟 DEV 僅需 `DEV_MODE_ENABLED=true` + email 白名單

---

## [2026-08-04] — feat(deploy)：生產資料播種 script（7-1a-3）+ Judge0 RapidAPI 鏈路實測

### Added
- **`backend/scripts/seed_production_content.py`**：把本機教學內容搬到生產庫。**核心問題＝`concepts` 的 seed migration 用 `uuid4()` 隨機產生 id（`c3d4e5f6a7b8:163`），生產庫 UUID 與本機完全不同** → 直接 `pg_dump` 會讓 `unit_content_staging.concept_id` 全數對不上。Script 以 **concept tag 為橋樑重新映射**：讀本機 staging join concepts 取 tag → 查生產庫同 tag 的新 UUID → 改寫後寫入
  - 分工：`documents` / `questions` 直接複製（前者 uploader_id 全 NULL、後者用 `concept_tags` 字串關聯，皆不依賴 UUID）；`unit_content_staging` 走 tag 重映射；**`data_codedge_rag` 由 LlamaIndex 執行期建表、不在 migration 內**，需先 `pg_dump` 連 schema 一起搬（script 偵測到表不存在時印出完整指令）
  - 防呆：拒絕 `TARGET_DB_URL` 指向本機（方向反了）、目標表非空需 `--force`、兩邊 concepts 數量不符即中止、`--dry-run` 預覽
  - JSON 欄位處理：依 `information_schema` 找出 json/jsonb 欄位顯式包 `Json()`——否則 psycopg2 會把 `concept_tags` 的 Python list 誤 adapt 成 PostgreSQL `text[]` 而型別衝突

### Verified
- **本機建 `prod_test` 庫完整演練**：跑完整 alembic → 確認 concept UUID 與本機不同（`bb615138…` vs `0e660c1e…`）→ pg_dump 搬 RAG 表 → 執行 script → **62 教材 / 628 題（503 MC + 125 coding）/ 861 chunks / 64 documents 全數寫入，0 孤兒、tag 對應與本機完全一致**
- **Judge0 RapidAPI 端到端實測**（此鏈路首次真正跑通）：正常執行（stdin `3 4` → `stdout='sum=7\n'`、0.003s / 1140KB）/ 編譯錯誤（g++ 訊息完整回傳）/ 服務不可用（`AppError 503 JUDGE0_UNAVAILABLE`）三路徑皆符合 `backend.md` 規範

### 部署進度（Zeabur）
- 四個 service 建立完成（手動建立，避開未實測的 `zeabur.json` PREBUILT schema）+ 網域綁定 + Google OAuth 登入通過
- 踩點記錄：Zeabur 預設埠 8080 與 backend 寫死的 8000 / web 的 3000 不符；`zeabur.app` 是公共後綴無法登記為 Google 授權網域 → 改用 OAuth 測試模式（100 人上限，1 月評估前需評估改用自訂網域）

---

## [2026-08-04] — fix(deploy)：Phase 7 部署前置檢查——生產映像缺 python-multipart 阻斷修復

### Fixed
- **🚨 生產 backend 容器會啟動即崩**（`backend/requirements.lock`）：5-5 作業附件加了 `python-multipart` 到 `pyproject.toml`，但 lock 檔停留在 4-1a 版本未重產；`backend/Dockerfile` 只 `pip install -r requirements.lock` → 生產映像缺此套件，FastAPI 註冊 `File()` 路由（`assignments.py` / `assignment_submissions.py`）時直接 raise，容器永遠起不來。以 `uv pip compile` 重產（既有 pin 全部保留，僅新增 `python-multipart==0.0.32`）
- **生產會用錯 LLM 模型**（`zeabur.json`）：backend env 未傳任何模型變數，`config.py` 預設 `LLM_MODEL=gpt-4o`（2024 舊世代）且三個分組變數 fallback 至它 → 6-M 任務導向路由在生產完全失效。補上 `LLM_MODEL` / `LLM_MODEL_GENERATE` / `LLM_MODEL_VALIDATE` / `LLM_MODEL_CONTENT` / `EMBEDDING_MODEL` 五個變數，值對齊 6-M 選型表

### Changed（文檔同步）
- `docs/deployment.md`：前置條件的 Judge0 段落改寫（正式方案＝自架於伺服器 B，RapidAPI 降為過渡方案，指向 server-plan.md）；checklist 的 lock 檢查改為「與 pyproject 同步」的實質規則（原「≥ 100 個 `==`」數字本身不成立）
- `docs/server-plan.md`：Judge0 authn header 技術債註記改為已完成（2026-07-18 消除），待辦清單對應項打勾

### Verified
- `docker build ./backend` 成功 → 容器內 `import multipart`（0.0.32）+ `from main import app` 成功載入 **81 條路由**（即生產啟動路徑可用）
- `zeabur.json` JSON 格式驗證通過

---

## [2026-07-21] — fix(workspace)：我的程式碼刪除修正 + 反思 modal 提交按鈕遮蔽

### Fixed
- **刪除檔案誤報「操作失敗」**（根因 `lib/api.ts`）：後端 DELETE 回 204 No Content，`api()` 無條件 `res.json()` 對空 body 解析失敗拋錯 → 被 catch 誤判失敗；實際已刪除（重整後列表重抓才看到消失）。加 `res.status === 204 → return undefined`；**同時修好「未立即刪除」**——樂觀 `setFiles` filter 原本在 throw 後永遠沒執行到，現正常即時移除
- **刪到當前開啟檔案無提示**（`code-files-sidebar.tsx` + `use-named-file.ts`）：刪除時偵測 `f.name === currentName`，跳出專屬確認「此為目前開啟檔案，刪除後將移除並跳回預設程式」；確認後呼叫新抽出的 `resetToDefault`（從 `newFile` 抽離、不含未存確認）重設編輯器為預設範本並清檔名關聯
- **反思計畫過長時提交按鈕消失**（`reflection-flow.tsx` + `reflection-flow-parts.tsx`）：modal Popup 原為 `max-h-[85vh] overflow-hidden` 但內部 header/題目(22vh)/body(60vh)/footer 直向堆疊無 flex 約束，總高超過即把 footer 裁出可視區且無法捲動觸及；改 Popup 為 `flex flex-col`、body 改 `min-h-0 flex-1` 吸收剩餘高度並內捲、header/題目/footer 加 `shrink-0` 固定 → 提交按鈕永遠可見（側欄編輯版本身已有 `overflow-y-auto`，不受影響）

### Tests
- 前端 tsc / eslint / build 全綠（前端此區無 vitest 測試層）

---

## [2026-07-18] — fix(tech-debt)：低風險技術債清償——Judge0 自架 authn / lazy-seed 空骨架 / pyproject / uv.lock

### Fixed
- **Judge0 自架 authn header**（`services/judge0.py`）：`_build_headers` 加 authn 分支——URL 含 rapidapi 網域 → `X-RapidAPI-Key`（現狀不變）；自架 + key → `X-Auth-Token`；無 key 不帶 auth header。新增可選 `JUDGE0_AUTH_MODE` 環境變數（rapidapi / self-hosted）顯式覆蓋自動判斷，供邊角情境救援；消除「切自架開 authn 會 401」技術債（生產實測仍待 Phase 7）
- **lazy-seed 空骨架**（`services/learning/generator.py`）：`generate_learning_path` seed units 時讀 `unit_content_staging`（status=approved）直接帶入 content，無 approved 才寫空骨架——promote 後才註冊的新帳號（含 DEV ghost user）概念說明 tab 不再落 pending fallback；與 promote script 整包覆蓋行為對齊（單一真相來源，讀取端零改動）
- **pyproject.toml hatchling packages**：補 `[tool.hatch.build.targets.wheel] packages`（flat layout 顯式列 api/core/models/services/scripts），`pip install -e .` 不再失敗；hatchling 隔離環境驗證 wheel target 可解析（151 files）

### Changed
- **`.gitignore` 加 `uv.lock`**：依賴鎖定正本維持 `requirements.lock`（Dockerfile 亦用它）；uv.lock 為先前 uv 指令副產品，不進版控避免雙鎖定檔 drift
- **git user.name/email 技術債關閉**：確認已設定（曾冠豪 / abbyabby41@gmail.com）

### Tests
- +6（judge0 authn 4 分支 + generator staging 帶入/非 approved 排除 2）；後端全量 **750 passed**

### 決策記錄
- OpenAI client ×9 重複：維持刻意延後（抽共用需連動 9 檔 + 大量測試 monkeypatch，收益不成比例）
- 429 toast / OpenAI 降級快取 / 6-4b 題庫補生：本輪不做（使用者裁決）

---

## [2026-07-16] — feat(chat)：Coddy 反思開場——進 Workspace 主動閱讀題目與反思計畫

### Added
- **`POST /chat/reflection-kickoff`**（`services/chat_kickoff.py`）：讀題目 + 反思全文 + 追問狀態 → Coddy 開場訊息（3–5 句：肯定亮點 → 接手被跳過的追問或補充最模糊處 → 邀請提出想先弄懂的概念）；建獨立新 session（title=實作題題幹）；LLM 失敗 fail-open 固定友善文案；僅本人 404 保護
- **與 modal 追問分工**（使用者定案「modal 一層，剩下交 Coddy」）：prompt 依 followup 狀態分流——被跳過的追問由 Coddy 換句話自然帶入；已回答的不重複問
- **前端**：實作題 handoff 進 Workspace → **自動展開 chat 面板** + 觸發開場（workspace-context 加 `requestReflectionKickoff` 事件含掛載前 queue；`useChat.loadKickoff` 建 session 顯示訊息）；sessionStorage 去重（同一反思只開場一次，重整不重發）

### Tests
- +4（開場持久化可讀回 / LLM 失敗 fallback / 他人反思 404 / 追問狀態三分支）；後端全量 **744 passed**；web tsc/eslint/build 全綠

---

## [2026-07-16] — feat(reflection)：反思評分初學者寬容化（使用者回饋：評分太難、反思變負荷）

### Changed（四項，使用者全數核准）
1. **追問變引導非門檻**：追問階段第一輪即可「直接開始作答」跳過（原本必答一輪）；回答過一次追問後無論分數一律放行（原 MAX 2 輪）——self-explanation 效益來自提示本身，非答對
2. **評分 rubric 改寫**（`evaluate.py`）：加入校準原則——自己的話重述題意 ≥ 0.6、口語概念（「用 if 判斷」）視同正確、2 個以上具體步驟 ≥ 0.5、僅空白/敷衍/明顯誤解 < 0.4；高分範例從競程級換成初學者級；追問須先肯定亮點、一次只問一件事
3. **門檻 0.6 → 0.45 + Bloom 自適應**（`_threshold_for`）：Bloom 1–2 → 0.4、Bloom ≥ 4 → 0.55
4. **學生端不再顯示品質分數**（追問 QualityBar / 側欄 QualityChip / Learn 與 demo 的「品質分數 xx%」全移除，改正向文案）；quality_score 照常入 DB，論文資料收集不受影響

### Tests
- +1（Bloom 自適應門檻）+ 既有 evaluate 測試適配；後端全量 **740 passed**；web tsc/eslint/build 全綠

---

## [2026-07-16] — feat(workspace)：實作題 handoff——自動命名開檔 + 反思按鈕限定實作題檔案

### Added
- **Learn 實作題 →「在 Workspace 作答」完整 handoff**：原本只是裸連結（不帶反思/程式碼），現在帶反思 id + 檔名 + 起手碼（`setActiveReflectionId(id, {fileName, starterCode})`，sessionStorage 加 `active_reflection_file`/`active_reflection_starter`）
- **自動命名**：由實作題進入的程式碼自動命名為「{章節名稱} 程式實作題」（`unit.concept_name_zh`）；首次進入以起手碼建檔（立即出現在我的程式碼）、已存過＝載入續作、草稿仍掛該檔＝優先草稿（最新工作內容）
- quiz-demo 同步帶檔名「程式實作題」+ 起手碼

### Changed
- **反思計畫按鈕限定實作題檔案**：只在「目前開啟檔案 === 反思綁定檔案」時顯示（切到其他檔/開新檔即隱藏並收合反思側欄，`effectivePanel` 派生、不加 setState）；一般檔案無反思按鈕
- **Toolbar 圖示順序**：我的程式碼 → 開新檔案 → 反思計畫（反思移至開新檔案右側）

### Verified
- web tsc/eslint/build 全綠；⚠ UI 待使用者驗收（Learn 實作題 → 反思 → Workspace 動線）

---

## [2026-07-16] — feat(workspace)：檔名關聯跨重整持久化 + page.tsx 拆分

### Added
- **重整/再登入停留在最後開啟的檔案**：`code_files` 草稿列加 `opened_name` 欄（migration `s5b6c7d8e9f0`，可逆驗證）；PUT /code/draft 省略欄位＝保留、帶 null＝清除（sentinel `KEEP_OPENED_NAME`，自動存檔不觸碰關聯）；載入/另存/開新檔即時持久化關聯；進頁還原內容+檔名；+1 test（739）

### Changed
- **page.tsx 拆分**（使用者核准；255 → 214 行）：抽出 `use-run-code.ts`（Judge0 執行 + isDirty）與 `use-draft-restore.ts`（草稿+檔名還原）；反思 handoff gating 改 lazy 初始值（消 react-compiler set-state-in-effect）；hook 回傳全面解構取用（消 preserve-manual-memoization）

### Verified
- 後端 739 passed；migration up/down/up 可逆；web tsc/eslint/build 全綠；⚠ UI 待使用者驗收

---

## [2026-07-16] — feat(workspace)：U2e 快捷鍵修訂——Ctrl/Cmd+S 儲存 + 開新檔案（仿主流編輯器）

### Added
- **Ctrl/Cmd+S 儲存**（`use-named-file.ts`）：已命名（載入過/存過）→ 直接覆寫並於檔名旁短暫顯示「已儲存」；未命名 → 開另存對話框（`save-as-dialog.tsx`，**檔名預填且反白**、Enter 確認、Esc 取消）；攔截瀏覽器預設另存網頁
- **開新檔案**：Toolbar FilePlus 按鈕；內容尚未存至「我的程式碼」時先 confirm，再重設為預設範本並解除檔名關聯
- **檔名關聯**：Toolbar 檔名顯示目前開啟的命名檔案（未命名顯示 main.cpp）；程式化載入/開新檔不誤標為使用者修改（suppress 機制）

### Changed
- 側欄儲存表單改與 Ctrl/Cmd+S 走同一 `saveNamed` 流程；外部儲存成功以 refreshToken 觸發側欄列表重抓

### Verified
- web tsc/eslint/build 全綠；⚠ UI 操作待使用者驗收

---

## [2026-07-16] — fix(workspace)：U2e 回饋修訂——側欄化 + 近實時存檔 + 游標跳行 + Enter 縮排

### Fixed
- **打字游標跳到第一行**：兩個根因——(1) CodeEditor 以父層 onChange 為重建依賴，父層 callback identity 每 render 變動 → 編輯器整個重建、游標重設；改 onChange 走 ref、重建僅依賴 `initialValue`。(2) 草稿還原 effect 以整個 autosave hook 物件為依賴 → 每 render 重抓草稿並覆寫存檔基準；改解構穩定 callback 為依賴
- **Enter 換行不對齊上一行**：CodeMirror `indentUnit` 預設 2 空格與 4 空格程式碼錯位（換行後需再按 Tab）；加 `indentUnit.of("    ")` 統一 4 空格，並保留語法感知縮排（`{` 後自動加深）

### Changed
- **「我的程式碼」改左側欄**（`code-files-sidebar.tsx`，取代 Toolbar dropdown）：與反思計畫同側、可收合；**互斥切換**（開一個自動收另一個，`sidePanel` 單一狀態）；Toolbar 加 FolderOpen toggle
- **近實時存檔**：停頓 0.4 秒即存；連續輸入不間斷時至多每 2 秒強制存一次（原為停止輸入 2 秒才存）

### Verified
- web tsc/eslint/build 全綠；⚠ UI 操作待使用者驗收

---

## [2026-07-16] — feat(workspace)：U2e 程式碼存檔（DB 草稿自動存 + 我的程式碼多檔管理）

### Added
- **`code_files` 表**（migration `r4a5b6c7d8e9`，up/down 可逆驗證）：單表兩用——草稿（name IS NULL，partial unique 每人一份）+ 命名檔案（UNIQUE(user_id,name) 同名覆蓋；上限 50；code CHECK ≤ 100k 字元）
- **API**（`services/workspace_files.py` + `api/routes/code_files.py`）：`GET/PUT /code/draft`（還原/upsert）+ `GET/PUT /code/files`（列表 meta / 同名覆蓋儲存）+ `GET/DELETE /code/files/{id}`；一律限本人（他人 404）
- **自動存檔**（`lib/use-draft-autosave.ts`）：停止輸入 2 秒 PUT 草稿 + Toolbar「儲存中…/已自動儲存」指示；beforeunload 與 SPA 卸載時 keepalive 搶救未存變更；內容未變不重複打 API
- **進 Workspace 還原草稿**：載入完成前不掛編輯器（避免預設範本閃現）；404/失敗 fail-open 用預設範本
- **Toolbar「我的程式碼」選單**（`code-files-menu.tsx`）：另存命名檔案（同名覆蓋）+ 列表（名稱+時間）載入/刪除；載入後 Toolbar 檔名同步

### Changed
- **CodeEditor 加受控 `value` prop**：外部值與現值不同時整段替換（載入檔案/還原草稿）；`initialValue` 行為不變（quiz 相容）。順帶修復 output 收合切換 remount 後編輯器內容重設的潛在 bug

### Tests
- +8（草稿 404/upsert/隔離、檔案存-列-載-刪、同名覆蓋、他人 404、空白檔名 422、上限 409）；後端全量 **738 passed**；web tsc/eslint/build 全綠

### Verified
- migration up/down/up 實跑可逆；dev server 熱載新路由（401 需登入）；⚠ UI 操作待使用者驗收

---

## [2026-07-12] — docs：驗收狀態同步 + 修正 6-3c 過時註記

### Changed
- **UI 驗收通過標記**（使用者 2026-07-12 驗收）：5-5b-3/4（含徽章+可點卡片修訂）、5-1c-4 加入班級、5-6a/b/c、DEV 六卡
- **修正過時註記**：6-3c「實機複審+批次生成待跑」→ 實已於 2026-07-06 隨 6-3d 跑完（436 MC + 57 coding + 舊題複審刪 15）；CLAUDE.md「下一步」6-3c → **批次 ⑧ U2e**
- Phase 5 教師端標記完成（5-3/5-4 等真實資料除外）

---

## [2026-07-12] — docs：伺服器需求規劃定案（兩台拓撲，Judge0 自架取代 RapidAPI）

### Added
- **`docs/server-plan.md`**：伺服器 A（主機 4C8G，Zeabur 託管 PokerNote_V2 + 本專案 4 service）+ 伺服器 B（2C2G Ubuntu 22.04 專跑自架 Judge0，SSH docker-compose 直跑、不走 Zeabur dashboard）；容量假設（30–60 人課堂）、安全硬性要求（authn token + 防火牆鎖 A 機 IP）、租用後待辦
- 決策背景：Judge0 RapidAPI 成本高（免費 50 次/天、付費訂閱制）且官方 pay-per-use（Sulu）已收攤 → 自架；Judge0 需 privileged + cgroup v1 → 獨立一台與主資料物理隔離

### Changed
- `docs/tech-debt.md` 新增：`judge0.py _build_headers()` 尚不支援自架 authn header（`X-Auth-Token`），Phase 7 部署前補

---

## [2026-07-12] — fix(assignment)：5-5b UI 動線修訂（使用者回饋）

### Changed
- **學生繳交表單**：「我的繳交」標題旁新增狀態徽章（未繳交/已繳交/已評分）+ 繳交時間；「繳交/更新繳交」按鈕邏輯保留
- **教師交件動線**：移除作業卡「交件」展開鈕 → 作業卡標題區改為可點入口（hover 變 link 色），點擊進入全頁 `TeacherAssignmentDetail`（作業資訊 + 交件情況 + 批改），返回鈕回列表；編輯/停用/刪除/附件操作留在列表卡
- `formatDateTime` 抽入 `lib/assignment-format.ts`（消除 assignment-card / submission-row / submission-form 三處重複）

### Verified
- web tsc + eslint 綠；⚠ UI 操作待使用者驗收

---

## [2026-07-12] — feat(classroom)：5-1c-4 學生加入班級 UI（補規劃缺口）

### Added
- **缺口背景**：`POST /classes/join` 後端（5-1b-3）一直存在，但前端從未排入輸入邀請碼的 UI，導致 5-5b 無法驗收
- **共用表單**（`components/classroom/join-class-form.tsx`）：6 位數字碼即時過濾 + 驗證；404（無效/停用碼）與 409（未填 profile）錯誤訊息直出
- **作業頁空狀態**：`/assignments` 無作業時顯示加入班級表單，加入成功即重載作業列表
- **Settings「我的班級」卡**（`my-classes-card.tsx`，僅學生顯示）：列已加入班級（班名 + 教師名）+ 加入表單
- 後端 `GET /classes/mine`（`list_joined_classes`）：學生列自己已加入班級；學生視角 schema 不含邀請碼/成員數

### Tests
- +2（未加入回空 / 加入後列出且不洩漏 invite_code）；後端全量 **730 passed**；web tsc 綠

### Verified
- ⚠ UI 操作待使用者驗收（解鎖 5-5b-3/4 驗收動線）

---

## [2026-07-12] — feat(assignment)：5-5b-4 教師交件檢視 UI（評分+評語）

### Added
- **交件檢視面板**（`components/teacher/submissions-panel.tsx`）：作業卡新增「交件」展開 → 名冊 × 繳交狀態列表 + 繳交率統計（已繳交 X / Y）
- **學生交件列**（`submission-row.tsx`）：姓名/email + 狀態徽章（複用 `submissionBadge`）+ 繳交時間；展開檢視繳交文字 + 下載繳交附件
- **評分表單**（`grade-form.tsx`）：分數（可留空=未評）+ 評語 → `PATCH /submissions/{sid}/grade`，儲存後即時回寫列表徽章
- 後端 `GET /assignments/{id}/submissions` 回應加 `attachments`（繳交附件 meta）：`list_attachment_meta_bulk` 批次查詢（單 query 避免 N+1）

### Tests
- +1（教師列表含繳交附件 + 教師下載繳交附件授權）；後端全量 **728 passed**；web tsc 綠

### Verified
- ⚠ UI 操作待使用者驗收（可與 5-5b-3 學生端一併驗）

---

## [2026-07-08] — feat(assignment)：5-5b-3 學生作業 UI + Dashboard 待辦卡片

### Added
- **學生導航加「作業」tab** → `/assignments`（`STUDENT_TABS`）
- **學生作業頁**（`components/assignments/`）：列表（標題/截止/繳交狀態徽章/逾期）→ 詳情（教師說明 + 下載教師附件 + 分數/評語 banner + 繳交表單）
- **繳交表單**：文字 + 拖曳上傳（複用 `FileDropzone`）+ 刪除自己的繳交附件；重繳覆蓋（`更新繳交`）
- **Dashboard「待辦作業」卡片**（`PendingAssignmentsCard`）：列未繳作業連往 `/assignments`；無作業不渲染
- `lib/assignments.ts` 學生/教師交件 API wrappers + `lib/assignment-format.ts`（截止格式化 + 狀態徽章）

### Verified
- web tsc/eslint 綠 + `next build` 成功（/assignments 註冊）
- ⚠ UI 操作待使用者驗收

---

## [2026-07-08] — feat(assignment)：5-5b 作業繳交後端（學生繳交 + 教師評分）

### Added
- **繳交 service**（`services/assignment/submissions.py`）+ **route**（`api/routes/assignment_submissions.py`）：
  - 學生：`GET /assignments/mine`（所屬班級 active 作業 + 我的繳交狀態）+ `GET /assignments/mine/{id}`（詳情含教師附件 + 我的繳交 + 我的附件）+ `PUT /assignments/{id}/submission`（文字 upsert，重繳覆蓋）+ `POST /submissions/{sid}/attachments`（繳交附件上傳）
  - 教師：`GET /assignments/{id}/submissions`（班級名冊 × 交/未交狀態）+ `PATCH /submissions/{sid}/grade`（score + feedback + graded_at）
  - 授權：學生限自己所屬班級 active 作業與自己的繳交；教師限自己作業
  - submissions router 先於 assignments router 註冊（`/assignments/mine` 優先於 `/assignments/{id}`）
### Changed
- `delete_attachment` 通用化：作業附件限該作業教師、**繳交附件限繳交本人**（`DELETE /attachments/{id}` 改 `get_current_db_user`）；`build_attachment` 共用 builder（作業/繳交附件）

### Tests
- +8（學生看到班級作業 / 非成員 404 / 繳交 upsert 覆蓋 / 繳交附件上傳+下載+刪除 / 教師列名冊×狀態 / 教師評分 / 學生不可評分 403）；後端全量 **727 passed**

### Note
- 前端 5-5b-3（學生 UI + Dashboard 卡片）/ 5-5b-4（教師交件檢視 UI）待做

---

## [2026-07-08] — feat(teacher)：5-6b Learn 教師全開 + 5-6c 單元題庫檢視

### Added
- **5-6c 教師題庫檢視**：
  - 後端 `GET /quiz/bank?tag=`（`require_roles(TEACHER)`）回完整 content（含正解 answer_index）+ 解析，僅 validated；複用 `list_questions_by_tag`；+2 tests（教師看得到正解 / 學生 403）
  - 前端 `TeacherQuestionBank` 元件 + `unit-content` 教師專屬「題庫（教師）」tab：列該單元 concept 題目，**解答預設隱藏 + 顯示/隱藏一鍵切換**（避免示範露答案），正解以綠框標示 + 解析
### Changed
- **5-6b Learn 教師權限全開**：`learn/page.tsx` `ghostUnlock = useGhostUnlock() || role==="teacher"`——複用 DEV-4 幽靈解鎖鏈路，教師可點閱全部 locked 單元（後端 `get_default_path` 本就 lazy-seed 全 59 單元）

### Verified
- 後端全量 **720 passed**；web tsc/eslint 綠 + `next build` 成功
- ⚠ UI 操作待使用者驗收

---

## [2026-07-08] — feat(teacher)：5-6a 角色化導航

### Changed
- **師生導航分流**（`components/layout/global-nav.tsx` + `lib/use-role.ts`）：
  - 教師頂部導航＝`班級 | 作業 | Workspace | Learn`（移除 Quiz/Knowledge）；學生維持原 5 頁籤
  - `班級管理`/`作業`從右上角 avatar 選單**移入頂部導航**（avatar 只留設定/登出）
  - 新 `useRole` hook（fetch /users/me role + 訂閱 ROLE_CHANGE_EVENT 即時更新）；role 未定前不渲染頁籤避免閃現
  - `/teacher` 是 `/teacher/assignments` 前綴 → active tab 精確比對
- **教師預設落地班級管理**：login callbackUrl `/workspace`→`/`；`app/(app)/page.tsx` 改 client 端依角色分流（教師→/teacher，其餘→/workspace）
- **`/teacher` 路由拆分**：`layout.tsx`（角色 gate 一次）+ `page.tsx`（班級）+ `assignments/page.tsx`（作業）；移除原頁內分頁切換

### Verified
- web `tsc` 綠 + eslint 綠（僅既有 img 警告）+ `next build` 成功（/teacher、/teacher/assignments 皆註冊）
- ⚠ UI 操作待使用者驗收

### Note
- 5-5a-3 教師作業 UI **UI 驗收通過**（本次回饋為導航位置調整，功能不變）

---

## [2026-07-07] — feat(teacher)：5-5a-3 教師作業 UI（程式碼完成，待 UI 驗收）

### Added
- **教師作業管理 UI**（`web/components/teacher/assignment-*.tsx` + `/teacher` 加分頁）：
  - `/teacher` 頁改「教師中心」+ 分頁切換「班級管理 / 作業」（active tab 沿用 #F78166 底線）
  - 建立作業：選班級 + 標題/內容/**截止時間**（datetime-local）+ **拖曳上傳**附件（`FileDropzone`，前端型別/10MB 即時驗證）→ 建立後依序上傳
  - 作業卡：顯示標題/內容/截止時間/停用徽章；**編輯**（含清除截止時間）、停用/啟用、刪除、展開附件面板（懶載入下載/刪除/續傳）
  - 元件拆分保持 < 150 行：fields / edit-form / dropzone / attachments / card / manager
- **API 層**：`web/lib/assignments.ts`（wrappers + `validateFile` + 下載 URL）；`api()` 支援 FormData（不覆寫 Content-Type，讓瀏覽器帶 multipart boundary）
- **後端補強**（UI 依賴）：`GET /assignments/{id}` 改回 `AssignmentDetailOut` 含 `attachments`（`list_attachment_meta` 只取中繼欄位不載 bytes）；+1 test

### Verified
- 後端全量 **718 passed**；web `tsc --noEmit` + eslint 綠 + `next build` 成功
- ⚠ UI 視覺/操作待使用者驗收（截止時間編輯、拖曳上傳、下載）

---

## [2026-07-07] — feat(teacher)：5-5a-2 教師作業 CRUD + 附件 API

### Added
- **作業 CRUD API**（`api/routes/assignments.py` + `services/assignment/crud.py`）：require_roles(TEACHER) + 擁有權（他人 404）
  - `POST/GET/GET{id}/PATCH{id}/DELETE{id} /assignments`；list 支援 `?class_id=` 過濾
  - **PATCH 可編輯 due_at**（截止時間）：用 `model_fields_set` 區分「未提供（保留）」與「明確 null（清除）」——UNSET 哨兵
  - DELETE 顯式清理多型附件 + 繳交（無 FK cascade）
- **附件 API**（`services/assignment/attachments.py`）：檔案存 bytea
  - `POST /assignments/{id}/attachments`（multipart 上傳，教師）+ `GET /attachments/{id}`（下載）+ `DELETE /attachments/{id}`
  - **安全**：副檔名白名單（word/pdf/pptx/程式碼/文字/zip）+ 單檔 ≤ 10MB（讀 MAX+1 偵測超標）+ 檔名去路徑；下載一律 `Content-Disposition: attachment`（防 inline XSS）+ 授權（作業附件＝教師或班級成員；繳交附件＝本人或該作業教師）
  - 上傳掛 `rate_limit("upload", 20)`
- 新依賴 `python-multipart`（pyproject）；main.py 註冊 assignments + attachments 兩 router

### Tests
- +15（CRUD 授權 / due_at 編輯+清除+保留 / 上傳白名單+空檔+超標 / 下載授權：教師/成員/非成員 403 / 刪附件）；後端全量 **717 passed**；ruff 綠

---

## [2026-07-07] — feat(teacher)：5-5a-1 作業 3 表 migration + models

### Added
- **作業指派 schema**（migration `q3f4a5b6c7d8` + `models/assignment.py`）：TronClass 式文件繳交
  - `assignments`：教師建立、指派整班（title/description/due_at/is_active）
  - `assignment_submissions`：學生繳交（text/score/feedback/graded_at）；UNIQUE(assignment_id, student_id) 每生每作業一份重繳覆蓋；score CHECK >= 0
  - `attachments`：多型附件（owner_type assignment/submission）檔案內容存 **bytea**（Zeabur 容器 fs ephemeral）；單檔 CHECK ≤ 10MB（`MAX_ATTACHMENT_BYTES`）
  - db-schema.md §Module 8 同步 3 表
- **設計決策（2026-07-07 使用者定案）**：作業＝文件繳交非題庫 quiz；指派整班；檔案存 Postgres；教師可評分+評語；學生雙入口（作業 tab + Dashboard 卡片）；**原 5-5b 熱力圖/錯誤統計改隸 5-4**（與文件繳交無關）

### Verified
- migration up/down/up 可逆（Postgres 實跑）；models 匯入；後端全量 **702 passed**（schema 步驟，API/UI 測試隨 5-5a-2 起補）

---

## [2026-07-07] — feat(dev)：DEV-E 假學生資料 seeder

### Added
- **假學生 seeder**（`services/dev_seed/` package + CLI `scripts/seed_fake_students.py`）：供教師端 / 行為分析本機開發
  - 三行為原型（主動 / 被動 / 掙扎）塑形資料，讓 5-2d 聚合與 5-3 群聚分析有可跑樣本
  - 每位學生：profile + 班級成員 + coding_events（成功/錯誤/hint）+ chat_messages（含 dialogue_act）+ student_mastery（confidence 依原型 gauss 抖動）
  - 可辨識 email 後綴 `@seed.dev`；一律先 purge 舊 seed 學生（顯式刪子表跨 SQLite/PG 一致）→ 可重現、不撞號
  - demo 教師 `seed-teacher@seed.dev` + demo 班級 get-or-create（reuse，purge 不動）；`--class-id` 可併入既有班級
  - seeded Random（`seed` 參數）保證可重現
  - **拆分**：`generators.py`（純 builder，130 行）+ `seeder.py`（編排，158 行）避免單檔逾 250 行門檻
- CLI 實機驗證：對 Postgres dev DB 生成 6 位（原型 2/2/2 均衡）

### Tests
- +4（seed 建學生+資料 / 可重現冪等 / purge 保留教師班級 / 與 5-2d 聚合整合）；後端全量 **702 passed**

---

## [2026-07-07] — feat(analytics)：5-2d 行為指標聚合 service

### Added
- **行為指標聚合 service**（`services/analytics/aggregate.py` `aggregate_user_behavior` + `BehaviorMetrics` dataclass）：
  - 從 coding_events + chat_messages 計算單一使用者指標：execution_count / success_count / success_rate / hint_request_count / avg_fix_duration_seconds / hint_distribution / dialogue_act_distribution
  - **修復時間**：時序配對「首次未解錯誤 → 下一次成功」的間隔平均（無配對回 None）
  - **dialogue_act 分布**：DB group_by（chat_messages join session；比照 6-R8 func.count），NULL 不計入
  - 支援 `since`/`until` 時間窗過濾
- **設計決策**：compute-on-read，**不建 `behavior_aggregates` 預聚合表 / 不排程**——初期 < 100 人查詢壓力低；預聚合屬效能優化，留待 5-3/5-4 有真實資料 + 查詢壓力再評估
- **範圍取捨**：concept_error_counts / active_seconds 暫不計（現有事件資料無乾淨來源，避免臆測）；API 端點屬 5-3d（延後至真實資料）

### Tests
- +7（空使用者 / 成功率 / 修復時間配對 / 無前置錯誤 / hint 分布 / dialogue_act 分布 / 時間窗過濾）；後端全量 **698 passed**

---

## [2026-07-07] — feat(analytics)：5-2c chat_messages dialogue_act 欄位（StudyChat schema）

### Added
- **`chat_messages.dialogue_act` 欄位**（migration `p2e3f4a5b6c7` + `models/chat.py` `DialogueAct` enum）：學生訊息對話行為分類
  - String(24) + CHECK（非 PG ENUM，比照 coding_events.event_type）；nullable，既有列不回填
  - 合法值＝StudyChat 6 類：asking_hint / clarification_request / debugging / off_topic / acknowledgment / verification（CC-BY-4.0）
- **啟發式分類器**（`services/analytics/dialogue.py` `classify_dialogue_act`）：純函式、零 LLM 呼叫（比照 5-2b `classify_execution`）
  - 優先序：明確 hint 請求（hint_level>0）> 簡短致謝 > 求證 > 除錯（附執行錯誤）> 文字求助 > 澄清提問；訊號不足回 None
  - `off_topic` 無可靠啟發式訊號暫不主動判定（保留合法值供未來 StudyChat 語料訓練分類器 / 人工標註）
- **掛鉤**：`chat interact` 於 fail-safe commit 前分類並隨 user message 一併持久化（僅用 LLM 呼叫前既有訊號）
- db-schema.md §Module 9 dialogue_act 註記同步（補齊 clarification_request / verification）

### Tests
- +11（分類器 10 單元含優先序 / interact 寫入驗證）；後端全量 **691 passed**

### Verified
- migration up/down/up 可逆（Postgres 實跑）

---

## [2026-07-07] — feat(analytics)：5-2b event logging service

### Added
- **event logging service**（`services/analytics/events.py`）：
  - `classify_execution`：Judge0 status → success / compile_error / runtime_error
  - `log_coding_event`：best-effort 寫 coding_events（失敗吞例外 + `logger.warning` + rollback，不擋主流程；code_snapshot 截斷 10k）
  - `log_execution`：從一次執行摘要結果（status/exit_code/time/memory/has_stderr）並寫入
- **掛鉤**：`/code/execute` 每次執行記錄結果事件；`chat interact` 當 `hint_level>0` 記 hint_request（帶 evidence concept_tags）

### Tests
- +6（classify 三態 / log_execution 寫入 / route 記 success / route 記 compile_error）；後端全量 **680 passed**

---

## [2026-07-07] — feat(analytics)：5-2a coding_events 表（ProgSnap2）

### Added
- **coding_events 表**（migration `o1d2e3f4a5b6` + `models/coding_event.py`）：程式行為事件收集（Module 9）
  - `event_type` 採 ProgSnap2 EventType 詞彙（submit/compile_error/runtime_error/success/hint_request/fix；String+CHECK）
  - id=EventID、user_id=SubjectID（ProgSnap2 五欄主鍵對映，CC-BY-4.0）
  - `concept_tags`/`execution_result`/`event_metadata` 用通用 JSON（相容 SQLite 測試）；`metadata` 保留字改名 `event_metadata`
  - `session_id` FK chat_sessions ON DELETE SET NULL；`(user_id, created_at)` 複合索引供時序查詢
- db-schema.md §Module 9 同步（JSON 取代 text[]/jsonb 註記）

### Verified
- migration up/down 可逆；欄位/索引/FK 正確；model 匯入；後端全量 **674 passed**

---

## [2026-07-07] — feat(auth)：5-1d-3/4 身分選擇 onboarding + 設定重置卡（前端，UI 驗收通過）

### Added
- **Onboarding 三段 gate**（`onboarding-gate.tsx`，原 profile-gate 改名）：① 未選身分 → `RolePicker`（教師/學生兩卡）② 學生未填 profile → `ProfileSetupForm` ③ 放行；選完身分後 gate 重新評估
- **Settings 身分重置卡**（`identity-card.tsx`，全使用者可見）：顯示目前身分 + 切換鈕；二段確認 + 明確警告「全部資料將永久清空」；成功後 `window.location` 導回 `/` 重走 onboarding
- **data layer** `lib/identity.ts`：`selectRole`
- DEV 身分切換卡（devSetRole，不清資料的測試用切換）與此並存互補

### Verified（自動）
- tsc / eslint 0 problem（沿用 dashboard 的 async setState disable）/ build 通過；元件皆 < 150 行
- **待使用者 UI 驗收**（既有帳號 role_selected=false → 下次登入先見身分選擇頁）

---

## [2026-07-07] — feat(auth)：5-1d-1/2 身分自選 + 切換全清（後端）

### Added
- **`users.role_selected`**（migration `n0c1d2e3f4a5`，server_default false）：區分「onboarding 已主動選身分」vs 首登預設；`/users/me`·`/auth/me` 回傳；既有帳號下次登入將被引導選身分
- **`POST /users/role`**（`services/identity.py`）：自選 student/teacher（admin 不可自選 → 422）；**首次選擇只設定不清資料；已選過再改＝重置**——全清 mastery/progress/quiz/chat（reuse `reset_user_data`）+ profile + 班級成員關係 + 教師擁有的 classes（顯式先刪成員）；回傳 `did_reset`

### Decision（2026-07-07）
- Production 身分：**onboarding 自選教師/學生**（提權風險已知悉、使用者接受，單一教授小課程情境）；**單一身分**；設定頁可切換身分＝**全資料重置 + 警告**

### Tests
- +5 route tests（首選不清 / role_selected 反映 / 切換清 profile / admin 422 / 未登入 401）；修 `test_user_table_columns` 加欄位；後端全量 **674 passed**

---

## [2026-07-07] — feat(teacher)：5-1c-3 右上角導覽顯示學生身分（待 UI 驗收）

### Added
- **avatar 選單顯示自填身分**（`global-nav.tsx`）：學生登入後右上角優先顯示 profile `real_name`（退回 Google 名）；avatar 旁加真名（sm+ 顯示、truncate）；下拉標頭加「校名 · 系所」+「學號」+ email
- profile 隨 `/users/me` 一併取得（role=student 才抓 `/profile`，404 視為未填）；訂閱 `ROLE_CHANGE_EVENT`，DEV 身分切換即時更新

### Verified（自動）
- tsc / eslint 0 errors（僅既有 img warning）/ build 通過
- **待使用者 UI 驗收**（學生右上角應顯示真名 + 校系）

---

## [2026-07-07] — feat(teacher)：5-1c-2 學生 profile 表單 + 首次登入 gate（待 UI 驗收）

### Added
- **首次登入 gate**（`components/onboarding/profile-gate.tsx`）：包在 `(app)/layout.tsx` 的 AppShell 外層；role=student 且 `GET /profile` 回 404 → 全屏擋在填寫頁；教師/admin 直接放行；非 404 錯誤 fail-open（不因後端暫時性問題鎖住使用者）
- **profile 表單**（`profile-setup-form.tsx`）：姓名/學號/學校/系所四欄 + email 唯讀顯示（登入帳號）；送出 `POST /profile` 成功後即時放行（onComplete，無需重整）；login 風格全屏卡片
- **data layer** `lib/profile.ts`：getMyProfile / submitProfile

### Verified（自動）
- tsc / eslint 0 問題 / `next build` 通過；元件皆 < 150 行
- **待使用者 UI 驗收**（切換為學生身分 + 未填 profile → 應被擋到填寫頁）

---

## [2026-07-07] — fix(nav)：身分切換即時更新選單 + 精簡 avatar 選單

### Fixed
- **DEV 身分切換後選單需重整才更新**：`devSetRole` 成功後廣播 `ROLE_CHANGE_EVENT`（比照 GHOST_UNLOCK 模式）；`global-nav` avatar 選單訂閱該事件重抓 `/users/me`，教師入口即時出現/消失，無需重整

### Changed
- **精簡 avatar 下拉選單**（使用者評估）：移除「學習總覽 `/overview`」（空殼、與已實作 Dashboard tab 語義重疊）與「通知 `/notifications`」（空殼、無後端通知機制）兩個連入空頁的項目；選單留 班級管理（教師）/ 設定 / 登出。頁面檔保留（`/overview` 仍被 mobile-nav 引用），僅自此選單移除；連帶清除 orphan 的 Home/Bell import

### Verified
- 5-1c-1 教師班級管理頁 **UI 驗收通過**（使用者確認）；tsc / eslint 0 errors / build 全綠

---

## [2026-07-07] — fix(auth)：/users/me 端點修 role 取得（NextAuth 路由碰撞）

### Fixed
- **`/auth/me` 經 Next.js proxy 取不到角色**（pre-existing，DEV-6 dev-role-card 從未驗過）：`/api/auth/*` 被 NextAuth `[...nextauth]` catch-all 攔截，`/api/auth/me` 到不了後端 → 「無法取得目前角色」；同時導致 5-1c-1 教師 gating（avatar 教師入口 / `/teacher` 頁）永遠失敗
- **解法**：後端 auth.py 抽出 `build_user_response`；新增 `api/routes/users.py` `GET /users/me`（不在 `/auth` 前綴 → proxy 正常轉發）；前端三處（dev-role-card / global-nav / teacher page）改呼叫 `/users/me`
- `/auth/me` 保留供後端測試（直打 ASGI 無碰撞）

### Tests
- +2（/users/me 未帶 token 401 / 回 role）；後端全量 **669 passed**；前端 build 通過

---

## [2026-07-07] — feat(teacher)：5-1c-1 教師班級管理頁（前端，待 UI 驗收）

### Added
- **`/teacher` 班級管理頁**（`app/(app)/teacher/page.tsx`）：role gate（`/auth/me`，非教師顯示無權限）
- **元件**（`components/teacher/`）：`class-manager`（列表+建立狀態）/ `create-class-form`（建班，綠色 btn-primary）/ `class-card`（邀請碼 + 複製 + 成員數 + 停用/啟用 + 名冊展開）/ `class-roster`（lazy 載名冊表格：姓名/學號/系所/校名/email）
- **data layer** `lib/classroom.ts`：listClasses / createClass / updateClass / getClassMembers
- **導覽入口**：avatar 下拉選單加教師專屬「班級管理」連結（`/auth/me` role 判定，非教師不顯示）

### Verified（自動）
- tsc 無誤 / eslint 0 errors（僅既有 img warning）/ `next build` 通過（`/teacher` route 產出）；元件皆 < 150 行
- **待使用者 UI 驗收**（可用 DEV 身分切換為教師測試）

---

## [2026-07-07] — feat(teacher)：5-1b-3 加入班級 + 學生 profile API

### Added
- **學生 profile**（`api/routes/profile.py` + `services/student_profile.py`）：
  - `POST /profile` upsert（school/department/student_id/real_name）；`GET /profile`（未填回 404 PROFILE_NOT_FOUND 供前端引導）；email 一律取自 users，不由前端提交
- **加入班級**（`POST /classes/join`）：以 6 位邀請碼入班，idempotent（重複加入不重複建 row）；**profile gate**——未填身分資料回 409 PROFILE_REQUIRED；邀請碼無效 / 班級停用回 404
- **教師名冊**（`GET /classes/{id}/members`）：回全班 profile + email，依加入時間排序；僅班級擁有者可看（他人 404、學生 403）
- `services/classroom.py` 加 `join_class` / `list_members`；註冊 `profile_router`

### Tests
- +13 route tests（profile upsert/404/422、join 409/200/idempotent/404×2/422、members 名冊/他人 404/學生 403）；後端全量 **667 passed**

---

## [2026-07-07] — feat(teacher)：5-1b-2 班級 CRUD API

### Added
- **班級 CRUD**（`api/routes/classes.py` + `services/classroom.py`）：
  - `POST /classes` 建班 → 產 6 位數字邀請碼（`secrets.randbelow` + DB unique 把關 + 碰撞重試 10 次）
  - `GET /classes` 列出教師自己的班級（outerjoin 算成員數、建立時間新到舊）
  - `PATCH /classes/{id}` 改名 / 停用（`is_active`）
- **授權**：全端點 `require_roles(UserRole.TEACHER)`（沿用既有依賴，非新建）；他人班級一律 404（不洩漏存在性）
- 註冊 `classes_router` 至 main.py

### Tests
- +7 route tests（6 位數碼 / 學生 403 / 空名 422 / 僅列自己班 / 停用改名 / 他人班 404 / 碼唯一）；後端全量 **654 passed**

---

## [2026-07-07] — feat(teacher)：5-1b-1 學生身分 profile 表 + 需求擴充決策

### Added
- **student_profiles 表**（migration `m9b0c1d2e3f4` + `models/student_profile.py`）：學生首次登入補填 school / department / student_id / real_name；`user_id` 當 PK（1:1 天然去重）；email 沿用 users
- **需求擴充決策**（AskUserQuestion 三裁決）：① profile 存獨立表（非 users 加欄位）② 首次登入強制引導填寫（僅 role=student，gate 由前端執行）③ 學號不做唯一約束（跨校撞號）；邀請碼定為 6 位數字
- 5-1b 拆為 5-1b-1（本次）/ 5-1b-2 班級 CRUD / 5-1b-3 加入班級+profile API

### Verified
- migration up/down 可逆實跑；欄位/PK/FK 正確；model 匯入 OK；db-schema.md §Module 8 同步

---

## [2026-07-07] — feat(teacher)：5-1a 班級資料表 migration

### Added（Phase 5 教師端起步）
- **classes / class_members 表**（migration `l8a9b0c1d2e3` + `models/classroom.py`）：對齊 db-schema.md §Module 8
  - `classes`：teacher_id(FK users, CASCADE) + invite_code(String12, unique+index) + is_active + created_at
  - `class_members`：複合主鍵 (class_id, user_id)，兩 FK 皆 ON DELETE CASCADE，天然去重
  - invite_code 產生與碰撞重試留待 5-1b（API 層），migration 只保證唯一性
- Model 註冊至 `models/__init__.py`（`Classroom` / `ClassMember`）

### Verified
- `alembic upgrade head` → 表/約束/FK 正確；`downgrade -1` 表全清可逆；re-upgrade 成功
- 既有取樣測試 156 passed（測試 metadata 建表流程未受影響）

---

## [2026-07-06] — feat(quiz)：6-3d QUIZ 弱項綜合測驗組 + 程式題強模型 + 題庫淨化

### Added（6-3d 弱項綜合測驗組）
- **多概念綜合出題**：`generate_question` 加 `extra_concepts`——system prompt 要求綜合測驗目標 + 相關概念（需綜合運用才可解），`concept_tags` 記錄全部概念
- **藍圖 + 節點選擇**（`weakness_set_plan.py`，不呼叫 LLM）：`compute_blueprint` 依題數 + 整體掌握度算配額（掌握度低→偏單節點；回升→提高綜合題比例）；`mastery_snapshot` 以 effective confidence 分弱項/已掌握；`plan_questions` 單節點 MC / 綜合 MC（弱項+前置）/ coding（弱項+已掌握鷹架）
- **組裝**（`weakness_set.py`）：題庫優先重用 ≤30% + 缺口並行生成（`asyncio.gather` + semaphore 6 併發，各自獨立 session，coding 用強模型）
- **端點** `POST /quiz/weakness-set?count=10|25`：回傳整組（mask 答案）+ `no_weakness` 旗標
- **前端** QUIZ 頁改弱項測驗：選 10/25 → 一次生成（動畫進度）→ 逐題作答（重用 MC/coding/hint/result）→ 總結；無弱項提示先去 LEARN；DEV 深連結 `?question=` 仍走舊 runner
- **文獻標注** references.md §5.1：Bjork 交錯/適欲難度、Vygotsky ZPD/鷹架、CAT content balancing、概念圖 GNN+RL 多跳

### Changed / Fixed（題庫品質）
- **程式題改強模型**（gpt-5.4 生成+審查）：cascade 弱生成幾乎全滅，改強模型後 LEARN 程式題覆蓋 2 → 57 部（v20/v53 仍生不出，資料驅動 tab 隱藏優雅處理）
- **審查加「考點有意義」面向**：擋考操作細節/瑣碎資訊（左上右下等）的題；複審舊 generated MC 刪 15 題不合格（答案錯 + 考點瑣碎）
- **LEARN 資料驅動 tab 隱藏**：`has_concept_quiz`/`has_coding_exercise` 依 batch 題存在與否決定；無可測驗概念的單元（DevC++ 安裝片）不顯示觀念題 tab
- **6-3c 知識點題庫實機生成**：batch 436 MC（覆蓋 61/62 片）+ 57 coding

### Tests
- +30（multi-concept、blueprint/plan、orchestration、endpoint、tab flags、knowledge points）；後端全量 **647 passed**；前端 tsc/eslint/build 全綠

---

## [2026-07-06] — feat(quiz)：6-3c 知識點驅動題庫 + LEARN 整組作答 + 審查加「考點有意義」

### Added（6-3c）
- **知識點萃取**（`services/quiz/knowledge_points.py`）：LLM（分析組 gpt-5.4-mini）讀該影片全部字幕 → 萃取 3-8 個重要知識點，明確排除操作細節（安裝步驟 / 介面位置 / 左上右下等畫面資訊）
- **題量依知識量**：批次改為每知識點 1 題觀念選擇題（`content.knowledge_point` 記錄對應點供覆蓋追溯）+ 每單元固定 1 題 coding（課程介紹單元 0 題）
- **題目來源分流**：新增 `QuestionSource.BATCH`（migration `k7f8a9b0c1d2`）——LEARN 單元題組只列 batch 預生成題；QUIZ 弱項現生題（`generated`）不列入
- **LEARN 整組作答 API**：`GET /quiz/unit-set`（`list_unit_question_set`）回傳某概念全部 batch 題 + 該生作答進度（answered/total）
- **`GET /quiz/generate` 加 knowledge_point / source 參數**；generate prompt 加「考點必須有意義」規則

### Changed
- **審查（validate）新增第 4 面向 `point_meaningful`**（使用者回饋）：題目若考操作細節 / 瑣碎資訊（左上角右下角等）→ 不通過；四面向全 AND 才 validated
- **LEARN 前端**：觀念題改整組逐題作答（`concept-quiz-tab.tsx`，答完顯示「已完成」+ 可重新作答）；程式題改讀預生成 batch 題（`exercises-tab.tsx`）；**LEARN 完全不呼叫 LLM**（AI 現生只在 QUIZ 弱項模式）；刪除 `exercises-mc-panel.tsx`、精簡 views

### Scripts
- `scripts/generate_unit_questions.py` 改知識點驅動摘要；新增 `scripts/rereview_questions.py`（以新標準複審既有題庫，刪除不合格題）

### Tests
- +19（knowledge_points 5、batch generator 重寫、unit-set bank 3 + route 4）；後端全量 **627 passed**；前端 tsc/eslint/build 全綠

---

## [2026-07-06] — feat(learn)：U2g tab 重構 + 範例程式移除 + 62 部內容全量上線

### Changed（U2g）
- **LEARN 單元 tab 改為「概念說明 / 程式實作題 / 觀念題」**：練習題兩面板升為獨立 tab（`ExercisesTab` 加 `category` prop 由 tab 指定題型）；課程介紹單元（v01-03）隱藏程式實作題 tab；移除練習題/Quiz 入口的「優先從題庫取題」開發者導向提示字樣
- **內容上線流程改使用者回饋制**（使用者決策）：6-4a 正式抽查移除；新增 `scripts/promote_unit_content.py` 全量 approve + promote **62 concepts → learning_units**（promote 時剝除 summary/code_examples 殘留 key）；品質問題待實際操作回饋（6-4b 局部重跑）

### Removed（範例程式全面下架）
- **前端**：`examples-tab.tsx`、`lib/pending-workspace-code.ts`（6-2d Workspace 轉場機制）、workspace page `initialCode` 消費、`learning.ts` CodeExample(s) 型別
- **管線**：`content_generator.py` CodeExample(s) model / `_EXAMPLES_TASK` prompt / `generate_code_examples()` / U2c intro 分支全移除（1 section = 1 LLM call）；`batch_generator` notes/聚合同步簡化

### Tests
- content/batch generator 測試改 1 section（-4 例）；後端全量 **611 passed**；前端 tsc + eslint + `next build` 全綠
- 遺留 tech-debt：lazy-seed 新使用者仍空骨架（generator 不讀 staging），既有帳號不受影響

---

## [2026-07-06] — docs(planning)：U2g/6-3c 定案——LEARN tab 重構、範例程式移除、知識點驅動題量

### Added（與使用者討論定案，4 項決策）
- **U2g（遞補原第 6 批）**：LEARN tab 改「概念說明 / 程式實作題 / 觀念題」；觀念題＝選擇題（**簡答題型不做**）；v01-03 課程介紹隱藏程式實作題 tab；範例程式全面移除（前端 + 管線 skip examples call，staging 資料留存不 promote）
- **6-3c（接 U2g）**：題量改依影片知識量——批次前置 LLM 知識點萃取（3-8 點/影片）→ 每知識點 1 題觀念題（JSON 記錄知識點供覆蓋追溯）；程式題固定 1 題（intro 0 題）；既有 138 題保留只補缺；估 $3-6

### Removed
- **U2f 範例程式製作作廢**（範例程式整個介面移除，製作無意義）
- **6-2d deferred-ui 驗收作廢**（範例卡片 → Workspace 轉場隨介面消失）；deferred-ui 僅剩 6-2c citation 跳轉

---

## [2026-07-06] — fix(learn)：練習題題型分類 + 反思僅限程式題 + 反思視窗置頂題目

### Fixed
- **反思誤套非程式題**：題庫混題型後（6-3a-3），LEARN 練習 tab 抽到選擇題仍被強制進反思流程（反思設計僅適用「先想解題思路再寫程式」的情境）；現改題型分類入口
- **反思視窗看不到題目**：學生填反思需關窗回看題目；`ReflectionFlow` 加 `questionStem` prop，題幹固定顯示於視窗頂部（獨立捲動區，不隨表單捲動）

### Changed
- **練習題入口改題型卡**（`exercises-tab-views.tsx`）：「程式實作題」（讀題 → 反思 gating → Workspace）/「觀念選擇題」（直接作答 + 立即對錯回饋，重用 Quiz 頁 `MCQuestion` + `submitAnswer`，答題驅動 BKT）；from-bank / generate 均帶 `question_type` 過濾
- 檔案拆分守規：`exercises-tab.tsx` 233 → 148 行；新增 `exercises-coding-panel.tsx`（原 QuestionPanel + 反思摘要搬出）與 `exercises-mc-panel.tsx`（MC 作答 + 結果）
- 驗證：`tsc --noEmit` + eslint + `next build` 全綠

---

## [2026-07-06] — feat(content)：第 5 批實機批次——6-2b content 62 部 + 6-3a-3 題庫 138 題

### Fixed（實機才暴露的兩個 bug）
- **gpt-5 世代參數不相容**：全系列拒收 `max_tokens`（須 `max_completion_tokens`）；`gpt-5-mini` reasoning 系拒收自訂 temperature 且預設把預算燒在內部推理回空內容（實測 `reasoning_effort="minimal"` → 0 reasoning tokens 正常輸出）。新增 `core/llm_params.py` 相容層純函式 `chat_model_kwargs()`，13 個呼叫點統一切換；gpt-5.4 系 / gpt-4o 行為不變；+5 tests
- **quiz batch `MissingGreenlet`**：validate 失敗的 rollback 會 expire session 內全部 concept（不只當前），下一輪迴圈屬性存取觸發同步 lazy-load 崩潰；`generate_all` 每輪 `db.refresh(concept)`；+1 回歸測試（未修復狀態精準重現）；後端全量 **614 passed**

### Added（實機批次結果）
- **6-2b content 批次（gpt-5.4）**：62/62 成功入 `unit_content_staging`（pending）；僅 v05 語法規則、v62 static 成員標 `needs_more_source`；抽查品質良好（v08 grounded markdown + 11 citations + 3 範例）
- **6-3a-3 題庫批次（gpt-5-mini 生成 + gpt-5.4 審查 cascade）**：62 concept 首輪 42 滿額 / 15 partial / 2 全滅 + 缺題 15 部補跑一輪 → 題庫 **138 題 validated**（MC + coding 約各半）；57/62 concept 滿額 2+ 題；v17/v41 兩輪全滅 + v11/v53/v61 各缺 1 題記 tech-debt 待 6-4b prompt 調整
- 費用實測遠低於預估（單 concept content 約 15-20 秒 × 2 call，總計約 $3-5，餘額充足）

---

## [2026-07-06] — feat(llm)：6-M1 分組模型環境變數（任務導向路由落地）

### Added
- **`core/config.py` 三組模型變數**：`LLM_MODEL_GENERATE` / `LLM_MODEL_VALIDATE` / `LLM_MODEL_CONTENT`，各配 lowercase fallback property（未設定 → `LLM_MODEL`，單一模型時代行為不變）；不抽共用 client（tech-debt 既有決策）
- **呼叫點切換**（依 6-M 選型表分流）：生成組 `llm_model_generate` = quiz/generate、quiz/hint、comprehension 出題（epl / predict_output / variation generate）；審查組 `llm_model_validate` = quiz/validate；內容組 `llm_model_content` = learning/content_generator（batch_generator `model_used` 記錄同步）；對話 + 分析組維持 `LLM_MODEL` 預設（edf/feedback、edf/evidence、reflection/evaluate、quiz/feedback、comprehension 評分）
- **variation `_call_llm_json` 加 `model` 參數**：出題與評分共用 helper，由 caller 分流
- **.env 套用選型**：`LLM_MODEL=gpt-5.4-mini`、`GENERATE=gpt-5-mini`、`VALIDATE=gpt-5.4`、`CONTENT=gpt-5.4`；`.env.example` 同步

### Tests
- 新增 `test_llm_model_routing.py` ×3（fallback / 全覆寫 / 部分覆寫）；後端全量 **608 passed**

---

## [2026-07-06] — feat(quiz)：第 4 批 U2d 題庫優先 + U2a 美化 + 重複曝光消除

### Added（U2d）
- **`GET /quiz/from-bank` 弱項模式**：省略 `concept_tag` → 後端以 `pick_target_concept`（原 orchestrator 私有函式轉公開）挑最弱概念再抽題庫；新增 `question_type` 過濾（尊重使用者選的題型）
- **重複曝光防護（tech-debt 消除）**：bank service 加 `exclude_answered_by`——server-side 排除該生已答過的題，Learn ExercisesTab 與 Quiz 頁同時生效、前端零改動；全部答過 → 404 → fallback 現生新題（validated 後入庫，題庫自然成長）
- **QuizRunner 題庫優先**：先 from-bank（< 1s）→ 404 QUESTION_BANK_EMPTY 才 LLM 現生；Loading 兩階段文案（「正在從題庫挑題」/「AI 正在生成新題」）

### Changed（U2a）
- Quiz 入口重設計：題型選擇改資訊卡（lucide icon + 一句話說明 + aria-pressed；active 用 border-emphasis 不用色塊，R8.5 合規）+ 視覺階層重整 + 「優先從題庫取題」提示
- 修 R8.2 符號字違規 ×2：exercises-tab「✓ 反思已記錄」、unit-action-bar「已完成 ✓」→ lucide CheckCircle2

### Tests
- bank service +2（type 過濾 / exclude_answered_by 雙使用者）；route +3（弱項模式 / type 過濾 404 / 已答過排除端到端）；`test_from_bank_concept_tag_required` 改寫（省略 tag 已是合法模式）；後端全量 **605 passed**

---

## [2026-07-06] — feat(mastery)：第 3 批 K6a/b/c 熟練度演算法 v2 + knowledge-graph 拆檔

### Added
- **K6a 訊號分級**：`BKT_CHAT_PARAMS(learn=0.05, slip=0.3, guess=0.4)`——chat「程式碼無錯」是弱證據（學生常帶寫到一半的碼求助），以 BKT 參數本身表達通道雜訊；`update_mastery` 加 `params` 參數，chat 傳弱證據、quiz/comprehension 沿用強證據預設；測試驗證雙向更新幅度皆顯著小於 quiz
- **K6b 遺忘衰減**：新模組 `services/mastery/decay.py`——`effective = floor + (stored−floor)×exp(−ln2×days/half_life)`；floor=0.25、基準半衰期 14 天、每次成功練習 +50%（FSRS 穩定度）、上限 180 天；惰性計算不改 DB、BKT 更新仍以 stored 為 prior（衰減=提取強度下降，非習得倒退）。套用點：mastery summary（K4 鷹架自動連動）、quiz Select（衰減回弱項重新被選中=遺忘驅動複習）、K3 診斷（久未練習的前置概念可成嫌疑）
- **K6c 事件級透明化**：`/concepts/mastery` 加 `raw_confidence`/`days_since_practiced`/`due_for_review`；detail panel 顯示「已 N 天未練習，掌握度自 X% 回落至 Y%——建議複習」（due 用 accent-orange）與輕量提示（差 ≥5% 才顯示避免雜訊）；圖譜 band 色以 effective confidence 驅動、衰減自然變暗；不做逐筆帳本
- 測試 +18（decay 純函式 17 + mastery route 衰減整合 1）；後端全量 **601 passed**

### Changed
- `knowledge-graph.tsx` 265 行 → 212 行：章節游標 + 鏡頭動作拆出 `use-graph-nav.ts`（119 行），tech-debt 消除

---

## [2026-07-06] — feat(learn)：第 2 批 U2b 移除摘要 + U2c 拔課程介紹範例

### Removed（U2b）
- **前端**：LEARN 摘要 tab（`unit-content.tsx` 4 tab → 3 tab）、`summary-tab.tsx` 刪除、`learning.ts` SummaryContent 型別與 content.summary 欄位移除
- **生成管線**：`content_generator.py` Summary model / `_SUMMARY_TASK` prompt / `generate_summary()` 全移除（3 section → 2 section，批次生成省 1/3 LLM calls）；`batch_generator.py` 聚合邏輯同步；lazy-seed 空骨架去 summary 欄位（既有 DB 內殘留 summary key 無害，前端直接忽略）

### Added（U2c）
- **`concept_category` 直通**：`UnitWithConcept` + `UnitOut` + 前端 `Unit` 型別加欄位；課程介紹單元（video 1-3）前端隱藏「範例程式」tab（含 activeTab 防呆退回概念說明）
- **批次生成跳過**：`generate_unit_content` 對 category=課程介紹 concept 不呼叫 examples LLM call，回空 examples 且不標 needs_more_source（避免 6-4 抽查誤判待補）

### Tests
- test_content_generator 改 2 section + 新增 intro 跳過測試；test_batch_generator fixtures 去 summary；test_learning_route 加 concept_category 斷言；後端全量 **583 passed**；前端 tsc + eslint 乾淨

---

## [2026-07-06] — fix(workspace)：第 1 批 U1a/b/c — 首登誤顯、反思側欄比例、反思 handoff gating

### Fixed
- **U1a**：根路由 `/`（`app/(app)/page.tsx`）原為 Phase 1「程式碼編輯器將在後續任務中實作」placeholder——首次登入 OAuth callback 偶爾落在 `/`（NextAuth callbackUrl 遺失時預設值）即誤顯此畫面；改為 server-side `redirect("/workspace")`
- **U1b**：反思側欄被壓成細縫的根因＝react-resizable-panels **v4 裸數字解讀為 px 而非 %**（`maxSize={40}` = 最大 40 像素）；workspace 頁全部 Panel size props 改百分比字串（`"28%"`/`"40%"` 等，含 editor/output 垂直組）
- **U1c**：反思顯示 gating——`setActiveReflectionId`（僅「前往 Workspace」按鈕呼叫）同步寫 `active_reflection_handoff` 標記；Workspace 進入改用 `getHandedOffReflectionId()`：標記不符（直接 navigate 的殘留）→ 自動清除不顯示；同 tab 重新整理仍保留（非一次性消費，保住「當下解題脈絡」語意）；舊 session 殘留無標記 → 下次進 Workspace 自動清
- 驗證：`tsc --noEmit` + eslint + `next build` 全綠（前端無既有測試套件）

---

## [2026-07-06] — docs(planning)：實作順序 + LLM 模型選型 v2 定案（任務導向路由）

### Added
- **roadmap 6-M LLM 模型選型 v2**（與使用者三輪討論定案，取代原論文指定的單一 GPT-4o）：任務導向路由——對話組（EDF Feedback）/ 分析組（Evidence、Reflection、Comprehension 評分）= `gpt-5.4-mini`；生成組（Quiz generate / Hint / Comprehension 出題）= `gpt-5-mini`；審查組（Quiz validate）= `gpt-5.4`（cascade：弱生成 + 強把關）；Unit content 6-2b 批次 = `gpt-5.4`（教科書品質優先）；Embedding 維持 text-embedding-3-small。6-M1 實作 = 分組環境變數（GENERATE/VALIDATE/CONTENT，fallback LLM_MODEL），不抽共用 client
- **費用估算**（依 2026-07 官方定價網查）：一次性批次 ≈ $6.6（content $4 + 生成 $1 + 審查 $1.6），儲值 $10；上線後即時互動 ≈ $35-40/月（100 學生，比 GPT-4o 省逾半）；不採 OpenAI Batch API（省 <$1.5 不值非同步改寫）
- **references.md §5.1 補論文文獻**：FrugalGPT（arXiv:2305.05176）+ RouteLLM（arXiv:2406.18665）——cascade / 模型路由設計依據
- **實作執行順序 10 批定案**（roadmap 已確認決策節）：U1 bugs → U2b/c 移除類 → k-graph 拆分 + K6 → quiz 模組（U2d/U2a/重複曝光） → 6-M1 + 實機批次 → U2f → 教師端（5-1→5-2→DEV-E→5-5） → U2e + 監控 → Phase 7 部署 → 5-3/5-4（待真實資料，Phase 5 資料策略註記同步修訂）

### Changed
- 真人驗收（K1d / K5d / K4d 語氣）改為使用者每次 session 後自測，不排入開發批次；K4d 的 RAG_MIN_SCORE 調參與對話組模型升級判斷併入第 5 批
- U2f 範例程式製作移至第 6 批（教師端之前）
- tech-debt：`OPENAI_API_KEY` 未填條目已消除（2026-07-06 驗證已填，僅驗證存在性）

### Decisions
- Claude 訂閱額度不能當 API key（訂閱與 API 分開計費），且後端鎖定 OpenAI——批次仍走 OpenAI，儲值 $10
- 論文處理：模型選型準則寫入方法論（FrugalGPT/RouteLLM 支撐）、實驗記錄確切模型版本，取代鎖死 GPT-4o

---

## [2026-07-06] — docs(planning)：session 規劃定案 — K6 熟練度演算法 v2 + Phase 6-U 學生端修正清單 + 文檔重整

### Added
- **roadmap K6 熟練度演算法 v2**（2026-07-06 與使用者 AskUserQuestion 裁決）：K6a 訊號分級 BKT 參數（quiz 強證據沿用現參數 / chat 弱證據 guess↑ learn↓，以 slip/guess 表達觀察通道雜訊、不外掛權重係數）+ K6b 遺忘曲線惰性衰減（`floor + (conf−floor)·exp(−λ·days)`，半衰期隨練習次數成長＝FSRS 穩定度概念，floor 防歸零，讀取端套用不需排程）+ K6c 事件級透明化（OLM；語意化事件不給逐筆帳本，衰減 framing 為複習提示接 K-Graph 節點變暗）
- **roadmap Phase 6-U 學生端修正**：U1a 首登誤顯 Workspace 待製作畫面 / U1b 反思 UI 比例 / U1c 反思顯示 gating（sessionStorage 殘留）/ U2a QUIZ 美化 / U2b 移除 LEARN 摘要 tab / U2c 拔除 1-3 章範例程式 / U2d QUIZ tab 改題庫優先 / U2e Workspace 程式碼存檔 / U2f 範例程式製作（低優先）；教師端＝既有 Phase 5 不另立項
- **references.md §5.1 論文關鍵文獻標注**（使用者論文引用需求）：BKT（Corbett & Anderson 1995）/ BKT+Forgetting（Khajah et al. 2016）/ Ebbinghaus 指數衰減 / FSRS 記憶穩定度 / Duolingo HLR（Settles & Meeker 2016）/ contextual guess-slip（Baker et al. 2008）/ OLM（Bull & Kay + 2020 系統性回顧）/ 生成式學習（Fiorella & Mayer 2015）
- tech-debt 新增：unit content 生成管線 `summary` 欄位閒置（U2b 移除 tab 後，6-4 批次重跑前評估從 prompt 移除以省 token）

### Changed
- roadmap 6-4a-deferred-ui 的 6-2e 摘要驗收作廢（U2b 決策）；tech-debt 同步
- tech-debt 重整：修正「練習題重複曝光」條目內錯置的 6-2d 驗收段落（歸回 deferred-ui 條目）；5 個 ✅ 已完成項目歸檔至「已消除」節

### Decisions（第一區現狀確認 + 第二區裁決）
- **題庫成本**：不採 NotebookLM（無公開 API、輸出對不齊題目 schema/citation）；批次 grounded 生成 + 題庫優先已是解方，QUIZ tab 補上題庫優先（U2d）即完整
- **題目入庫**：即時生成題 validated=True 後永久入庫且會被 from-bank 重複抽用（現行機制確認保留）
- **代碼存儲**：chat 快照 + 作答記錄入 DB；編輯器本身無存檔（重整即失）→ 列 U2e
- **反思粒度**：現行即「每題一份」（quiz source + question id），符合預期不改
- **LEARN 摘要**：直接移除（生成式學習研究：提供現成摘要效益低 + 冗餘效應）

---

## [2026-07-05] — feat(DEV-7~9)：EDF Debug 面板 + K3 診斷模擬器 + 題庫檢視器（開發者模式收尾）

### Added
- **DEV-7 EDF Debug 面板**：`interact()` / `generate_feedback()` 新增 `debug_sink` 參數（dev 帳號由 route 以 `is_dev_email` 判定才建 sink，一般帳號 None 零開銷、回傳形狀不變）——收集 evidence / strategy（hint level + 策略指令）/ RAG 命中（cosine 分數 + 200 字預覽）/ kgraph 鷹架 block；`InteractResponse.debug` 附回，前端 AI 訊息下方 `EdfDebugPanel` 摺疊面板（JetBrains Mono 灰階；僅當輪互動有，不持久化、載歷史不顯示）
- **DEV-8 K3 診斷模擬器**：`POST /dev/simulate-failures {tag, count}` 注入連續答錯紀錄（找既有含該 tag 題目、無則建 `[dev]` stub 題並重用；answered_at 毫秒遞增保排序）→ 立即回診斷摘要（streak / triggered / 嫌疑 tags）；Settings 卡顯示結果 + 知識圖譜 `?remedial=` 補救高亮連結
- **DEV-9 題庫檢視器**：`GET /dev/questions?tag=` python 端過濾 concept_tags（與 diagnosis 同款、dev 題量小可接受）回傳題型/Bloom/難度/validated/題幹摘要；Settings 卡列題 + 「作答」→ **`/quiz?question=<id>` 深連結**（QuizRunner 讀 searchParams 直接載入指定題，Quiz 頁補 Suspense 邊界）
- 共用 `DevConceptSelect`（章節+概念下拉）與 `fetchConceptGraph()` module 快取（熟練度/診斷/題庫三卡共用，session 只打一次 graph）
- Tests +8（debug sink 2 / 診斷模擬 3 / 題庫 1 / 403 防線 2）；後端全量 583 passed
- 另修 K5 Cytoscape console 警告：移除自訂 `wheelSensitivity`、`font-family` 去引號（Cytoscape 樣式解析器不接受）

---

## [2026-07-05] — feat(DEV-2~6)：開發者工具 Settings 區塊（分類重置 / 幽靈解鎖 / 熟練度編輯 / 身分切換）

### Added
- **後端**（`services/dev_tools.py` + `/dev` 路由擴充，全掛 `require_dev_user`，操作寫 log 留痕）：
  - `POST /dev/reset`：分類刪除使用者資料——mastery（student_mastery）/ progress（learning_paths+units+unit 反思；刪後 Learn 頁 lazy re-seed 全新路徑）/ quiz（student_answers+quiz 反思）/ chat（sessions+messages）；子表顯式先刪不依賴 FK cascade（SQLite/Postgres 行為一致）
  - `PUT /dev/mastery`：tags 或整章 category 擇一（model_validator 強制）+ confidence 0-1 upsert；新記錄 exposure_count=1 讓前端 band 顯示為已互動
  - `PUT /dev/role`：student ⇄ teacher 真改 `users.role`（admin 不開放）
- **前端**（Settings 頁「開發者工具」區塊，非 dev 帳號完全不渲染；防線仍在後端）：
  - `lib/dev-mode.ts`（API wrappers + is_dev module 快取 + 幽靈解鎖 localStorage/CustomEvent）+ `hooks/use-dev-mode.ts`（useDevMode / useGhostUnlock）
  - 四張卡：身分切換（顯示 /auth/me 當前角色）/ 幽靈解鎖 toggle / 熟練度編輯（章節+概念下拉 from `/concepts/graph` + 滑桿）/ 分類重置（二段確認：點一下待確認 3 秒內再點執行，回報刪除筆數）
  - **DEV-4 幽靈解鎖**：Learn 頁 locked unit 變可點瀏覽（列表 + 上一/下一單元導航）；unit 內容後端本就回傳給本人、action bar 對 locked 只顯示「尚未解鎖」，故不改後端、不影響 BKT
- Tests +14（`test_dev_tools.py`：403 防線 3 / reset 3 / mastery 6 / role 2）；後端全量 575 passed

### Fixed
- `core/errors.py` `validation_error_handler` 潛在 bug：pydantic v2 `model_validator` 的 ValueError 會出現在 `errors()` 的 ctx，直接進 JSONResponse 會 TypeError → 加 `jsonable_encoder`（對齊 FastAPI 預設 handler 行為）

---

## [2026-07-05] — feat(DEV-1)：開發者模式後端 gating 基礎 + rate limit 豁免

### Added
- **開發者模式規劃定案**（與使用者 AskUserQuestion 四項裁決）：首版含使用者 4 項（分類重置 / 幽靈解鎖 / 熟練度編輯 / 身分切換真改 role）+ 追加 A EDF Debug 面板、B rate limit 豁免、C K3 診斷模擬器、D 題庫檢視器；UI 入口 = Settings 頁區塊；完整拆解見 roadmap DEV-1 ~ DEV-9（E 假學生 seeder 延後 Phase 5）
- **DEV-1 後端 gating 基礎**：
  - `core/config.py` 新增 `DEV_MODE_ENABLED`（總開關，生產預設關）+ `DEV_MODE_EMAILS`（逗號分隔白名單，環境變數不進 git）；`core/dev_mode.py` `is_dev_email()`（小寫/空白正規化，開關關閉一律 False）
  - `api/deps.py` 新增 `require_dev_user` dependency（後續所有 dev 變更端點的統一防線，非 dev 403）
  - `GET /dev/status`：已登入使用者查自己 `is_dev`，供前端決定是否渲染開發者區塊
  - **Rate limit 豁免（追加功能 B）**：dev 帳號跳過 per-user 限流（不寫入 Redis 計數），一般帳號行為不變
  - 本機 `backend/.env` 已加 `DEV_MODE_ENABLED=true` + 白名單（gitignored）；`.env.example` 補範本
- Tests +11（`test_dev_mode.py`：白名單判定 5 / status 端點 4 / 限流豁免 2）；後端全量 561 passed

---

## [2026-07-05] — fix(K5-視覺淨化)：移除星雲背景圖層 + 修 detail panel setState-in-effect（使用者七驗回饋）

### Removed
- **星雲背景圖層**（使用者裁決：嚴重影響視覺體驗，語意縮放效果本身已獲肯定）：章節 compound parent 改為無填色、僅章名標籤；刪除孤兒檔 `galaxy-backgrounds.ts`；`/knowledge` 只剩黑色畫布 + 灰階星空點與軌道虛線
- `.claude/rules/frontend.md` R8 白名單撤銷「Knowledge Graph 星系背景」裝飾例外（剩餘星空點/導覽鈕皆灰階，屬既有白名單）

### Fixed
- `concept-detail-panel.tsx` react-hooks lint error（effect 內同步 `setState(null)` 重設會 cascading render）：改為 tag 綁定單一 state + render 期 derived-state 重設（與 knowledge-graph.tsx chapterIdx 同模式），loading 狀態由 `state.tag !== tag` 推導
- 驗證：`tsc` + `eslint components/knowledge`（0 error）+ `next build` 通過

---

## [2026-07-05] — refactor(K5-語意縮放)：全覽改「全節點放大重排」，移除章節星系節點層（使用者六驗回饋）

### Changed
- **五驗雙層視圖會錯意修正**：使用者要的不是 zoom out 換成章節級星系節點，而是**同一批概念節點與名稱全部保留**，依 zoom 比例調整節點大小、字體與排列。現改為語意縮放（semantic zoom）：
  - **zoom < 0.45**：全部 59 個概念節點放大（節點 ×1.7、字體 11→30px 世界座標、文字轉主色）並重排為緊湊網格——9 章排 3×3、章內近方形 cell 網格（新 `overview-layout.ts`，cell 260×180 配合字體推算）；全覽 fit（zoom ≈ 0.3）下名稱約 9-10px 螢幕可讀且互不重疊
  - **zoom ≥ 0.45**：回到蛇形星系佈局與原尺寸；切換時節點位置 320ms 動畫過渡 + 尺寸/字體 style transition，`graph-mode.ts` 改傳雙佈局座標
- 移除 overview 星系節點層與章間聚合邊（`overviewElements` / `GALAXY_ID_PREFIX` / `.mode-hidden` crossfade 機制）；跨章依賴邊改在全覽時 opacity 0.3 呈現（detail 仍 0.18 淡出）
- 軌道弧線 underlay 依模式 crossfade 兩條路徑（detail 蛇形 / overview 網格蛇形順序），SVG 抽出為 `orbit-underlay.tsx`；星空範圍覆蓋兩佈局聯集
- 鏡頭改瞄準「目標佈局包圍盒」而非元素現況（`graph-camera.ts` 新增 `boundsOf` + `animateToBounds`）：從全覽點章 zoom in 時節點正在移回 detail 位置，fit 對元素現況會對錯座標
- 驗證：`tsc` + `next build` 通過；視覺效果與間距參數待使用者實機驗收調整

### 技術債
- `knowledge-graph.tsx` 265 行（>250 硬性門檻）：已提出拆分計畫（抽章節導覽/鏡頭 hook），待使用者核可

---

## [2026-07-05] — feat(K5-雙層視圖)：星雲回歸 + 章節級全覽排版 + 點擊聚焦（使用者五驗回饋）

### Changed
- **太陽系行星 → 星雲星系回歸**（使用者裁決：行星干擾視覺、不簡潔）：恢復 `galaxy-backgrounds.ts` 星雲生成器（本次帶 `width`/`height` 修正，先前隱形問題不再發生）；刪除 `planet-svg.ts` / `planet-theme.ts`
- **雙層視圖（semantic zoom）**：解決「zoom out 後節點與字體小到看不見」——
  - **Overview 層**（zoom < 0.45）：每章一顆大型星系節點（星雲背景 + 52px 章名 + 概念數，全覽縮放下約 15px 可讀）+ 章間聚合依賴箭頭；概念層整層淡出
  - **Detail 層**（zoom ≥ 0.45）：原概念級視圖（mastery 填色 + 路徑 ring + 星雲章節容器）
  - **平滑過場**：模式由 viewport zoom 門檻驅動（`graph-mode.ts`），雙層各帶 220ms opacity transition——鏡頭縮放動畫穿越門檻時自然 crossfade，無跳切
- **點擊即聚焦**：點星系（overview）/ 章節容器 / 概念節點，鏡頭一律動畫 zoom in 至該章（概念節點同時開詳情面板）；統一走 `node[category]` tap handler
- 全覽按鈕改 fit overview 星系層（500ms ease-in-out）
- 驗證：`tsc` + `next build` 通過；headless Edge 雙模式截圖抽查（overview 章名可讀性 / detail 星雲融入度）

---

## [2026-07-05] — refactor(K5-太陽系主題)：改程序生成 SVG 星球 + 全覽按鈕（使用者四驗回饋）

### Changed
- **NASA 影像 → 程序生成 SVG 星球**（使用者裁決：真實照片無法融入背景且搶走視覺焦點）：新 `planet-svg.ts` 生成低飽和 token 色相的漸層球體 + 特徵組合（太陽光暈/土星環/木星條紋/水星隕石坑/地球陸塊），data URI 帶明確 width/height（規避 canvas rasterize 坑）；`background-image-opacity` 0.55 維持低調；headless 驗證星球融入 #0D1117 且節點仍為主角
- **章節標籤去天體名**：parent 標籤與導覽 pill 只顯示原分類名（如「運算子（4/10）」）——星球是介面主題非主角
- 刪除 `web/public/planets/*.jpg` + `CREDITS.md`（NASA 方案棄用）與 `galaxy-backgrounds.ts`（星雲備援被星球 SVG 取代）；mulberry32 抽至 `prng.ts`；`fitWithCap` 抽至 `graph-camera.ts`（knowledge-graph.tsx 239→217 行）

### Added
- **全覽按鈕**（GalaxyNav 底部 pill 旁 Maximize 鈕）：動畫 zoom out 至涵蓋所有節點，供使用者隨時查看整張圖
- 驗證：`tsc` + `next build` 通過；headless Edge 渲染抽查（SVG 星球 × cytoscape parent）

---

## [2026-07-05] — feat(K5-太陽系主題)：NASA 行星影像 + 蛇形軌道佈局（與使用者共同定案）

### Added
- **太陽系主題定案**（AskUserQuestion 四項裁決）：十章依課程順序對應「離太陽距離」（課程介紹=太陽 → 物件導向=冥王星）；NASA 真實影像優先（效果不佳再退程序生成 SVG）；蛇形軌道佈局；行星大小依章節概念數
- **NASA 影像資產** `web/public/planets/*.jpg`（10 張，public domain，來源與後製記錄於 `CREDITS.md`）：太陽 SDO / 水星 MESSENGER / 金星 Mariner 10（裁單盤）/ 地球 Blue Marble 2012 / 火星 Viking / 木星 Cassini / 土星 Cassini / 天王星、海王星 Voyager 2 / 冥王星 New Horizons；`planet-theme.ts` 對應表
- **軌道弧線 + 星空 underlay**（`orbit-scene.ts`）：Catmull-Rom 平滑軌道虛線貫穿十章錨點 + 140 顆 seeded 星點，掛在 cytoscape canvas 底下的 SVG `<g>`，監聽 `viewport` 事件同步 pan/zoom transform
- 章節容器背景改 NASA 行星影像（ellipse 裁圓盤、`background-image-opacity: 0.55`、影像大小隨 cluster 自動縮放 = 行星大小 ∝ 概念數）；章名標籤改「章節 · 天體」

### Fixed（使用者三驗回饋）
- **星系背景隱形根因**：程序生成 SVG 缺 `width`/`height` 屬性，canvas rasterize 退回 300×150 預設尺寸 → cover 錯位成角落污漬（headless Edge 對照實驗證實）；NASA 影像為 JPG 無此問題，`galaxy-backgrounds.ts` 保留為備援並註記此坑
- **zoom 過大**：`fitWithCap` 取代裸 fit——fit zoom 與 `ZOOM_CAP=1.0` 取小，小章節不再貼臉
- **節點過密**：phyllotaxis 步距 52→74；章距 380→700、行距 680（蛇形 2×5）
- **線條凌亂**：跨章依賴邊預設 opacity 0.18 淡出（`edge[?cross]`），hover 高亮恢復；章內邊維持 0.7
- 驗證：`tsc` + `next build` 通過；headless Edge 實渲染抽查（地球章節聚焦圖）確認影像/裁切/zoom 上限效果

---

## [2026-07-05] — feat(K5-視覺調整二)：進度星系聚焦 + 導覽 + 星雲增亮（使用者二驗回饋）

### Added
- **進場鏡頭聚焦**：進 `/knowledge` 不再顯示全圖縮小狀態，直接 zoom 至「目前進度單元」所在星系（`?remedial=` 補救跳轉仍優先框住嫌疑鏈）；無路徑資料時退回第一章
- **星系導覽 `galaxy-nav.tsx`**：左右半透明圓鈕（灰階 `bg-surface-1/70`，R8 白名單）+ 底部章名指示 pill（如「運算子（4/10）」）；點擊以 350ms ease-in-out 動畫切換星系，拖移/縮放原生手勢不受影響
- **規則協作原則**：全域 CLAUDE.md 新增「規則衝突處理」——需求與規則文檔衝突時先與使用者討論，核准例外回寫規則文檔；星系背景已登記至 frontend.md R8 例外白名單（限 /knowledge）

### Changed
- **星雲透明度整體調亮**（原本幾乎看不見）：SVG 核心 0.28→0.5、星雲橢圓 0.10-0.20→0.18-0.32、cytoscape `background-image-opacity` 0.5→0.8
- 驗證：`tsc` + `next build` 通過；lint 僅剩既有 concept-detail-panel 舊錯誤

---

## [2026-07-05] — feat(K5-視覺調整)：確定性星系佈局（使用者初驗回饋）

### Changed
- **佈局改確定性 preset**（取代 fcose 隨機 force-directed）：章節沿左→右 S 曲線排列（`graph-layout.ts`：spacing 380 / 振幅 170），章內節點以 phyllotaxis 黃金角螺旋展開（形似星團、零重疊）；排序依據 = `video_order`（`/concepts/graph` 新增此欄位）——同資料每次渲染座標完全一致
- **背景統一 + 星系區隔**：章節容器移除填色與邊框（背景與畫布一致 #0D1117），改掛程序生成的低透明度星雲 SVG（`galaxy-backgrounds.ts`：mulberry32 seeded → 每章樣式獨特且固定；色相僅用 token 藍/紫/灰 + `background-image-opacity: 0.5`）；拖曳章節（parent）可整體移動該星系
- 移除 `knowledge-graph.tsx` 的 fcose import（`cytoscape-fcose` 依賴保留於 package.json，未從其他處使用）
- ⚠ 設計註記：星系背景屬裝飾性視覺，與 frontend.md R8.4 有張力——依使用者 2026-07-05 明示要求實作，以低飽和灰藍紫階壓低違和
- 驗證：`tsc` + `next build` 通過；後端 550 tests 全綠；星雲 SVG 以 qlmanage 轉圖抽查確認柔和不搶主體

---

## [2026-07-05] — feat(K5+K3e)：知識圖譜視覺改版 + 診斷前端入口

### Added
- **K5a 套件決策記錄**（`docs/references.md` §1）：維持 Cytoscape.js + fcose——fcose 是唯一同時支援 compound node + constraint 的 force-directed layout；dagre 不支援 compound（無法分章 cluster）；React Flow 定位 workflow editor、遷移需重寫全部 graph 程式碼無決定性優勢；D3 手刻本已禁用
- **K5b 熟練度視覺**：節點填色改為 mastery band（綠=已掌握 / 橙=學習中 / 紅=需加強 / 灰=尚未互動，取代原 category 填色 + underlay 外圈）；每個 category 產生 compound parent 形成分章 cluster（fcose `nestingFactor: 0.15`）；prerequisite 邊箭頭放大（arrow-scale 0.75→1）+ 不透明度提高（0.55→0.7）；`toElements` 自 style 檔拆至 `knowledge-graph-elements.ts` 控制檔案大小
- **K5c 路徑高亮**：underlay ring 改承載路徑語意——藍 ring=目前單元（in_progress，無則取 order 最小 available）/ 綠 ring=已完成 / 紅 ring=補救嫌疑；overlay 由 `/learning/paths/default` 衍生（`path-overlay.ts` 純函式，載入失敗不擋圖譜主體）；`/knowledge?remedial=tag1,tag2` query 觸發紅 ring + 鏡頭聚焦（K3e 跳轉入口）；header 圖例改共用 `graph-legend.tsx`
- **K3e 診斷前端入口**：quiz 結果頁答錯自動查 `GET /concepts/{tag}/diagnosis`（未觸發或失敗自動隱藏，符合 K3d 設計）；觸發時顯示嫌疑鏈（depth / 熟練度 / 盲區標示）+ 每節點「微測驗」按鈕（新端點 `GET /quiz/questions/{id}` 直取 K3c 附掛的題庫診斷題，僅 validated）+「開放補救路徑」（POST remediate → 顯示重開單元順序 + Learn 連結）+「在知識圖譜查看嫌疑鏈」（`?remedial=` 跳轉）
- 後端新增 `api/routes/quiz_questions.py`（獨立檔避免 quiz.py 破 250 行）+ 4 route tests（550 tests 全綠）

### Changed
- `quiz-runner.tsx`（291 行超標）拆出靜態子視圖至 `quiz-runner-views.tsx`（184 + 133 行）；ResultView 增 `onStartQuestion` 讓微測驗直接切入作答流程
- Knowledge 頁改用 `useSearchParams`（補 Suspense boundary 符合 Next.js CSR bailout 規範），並行載入 default path 作 overlay
- 驗證：`tsc --noEmit` + `next build` 通過；後端 550 tests 全綠；lint 僅剩既有 `concept-detail-panel.tsx` set-state-in-effect 舊警告（本次未觸碰）

---

## [2026-07-04] — fix(chat)：Coddy 回覆 Markdown 渲染 + IME Enter 誤送出 + 樂觀顯示

### Fixed
- **Markdown 未渲染**：Coddy 回覆的粗體 / 列表 / inline code / code block 原本以純文字逐行顯示 → 新增共用 `components/ui/markdown.tsx`（`MarkdownContent`，react-markdown + remark-gfm，樣式對齊 frontend.md Code Block 規格：bg-inset / border / JetBrains Mono），`message-bubble.tsx` assistant 訊息改走 Markdown；使用者訊息維持純文字（輸入非 Markdown）；`concept-tab.tsx` 改 import 共用元件消除重複的 MARKDOWN_COMPONENTS
- **中文輸入法 Enter 誤送出**：`chat-input.tsx` keydown 加 `e.nativeEvent.isComposing || e.keyCode === 229` 判斷——IME 組字中的 Enter 是確認選字，不再直接送出（Safari 相容以 229 補判）
- **使用者訊息未即時顯示**：`use-chat.ts` `sendMessage` 改樂觀更新——送出後立即以暫時 id 上畫面（後接「Coddy思考中」indicator），API 成功後原位替換為 server 版訊息；失敗時保留使用者訊息、只補錯誤回覆（原本失敗才補 user 訊息的邏輯移除）
- 驗證：`tsc --noEmit` + `next build` 通過（前端無測試基礎設施，UI 行為請手動驗收）

---

## [2026-07-04] — feat(K4c)：補救路徑 — 診斷結果重新開放前置單元

### Added
- `services/learning/remedial.py`：`open_remedial_units` — 嫌疑概念在學生 default path 的既有 units 重新開放（completed/locked → available + 清 completed_at；available/in_progress 不動仍列入回傳）；**不新建 row**（62 concept 都已有 unit），不觸碰 (path_id, order_index) 唯一約束；completed → available 為系統級動作（手動 transition 禁止，但診斷已證明概念沒學牢，有教學依據）
- `POST /concepts/{tag}/diagnosis/remediate`：先跑診斷（404 未知 concept / 409 未觸發），觸發後開放全部嫌疑 units，回傳 order_index 升冪的補救清單（= 建議學習順序，最基礎先學）
- `tests/test_remedial.py` 5 tests（service reopen/noop + route 409/404/整合）→ **後端 546 tests 全綠**

### Changed
- `docs/api-spec.md` 補 remediate 端點；roadmap K4c 勾選
- K4 僅剩 K4d 真人驗收（需 OPENAI_API_KEY，建議與 6-4a 實機批次合併執行）

---

## [2026-07-04] — feat(K4a/b)：Coddy 自適應提示 — K-Graph 鷹架 + RAG 相關性觸發

### Added
- **K4a** `services/edf/kgraph_context.py`：學生知識狀態 → prompt block（解析 evidence tags 直接命中 + `edf_parent_tag` group 已曝光成員、弱者優先取 6 筆）+ 鷹架分級指令（以**最弱**相關概念 confidence 決定：<0.4 框架填空/逐行拆解、0.4-0.7 引導式提問、>0.7 只點 edge case）；best-effort 無資料回空字串不擋教學流程
- `chat.py` interact 在 mastery 更新後讀取 kgraph block（鷹架依最新狀態）注入 `generate_feedback`
- 測試 +9（7 kgraph + 2 RAG 分數過濾）→ **後端 541 tests 全綠**

### Changed
- **K4b（原 6-5a）** RAG 觸發改內容相關性：`TeachingStrategy` 移除 `use_rag` 欄位與 `hint>=2 && bloom>=ANALYZE` 寫死規則；`fetch_rag_chunks_safe` 每次互動都檢索、只注入 cosine >= `RAG_MIN_SCORE`（0.40 初始值，K4d 實測調參）的 chunks，全低於門檻回空（該查就查、不相關不硬塞）
- **K4a（原 6-5b）** persona 語氣改寫：Coddy 具名、先肯定再引導、提問具體到程式碼、小事直接回答；RULE-5 從「永遠以提問結尾」放寬為「自然的下一步收尾（提問或行動建議），不必刻意反問」
- `.claude/rules/edf-pipeline.md` 同步：RAG 觸發規範改為相關性分數、prompt 組裝順序加 kgraph 層、persona 描述更新
- 既有 decision / feedback 測試配合 `use_rag` 移除改寫

---

## [2026-07-04] — feat(K3)：根源弱點定位器後端（圖回溯認知診斷）

### Added
- `services/diagnosis/root_cause.py`：**K3a** stateless 觸發判定（該 concept 最近作答連續失敗 streak，遇答對截斷，>= 3 觸發）+ **K3b** closure（max_depth=3）回溯嫌疑排序（已曝光低 confidence 優先 → 未曝光盲區；高 confidence 前置排除；上限 3）+ **K3c** 每個嫌疑附題庫 validated 診斷題 question_id
- **K3d-API** `GET /concepts/{tag}/diagnosis`（獨立 route 檔避免 concepts.py 破 250 行；純 DB 讀取不掛 rate limit；未觸發回 triggered=false 供前端隱藏入口）
- `tests/test_diagnosis.py` 9 tests（streak 截斷 / 嫌疑排序 / 高 conf 排除 / 題庫附題 / route 401+404+整合）→ **後端 533 tests 全綠**
- 新增 K3e（前端入口）追蹤項，建議與 K5 視覺改版一併設計

### Changed
- `docs/api-spec.md` 補 diagnosis 端點；roadmap K3a-d 勾選
- ⚠ `services/diagnosis/root_cause.py` 165 行（>150 提醒門檻）：單一職責完整（觸發+排序+附題），暫不拆分，K4c 補救路徑若復用再評估

---

## [2026-07-04] — feat(K2)：動態知識狀態追蹤 — EDF 對話重新驅動 BKT

### Added
- **K2a** migration `j6e7f8a9b0c1`：`concepts.edf_parent_tag` 欄位 + index + mapping seed（EDF 20 粗 tag 中 10 個對映 59 個影片 concept；課程介紹 3 個 NULL；STL/template/concurrency 等課綱未涵蓋 tag 照舊跳過）
- **K2a** `services/mastery/resolve.py`：三層 fan-out 解析（① tag 直接命中 → ② parent group 只更新該生已曝光組員 → ③ 全未曝光只更新組內 video_order 最小的入門 concept）——讓 Workspace 對話重新驅動 BKT，同時防止粗 tag 對話噪音淹沒 quiz / comprehension 精準信號；消除 tech-debt「EDF Mastery 連動暫時退場」
- **K2b** `GET /concepts/mastery` 加 `last_practiced_at`（K4 Coddy prompt 的時序信號；缺口分析後改為擴充既有端點、不新建 k-state API）
- **K2c 決策記錄**：暫不引入真 AST（tree-sitter/libclang）——LLM Evidence 已輸出等效信號；Phase 5 有行為資料後重評（記 tech-debt）
- 測試 +6（5 fan-out + 1 endpoint 欄位）→ **後端 524 tests 全綠**

### Changed
- `services/mastery/updater.py`：`update_mastery` 改走 resolve 三層解析 + 跨 tag 去重（同 concept 每次 evidence 只更新一次）；移除被取代的 `_get_concept_id_by_tag`
- 實機驗證：alembic upgrade 實跑 + mapping 分布查核（syntax-basic 20 / control-flow 11 / function-design 11 / ...共 59 對映）
- `docs/roadmap.md`：K2/K3 依缺口分析細化（K2b 改擴充既有 API、K3a 改 stateless 查詢設計）並勾選 K2a/b/c；`docs/api-spec.md` Knowledge Graph 段修正為實際路徑 `/concepts/*` + 欄位更新；`docs/tech-debt.md` EDF Mastery 項 ✅ + 新增 AST 決策記錄

---

## [2026-07-04] — feat(K1)：K-Graph 自適應學習引擎啟動 — 跨章多對多依賴 DAG

### Added
- **Phase 6-K 納入 roadmap**（功能規格書五大功能）：K1 跨章多對多圖 / K2 動態知識狀態 / K3 根源弱點定位 / K4 Coddy 自適應（吸收原 6-5 全部）/ K5 視覺改版（吸收原 6-6a/c/d）；執行順序 K1→K2→K3→K4→K5 依技術相依性排定
- **K1a** migration `i5d6e7f8a9b0`：curated 依賴 map（每 concept 1-3 個真實直接前置，依 C++ 教學相依性判斷）取代線性 PREREQUISITE 鏈 61 條 → **90 條多對多邊**；不變量：全邊 source.video_order < target.video_order（無環）、除 video 1 外每節點 ≥1 入邊（連通）；downgrade 可還原線性鏈
- **K1b** `services/graph/traversal.py`：`get_prerequisite_closure(db, tag, max_depth)` — 單查詢載全邊 + 記憶體 BFS 回溯 + 菱形去重，回傳 (concept, depth) 依 (depth, video_order) 排序；供 K3 根源診斷使用；5 個新測試（**後端 518 tests 全綠**）
- **K1c** 實機驗證：alembic upgrade 實跑 dev DB + SQL 驗證（90 prerequisite 邊 / cpp-47-recursion ← 25 if-else + 37 參數 + 38 回傳值 / 0 孤兒節點 / 0 反向邊）

### Changed
- `docs/roadmap.md`：**移除 6-5 / 6-6 段**（內容完整整併至 K4 / K1+K5，留整併說明）；已確認決策更新（知識圖譜重構決議標記完成、新增 Phase 6-K 決策）
- `docs/tech-debt.md`：「跨章節 PREREQUISITE 邊未標」✅ 消除（K1a）；「EDF Mastery 連動退場」cross-ref K2a；「Learn 頁 graph 版」併入 K5
- `docs/modules.md` Module 5 升級為 K-Graph 引擎描述；`docs/db-schema.md` 補邊資料現況注記
- 可行性檢查結論：schema 原生支援多對多（unique triple）、拓撲排序已處理 DAG、quiz select 的出度中心性加權在 DAG 下才真正生效（線性鏈時全部 out_degree=1 無區分度）——K1 為資料工程而非架構重寫

---

## [2026-07-04] — feat(6-R)：健壯性強化（架構審查）+ 移除教授抽查

### Added
- `backend/core/rate_limit.py`：per-user rate limit dependency（Redis INCR+EXPIRE 固定窗口，Redis 掛掉 fail-open 放行）；掛上 12 個 LLM 端點（chat interact / quiz generate+hint / quiz feedback / reflection create / comprehension epl+predict+variation 全系列）+ `/code/execute`；429 回 `RATE_LIMITED` + `detail.retry_after_seconds`
- `core/auth.py`：NextAuth token `exp` claim 驗證，過期回 401 `TOKEN_EXPIRED`（原本被竊 cookie 永久有效）
- `core/errors.py`：`unhandled_error_handler` 補 `logger.exception` traceback（原 500 完全無痕跡）；新增 `validation_error_handler` 把 422 轉統一 `{error, message, detail}` 格式
- `tests/test_rate_limit.py`（5 tests）+ auth exp / errors logging+422 / judge0 網路例外 / evidence schema / chat fail-safe / user 節流 共 14 個新測試 → **後端 513 tests 全綠**
- `docs/api-spec.md` 新增「標準錯誤格式」一節（全部 error code 對照表）

### Changed
- `services/judge0.py`：httpx 網路例外（ConnectError / Timeout）submit 階段轉 503 `JUDGE0_UNAVAILABLE`、polling 階段視同該輪失敗重試（原直接冒泡 500）
- `services/edf/evidence.py`：LLM 回傳合法 JSON 但不符 schema（ValidationError）→ 502 `LLM_PARSE_ERROR`（原冒泡 500）
- `services/chat.py`：**fail-safe 持久化** — user message 於 LLM 呼叫前先 commit，OpenAI 失敗不再連學生輸入一起 rollback；`list_sessions` count 改 `func.count()`（原全表載入）
- `services/user.py`：首登並發 race 防護（IntegrityError → rollback 重查）+ `last_login_at` 1 小時節流（原每個 authenticated request 都寫 DB）；lookup 改用 `google_id or sub`（修 google_id=None 永遠 miss 的邊界）
- `services/quiz/orchestrator.py`：`list_history` count 改 `func.count()`
- 容錯 swallow 全面補 `logger.warning`（chat / orchestrator / mastery_hook / quiz generate RAG fallback）
- `web/lib/api.ts`：401 統一重導 `/login`（原為 TODO；已在 /login 不重導避免迴圈）
- `web/app/api/[...path]/route.ts`：proxy 加 30 秒 `AbortSignal.timeout`，逾時回 504 `BACKEND_TIMEOUT`（原 backend 卡死時前端 request 無限懸掛）
- `.claude/rules/backend.md` 錯誤處理表補「Token 過期 / 網路層例外 / LLM schema」三列 + 容錯 swallow 必須留痕規則
- `docs/roadmap.md`：新增 6-R 段（8 項全勾）；**6-4 移除教授抽查改為自行品管**（實機批次跑 + deferred-ui 驗收保留）；Phase 7 前置條件加註 6-R 完成
- `docs/tech-debt.md`：新增 3 筆刻意延後項（OpenAI client 抽取 / 429 toast UI / LLM 降級快取）+ 教授抽查字樣同步修訂
- 既有 `test_user_service.py` 2 個測試配合節流行為改寫 + 新增節流內不寫 DB 測試

---

## [2026-06-23] — docs：新增 roadmap 6-6 知識圖譜優化（使用者反饋）

### Added
- `docs/roadmap.md` Phase 6 新增 **6-6 知識圖譜優化（視覺 + 核心機制）**：
  - 背景：使用者反饋 `/knowledge` 頁面視覺不佳；現況 62 節點僅線性 PREREQUISITE 鏈（58 條邊），fcose layout 呈現接近一條長鏈，不直觀。呼應既有決議「知識圖譜重構為 Phase 6 後續工作」與 tech-debt「跨章節 PREREQUISITE 邊未標」項目，擴大範圍納入學術研究調研
  - 6-6a：查 `docs/references.md` §5 學術資源尋找知識圖譜輔助學習的實證設計參考（Cytoscape.js 為 Tier 1 鎖定套件，僅調整用法不換套件）
  - 6-6b：跨章關鍵依賴重構多對多 PREREQUISITE 圖
  - 6-6c：依研究結論重新設計 stylesheet/layout，對照 frontend.md R1-R8 規則檢核
  - 6-6d：真人測試驗收（學生是否真能讀懂學習進度，不只是好看）
- `docs/tech-debt.md` 既有「跨章節 PREREQUISITE 邊未標」項目加註 cross-ref 至 roadmap 6-6
- 本次僅新增 roadmap 追蹤項目，未動程式碼

---

## [2026-06-23] — docs：新增 roadmap 6-5 Coddy 對話品質優化（使用者反饋）

### Added
- `docs/roadmap.md` Phase 6 新增 **6-5 Coddy（EDF Chat）對話品質優化**：
  - 背景：使用者實測後反饋 Coddy 反問語氣生硬不自然；且 RAG 是否查影片內容目前綁在 `services/edf/decision.py` 的 `use_rag = clamped_hint >= 2 and bloom >= ANALYZE` 門檻，而非「問題是否真的需要影片內容」
  - 6-5a：RAG 觸發條件改為內容相關性判斷（取代 hint_level 門檻寫死規則）
  - 6-5b：`services/edf/feedback.py` persona/preamble 語氣優化
  - 6-5c：真人測試驗收
- 本次僅新增 roadmap 追蹤項目，未動程式碼（依專案規範：單一最小任務、不擅自實作）

---

## [2026-06-23] — chore：清理未追蹤垂圾檔 + 新增 dev-start.sh

### Removed
- `web/next`、`web/web@0.1.0`：誤建空檔（疑為指令打錯產生），已刪除
- `.claude/scheduled_tasks.lock`：對應 PID 已不存在的過期 lock，已刪除

### Added
- `dev-start.sh`：本機一鍵啟動腳本（Colima → docker-compose → 等 Postgres → alembic current → uvicorn），路徑改用 `$(dirname "$0")` 可攜寫法

### Changed
- `.gitignore`：新增 `.claude/scheduled_tasks.lock`（runtime lock）與 `ScreenShot/`（本機暫存截圖，非專案文件資產）

---

## [2026-05-22] — Phase 6-3b ExercisesTab 題庫優先（GET /quiz/from-bank + 前端分流 fallback）

### Verified (2026-05-22 透過 `pytest -q` + `npx tsc --noEmit` + `npx eslint`)
- 後端 499 passed in 9.27s（原 488 + 新 11：bank 6 + route 5）
- 前端 TypeScript / ESLint 全綠
- Fallback path 直接驗證（DB 無 validated 題 → 預期跳 generate 流程）；命中題庫 path 延至 6-3a-3 / 6-4 實機跑出 grounded validated 題後驗

### Added
- **`backend/services/quiz/bank.py`** (45 行)：`pick_random_validated_question(db, concept_tag, exclude_question_ids?)`
  - 篩 `validated=True` + Python 端 filter `concept_tags` 含 tag（避開 JSON contains 跨方言差異）
  - 隨機抽用 `random.choice`（候選 n 不大）；無題回 `None`
  - `exclude_question_ids` 預留給未來「不重複曝光已答題」加強，本次前端未啟用
- **`GET /quiz/from-bank?concept_tag=...`** endpoint（api/routes/quiz.py）
  - 命中 → 200 + `QuestionForStudentOut`（復用 `from_question` mask 答案）
  - 無題 → 404 `QUESTION_BANK_EMPTY`，前端可 fallback
  - `concept_tag` 必填（FastAPI Query 預設驗證 → 422）
- **`web/lib/quiz.ts`**：`getQuestionFromBank(conceptTag)` helper
- **`web/components/learn/exercises-tab-views.tsx`** (58 行)：`IdleView` + `LoadingView`（純展示元件，由 exercises-tab.tsx 拆出避免主檔超 250 行門檻）
- **`backend/tests/test_quiz_bank.py`** (約 130 行)：6 個 service 單元測試
  - 命中題、無題、validated=False 不被抽中、不同 tag 不串題、exclude_question_ids 過濾、多次抽都符合條件
- **`backend/tests/test_quiz_route.py`** 加 5 個 endpoint integration 測試（test_from_bank_*）

### Changed
- **`web/components/learn/exercises-tab.tsx`**：
  - `Phase` type 加 `loading-bank` / `loading-generate`（取代原單一 `loading`）
  - `startExercise()`：先 `getQuestionFromBank` → catch `ApiRequestError(404, QUESTION_BANK_EMPTY)` → fallback `generateQuestion`；其他錯誤一律 humanize
  - `LoadingView` 改 prop-driven 文案：bank 顯示「查找題庫題目（< 1 秒）」/ generate 顯示「AI 正在生成題目（5-15 秒）」
  - 拆出 IdleView / LoadingView 至 exercises-tab-views.tsx（主檔 261 → 227 行，回到 < 250 健康水位）
- **`backend/services/quiz/__init__.py`**：export `pick_random_validated_question`
- **`backend/api/routes/quiz.py`**：212 → 237 行（< 250），新增 from-bank endpoint + 對應 import

### Implementation note
- **為什麼 endpoint 用 GET 而非 POST**：抽題是冪等讀取操作（每次隨機抽 1 題；非建立資源），語意上 GET 更合適；URL 中 `concept_tag=` 也便於除錯 / 觀察。
- **為什麼 random.choice 在 Python 端而非 SQL `ORDER BY RANDOM()`**：JSON contains（`concept_tags @> [tag]`）跨 SQLite/Postgres 寫法差異大；既然候選量 n ≤ 數十，先撈出再 Python random 是可攜的低成本選擇。未來流量大或 dedup 需要更複雜邏輯時可升級。

### Tech debt
- 已答題排除尚未啟用：service 已支援 `exclude_question_ids`，但前端 ExercisesTab 未維護「使用者已答題清單」；學生重複進同 unit 練習可能抽到同題（中短期可接受，列為 tech-debt）

### Tests
- 後端 499 tests 全綠（pytest -q 9.27s）
- 前端 typecheck + lint 全綠

### Health metrics
- `bank.py` 45 行（健康）
- `quiz.py` (routes) 237 行（< 250 ⚠ 門檻）
- `exercises-tab.tsx` 227 行（< 250；超 150 ⚠ 但與既有 261 同水位）
- `exercises-tab-views.tsx` 58 行（< 150）
- `test_quiz_bank.py` 約 130 行（測試檔）

### Deferred（已錨定）
- 命中題庫 path 真實驗收：延至 6-3a-3 / 6-4 實機跑出 grounded validated 題後 → roadmap 6-4a-deferred-ui 紀錄 / tech-debt 延遲驗收區
- Dedup 「不重複出已答題」：service `exclude_question_ids` 已預留 → 前端維護已答題清單後再啟用

---

## [2026-05-22] — Phase 6-3a-2 批次練習題生成 service + CLI（程式碼 + mock+DB 測試完成；實機跑延 6-4）

### Verified (2026-05-22 透過 `pytest -q`)
- `tests/test_quiz_batch_generator.py` 8 passed
- 全套 488 passed in 9.21s（原 480 + 新 8，無 regression）

### Added
- **`backend/services/quiz/batch_generator.py`** (217 行)：批次層
  - `generate_questions_for_concept(concept, question_types, bloom_level)` — per-concept 跑 N 題、每題 generate（grounded mode：`video_order=concept.video_order`）+ validate（retry max 2）
  - `generate_all(only, skip_existing, question_types, bloom_level)` — 入口；`skip_existing=True` 時跳過已有 ≥ N validated 題的 concept（用 `_count_validated_questions` 掃 `concept_tags` JSON array）
  - `list_target_concepts(only)` — `Concept.video_order IS NOT NULL` + 可選 video_order filter（與 6-2b 同策略，含 1-3 課程介紹）
  - dataclasses `QuestionAttempt`、`ConceptBatchResult`（含 `validated_count` property）
  - 預設 `DEFAULT_QUESTION_TYPES = (MULTIPLE_CHOICE, CODING)`、`DEFAULT_BLOOM_LEVEL = APPLY=3`
- **`backend/scripts/generate_unit_questions.py`** (124 行)：CLI
  - `--only N` 單一 video_order；`--force` 跳 skip_existing；`--dry-run` 只列 concept
  - 輸出 per-concept progress（marker：✅完整 / ⚠ partial / ❌全失敗 / ⏭️ skipped）+ summary（concepts / full success / partial / all-failed / skipped / total validated questions inserted）+ failed details
- **`backend/tests/test_quiz_batch_generator.py`** (約 270 行)：8 個 mock+DB 測試
  - per-concept 2 題全 validated → 入庫
  - validate concept_fits=False 兩次 retry 失敗 → 該題 rollback、不阻擋下一題
  - generate LLM_PARSE_ERROR → 該題直接 abort（不 retry）、不阻擋下一題
  - NO_VIDEO_ORDER concept → 422 防呆
  - `generate_all` `skip_existing=True` 跳過已有足量 validated 題的 concept
  - `--force`（skip_existing=False）強制重生
  - `list_target_concepts` only 過濾 + 排除無 video_order
  - `ConceptBatchResult.validated_count` property

### Fixed / Implementation note
- **ORM attr expire 問題**：rollback / commit 後 SQLAlchemy 預設 `expire_on_commit=True` 會把 ORM 物件 attr 標 expired，下次 access 觸發 async lazy reload；在 retry loop 內每次 IO 後加 `await db.refresh(concept)` 確保下一輪訪問 `concept.video_order / .tag / .difficulty_level` 時不會拋 `MissingGreenlet`。

### Changed
- **`docs/roadmap.md`** 6-3a-2 勾選 + 補執行成本估計（62 × 2 × 2 LLM call ≈ 250-500k token / $5-15 USD）

### Tests
- 後端 488 tests 全綠（pytest -q 9.21s）

### Health metrics
- `batch_generator.py` 217 行（< 250 ⚠ 門檻）
- `generate_unit_questions.py` 124 行（< 150 ⚠ 門檻）
- `test_quiz_batch_generator.py` 約 270 行（測試檔無門檻；逐塊獨立）

### Deferred（已錨定）
- 6-3a-3 實機 LLM 全跑：延至 6-4a 與 6-2b 批次跑合併執行
- 重複避免目前用「已 validated 題數 ≥ requested」判斷；題目雖然 grounded 但語意可能近似，未做相似度 dedupe（如有重複可手動 invalidate）

---

## [2026-05-22] — Phase 6-3a-1 grounded mode 接入 `generate_question`（程式碼 + mock 測試完成；批次 script 與實機跑延 6-3a-2 / 6-4）

### Verified (2026-05-22 透過 `pytest -q`)
- `tests/test_quiz_generate.py` 12 passed（含 4 個新 grounding 測試）
- 全套 480 passed in 9.23s（原 476 + 新 4，無 regression）

### Added
- **`backend/services/quiz/generate.py:_GROUNDING_RULES`** — 3 條 grounding rule（題目情境 / 嚴禁發明 / 字幕不足時降難度）
- **`backend/services/quiz/generate.py:_fetch_grounded_chunks_for_video`** — 包 `get_chunks_by_video_order`，失敗 fallback 空 chunks（同 semantic path 容錯）
- **`backend/tests/test_quiz_generate.py`** 新增 4 測試：
  - `test_grounded_mode_uses_video_chunks_and_skips_semantic_retrieve` — `video_order` 提供時 `get_chunks_by_video_order` 被呼叫、`retrieve_chunks` 不被呼叫；TRANSCRIPT header + chunk 內文進 user prompt
  - `test_grounded_mode_injects_grounding_rules_into_system_prompt` — system prompt 含「Grounding 規則」+「嚴禁發明字幕未提到的程式碼」
  - `test_non_grounded_mode_preserves_legacy_path` — `video_order=None` 走 `retrieve_chunks`、prompt 不含 grounding 規則（backward compat）
  - `test_grounded_retrieve_failure_does_not_block_generation` — `get_chunks_by_video_order` 拋例外仍能出題（fallback 空 chunks）

### Changed
- **`backend/services/quiz/generate.py:generate_question`** 簽名加 `video_order: int | None = None`；提供時 grounded mode（不需改 orchestrator / API；學生現生題路徑不變）
- **`backend/services/quiz/generate.py:_build_system_prompt`** 加 `grounded: bool` 參數，true 時 append `_GROUNDING_RULES`
- **`backend/services/quiz/generate.py:_build_user_prompt`** 加 `grounded: bool` 參數，true 時 user header 改為「以下 TRANSCRIPT 為教授實際 YouTube 影片字幕（依時間順序）」
- **`backend/tests/test_quiz_generate.py:patched_llm`** 擴充：同時 patch `retrieve_chunks` + `get_chunks_by_video_order`；`yield` 回 3 個 mock 供新測試 assert 呼叫行為
- **`docs/roadmap.md`** 6-3a 拆 3 子項：6-3a-1（程式碼，本次完成 ✅）/ 6-3a-2（批次 script，next）/ 6-3a-3（實機跑，延 6-4）

### Tests
- 後端 480 tests 全綠（pytest -q 9.23s）

### Health metrics
- `generate.py` 221 → 248 行（< 250 ⚠ 門檻；曾觸頂 268 行，主動壓縮 docstring + 縮短 grounding rules 字串後回到健康水位）
- `test_quiz_generate.py` 250 → 359 行（測試檔，無 ⚠ 強制門檻；逐塊獨立可讀）

### Deferred（已錨定）
- 6-3a-2 批次 script + 6-3a-3 實機跑：roadmap 6-3 子項已標
- 學生現生題 backward compat：本次未動 `orchestrator.generate_for_student`，學生路徑仍走 semantic RAG；待 6-3b 改造 ExercisesTab 時再決定是否切到題庫優先

---

## [2026-05-22] — Phase 6-2e 程式碼完成：摘要 tab 渲染 grounded key_points + citation 標籤（fallback 已驗證 / grounded 狀態延至 6-4 驗收）

### Verified (2026-05-22 透過 `npx tsc --noEmit` + `npx eslint`)
- TypeScript / ESLint 全綠；既有 lazy-seed empty 形狀仍顯示「重點摘要尚未匯入」placeholder（與 6-2c/d 行為一致）
- grounded 主路徑（`needs_more_source` notice / key_points bullet + citations）：**因 DB 尚無任何 promoted `summary` object 形狀**，延至 Phase 6-4a-deferred-ui 合併驗收

### Added
- **`web/components/learn/summary-tab.tsx`** (約 115 行)：grounded summary 渲染元件
  - 四段狀態：grounded 且 `needs_more_source=true` → reason notice；grounded 且 `key_points` 非空 → bullet list + citation 列表；舊 `summary: string` → legacy fallback；都沒有 → empty placeholder
  - citation 採靜態時間戳 + 節錄文字（不嵌 YT player，提示使用者回概念 tab 點 citation）

### Changed
- **`web/lib/learning.ts`**：新增 `SummaryContent` 介面（與後端 `content_generator.py:Summary` 對齊：`needs_more_source` / `reason` / `key_points` / `citations`）；`UnitContent.summary` 由 `string` 擴為 `string | SummaryContent`，相容舊 lazy seed 與 promote 後形狀
- **`web/components/learn/unit-content.tsx`**：移除 inline `SummaryTab` + `EmptyTab`（共 19 行），改 import `SummaryTab` from `./summary-tab`；保持 ≤ 150 行健康水位
- **`docs/roadmap.md`**：勾選 6-2e；6-4a-deferred-ui 子項「**6-2e grounded path**」補完內容說明（驗收 needs_more_source notice + key_points bullet 渲染）

### Tests
- 後端無新增測試（API 與 schema 未動）；後端 476 tests 全綠
- 前端 TypeScript check 通過 (`npx tsc --noEmit` exit 0) + ESLint 通過

### Health metrics
- `summary-tab.tsx` 約 115 行（< 150 ⚠ 門檻）；`unit-content.tsx` 154 行（仍超 ≤150 警戒線少許，與 6-2d 完成時同水位，本任務未惡化）
- `learning.ts` 新增 7 行 interface + 1 行 union 擴充，未跨 ⚠ 門檻

---

## [2026-05-22] — Phase 6-2d 程式碼完成：範例 tab 渲染 grounded code + 「在 Workspace 開啟」轉場（fallback 已驗證 / 卡片狀態延至 6-4 驗收）

### Verified (2026-05-22)
- 使用者於 Unit 1「什麼是程式語言」範例 tab 看到「程式範例尚未匯入」placeholder — fallback 分支運作正確
- 卡片列表（grounded code_examples）+ 「在 Workspace 開啟」轉場 + 一次性消費 sessionStorage：**因 DB 尚無任何 promoted `code_examples` JSON 而無法本次驗收**；延至 Phase 6-4 教授抽查 + 實機 LLM 批次跑完後合併驗收

### Deferred verification anchored at 3 places (避免被遺忘)
- `docs/roadmap.md` — 6-4a 下新增 `6-4a-deferred-ui` 子 checkbox，明列 6-2c / 6-2d 待補驗的 grounded 主路徑（含 sessionStorage 一次性消費關鍵驗收步驟）
- `docs/tech-debt.md` — 新增「延遲驗收（Phase 6-2 → 6-4 必跑）」段，含失敗排查指引（`pending-workspace-code.ts` removeItem / `workspace/page.tsx` useState lazy initializer）
- `CLAUDE.md` 當前狀態 — 6-2c / 6-2d 標記改為「✅程式碼完成 + fallback 已驗」，下一步段強調「6-4a-deferred-ui 必跑」

### Added
- **`web/components/learn/examples-tab.tsx`** (147 行)：grounded code examples 渲染元件
  - 四段狀態：`needs_more_source=true` → reason notice；有 grounded examples → 卡片列表；舊形狀 `examples: string[]` → legacy fallback；都沒有 → empty placeholder
  - `ExampleCard`：title + code block（mono / bg-inset）+ explanation + optional citation 標籤 + 「在 Workspace 開啟」按鈕
  - citation 採靜態時間戳 + 節錄文字（不嵌 YT player，避免每 tab 各跑一個 IFrame）；要跳影片時間請回概念 tab 點 citation
- **`web/lib/pending-workspace-code.ts`** (53 行)：sessionStorage helper for 跨頁攜帶程式碼
  - `setPendingWorkspaceCode(code)` / `consumePendingWorkspaceCode()`（讀完即清，避免下次重整誤覆蓋）
  - 復用 `active-reflection.ts` pattern（CustomEvent 同 tab 通知 + SSR safe try/catch）

### Changed
- **`web/lib/learning.ts`**：新增 `CodeExample` / `CodeExamples` 介面（與後端 `content_generator.py:CodeExample/CodeExamples` 對齊）；`UnitContent` 加 optional `code_examples?: CodeExamples`
- **`web/components/learn/unit-content.tsx`**：移除 inline `ExamplesTab`（17 行），改 import `ExamplesTab` from `./examples-tab`；檔案 188→173 行（更接近 ≤ 150 健康水位）
- **`web/app/(app)/workspace/page.tsx`**：mount 時用 `useState` lazy initializer 消費 `consumePendingWorkspaceCode()`，作為 `<CodeEditor initialValue={...}>` 一次性 prop；後續 re-render 不重複 consume

### Tests
- 後端無新增測試（API 與 schema 未動）；後端 476 tests 全綠
- 前端 TypeScript check 通過 (`npx tsc --noEmit` exit 0)
- 前端無 component test 基建（沿用 Phase 1-6 既定策略：UI 由使用者驗證）

### Why
6-2d 為 NotebookLM grounded 模式的「程式範例 tab」前端呈現：完成此 task 後使用者進入單元頁範例 tab 即可看到 LLM 從字幕生成的 1-3 個 C++ 程式範例 + 一鍵「在 Workspace 開啟」即時上手實驗。citation 與概念 tab 結構一致，讓學生能回溯字幕出處。配合 6-2c 概念 tab + 後續 6-2e 摘要 tab，三段 grounded 內容呈現基線完成。

### How to verify (使用者待測)
1. 前端 dev 環境（`npm run dev`）登入 → 進 Learn 頁 → 點開任一單元 → 切到「範例程式」tab
2. 若該單元 `learning_units.content.code_examples` 已有 promoted 資料：
   - 應顯示卡片列表，每張卡片含標題 + 程式碼 + 說明 + 出處（時間戳+節錄）+ 「在 Workspace 開啟」按鈕
3. 點任一範例的「在 Workspace 開啟」→ 路由跳 `/workspace` → 編輯器應載入該範例程式碼（取代 default Hello World）
4. 在 Workspace 內手動 navigate 回去再進來，編輯器應**不會**再次被該範例覆蓋（一次性消費）
5. 若該單元尚未 promoted（多數 unit 目前如此）：應顯示 empty placeholder 或舊形狀 fallback

## [2026-05-22] — Quiz cold-start fallback robust 補強（V2 cpp-XX schema 兼容）

### Changed
- **`backend/services/quiz/orchestrator.py:_pick_target_concept`** 改為兩段 fallback：
  1. 先查 `COLD_START_FALLBACK_TAG`（V1 schema 兼容；測試環境直接 seed 此 tag 仍可用）
  2. 若無，動態查 `difficulty_level` ASC + `video_order` ASC 取最低難度且最前序 concept
  3. 兩段都失敗才回 503 `QUIZ_UNAVAILABLE`

### Tests
- **`backend/tests/test_quiz_route.py:test_generate_cold_start_dynamic_fallback_when_no_legacy_tag`** 新增：seed `cpp-04-first-program`（difficulty=1, video_order=1）+ `cpp-05-syntax`（difficulty=1, video_order=2）+ `cpp-25-if-else`（difficulty=2）；不含 `syntax-basic` legacy tag；驗證 cold-start 取到 `cpp-04-first-program`
- 後端 476 tests 全綠

### Why
V1 cold-start 仰賴固定 tag `syntax-basic`，但 V2 cpp-XX 章節制 seed（62 部影片 concept）不含此 tag；無弱項 + 無 legacy tag 時 prod 會直接回 503。動態 fallback 讓部署初期（沒有任何 mastery 紀錄）的學生也能正常觸發出題。

## [2026-05-22] — Phase 6-2c 使用者驗證通過（YT 播放 + citation 跳轉 + grounded markdown 渲染正常）

### Verified
- 使用者於本機 dev 環境登入 → 進 Learn 頁 → 點開已 PATCH `video_youtube_id` 的單元，確認：
  - YT IFrame player 載入並可播放
  - grounded markdown 內容正確渲染（react-markdown + remark-gfm）
  - citation 列表點擊可呼叫 `player.seekTo` 跳到對應 timestamp
- 6-2c 正式 close；`docs/roadmap.md` 該行勾選 `[x]`；`CLAUDE.md` 當前狀態更新「下一步：6-2d 範例 tab」

### Next
- 6-2d 範例 tab：渲染 LLM 生成的程式碼範例 + 「在 Workspace 開啟」按鈕（復用 Phase 2-5d sessionStorage）+ citation 標示

## [2026-05-22] — 設計反轉：video_order 1-3（課程介紹）加回學習路徑

### Changed
- **新 alembic migration `h4c5d6e7f8a9_seed_intro_video_prerequisites.py`**：補 3 條 PREREQUISITE 邊
  - `cpp-01-language-intro` → `cpp-02-cpp-overview`
  - `cpp-02-cpp-overview` → `cpp-03-devcpp-install`
  - `cpp-03-devcpp-install` → `cpp-04-first-program`
  - 完整鏈：1→2→3→4→...→62（共 61 條 prerequisite 邊）
- **`backend/services/learning/generator.py`**：移除 `EXCLUDED_FROM_PATH_CATEGORIES` 常數與 `notin_` 過濾條件；`_fetch_concepts` 改為純 `select(Concept)` + optional category filter
- **`backend/services/learning/batch_generator.py`**：移除 EXCLUDED 過濾；`list_target_concepts` 改為只過濾 `video_order IS NULL`；docstring 更新「涵蓋全部 62 部（含 1-3）」
- **保留 `category="課程介紹"` 不變**：未來知識圖譜頁可用此 category 做 styling 區分（不再做路徑過濾用途）
- **`docs/roadmap.md`**：6-1c 條目 + 「已確認決策」段 1-3 處理方式 + Phase 6 開頭「Concept 範圍」說明 — 三處同步修訂

### Tests
- **`backend/tests/test_learning_generator.py`**：
  - `test_intro_category_concepts_excluded_from_path` → `test_intro_category_concepts_included_in_path`（assert 三筆 concept 全部進路徑）
  - `test_all_intro_category_raises_422` → `test_path_with_only_intro_category_still_succeeds`（assert 不再拋 422，能正常生成）
- **`backend/tests/test_batch_generator.py:test_list_target_concepts_filters_intro_and_no_video_order`** → `test_list_target_concepts_includes_intro_filters_no_video_order`（assert 課程介紹也會被批次生成）
- alembic upgrade head 套用成功；後端 476 tests 全綠

### Why
原 6-1c 把 1-3 列為「選看」類不進路徑；2026-05-22 使用者決定 1-3 教學內容（語言介紹 / C++ 概述 / DevC++ 安裝環境）對線性學習路徑而言是必要前置，應強制要學。加 PREREQUISITE 邊比「移除 filter 讓 1-3 與 4 並列 in_degree=0」更穩定，保證路徑順序固定為 1,2,3,4,...,62。

### Migration
本機 dev 環境：`cd backend && alembic upgrade head`
部署環境（Phase 7）：deployment 流程自動跑 `alembic upgrade head`，無額外動作

## [2026-05-22] — Phase 6-2c 程式碼完成：概念說明 tab 嵌入 YT IFrame player + grounded markdown + citation 跳轉（待使用者 UI 驗證）

### Added
- **`web/components/learn/youtube-player.tsx`** (142 行)：YT IFrame Player API wrapper
  - lazy load `https://www.youtube.com/iframe_api`（全域 script 只 inject 一次，多 player 共用）
  - `forwardRef` + `useImperativeHandle` 暴露 `seekTo(seconds)`；player 尚未 ready 時暫存待 `onReady` 補跳
  - `videoId` 變更時 `cueVideoById` 重置（換單元不重建 iframe）
  - 元件卸載時 `destroy()` 防 leak
- **`web/components/learn/concept-tab.tsx`** (229 行)：grounded 內容渲染元件
  - 三段狀態：無 youtube_id → placeholder；有影片無 grounded → player + 簡介；完整 → player + Markdown + citation 列表
  - `ReactMarkdown` + `remarkGfm` 渲染 LLM 生成的 `concept_explanation.markdown`；自訂 12 個 element class（無 `@tailwindcss/typography` 仍維持可讀性）
  - `parseTimestampStart()` 解析 `mm:ss` / `mm:ss-mm:ss` / `hh:mm:ss` → 秒數；citation 列表按鈕點擊呼叫 `player.seekTo`
- **`web/components/learn/unit-action-bar.tsx`** (85 行)：從 unit-content.tsx 拆出 NavButton + ActionButton（讓 unit-content.tsx 降至 191 行 < 250 行硬上限）

### Changed
- **後端 `backend/api/routes/learning.py:UnitOut`** 新增 `video_youtube_id: str | None` / `video_duration_seconds: int | None`，由 concept JOIN 帶出
- **後端 `backend/services/learning/queries.py:UnitWithConcept`** dataclass 同步擴充兩欄
- **前端 `web/lib/learning.ts`**：`Unit` 加 `video_youtube_id` / `video_duration_seconds`；`UnitContent` 加 optional `concept_explanation`（grounded 形狀，含 markdown + citations）；新增 `Citation` / `ConceptExplanation` 介面
- **前端 `web/components/learn/unit-content.tsx`**：原 inline `ConceptTab` + `VideoPlayerPlaceholder` 移除，改 import `ConceptTab`；NavButton + ActionButton 改 import 自 unit-action-bar
- **新增 npm 套件**：`react-markdown@^10.1.0` + `remark-gfm@^4.0.1`

### Tests
- **`backend/tests/test_learning_route.py:test_get_path_returns_units_in_order`** 補斷言 `video_youtube_id` / `video_duration_seconds` 直通 UnitOut；`_seed_concepts` helper 容許 spec 帶這兩欄
- 後端 476 tests 全綠（無新增測試檔；既有 route 測試擴充即可覆蓋 6-2c 新欄位）

### Why
6-2c 為 NotebookLM grounded 模式的「概念說明 tab」前端呈現：完成此 task 後使用者進入單元頁即可看到實際 YT 影片 + LLM grounded markdown + citation timestamp 跳轉，達成「LLM 生成內容必須引用 transcript 出處 + 學生可立即比對影片真實時間點」的設計目標。6-2b 已完成批次生成 + promote helper，配合本任務後即可端到端跑通 grounded 內容生成 → 前端呈現。

### How to verify (使用者待測)
1. 前端 dev 環境（`npm run dev`）登入 → 進 Learn 頁 → 點任一已 PATCH `video_youtube_id` 的單元（video_order 4-62）
2. 確認概念說明 tab 顯示 YT player 並可播放
3. 若該 unit `content.concept_explanation` 有資料 → 應顯示 markdown + citation 列表；點 citation 按鈕應跳轉至對應時間點
4. 若 unit 仍是空 content → 應顯示 player + 「概念簡介」fallback 文字

## [2026-05-13] — chore(web): middleware → proxy 遷移（Next.js 16 deprecation）

### Changed
- **`web/middleware.ts` → `web/proxy.ts`**：Next.js 16 將 `middleware` 檔案規範改名為 `proxy`，原檔仍可運作但會發 deprecation warning。export 從 `auth as middleware` 改為 `auth as proxy`，`config.matcher` 規格不變。

### Why
`npm run dev` 出現 deprecation 警告 `The "middleware" file convention is deprecated. Please use "proxy" instead.`。Next.js 官方理由：避免與 Express middleware 概念混淆，且明確標示其位於 Edge Runtime 上的 proxy 性質。

## [2026-05-13] — docs: dev-setup.md 新增 Windows (PowerShell) 啟動章節

### Added
- **`docs/dev-setup.md` §1B**：Windows 對應啟動流程
  - 最小啟動（DB + Redis）/ 完整開發（後端 + 前端三 terminal）/ 收工關閉 三段 PowerShell 指令
  - Windows 與 macOS 對照表（路徑、Docker daemon、venv 啟動、shell 語法）
  - 標註 Windows 路徑為 `C:\Users\hao\Desktop\Projects\...`（複數 Projects），與 macOS `Project`（單數）不同
- **`docs/dev-setup.md` §1**：標題加註 `(macOS / 已裝完工具)` + 開頭指引「Windows 環境見 §1B」

### Why
原 §1 僅 macOS / Colima 流程；Windows 環境 session 啟動時無對應指引。

## [2026-05-08] — Phase 6-2b 程式碼完成：grounded 批次生成 + staging table + retry + promote helper（待使用者實機驗證）

### Added
- **`backend/services/rag/retrieve.py`** 擴充：新 `get_chunks_by_video_order(video_order)` 直接 SQL 查 `data_codedge_rag.metadata_->>'video_order'`，依 `start_time_seconds` 排序回傳該 video 完整字幕 chunks（非語意 top-k，避免跨 video 污染與順序錯亂）
- **`backend/services/learning/batch_generator.py`** (251 行)：批次生成核心
  - `generate_for_concept(db, concept) -> GenerationResult`：retrieve → generate_unit_content → UPSERT staging
  - `_generate_with_retry`：transient 錯誤（LLM_UNAVAILABLE / LLM_PARSE_ERROR）退避重試 max 3 次；非 transient 直接拋
  - `_aggregate_needs_more_source` / `_flatten_notes`：3 section 任一 flag → row 標 True；reasons 串接成 `notes` 給 6-4 抽查介面用
  - `list_target_concepts`：自動過濾 `EXCLUDED_FROM_PATH_CATEGORIES=("課程介紹",)` + 缺 `video_order` 的 concept
  - `generate_all(db, only=None, skip_existing=True)`：批次入口；預設跳過已 approved 的 concept 避免覆蓋審查通過內容
  - SELECT-then-INSERT/UPDATE 取代 PG dialect on_conflict（保持 SQLite 測試相容）
- **`backend/services/learning/unit_content_promote.py`** (58 行)：6-4 抽查通過後 `promote_concept(db, concept_id) -> int` 把 staging.content 寫入該 concept 對應的所有 `learning_units.content`；強制 status='approved' 才執行
- **`backend/alembic/versions/g3b4c5d6e7f8_create_unit_content_staging.py`**：staging 表 migration
  - schema：concept_id UNIQUE / content JSON / status CHECK ('pending', 'approved', 'rejected') / needs_more_source / notes / attempt_count / model_used / generated_at / reviewed_at
  - 雙索引：status / needs_more_source（給 6-4 抽查介面 filter）
- **`backend/models/unit_content_staging.py`**：對應 ORM + `StagingStatus` enum
- **`backend/scripts/generate_unit_content.py`** (90 行) CLI：`--only N` / `--force` / `--dry-run`；摘要列印 success / skipped / needs_more_source / failed
- **`backend/tests/test_batch_generator.py`** (~330 行)：18 個新測試
  - pure helpers ×3（aggregate / flatten_notes 兩種情境）
  - retry 機制 ×3（second-attempt 成功 / 連 max retries / 非 retryable 立即拋）
  - generate_for_concept ×4（成功寫 staging / 失敗不寫 / 缺 video_order 422 / partial needs_more 聚合）
  - UPSERT ×1（重生時 reset reviewed_at + status）
  - list_target_concepts / generate_all ×4（過濾 / only filter / skip approved / force regenerate）
  - promote_concept ×3（成功 / pending 422 / 缺 row 404）
- 全套 backend 從 458 → **476 tests 全綠**

### Design 亮點
- **per-concept 不 per-unit**：1 concept N user units 共用 grounded content；staging 用 `concept_id UNIQUE`，promote 時一次更新所有相關 units
- **needs_more_source vs retry 互斥**：retry 處理「LLM 失敗」（網路 / parse），needs_more_source 處理「資料不足」（字幕短 / 偏題）
- **vendor-neutral upsert**：避開 PG dialect `on_conflict_do_update`，用 SELECT-then-INSERT/UPDATE 維持 SQLite 測試相容；UNIQUE(concept_id) 仍由 schema 強制
- **promote 與 generate 拆檔**：6-4 觸發的後段流程獨立，不與 batch generation 耦合；保持單一檔案 ≤ 250 行硬限

### Sync
- migration `g3b4c5d6e7f8` 已 apply 至 dev DB
- `data_codedge_rag` retrieve 對齊 6-1e ingest 時寫入的 `video_order` / `start_time_seconds` metadata
- dry-run 驗證：59 concept(s) would be processed（v04-v62），課程介紹 v01-v03 自動排除

### 待使用者驗證
- ⏳ 實際批次跑 1 部影片（建議 `--only 47` 遞迴）驗證 LLM 生成品質 + staging 寫入
- ⏳ 全 59 部批次跑（成本估 $5-10 USD）後檢查 needs_more_source 比例

### Why
6-2a 完成 prompt + 模型驗證後，6-2b 把它接到實際 RAG infrastructure：對每 concept 用 video_order metadata filter retrieve 該影片字幕 → call generate_unit_content → 落到 staging 供 6-4 教授抽查。staging 表設計為 1 concept 1 row（不依賴用戶），審查通過後 promote 一次更新所有用戶的對應 unit。

---

## [2026-05-08] — Phase 6-2a 完成：grounded prompt template + Pydantic 模型 + 13 mock-LLM 測試

### Added
- **`backend/services/learning/content_generator.py`** (235 行)：3 個 section 生成 function
  - `generate_concept_explanation` / `generate_code_examples` / `generate_summary`：各自獨立呼叫 LLM，回傳對應 Pydantic 模型
  - `generate_unit_content`：orchestrator，依序呼叫 3 個 section
  - `_call_llm_json` 共用 helper：OpenAI `json_object` mode + temperature 0.3 + Pydantic validate + 503/502 分層錯誤
- **Pydantic 輸出模型** 6 個：`Citation` / `ConceptExplanation` / `CodeExample` / `CodeExamples` / `Summary` / `UnitContent`，皆內建 `needs_more_source` + `reason` 欄位作為 graceful degradation
- **`tests/test_content_generator.py`** (~250 行)：13 個 mock-LLM 單元測試
  - 成功路徑 ×3（3 種 section 各自正確解析）
  - needs_more_source 路徑 ×2（transcript 不足時 LLM 回 true，content 留空）
  - 失敗路徑 ×3（503 LLM_UNAVAILABLE / 502 invalid JSON / 502 schema 違反）
  - Grounding 機制 ×3（context_block 真的注入 chunks / 空 chunks 自動引導 / chunks 確實傳到 LLM）
  - Orchestrator ×1（generate_unit_content 確實呼叫 3 次）
  - Pydantic 驗證 ×1（Citation excerpt 字數上限）

### Design 亮點
- **Grounding 雙重把關**：prompt 5 條絕對規則 + Pydantic 嚴格 schema；LLM 回 hallucinate 直接被 502 攔下
- **needs_more_source 機制**：每個 section 獨立判斷（concept ok 但 examples 沒料 → 只 examples needs_more）；不全有全無
- **citation 嵌入 markdown**：LLM 在 markdown 中內嵌 `[mm:ss]`，前端顯示時可解析為跳轉連結
- **caller 解耦**：generate function 只接 pre-fetched chunks，不自己呼叫 retrieve；6-2b 才負責 video_order metadata filter

### Sync
- `docs/roadmap.md` Phase 6-2a 標 [x] 並寫入完成細節
- `CLAUDE.md` 進度更新

### Why
依 Phase 6 NotebookLM 模式設計（2026-05-07 確認），LLM 生成 unit content 必須 grounded 在 Whisper transcript 上、禁止 hallucinate。本次完成的是 prompt 設計 + 模型 + 測試的「設計與驗證」階段；6-2b 將實際呼叫此 service 為 62 個 unit 批次生成 content。

---

## [2026-05-08] — Phase 6-1e 完成：Whisper 全 62 部 transcript + 二次審核 + 861 chunks 入 RAG（NotebookLM 核心就緒）

### Why A 方案改 B1
原計畫 A（yt-dlp 抓 zh-Hant 自動字幕）**徹底失敗**——6/6 樣本影片皆 "no automatic captions, no subtitles"（教授頻道未開或 YT 未生成）。改採 B1（OpenAI Whisper API），實測品質高（教授名「黃國豪」抓對；C++/devc++/Cout 等術語多數正確），唯一系統性錯辨「黃國昊」（同音字 hào），由二次審核 corrections.json 全域替換解決。

### Added — 4 個 script + 配置 + 資料
- **`backend/scripts/transcribe_videos.py`** (~190 lines)：yt-dlp 抓 audio + OpenAI `whisper-1` API；idempotent（skip 已存 transcripts）+ 成本上限保護（COST_CAP_USD=5）+ prompt 注入 title_zh 提升技術術語準度
- **`backend/scripts/apply_corrections.py`** (~120 lines)：corrections.json 兩層替換（global + per_video segment-id）→ transcripts_corrected/；保留 raw 不動
- **`backend/scripts/flag_transcripts.py`** (~140 lines)：GPT-4o-mini 自動掃可疑段落（type=term/semantic/repetition + confidence 0-1）→ issues_proposal.json；不誤報優於不漏報
- **`backend/scripts/ingest_transcripts_rag.py`** (~180 lines)：60 秒時間視窗分組 → LlamaIndex Document（text 含 `[mm:ss]` timestamp markers）→ pipeline.arun → 寫入 data_codedge_rag；--reset 旗標可砍重來
- **`data/teaching_content/corrections.json`**：12 條 global_replacements + per_video（目前空，留給 6-4 教授抽查補）
- **`data/teaching_content/transcripts/`**：62 個 raw Whisper JSON（3.4 MB）
- **`data/teaching_content/transcripts_corrected/`**：62 個套用 corrections 後的 JSON
- **`data/teaching_content/issues_proposal.json`**：209 個 LLM-flagged issues 的完整審核清單（68 KB）

### Results
- **Whisper batch**：62/62 全成功；總時長 7.2 hr → 成本 $2.621 USD
- **Flag scan**：209 issues（term ×152 / semantic ×48 / repetition ×9）；高 confidence ≥0.9 共 41 個
- **採納修正**：12 條 global（黃國昊×31, Double×17, Cout×8, 黃國華×8, ioString×3, Void×2, iostring×1, WCHART×1, objective oriented×1 + 預防性 IOStream / objective-oriented）；per_video 0 條（保留給 6-4 教授抽查）
- **RAG 入庫**：62 documents 行 + **861 chunks** 寫入 data_codedge_rag；每 chunk metadata 含 video_order / youtube_id / title_zh / start_time_seconds / end_time_seconds / source_type
- **Spot retrieve 驗證**：4/4 query 命中 expected video（遞迴→v47 / 指標→v51 / 物件導向→v59 / 階乘→top-3 含 v47）
- 總成本 6-1e: ~$2.69（Whisper $2.621 + Flag $0.07 + Embeddings $0.002）

### 設計亮點
- **不破壞原始**：raw transcripts 永不修改；錯誤定位 + 重跑 apply 都很方便；可重複迭代 corrections
- **Timestamp markers 嵌入 chunk text**：LLM 在 6-2 生成時可直接抽出 `[mm:ss]` 做 citation，不用查 metadata（雖然 metadata 也保留 start/end_time_seconds）
- **二次審核機制**：global 解決系統性錯誤（一條 fix 多影片）；per_video 留給 6-4 抽查階段針對性修
- **Reset & re-ingest 高效**：發現「黃國華」漏網後，加 1 條 global → re-apply → --reset + re-ingest 全程 < 2 min

### Sync
- `docs/roadmap.md` Phase 6-1e/f 標 [x] 並寫入完成細節
- `CLAUDE.md` 進度更新：6-1 整節完成
- `.gitignore` 新增 `data/teaching_content/audio_cache/` 排除（transient）

---

## [2026-05-07] — Phase 6 升級為 NotebookLM grounded 模式 + 6-1a/b 完成

### Changed（roadmap Phase 6 大幅細化）
- **採 NotebookLM grounded 模式**（核心架構決策）：所有 LLM 生成的 unit content / 練習題必須 grounded 在教授實際 YT 影片字幕上，禁止 LLM 自由發揮。Source = YT 自動字幕（A 方案，零成本，`yt-dlp --write-auto-subs`），品質不夠的 unit 在 6-4 抽查階段評估升級到 Whisper 重 transcribe（B 方案）
- **Concept 範圍 59 → 62**：video_order 1-3（課程簡介、環境安裝、語言簡介）加回為 concept；標記 `category="課程介紹"` **不參與 PREREQUISITE 鏈**（learning_path generator 過濾此 category，知識圖譜頁仍顯示但 styling 區分）
- **Phase 6-1 拆細**（原 6-1a/b/c → 6-1a~6-1f 共 6 子任務）：
  - 6-1a 教授交付 playlist URL ✅（2026-05-07 完成，`PLJDZAE4d-ihqvGtBMhgMv8Zp6Tv6D1l-M`，62 部影片完整對齊）
  - 6-1b fetcher script 已寫 + 產 59 列 CSV ✅（`backend/scripts/fetch_playlist_metadata.py`；title_zh 與 DB name_zh 59/59 完全一致）
  - 6-1b+ 待擴充 fetcher EXPECTED 1-62 + 重產 62 列 CSV
  - 6-1c 待加 video 1-3 concept seed migration
  - 6-1d 待開發 PATCH script + 執行寫入 DB
  - 6-1e 待開發字幕 RAG ingest（NotebookLM 核心）
  - 6-1f 待同步 tech-debt
- **Phase 6-2/6-3 升級為 grounded 版本**：prompt template 強制引用 transcript chunks + timestamp citation；禁止引入字幕未出現的概念；不足以生成時回 `needs_more_source=true` 而非 hallucinate

### Added
- `backend/scripts/fetch_playlist_metadata.py`（156 行，yt-dlp wrapper，含對齊驗證 + 缺漏報告）
- `data/teaching_content/videos.csv`（59 列；待擴充 62 列）
- `已確認決策` 加 3 條：NotebookLM 模式、62 個 concept 範圍、知識圖譜重構為後續工作
- `tech-debt.md` 新增「video 1-3 不參與 PREREQUISITE」設計註記
- 系統工具：`brew install yt-dlp`（2026.03.17）

### Why
原 Phase 6-2 計畫只注入「concept 名稱 + 影片標題」給 LLM，會生成「對 C++ 通用課程合理但未必對齊本課程教法」的內容（hallucination 風險）。使用者明確要求採 NotebookLM 模式（grounded on user-provided sources），確保 unit content 真實反映教授實際教法。同時將過去因「DB 04-62 而忽略 1-3」的限制解除，補齊 62 個影片完整對應。

---

## [2026-05-07] — Roadmap 新增 Phase 6 教學內容建構，原上線實測順延 Phase 7

### Added
- **`docs/roadmap.md` 新增 Phase 6：教學內容建構**（4 節 12 子任務，本機可完成 / 部分依賴教授交付資料）
  - **6-1 影片 metadata 整合**：6-1a 教授交付 metadata / 6-1b PATCH script / 6-1c 執行+驗證
  - **6-2 Unit content 批次生成**：6-2a prompt template / 6-2b LLM 批次寫入 / 6-2c 概念說明 YT player / 6-2d 範例 tab / 6-2e 摘要 tab
  - **6-3 練習題庫補充**：6-3a Phase 2-4 batch 模式生成 / 6-3b ExercisesTab 改為優先讀題庫
  - **6-4 內容品管**：6-4a 教授抽查 / 6-4b 修正 prompt 重跑

### Changed
- **原 Phase 6 上線實測 → Phase 7**：6-1/6-2/6-3 整段順延為 7-1/7-2/7-3，所有子任務同步重編號（cross-ref 註解保留歷史軌跡：原 4-3a → 6-1 → 7-1）
- **Phase 5 ⇄ Phase 6 平行關係**：執行策略 / 已確認決策最後一條同步調整為「兩者可平行 / 先後皆可，依教授資料準備進度而定」
- **Phase 7 前置條件加強**：除原 Zeabur + VPS 就緒外，新增「Phase 6 至少 6-1 + 6-2b 完成」（避免部署後 Learn 頁面仍空殼）

### Synced
- `CLAUDE.md` 當前狀態：呈現 Phase 5 ⇄ Phase 6 平行 + Phase 7 收尾的三段結構
- `docs/tech-debt.md` 兩條教學內容相關項目加 cross-ref 至 Phase 6-1 / 6-2~6-4（原內容保留作為背景說明）

### Why
使用者反映「整合教材」未進 roadmap 追蹤；目前只有 tech-debt + 內聯註釋，容易被忘。同時使用者明確指出「教師端 / 教學內容看實際狀況」決定先後，故將 Phase 5 與 Phase 6 設計為可平行關係，避免硬性綁定誰先誰後。

---

## [2026-05-07] — Roadmap 重整 follow-up：修正其他 doc 殘留舊 Phase 標號

### Fixed
- **`docs/design-plan.md` §4.5**：`1-7c 上線驗證` → `Phase 6 上線實測（原 1-7c → 4-3a → 6-1b Golden path）`，保留歷史演進 cross-reference
- **`docs/modules.md` Module 8 / 9**：Phase 4 → **Phase 5**（教師 Dashboard / 學習行為分析屬教師端，非部署）
- **`docs/db-schema.md` chat_messages 擴充欄位註記**：Phase 4-2c → **Phase 5-2c**（dialogue_act 屬行為資料收集，原本就在 5-2c，4-2c 為誤標）
- **`docs/roadmap.md` Phase 1 結尾註記**：「部署原 1-7 已移至 Phase 4」補完為「Phase 4（容器化 / 配置層）+ Phase 6（上線實測）」反映當前兩段切分

### Verified clean（未動）
- `docs/changelog.md` 歷史 entry（line 1670 / 1897 / 1898 / 2221）：屬當時決策的歷史記錄，保留原貌不改
- `docs/dev-setup.md` Phase 4-1b 引用：4-1b 仍在 Phase 4，無誤
- `docs/references.md` Phase 4 / 5-1 / 5-2 / 5-3 引用：全部與重整後結構一致

---

## [2026-05-07] — Roadmap 重整：上線實測類任務集中至 Phase 6

### Changed
- **`docs/roadmap.md` 結構調整**：將「需要實際部署到 Zeabur / VPS 才能驗證」的工作集中到新的 **Phase 6 上線實測**
  - 原 `Phase 4-3 上線驗證`（4-3a/b/c）整段移至 Phase 6
  - 4-3a Golden path → **6-1**（拆成 6-1a 部署 / 6-1b Golden path / 6-1c 教師端 e2e 三步驟）
  - 4-3b 監控 → **6-2**（拆出 6-2a/b/c 程式碼可本機完成 + 6-2d 須實際部署驗證告警鏈路）
  - 4-3c 效能 baseline → **6-3**（拆成 6-3a TTFB/LCP / 6-3b LLM p95 / 6-3c Judge0 / 6-3d 寫入 baseline 文件）
- **Phase 4 改名**：「部署上線」→「部署準備（容器化 + 配置層，本機可完成）」標記 ✅，明確區分本機可完成與須實際部署
- **Phase 5 前置條件放寬**：原「Phase 4 部署完成」→「Phase 4 配置層完成」，加註資料策略：5-1/5-2/5-5 純本機可完成；5-3/5-4 程式碼可先用合成資料寫，部署後以實測資料調校
- **執行策略 / 已確認決策**：頂部與底部同步更新為 Phase 2→3→4→5→6 新順序

### Synced
- `CLAUDE.md` 當前狀態區塊：Phase 4 標記為 ✅（容器化+配置層），下一階段呈現「Phase 5（本機可開發）vs Phase 6（須部署）」二選一供使用者選

### Why
使用者明確表示「還沒準備好部署」，但 Phase 4-3 包在 Phase 4 中容易給人「部署是當前阻塞」的錯覺。重整後，Phase 5 教師端（不需部署）就可獨立推進，Phase 6 維持為部署完成後一次驗收，避免邊開發邊維運耗能。

---

## [2026-05-06] — `from X import Y` 對 mutable global 的 binding 陷阱

`health.py` 寫 `from core.redis import redis_client`，import 當下抓到的是 `None`
（`init_redis()` 啟動時才 set global），之後 lifespan 設好的 client 不會反映到這個
reference → `/health` **永遠回 `redis: disconnected`**，即使 Redis 正常。

**規則**：module 層級的 mutable global 一律 `import X` 後用 `X.Y`，或包 getter 函式；
只有不變的常數與型別才能直接 `from X import Y`。

**為什麼 442 個測試沒抓到**：`test_health.py` 用 fixture 把 `redis_client` mock 掉了，
從沒實測「lifespan 啟動 → ping」整條鏈路。其他端點都走 `get_redis()`（每次 lookup
當前 global）所以正常——只有 health.py 自己誤報。

## [2026-05-05] — Phase 4 部署配置：環境分層與 Zeabur 適配

**三套環境配置各自獨立**（dev / self-host / Zeabur），不共用一份 `.env` ——
混用會讓生產密碼流入開發環境。敏感變數在文件中用 🔒 標記，部署時一眼看出哪些要設 Secret。

**Zeabur 適配要點**
- **`AUTH_TRUST_HOST` 必填**：NextAuth v5 安全預設不信 forwarded headers，
  不設會卡在 callback redirect
- **`NEXTAUTH_SECRET` 兩端同源**：`zeabur.json` 的 backend 與 web 都引用同一個
  `${AUTH_SECRET}` project variable，自動保證一致
- **`POSTGRES_PASSWORD` 用 `${PASSWORD}`** 由 Zeabur 注入隨機強密碼，使用者不必自己設
- 唯讀變數（HOST / PORT / DATABASE / USERNAME）標 `readonly: true` 防誤改；
  `${CONTAINER_HOSTNAME}` 自動給內部 DNS 名
- **CORS 對尾斜線做 rstrip 容錯**而非禁止 —— 與其要求使用者填 `.env` 時守紀律，不如 server 容錯

**dev / prod 用同一個 image**（`pgvector/pgvector:pg16`）：避免 dev 過、prod 才在 alembic 掛掉。
prod compose **不暴露 PG / Redis host port**。

**Judge0 自架獨立成一份 compose**（不併入 prod）：它是可選元件，且需要 privileged，
併進去會讓主 compose 臃腫。**Zeabur 跑不了自架 Judge0**（privileged 限制）→ 該環境走 RapidAPI。
`JUDGE0_API_KEY=""` 即表示自架模式，`_build_headers` 據此不加 RapidAPI header。

**`requirements.lock` 一次重產**：Phase 2-1 / 2-3 陸續加的套件一直沒同步，
4-1a 是部署前最後修正機會。**pyBKT 不進 lock** —— 線上更新用純公式不需套件，
它只在 Phase 5 跑 `fit()` 時才需要。


## [2026-05-05] — Phase 3-3c：Dashboard 精熟度詳細總覽（Phase 3 完成 🎉）

### 新增（Backend）
- `backend/services/dashboard/mastery.py`（111 行）：
  - dataclass：`ConceptMasteryDetail` / `CategoryBreakdown` / `MasteryBreakdown`
  - `get_mastery_breakdown(db, user_id)`：一次 outerjoin 取所有 (concept, mastery_for_user)；application 層分群 + 排序
  - 分群：依 `concept.category`
  - 排序：concept 內依 `video_order ASC`（None 排尾）+ tag 穩定 fallback；category 依 earliest video_order ASC
  - `MASTERED_THRESHOLD = 0.8` 與 dashboard.queries / generator 一致
- `backend/api/routes/dashboard.py`：加 `GET /dashboard/mastery-overview`
  - response：`{ categories: [{ name, total, started, mastered, concepts: [{ tag, name_zh, video_order, difficulty, confidence }] }] }`

### 新增（Frontend）
- `web/lib/dashboard.ts`：加 types + `getMasteryOverview()` helper
- `web/components/dashboard/mastery-breakdown.tsx`（130 行）：
  - useEffect async fetch + cancelled flag
  - 4 狀態：loading / error / empty / list
  - 全展開（無摺疊互動）— 8 個 category section 全部顯示
  - Category header：name + 摘要 (mastered/total) + overall progress bar
  - Concept row：video_order + name + difficulty pill + mini progress bar + percent
  - 顏色語意：mastered 用 accent-green / 其他用 accent-blue
- `web/app/(app)/dashboard/page.tsx`：加 `<MasteryBreakdown />` section

### 測試
- `backend/tests/test_dashboard_mastery.py`（8 個 service + HTTP）：
  - 401 / 空狀態 / 多 category 分群 + summary / category 排序 / video_order=None 排尾 / 未練 confidence=0 / threshold 0.8 邊界 / HTTP 完整 payload
- 全套 439 backend tests 全綠（431 → 439，+8 個新測試，零 regression）

### 設計關鍵
- **單次 outerjoin 而非 N+1**：59 concepts 只 1 個 query，不是 60+
- **教學順序排序**：concept video_order ASC / category 依 earliest video_order
- **MASTERED_THRESHOLD = 0.8 共用**：與 generator / dashboard.queries 一致；單一語意
- **全展開 vs 摺疊**：60 rows 一覽比 click ladder 直觀

### Phase 3 整體里程碑（學習體驗 🎉）
- ✅ 3-1 結構化學習路徑（7 個 sub-tasks）
- ✅ 3-2 Quiz 完整版（3 個 sub-tasks）
- ✅ 3-3 Dashboard（3 個 sub-tasks）
- 學生端完整體驗就緒：登入 → Learn → Quiz → Dashboard 全閉環
- 後端測試從 Phase 3 開始時的 320 → 完成時的 439（+119）

---

## [2026-05-05] — Phase 3-3b：Dashboard 最近活動時間線

### 新增（Backend）
- `backend/services/dashboard/timeline.py`（142 行）：
  - dataclass: `ActivityType` Literal["quiz", "reflection", "unit_completed"] + `ActivityItem`
  - 3 個 fetch helper（每類各取 limit 筆）：
    - `_list_quiz`：student_answers join question；標題含對錯與題幹截斷；detail 含題型/難度/提示用量
    - `_list_reflection`：reflections；含 quality_score 百分比 + 步驟數
    - `_list_completed_units`：learning_units WHERE completed_at IS NOT NULL（透過 path.user_id 過濾）
  - `list_recent_activities` 主流程：merge 三類 → sort by timestamp desc → 取 limit
- `backend/api/routes/dashboard.py`：加 `GET /dashboard/timeline?limit=N`
  - 422 if limit out of [1, 100]
  - response: `{ items: [{ type, timestamp(ISO), title, detail, link?, is_correct? }] }`

### 新增（Frontend）
- `web/lib/dashboard.ts`：加 `ActivityType` / `ActivityItem` types + `getRecentActivities(limit)` helper
- `web/components/dashboard/activity-timeline.tsx`（150 行）：
  - useEffect async fetch + cancelled flag 防 race
  - 4 狀態：loading skeleton / error / empty / list
  - `ActivityIcon` 依 type 與 is_correct 顯示對應 lucide icon + 顏色：
    - quiz 對 → CheckCircle2 綠 / quiz 錯 → XCircle 紅
    - reflection → ClipboardList 紫
    - unit_completed → GraduationCap 藍
  - `formatRelative(iso)` 相對時間（剛才 / N 分前 / N 小時前 / N 天前 / 完整日期）
  - 有 link 的 item 整列為 Link；無 link 為純 div
- `web/app/(app)/dashboard/page.tsx`：在 today suggestion 下加 `<ActivityTimeline />` section

### 測試
- `backend/tests/test_dashboard_timeline.py`（9 個 service + HTTP）：
  - 401 / 空狀態 / 三種事件類型完整出現 / quiz 含 is_correct + 提示用量 detail / reflection 品質百分比 / unit 限 completed / limit 截斷 / HTTP ISO timestamp / HTTP 422 limit 範圍
- 全套 431 backend tests 全綠（422 → 431，+9 個新測試，零 regression）
- TypeScript / ESLint / next build 全綠

### 設計關鍵
- **每類各取 limit 後合併**：避免單一事件類型（如 quiz）量大時遮蔽其他類型；merge 後再取最終 limit
- **不含 comprehension 事件**：schema 沒專屬 completed_at；後續加欄位再加（記入 tech-debt）
- **不含 chat 訊息**：量大且不算「學習進度」級別的事件
- **R8 反 AI 感**：4 種 icon 全 lucide（無 emoji）；色彩僅用於語意（綠對 / 紅錯 / 紫反思 / 藍完成）
- **link 可空**：reflection 無對應 detail 頁面 → link=null；前端 row 渲染區分
- **相對時間在前端格式化**：後端只給 ISO；不在 JSON 預處理（避免時區邊界判斷複雜化）
- **限 limit ≤ 100**：避免 SQL 大 query；前端預設 20（dashboard 概覽用）

---

## [2026-05-05] — Phase 3-3a：學生 Dashboard 統計卡片 + 今日建議

### 新增（Backend）
- `backend/services/dashboard/queries.py`（231 行）：
  - dataclass：`PathProgressSummary` / `WeekQuizStats` / `MasteryOverview` / `TodaySuggestion` / `DashboardStats`
  - 4 個 fetch helper 對應 4 統計卡：
    - `_path_progress`：取最早 path（與 `ensure_default_path_exists` 一致）+ 計算 completed/total/percent
    - `_week_quiz_stats`：限近 7 天 student_answers + 答對率
    - `_mastery_overview`：total_concepts / started_count（mastery 表 row 數）/ mastered_count（confidence ≥ 0.8）
    - `_reflection_count`：累計反思次數
  - `_today_suggestion`：規則版（無 LLM）— 依 unit status 推薦下一動作：
    1. 有 `in_progress` unit → 「繼續學習：xxx」
    2. 有 `available` unit → 「開始下一單元：xxx」
    3. 全部 `completed` → 「課程完成，挑戰 Quiz」
    4. 無 path → fallback「進入 Learn 開始」（ensure_default_path 後不該發生）
  - 主入口 `get_dashboard_stats(db, user_id)` 組合所有
- `backend/api/routes/dashboard.py`（91 行）：`GET /dashboard/stats` endpoint
- `backend/main.py`：註冊 `dashboard_router`

### 新增（Frontend）
- `web/lib/dashboard.ts`：types + `getDashboardStats()` helper
- `web/components/dashboard/`：
  - `stats-cards.tsx`（145 行）— 4 張卡片網格（grid 1/2/4 列響應式）：路徑進度（含 progress bar）/ 本週 Quiz / 精熟度概覽 / 反思次數
  - `today-suggestion.tsx`（38 行）— 建議標題 + 描述 + 「立即前往」按鈕
- `web/app/(app)/dashboard/page.tsx`：完全重寫，從 placeholder 升級為功能頁
  - View union（loading / error / ready）
  - 統一 humanizeError（401 等）

### 測試
- `backend/tests/test_dashboard.py`（10 個 service + HTTP）：
  - 401 / 空狀態 / path_progress 計算 / week_quiz 7 天篩選 / mastery 三欄 / reflection 計數
  - today_suggestion 三規則（in_progress 優先 / 只 available / 全 completed）
  - HTTP 完整 payload 結構檢查
- 全套 422 backend tests 全綠（412 → 422，+10 個新測試，零 regression）
- TypeScript / ESLint / next build 全綠

### 設計關鍵
- **規則版 today_suggestion 而非 LLM**：MVP 階段；個人化 LLM 建議留給 3-3b/c 或 Phase 4+；對學生而言「下一個該做什麼」清晰即可
- **Mastered threshold = 0.8**：與 generator 的 `DEFAULT_SKIP_MASTERED_THRESHOLD` 一致；單一語意「熟練」
- **Week 範圍 7 天**：rolling window（不是 ISO 週）；學生看到的是「最近 7 天」
- **path 取最早建立**：與 onboarding 的「ensure default path」一致；學生通常只有 1 條，無爭議
- **Path Progress percent 用整數**：避免顯示 24.5% 這種偽精確；`int((c/t)*100)`
- **空狀態完整可顯示**：cold start 學生 path=None / 全 0 也能正常渲染卡片（顯示「尚未建立」/「本週尚未作答」）
- **R8 反 AI 感**：4 卡片用 lucide icon，無 emoji；色彩僅用於語意（accent-green 進度條 / accent-purple 建議）

---

## [2026-05-05] — Phase 3-2c：作答後 EDF 回饋（Phase 3-2 完成 🎉）

### 重點
作答後的個人化回饋頁，整合 BKT 精熟度 + LLM 建議 + 推薦學習單元連結。
與 `/quiz/submit` 即時對錯分離（async fetch），保持結果頁載入快但內容豐富。

### 新增（Backend）
- `backend/services/quiz/feedback.py`（250 行）：
  - dataclass: `ConceptMasteryItem` / `RecommendedUnit` / `QuizFeedbackResult`
  - `_get_owned_answer` 擁有權檢查（非本人 → 404 STUDENT_ANSWER_NOT_FOUND）
  - `_fetch_concept_mastery`：outerjoin Concept × StudentMastery，未練概念視為 0
  - `_fetch_recommended_units`：限同 user 路徑 + 未完成 + concept 匹配
  - `_llm_suggestion`：依對錯 + mastery 給 1-2 句建議；4 種 fallback 路徑保證不擋學生
  - `generate_quiz_feedback` 主流程
- `backend/api/routes/quiz.py`：`SubmitResponse` 加 `answer_id`（前端要能拿來 fetch feedback）
- `backend/api/routes/quiz_feedback.py`（77 行，獨立檔避免主 quiz.py 超 250）：
  - `GET /quiz/answers/{answer_id}/feedback` endpoint
  - response 含 mastery 列表 + suggestion + suggestion_fallback flag + recommended_units
- `backend/main.py`：註冊 `quiz_feedback_router`

### 新增（Frontend）
- `web/lib/quiz.ts`：
  - `SubmitResponse` 加 `answer_id` 欄位
  - 加 `ConceptMasteryItem` / `RecommendedUnit` / `QuizFeedbackResponse` types
  - 加 `getQuizFeedback(answerId)` helper
- `web/components/quiz/feedback-section.tsx`（172 行）：
  - useEffect async fetch + cancelled flag 防 race
  - SkeletonView（loading）+ SuggestionCard / MasteryCard / RecommendedCard 三段式
  - MasteryRow 進度條（0-100%）對齊 design tokens（accent-green）
  - RecommendedUnit Link 帶 video_order 編號顯示
  - 統一 humanizeError
- `web/components/quiz/result-view.tsx`：在 CorrectAnswerSection 與導航按鈕之間嵌入 `<FeedbackSection answerId={result.answer_id} />`

### 測試
- `backend/tests/test_quiz_feedback.py`（14 個 unit + HTTP）：
  - 6 unit：5 種 _llm_suggestion fallback 路徑（no client / exception / invalid JSON / empty / 對錯各一）+ success
  - 4 service integration：擁有權 404 / mastery 0 補位 / 推薦 unit 過濾（已完成 / 不匹配 concept）/ 推薦 unit 正向案例
  - 4 HTTP：401 / 跨使用者 404 / success 完整 payload / submit response 含 answer_id（3-2c 新增欄位）
- 全套 412 backend tests 全綠（398 → 412，+14 個新測試，零 regression）
- TypeScript / ESLint / next build 全綠

### 設計關鍵
- **submit 與 feedback 分離**：submit 立即回對錯（快）；feedback async fetch（LLM 慢，UI loading state 不擋畫面）
- **不重做 EDF Evidence**：quiz answer 結構化已知（is_correct + concept_tags），不需 LLM 拆解錯誤類型；EDF Evidence Pipeline 仍服務 chat 場景（學生提問時用）
- **未練概念視為 0**：`outerjoin` + 預設 0.0 — 顯示完整 concept_tags 不留空白，cold start 學生看到 0% 也比看到「無資料」直覺
- **推薦過濾三層**：同 user 的 path × 未完成 × concept_tag 匹配；避免推已學完的 unit 或他人路徑的 unit
- **獨立 route 檔**：`quiz_feedback.py` 拆出避免主 quiz.py 超 250 行（schema 定義較長）
- **LLM 失敗 fallback 對稱**：與 hint / EPL / Comprehension 設計一致；`suggestion_fallback` flag 讓前端顯示「離線」狀態
- **RecommendedUnit 連結到 /learn**：MVP 直接導向學習路徑首頁；未來可加深 deep-link 直跳特定 unit

### Phase 3-2 整體里程碑
- ✅ 3-2a Quiz 頁面：選擇題 + 程式撰寫題 UI
- ✅ 3-2b 計時器 + 提示系統（5 級 hint ladder）
- ✅ 3-2c 作答結果頁 + EDF 回饋顯示
- 全套 412 backend tests 全綠；學生 Quiz 完整閉環：選題型 → 取題 → 作答（含計時 + 提示）→ 對錯 + 解釋 + EDF 個人化回饋

---

## [2026-05-05] — Phase 3-2b：Quiz 計時器 + 5 級提示系統

### 新增（Backend）
- `backend/services/quiz/hint.py`（164 行）：
  - `HintResult` dataclass（level + hint + fallback flag）
  - `_FALLBACK_HINTS` dict — 對應 1-5 level 各一句固定鼓勵句（LLM 不可用時用）
  - `_ladder_description(level)` — 對應 .claude/rules/edf-pipeline.md 的 Hint Ladder 規則文字
  - `_format_question_for_prompt` — 題型 dispatcher（MC 含選項 / coding 含 starter）
  - `generate_hint(question, hint_level, student_attempt?)` async LLM；失敗回 fallback
- `backend/api/routes/quiz.py`（209 行）：加 `POST /quiz/hint` endpoint
  - body: `{ question_id, hint_level (1-5), student_attempt? }`
  - 404 QUESTION_NOT_FOUND / 400 QUESTION_NOT_VALIDATED / 422 invalid level
  - response 含 `fallback` flag 讓前端顯示「離線 fallback」標籤

### 新增（Frontend）
- `web/lib/quiz.ts`：加 `requestHint(payload)` helper + `HintResponse` type
- `web/components/quiz/timer.tsx`（39 行）：
  - 純 prop-driven，caller 傳 `startedAt: number`（Date.now() 時戳）
  - useEffect 每秒 setState tick；mm:ss 格式
- `web/components/quiz/hint-panel.tsx`（57 行）：
  - 累計顯示已取得 hints（依 level 排）+ 「取得第 N 個提示」遞增按鈕
  - **強制遞增**：學生不能跳級看 level 5（避免直接看答案）
  - 達到 max=5 後按鈕 disabled
  - fallback 提示加「（離線 fallback）」標示
- `web/components/quiz/quiz-runner.tsx`：
  - 加 `hints: HintResponse[]` + `hintBusy` state
  - `handleRequestHint` 永遠請 next level（current count + 1）
  - submit 時帶 `hint_level_used = hints.length`（持久化）
  - 換題時清空 hints
  - 顯示 Timer（question 模式）+ HintPanel（始終顯示）

### 測試
- `backend/tests/test_quiz_hint.py`（13 個 unit + HTTP）：
  - 6 unit：prompt ladder 描述 / MC prompt 含 options / LLM 成功 / no client fallback / exception fallback / invalid JSON fallback / empty hint fallback
  - 7 HTTP：401 / 422 (4 種 invalid level) / 404 / 400 / 200 success / 200 fallback
- 全套 398 backend tests 全綠（385 → 398，+13 個新測試，零 regression）
- TypeScript / ESLint / next build 全綠

### 設計關鍵
- **Hint Ladder 對齊 EDF Pipeline 規則**：`_ladder_description` 直接引用 `.claude/rules/edf-pipeline.md` 5 級定義；保證 hint 風格與 chat 評估的「直接給答案」防護一致
- **LLM 失敗 fallback 不擋學生**：類似 EPL/Comprehension 設計；fallback 句子分 5 個 level 預先寫好，前端用 `fallback` flag 提示「離線」狀態
- **強制遞增不可跳級**：教學原則防止學生直接看 level 5；後端不限制（接收 1-5 任何值），由前端 UX 控制
- **Hint 不寫入 DB**：純即時生成；`hint_level_used` 已透過 `/quiz/submit` 持久化（quiz history 可分析學生提示依賴度）
- **Timer 純前端**：不影響 submit 流程；submit 時 caller 仍從 startedAt 計算 time_spent_seconds（與 3-2a 邏輯一致）
- **MC 也支援 hint**：UI 統一；雖然 MC hint 教學意義較弱，但保留選擇權

---

## [2026-05-05] — Phase 3-2a：Quiz 頁面 — 選擇題 + 程式撰寫題正式版

### 新增（Frontend）
- `web/lib/quiz.ts`（+30 行）：
  - `SubmitAnswer` discriminated union（依題型不同）：`{selected_index}` / `{code}` / `{answers}`
  - `SubmitQuestionPayload` / `SubmitResponse` types
  - `submitAnswer(payload)` helper → POST `/quiz/submit`
- `web/components/quiz/`（4 新元件）：
  - `quiz-runner.tsx`（200 行）— 主流程容器；五狀態 union（idle / loading / question / submitting / result）；題型 dropdown（選擇題 / 程式撰寫題）；計時 startedAt → time_spent_seconds 提交時帶入；統一 humanizeError
  - `mc-question.tsx`（68 行）— radio-style options + Lucide CheckCircle2/Circle 圖示；提交按鈕 disabled until 選中
  - `coding-question.tsx`（68 行）— 復用 `CodeEditor`（CodeMirror 6 + cpp + oneDark）；提示「Judge0 自動判分屬 Phase 4」；切題自動 reset content
  - `result-view.tsx`（115 行）— 對錯 banner（綠勾 ✓ / 紅叉 ✗ + Lucide）；feedback + explanation；MC/fill_blank 揭露正確答案；coding 不揭露（待 Judge0）；下一題 / 結束按鈕
- `web/app/(app)/quiz/page.tsx`：完全重寫，從 Phase 2-5c demo 升級為正式 Quiz 頁面；純包裝 `<QuizRunner />`

### Backend
- 無變動（既有 `/quiz/generate` + `/quiz/submit` API 已支援整個 3-2a 流程）
- 後端 385 tests 仍全綠（純前端任務）

### 設計關鍵
- **設計分工釐清**：Quiz 頁面 = 純測驗（取題 → 作答 → 結果），無反思流程；Learn 練習 tab（3-1e）= 學習場景含 Pre-Coding Reflection。避免在 Quiz 頁面強制反思打斷測驗節奏
- **Coding 題目前 is_correct=False**：`backend/services/quiz/grade.py` 的 coding 分支永遠回 False（Judge0 整合屬 Phase 4）；UI 提示這點，避免使用者困惑
- **Discriminated union for SubmitAnswer**：對應後端 `answer: dict` 但 TS 端用 union 強制型別 — 防止 caller 對 MC 傳 code 等錯誤
- **time_spent_seconds 自動計**：runner 在 question 模式記錄 `startedAt`，submit 時計算秒差送 server（為 3-2b 計時器顯示鋪路）
- **hint_level_used = 0 hardcoded**：3-2b 提示系統未實作前一律 0；submit API 已支援 0-5 範圍
- **coding 不揭露答案**：Phase 4 Judge0 整合後改用實際執行結果判分；3-2a 階段保留學生再思考空間
- **fill_blank UI 未做**：roadmap 明列 3-2a 為「選擇題 + 程式撰寫題」；fill_blank 在 result-view 已支援揭露答案邏輯，UI 待後續任務（顯示 `UnsupportedTypeNote` placeholder）
- **CodeEditor 復用**：直接 import 現有元件（守則 #7 不重複造輪子）；CodeMirror 6 + cpp + oneDark 已調整為 GitHub Dark token 對齊

### 待驗證（手動）
- 進 `/quiz` → 選題型 → 點開始 Quiz
- 選擇題：點選項 → 提交 → 看到對錯 + 解釋 + 正確答案揭露 → 下一題 or 結束
- 程式撰寫題：在 CodeMirror 寫 code → 提交 → 看到「答錯了」（因 coding 未接 Judge0）+ 解釋 → 下一題

---

## [2026-05-05] — Phase 3-1e：練習 tab 嵌入 Pre-Coding Reflection 觸發點（Phase 3-1 完成 🎉）

### 新增（Backend）
- `backend/services/quiz/orchestrator.py`：
  - 新增 `_resolve_concept_by_tag(db, tag)` helper（404 CONCEPT_NOT_FOUND if missing）
  - `generate_for_student` 加 optional `concept_tag` 參數：指定時直接針對該 concept 出題（跳過弱項邏輯）；省略則維持原弱項補強行為（向後相容）
- `backend/api/routes/quiz.py`：`GenerateRequest` 加 `concept_tag: str | None`，透傳到 service

### 新增（Frontend）
- `web/lib/quiz.ts`（55 行）：Question / Content type union + `generateQuestion(payload)` helper
- `web/components/learn/exercises-tab.tsx`（206 行）：
  - 三狀態流程：idle（「開始練習」按鈕）→ loading → question（顯示題目 + 「開始反思」）→ reflecting（彈 ReflectionFlow modal）→ done（反思摘要 + 後續導引）
  - 取題：`generateQuestion({ type: "coding", bloom_level: 3, concept_tag: unit.concept_tag })`
  - 復用 `ReflectionFlow` 元件（Phase 2-5）：`sourceType="quiz"` + `sourceId=question.id`
  - 反思 approve → 顯示反思摘要（含 quality_score 百分比 + followup question 若有）+ 提示「在 Workspace 作答」連結 + 「回上方點完成單元」
  - 「重新出題」按鈕（reset 狀態）
  - humanizeError 處理 CONCEPT_NOT_FOUND / QUIZ_VALIDATION_RETRY_EXHAUSTED / QUIZ_UNAVAILABLE / 401
- `web/components/learn/unit-content.tsx`：把原 `ExercisesTab` placeholder 改用新元件，傳入 `unit.concept_tag` + `unit.concept_name_zh`

### 測試
- `backend/tests/test_quiz_route.py` 加 2 個 HTTP 測試：concept_tag 指定 → 該 concept 出題；不存在 tag → 404 CONCEPT_NOT_FOUND
- 全套 385 backend tests 全綠（383 → 385，+2 個新測試，零 regression）
- TypeScript / ESLint / next build 全綠

### 設計關鍵
- **「觸發點」非「完整作答」**：3-1e 範圍嚴格限於「在練習 tab 內取題 + 觸發反思」；完整 coding 作答 UI（編輯器 + Judge0 提交 + 判分回饋）屬 Phase 3-2 Quiz 完整版
- **向後相容的 quiz/generate**：新增 `concept_tag` 為 optional，原 cold-start fallback / 弱項補強邏輯不變
- **復用 ReflectionFlow 而非重寫**：對齊「不重複造輪子」（CLAUDE.md 守則 #7）；reflection 元件已成熟，直接 import 即可
- **Workspace 導引**：反思 approve 後的「在 Workspace 作答」連結會配合 Phase 2-5d 的 `setActiveReflectionId`（reflection_id 寫 sessionStorage）— 學生跳到 /workspace 寫程式時 AI Tutor 自動帶入此反思（EDF Pipeline 注入），完整閉環
- **題型固定 coding**：教學影片內容多為 coding 練習；MC/fill_blank 對「練習」概念意義較弱，3-1e 不暴露選擇

### Phase 3-1 整體里程碑
- ✅ 3-1a Schema + ORM
- ✅ 3-1b 路徑生成 service（priority Kahn's）
- ✅ 3-1c Learn 頁面 + 4 endpoints
- ✅ 3-1c+ Concept Graph 重建（59 影片）
- ✅ 3-1c++ Learn UX 簡化（lazy seed + 移除生成 UI）
- ✅ 3-1d 學習單元內容頁（4 tab + status transition）
- ✅ 3-1e 練習 tab 嵌入 Reflection 觸發點
- 全套 385 backend tests 全綠；學生 onboarding → 學習 → 練習 → 反思 → 完成單元的完整閉環就緒

---

## [2026-05-05] — Phase 3-1c+ 簡化：onboarding 自動 seed 預設路徑（移除無意義的「生成路徑」UX）

### 重新評估
- 3-1c 原設計含「+ 生成新路徑」按鈕 + EmptyState + 多路徑列表，預期學生會手動建立多條路徑
- 但 3-1c+ concept graph 重建為固定 59 影片線性鏈後，每位學生「生成」結果完全相同
  → category filter 是唯一變數但 99% 學生會學完整課程
  → 「生成」變無意義儀式，違反「不為不存在的需求設計」原則（YAGNI / CLAUDE.md 守則 #7）
- 結論：移除手動生成 UI，改為 onboarding 自動 seed

### Backend
- `backend/services/learning/queries.py`：
  - 加 `DEFAULT_PATH_TITLE = "C++ 完整課程"` + `DEFAULT_PATH_DESCRIPTION` 常數
  - 加 `ensure_default_path_exists(db, user_id) -> LearningPath`：學生有任何路徑 → 回最早建立的；無 → 呼叫 generate_learning_path 用預設 title/description
- `backend/api/routes/learning.py`：
  - 加 `GET /learning/paths/default` endpoint — Learn 頁面唯一入口
  - 抽 `_build_path_detail` helper 共用於 GET /paths/{id} / POST /paths / GET /paths/default 三處
  - **保留** POST/DELETE/GET list endpoints 供未來教師端 / 自訂路徑使用，前端不暴露

### Frontend
- `web/lib/learning.ts`：精簡 — 加 `getDefaultPath()`；**刪除** `listPaths` / `generatePath` / `deletePath` / `progressPercent` / `GeneratePathPayload` / `PathSummary`（前端不再需要）
- `web/components/learn/path-card.tsx`：**整檔刪除**
- `web/components/learn/generate-path-dialog.tsx`：**整檔刪除**
- `web/components/learn/path-detail.tsx`：移除 `onBack` prop + 「返回路徑列表」按鈕（無 list 可返）
- `web/app/(app)/learn/page.tsx`：**完全重寫**
  - 兩模式：detail（預設視圖）/ unit（內容頁）— 移除原 list / loading-detail
  - 進入 → 自動 fetch `/learning/paths/default`（後端 lazy seed）→ 直接顯示 detail
  - 移除：EmptyState / 「+ 生成新路徑」按鈕 / 刪除按鈕 / dialog 整套
  - 學生 onboarding 體驗：登入 → Learn → 立刻看到「C++ 完整課程」59 個 unit

### 測試
- `backend/tests/test_learning_route.py` 加 4 個 HTTP 測試：401 / lazy seed 首次 / 已有路徑回最早建立 / 422 無 concepts
- 全套 383 backend tests 全綠（379 → 383，+4 個新測試，零 regression）
- TypeScript / ESLint / next build 全綠（Route summary 含 `/learn` ○ static prerender）

### 設計關鍵
- **「ensure 而非 default-named」語意**：`ensure_default_path_exists` 回任何已存在路徑（不檢驗 title），避免使用者手動建立非預設 title 後又被自動建一條重複的
- **Backend endpoints 完全保留**：POST/DELETE/GET list 仍在；schema 完全保留；前端不暴露但 schema 仍支援多 path（為未來教師端 / 複習路徑預留）
- **無 list 視圖反而更簡潔**：原 path-card.tsx 在只有 1 條路徑時是視覺噪音；直接顯示 detail 更直覺
- **path-detail 移除 onBack**：detail 變主畫面，無「返回」目的地；unit-content 內仍有「返回路徑：xxx」按鈕（unit → detail 的返回有意義）
- **不刪除 schema/migration**：方案 A 純 UX 簡化，零 schema 變動；未來真有教師端再 git revert 復活 path-card / generate-dialog 即可

---

## [2026-05-05] — Phase 3-1d：學習單元內容頁（4 tab + status transition + 自動解鎖）

### 新增（Backend）
- `backend/services/learning/units.py`（129 行）：
  - `update_unit_status(db, user_id, unit_id, new_status)` — status transition + 解鎖下一單元
  - 合法 transition：available → in_progress、in_progress → completed、in_progress → available（revisit）
  - 非法 transition 一律 422 LEARNING_UNIT_INVALID_TRANSITION（locked 不可手動設、completed 不可重置）
  - completed 自動連動：同 path 內 order_index = current+1 的 unit（若 locked）→ available
  - 擁有權檢查透過 unit.path_id → path.user_id；非本人 → 404
- `backend/api/routes/learning_units.py`（85 行，獨立檔避免主 learning.py 超 250）：
  - `PATCH /learning/units/{unit_id}` body `{ status: "available" | "in_progress" | "completed" }`
  - `_parse_status` 422：非合法 enum / locked
  - `UnitTransitionOut` 含 `unit` + `next_unlocked_unit`（若有）

### 新增（Frontend）
- `web/lib/learning.ts`：加 `updateUnitStatus(unitId, status)` + types `WritableUnitStatus` / `UnitBasic` / `UnitTransitionResult`
- `web/components/learn/unit-content.tsx`（230 行）：
  - 4 tab：概念說明 / 範例程式 / 練習題 / 摘要
  - 概念說明 tab：YT player placeholder（待教授補 video_id）+ concept 簡介
  - 範例程式 / 摘要：unit.content 為空時顯示 EmptyTab placeholder
  - 練習題：3-1e 整合 placeholder
  - 上一/下一單元導航（locked unit 不可導航）
  - ActionButton 依 status 顯示「開始學習」/「完成單元」/「已完成 ✓」/「尚未解鎖」
- `web/components/learn/path-detail.tsx`：unit 變可點，locked 用 opacity-60 + cursor-default
- `web/app/(app)/learn/page.tsx`：
  - View union 加 `unit` 模式（持 detail + unitIndex）
  - 新增 `UnitView` 包裝 — status transition 後重 fetch path detail + 維持當前 unitIndex
  - 解鎖的下一 unit 經 path detail 同步刷新自動可見

### 測試
- `backend/tests/test_learning_units.py`（13 個 service + HTTP）：
  - Service：合法 transition / completed 解鎖 / last unit no next / locked rejected / completed→available rejected / revisit 清 completed_at / 跨使用者 404
  - HTTP：401 / 422 invalid status string / 422 locked / 200 + next_unlocked / 422 invalid transition / 跨使用者 404
- 全套 379 backend tests 全綠（366 → 379，+13 個新測試，零 regression）
- TypeScript / ESLint / next build 全綠

### 設計關鍵
- **status transition 用查表** (`_VALID_TRANSITIONS: dict[str, set[str]]`)：宣告式比 if/else 易擴充與檢驗
- **completed → 任何狀態都拒絕**：避免精熟度反覆波動造成 BKT 信心度震盪（現實中重學的學生應該再走 quiz/comprehension 重新評估，不是直接 reset unit）
- **revisit 路徑（in_progress → available）**：學生想重看不算完成，清空 `completed_at`；不影響後續解鎖（解鎖只發生在 completed transition）
- **解鎖只往前推一個**：unit N 完成 → unit N+1 解鎖；不會跨章節同時解鎖（教學節奏控制）
- **route 拆獨立檔**：`learning_units.py` 與 `learning.py` 分檔避免單檔超 250 行；前綴都用 `/learning` 路由 namespace
- **`_basic` response 不含 concept join**：transition response 給前端最小欄位（id/order_index/status/completed_at），需要完整 unit 資料時前端重 fetch path detail
- **前端切換 view 用 union state**：相比 nested route 簡化，不需設計 layout 共用 / breadcrumb；學生在 unit 頁完成 transition 後直接看到下一 unit 解鎖
- **YT player placeholder + content 空骨架 placeholder**：3-1d 範圍只做 UI 容器，內容（video_id / examples / summary）等教授補資料或 LLM 生成（見 tech-debt.md）

---

## [2026-05-05] — Phase 3-1c+：Concept Graph 重建（教授 C++ 課程 59 影片整合）

### 重大決策
- **完全替換 V1 20 個 EDF concept** → 改為 62 部 YT 影片中排除 01-03 介紹後的 **59 個影片 concept**（每影片 = 1 concept node）
- EDF 的 20 個 ConceptTag enum **保留**在 `services/edf/models.py` 純粹做 LLM 錯誤分類提示用，**不再寫入 concepts 表**
- chat-driven mastery 暫時退場（EDF 評估 LLM 回的粗 tag 在 concepts 表找不到 → 既有 fallback 跳過更新）；mastery 改由 quiz 答題 + comprehension 驅動（這些用 question.concept_tags = 影片 tag）

### Schema
- `backend/alembic/versions/d0e1f2a3b4c5_add_video_metadata_to_concepts.py`（67 行）：
  - `concepts` 加 3 nullable 欄位：`video_youtube_id` (VARCHAR 20) / `video_duration_seconds` (INT) / `video_order` (INT)
  - 2 個 CHECK constraints + 1 個 index on `video_order`
- `backend/models/concept.py`：對應 ORM 加 3 欄位

### 內容（destructive seed）
- `backend/alembic/versions/e1f2a3b4c5d6_seed_cpp_video_concepts.py`（180 行）：
  - ⚠ 清空 `learning_units` / `learning_paths` / `concept_edges` / `student_mastery` / `concepts`
  - Seed **59 個影片 concept**，依教授課程順序 04-62
  - tag 命名：`cpp-NN-keyword`（NN 兩位編號 + 簡短英文）
  - 8 個 category：入門 / 變數與型別 / 運算子 / 流程控制 / 迴圈 / 函式 / 陣列 / 指標與記憶體 / 物件導向
  - difficulty_level 1-5 依教學順序漸進
  - Seed **58 條 PREREQUISITE 線性鏈**（04→05→...→61→62）
  - YT video_id / duration 暫 NULL，等教授補後 PATCH
- 修正：`concept_edges.edge_type` 是 PG ENUM `concept_edge_type` 不能從 VARCHAR 隱式轉型 → 用 `sa.Enum(..., create_type=False)` 顯式宣告

### 驗證
- PG 上 alembic upgrade head 成功；`SELECT COUNT(*) FROM concepts` = 59；`prerequisite` edges = 58
- 全套 366 backend tests 全綠，零 regression（ORM 加 nullable 欄位無破壞性）

### 設計關鍵
- **方案 B（完全替換）vs A（共存）/ C（替換+對應）**：選 B 因為 chat-driven mastery 本來噪音多，真正可信信號來自 quiz/comprehension；簡化 99% 複雜度，符合 YAGNI 原則
- **線性 PREREQUISITE 鏈為主**：跨章節依賴（如 47 遞迴 ← 29 for）等教授後續標註；MVP 先簡單可用
- **Migration 不可重跑（destructive）**：alembic 只跑一次此 revision，OK；dev/prod 都會清掉舊 concept；目前未上線無真實學生資料風險
- **學習路徑生成可立即運作**：拓撲排序在 59 個 concept + 58 條線性邊上產生有意義路徑；弱項補強仍能依 BKT 信心度排序
- **YT player 整合延後**：`video_youtube_id` 已在 schema，等教授補資料後 3-1d 學習單元頁實作

### 待辦（教授提供資料後）
- [ ] PATCH script 一次更新 59 影片的 `video_youtube_id` + `video_duration_seconds`
- [ ] 跨章節 PREREQUISITE 邊補強（如 47 遞迴 ← 29 for；65 條左右）
- [ ] Learn 頁面影片 thumbnail / duration 顯示（需 youtube_id）

---

## [2026-05-05] — Phase 3-1c：Learn 頁面 — 路徑視覺化 + 進度條

### 新增（Backend）
- `backend/services/learning/queries.py`（135 行）：
  - `PathProgress` / `UnitWithConcept` dataclass
  - `list_paths_for_user`（一次取所有 units 算進度，避免 N+1）
  - `get_path_with_units`（join concepts 取 tag/name_zh/difficulty，避免前端再 join）
  - `delete_path`（CASCADE 連動 units）
  - `_get_owned_path` 擁有權檢查 → 404（避免列舉攻擊）
- `backend/api/routes/learning.py`（186 行）— 4 endpoints：
  - `POST /learning/paths`（201）→ 完整 detail
  - `GET /learning/paths` → list + 進度概覽
  - `GET /learning/paths/{id}` → detail + units
  - `DELETE /learning/paths/{id}`（204）

### 新增（Frontend）
- `web/lib/learning.ts`（76 行）：types + 4 API helpers + `progressPercent` utility
- `web/components/learn/`：
  - `path-card.tsx`（83 行）— 卡片含進度條 + hover 顯示刪除按鈕
  - `unit-status-icon.tsx`（37 行）— 4 種 status icon（CheckCircle2/PlayCircle/Circle/Lock）+ 中文 label
  - `path-detail.tsx`（76 行）— 路徑詳細頁含 unit ordered list
  - `generate-path-dialog.tsx`（132 行）— 表單 modal（title/description/category）
- `web/app/(app)/learn/page.tsx`（重寫，180 行）：
  - 三模式：list / detail / loading-detail
  - 整合：listPaths / getPath / generatePath / deletePath
  - 統一 error handling 翻譯成中文（LEARNING_PATH_EMPTY / LEARNING_PATH_NOT_FOUND / 401）
  - EmptyState（無路徑時引導生成）

### 測試
- `backend/tests/test_learning_route.py`（13 個 HTTP 整合）：4 endpoint × 401 / POST 完整流程 / POST 422 / list 空 + 含進度 / GET 排序 / GET 跨使用者 404 / GET 不存在 404 / DELETE 移除 / DELETE 跨使用者 404
- 全套後端 366 tests 全綠（353 → 366，+13 個新測試，零 regression）
- TypeScript / ESLint / next build 全綠

### 設計關鍵
- **單元擁有權檢查走 path**：unit 沒獨立 user_id；過 path.user_id 過濾即可（DB schema 設計就如此）
- **list 一次撈避免 N+1**：`list_paths_for_user` 先撈所有 paths 後一次 IN 撈所有 units，application 層分群算進度
- **detail join concepts**：`get_path_with_units` server-side join，避免前端再 fetch concept 資訊
- **GET 路徑不存在 vs 跨使用者**：兩者都回 LEARNING_PATH_NOT_FOUND（避免列舉攻擊揭露存在性）
- **R8 反 AI 感**：UI 全用 lucide icon（無 emoji），status 顏色僅 4 種語意化（綠=完成 / 藍=進行 / 白=可學 / 灰=鎖定）
- **元件控制反向**：page.tsx 持狀態，子元件純 prop-driven（path-card / path-detail / dialog 全 stateless）
- **生成 dialog 預填 title**：「C++ 基礎學習路徑」減少使用者打字成本（cold start 友善）

---

## [2026-05-05] — Phase 3-1b：學習路徑生成 service（拓撲排序 + 弱項補強）

### 新增（Service）
- `backend/services/learning/topology.py`（73 行）：
  - `topological_sort_with_priority(nodes, edges, priority, default_priority)` — priority Kahn's algorithm
  - 純函式無 DB 依賴；O((N+E) log N)
  - 同層內按 priority 升序（弱項優先）；priority tie 用插入順序穩定破除
  - Cycle 容錯：殘留節點按 priority 附加到尾端，不擲錯
  - 邊指向 nodes 集合外的節點 → 忽略不擲錯（filter 後常見）
- `backend/services/learning/generator.py`（160 行）：
  - `generate_learning_path(db, user_id, title, description, category, skip_mastered_threshold)`
  - 流程：fetch concepts → fetch PREREQUISITE edges → fetch user mastery → 篩除已熟練 → priority Kahn's 拓撲 → 寫入 LearningPath + LearningUnits
  - 第一個 unit 設 `available`，其餘 `locked`（漸進解鎖機制）
  - 預設 `DEFAULT_SKIP_MASTERED_THRESHOLD = 0.8`
  - `content` 預留空骨架 `{"summary": "", "examples": [], "exercise_question_ids": []}`，由後續 service 填入
  - 422 LEARNING_PATH_EMPTY：無概念 / 全部已熟練 / category filter 無匹配
- `backend/services/learning/__init__.py`：export

### 測試
- `backend/tests/test_learning_topology.py`（12 個 unit）：空圖 / 單節點 / 線性鏈 / 弱項優先 / 拓撲約束維持 / cold start default / 穩定性 / diamond / cycle 容錯 / 外部邊忽略 / 多獨立鏈
- `backend/tests/test_learning_generator.py`（9 個 DB 整合）：3 種 422 / 線性鏈生成 / 跳過已熟練 / 同層弱項優先 / content 骨架 / category filter / 邊指向已熟練節點不破壞拓撲
- 全套 353 tests 全綠（332 → 353，+21 個新測試，零 regression）

### 設計關鍵
- **不採 RL**（守則 #7）：純拓撲 + 弱項補強已足夠；OATutor RL 屬過度工程，明確排除
- **priority Kahn's**：在 in-degree=0 候選中用 min-heap 選 confidence 最低 → 同時保證拓撲安全 + 弱項優先
- **Cold start = 弱項**：未練概念 confidence=0 → 自動排前面，符合「先學最不會的」直覺
- **跳過已熟練 (≥ 0.8)**：避免重複學；篩除後重算 edges 集合，剔除指向已熟練節點的邊（不破壞剩餘拓撲）
- **content 空骨架**：`{summary, examples, exercise_question_ids}` 預留 shape，後續 LLM 生成或編輯介面填入；不一次到位避免綁死
- **Cycle 容錯不擲錯**：PREREQUISITE 理論上 DAG，但程式不假設；殘留節點附加比硬報錯實用
- **演算法 vs DB 拆分**：topology.py 純函式無 DB 依賴 → 12 unit test 直接覆蓋演算法；generator.py 整合 DB → 9 integration test

---

## [2026-05-05] — Phase 3-1a：學習路徑基礎 schema（Module 7 啟動）

### 新增（Schema / Migration）
- `backend/alembic/versions/c9d0e1f2a3b4_create_learning_paths_and_units.py`（114 行）：
  - `learning_paths`：id / user_id (FK CASCADE) / title (VARCHAR 200) / description / created_at / updated_at + index user_id
  - `learning_units`：id / path_id (FK CASCADE) / concept_id (FK RESTRICT) / order_index / content (JSON) / status (VARCHAR 20 + CHECK enum) / completed_at + UNIQUE(path_id, order_index) + CHECK order_index >= 0 + index path_id, concept_id
  - status enum 4 值：`locked` (預設) / `available` / `in_progress` / `completed`

### ORM
- `backend/models/learning.py`（109 行）：
  - `LearningUnitStatus(str, Enum)` — locked/available/in_progress/completed
  - `LearningPath` + `LearningUnit` model（與 alembic 對齊）
- `backend/models/__init__.py`：export `LearningPath` / `LearningUnit` / `LearningUnitStatus`

### 測試
- `backend/tests/test_learning_models.py`（12 個）：metadata / 欄位 / status enum 值 / 預設 status=locked / UNIQUE(path, order) 衝突 / status CHECK 阻擋非法值 / order_index < 0 阻擋 / FK ondelete CASCADE 宣告
- 全套 332 tests 全綠（320 → 332，+12 個新測試，零 regression）

### 設計關鍵
- **status 用 String + CHECK**：與 quiz/concept/reflection/comprehension 慣例一致；避開 PG ENUM 雙寫法 + SQLite 測試相容
- **`(path_id, order_index)` UNIQUE**：強制同路徑內位置唯一，禁止碰撞
- **`concept_id` ON DELETE RESTRICT**：概念被刪需先處理路徑（避免遺孤學習單元）
- **`path.user_id` ON DELETE CASCADE**：使用者刪除帳號連動刪除路徑與單元
- **預設 status='locked'**：路徑生成（3-1b）後由 service 解鎖第一單元，後續漸進解鎖
- **`content` 用 JSON dict 不強制 shape**：unit 內容（summary / examples / exercise_question_ids）依教學需求演進，application 層驗證
- **不加 `is_active` / `archived_at`**：MVP 不支援軟刪除，避免不必要欄位（精準修改不擴散）
- **預留 polymorphic target**：reflections.source_type='learning_unit' 已預留指向 learning_units.id（無 FK，application 層驗證）

---

## [2026-05-05] — Phase 2-6e：動態觸發頻率 + 驗證結果驅動 BKT（Phase 2-6 完成 🎉）

### 新增（Service）
- `backend/services/comprehension/mastery_hook.py`（51 行）：
  - `apply_comprehension_mastery(db, user_id, question, passed)` — comprehension 通過/不通過 → BKT
  - `passed=True` → Evidence(NONE) 上調 confidence；`passed=False` → Evidence(LOGIC) 下調
  - `passed=None`（EPL fallback）→ no-op（無有效信號避免噪音）
  - `update_mastery` 異常 swallow（best-effort，與 quiz/submit 容錯一致）
- `backend/services/comprehension/trigger.py`（120 行）：
  - `TriggerDecision` dataclass + `decide_trigger(db, user_id, student_answer_id)`
  - 純規則 `_decide(pass_rate, is_coding)`（獨立函式方便 unit test）
  - 取近 5 筆有 `comprehension_passed` 的紀錄算 pass_rate；無紀錄 = cold start
  - 規則表：cold start → EPL；≥0.8 → 不觸發；[0.6, 0.8) → VARIATION；[0.3, 0.6) → PREDICT_OUTPUT；<0.3 → EPL
  - 非 coding 題 → PREDICT_OUTPUT/VARIATION 自動 fallback EPL（reason 補上 `（題型非 coding，fallback EPL）`）

### Workflow 整合
- `services/comprehension/orchestrator.py`：`submit_epl_for_answer` + `submit_predict_for_answer` 在 commit 前呼叫 `apply_comprehension_mastery(...)`
- `services/comprehension/variation.py`：`submit_variation_for_answer` 同樣串接 mastery hook
- 三條 grade pipeline 通過後皆驅動 BKT；EPL passed=None 跳過

### API
- `backend/api/routes/comprehension_trigger.py`（57 行）：
  - `GET /comprehension/trigger-suggestion/{student_answer_id}` → `TriggerDecisionOut`（should_trigger / suggested_type / pass_rate / sample_size / reason）
- `backend/main.py`：註冊 `comprehension_trigger_router`

### 測試
- `backend/tests/test_comprehension_trigger.py`（12 個 unit）：cold start / 高 / 中高 coding+非 coding / 中等 coding+非 coding / 低；threshold 邊界值
- `backend/tests/test_comprehension_mastery_hook.py`（4 個 unit）：passed=True/False/None / update_mastery 異常 swallow
- `backend/tests/test_comprehension_trigger_route.py`（6 個 HTTP）：401 / 跨使用者 404 / cold start / 高 skip / 中等 predict / 中高非 coding fallback / 低 EPL
- `backend/tests/test_comprehension_mastery_integration.py`（4 個整合）：EPL grade 通過 → mastery confidence > 0；EPL passed=None → mastery row 不存在；Predict / Variation grade 通過 → mastery 上調
- 全套 320 tests 全綠（293 → 320，+27 個新測試，零 regression）

### 設計關鍵
- **passed=None 不觸碰 mastery**：BKT 演算法對「答錯」與「未評分」應有差別 — fallback 不該被當作扣分，否則 LLM 偶發失敗會誤傷學生信心度
- **trigger 純規則 + DB 查詢**：可預測、易測；不引入隨機性 / RL（避免過度工程，符合守則 #7「不過度設計」）
- **threshold 集中常數**：`HIGH_PASS_THRESHOLD` / `MID_HIGH_PASS_THRESHOLD` / `MID_LOW_PASS_THRESHOLD` 提到 module 頂端，方便未來 A/B test 調參
- **`_decide` 獨立函式**：12 個 unit test 直接覆蓋規則矩陣，不需 DB；`decide_trigger` 只負責 fetch + dispatch
- **route 拆獨立檔**：trigger endpoint 放 `comprehension_trigger.py`，主 `comprehension.py` 維持 242 行不超 250

### Phase 2-6 整體里程碑
- ✅ 2-6a Schema 擴充 + Comprehension API
- ✅ 2-6b EPL 驗證
- ✅ 2-6c 預測輸出驗證
- ✅ 2-6d 變體挑戰
- ✅ 2-6e 動態觸發 + BKT 串接
- 全套後端 320 tests 全綠，準備迎接 Phase 3 學習體驗（Learn / Quiz / Dashboard 頁面）

---

## [2026-05-05] — Phase 2-6d：變體挑戰（LLM 生變體題 + 評分學生新解）

### 新增（Service）
- `backend/services/comprehension/variation.py`（242 行）：
  - `VariationGenerationResult` / `VariationGradeResult` dataclass
  - `_call_llm_json` 共用 helper（dedupe 兩 LLM 呼叫的 boilerplate；換取行數壓在 250 限制內）
  - `generate_variation(question, student_code)` / `grade_variation(...)` LLM 函式
  - `start_variation_for_answer` / `submit_variation_for_answer` workflow（DB + LLM 整合）
  - **StrictBool**：`_GradeResponse.passed` 拒絕 `"yes"` / `"true"` / `1` 等 LLM 文字噪音的隱式轉型
- `backend/services/comprehension/variation_prompts.py`（90 行）：
  - `build_generate_prompt`：強調「同核心概念、變更非本質特徵」（情境 / 數值 / 邏輯方向）
  - `build_grade_prompt`：LLM 心智模擬執行學生 code 對 test_cases；binary passed + feedback

### API
- `backend/api/routes/comprehension_variation.py`（99 行，獨立檔避免 comprehension.py 超 250 限制）：
  - `POST /comprehension/{id}/variation/generate` — 露 stem/starter/test_cases/concept_focus
  - `POST /comprehension/{id}/variation/grade` — body `{student_code: str}`
- `backend/main.py`：註冊 `comprehension_variation_router`

### 測試
- `backend/tests/test_comprehension_variation.py`（13 個 unit）：prompt 組裝 / generate 5 種 fallback / grade 通過 + 不通過 + LLM 不可用 + StrictBool ValidationError + 空 feedback 正規化
- `backend/tests/test_comprehension_variation_route.py`（10 個 HTTP 整合）：401 / generate 持久化 + 清空舊 / 422 非 coding / 503 LLM 失敗 / 跨使用者 404 / 400 未先 generate / grade 通過 / grade LLM 失敗 fallback / 跨使用者 grade 404
- 全套 293 tests 全綠（270 → 293，+23 個新測試，零 regression）

### 設計關鍵
- **題型限制**：variation 僅對 coding 有效（其他 → 422 VARIATION_NOT_APPLICABLE）；MC/fill_blank 的「變體」概念意義有限
- **Storage**：完整題目 payload（stem + starter_code + test_cases + concept_focus）JSON 編碼存 `comprehension_prompt`
- **test_cases 公開**：學生需看 test_cases 才知道目標 I/O，與 predict_output 的「藏 expected」不同
- **「禁用 AI」屬前端責任**：variation 流程不串接 chat / EDF / hint，純 LLM 出題 + 評分閉環；前端 UI 應隱藏 chat panel（後續 UI task 處理；docstring 註明 design intent）
- **保守 fallback**：grade LLM 失敗 → `passed=False`（避免錯給通過拉高 mastery 信心度，與 EPL 的 `passed=None` 不同 — Variation 是「最後一關」更謹慎）
- **StrictBool**：拒絕 LLM 文字噪音 `"yes"` 被隱式轉為 True；保證 passed 真實反映 LLM 判斷
- **拆檔**：variation.py 原 269 行 → 抽 `_call_llm_json` helper 後 242 行；route 拆獨立檔避免 comprehension.py 超 250

---

## [2026-05-05] — Phase 2-6c：預測輸出驗證（自動生新測資 + 兩階段比對）

### 新增（Service）
- `backend/services/comprehension/predict_output.py`（199 行）：
  - `PredictGenerationResult` / `PredictGradeResult` dataclass（frozen）
  - `normalize_output(text)` — trim + 折疊內部空白 + 去空行（Stage 1 嚴格比對前置）
  - `generate_predict_test(question, student_code)` — LLM 生新測資 + expected
  - `grade_predict_answer(...)` — 兩階段：嚴格 → LLM 語意 → fallback mismatch
  - `match_method` ∈ {exact, semantic, mismatch}
- `backend/services/comprehension/predict_output_prompts.py`（86 行）：
  - `build_generate_prompt`：強調「不重複 test_cases」+「對學生實際程式」推理 expected（含 bug 行為）
  - `build_semantic_grade_prompt`：判斷「語意一致」（允許格式差異 / 拒絕邏輯錯誤）
- `backend/services/comprehension/orchestrator.py`（+108 行）：
  - `start_predict_for_answer` — 拒非 coding（422）→ LLM → JSON 寫入 prompt（input + expected）+ 清空舊 answer/passed
  - `submit_predict_for_answer` — 從 prompt 解 JSON → 比對 → 寫 answer/passed

### API
- `backend/api/routes/comprehension.py`（242 行，+68）：
  - `POST /comprehension/{id}/predict_output/generate` — 回 input；不洩漏 expected
  - `POST /comprehension/{id}/predict_output/grade` — body `{predicted_output: str}`；回 passed + match_method + expected_output（學生已答完可對照）
  - `PredictGenerateOut` / `PredictGradeOut` response schemas

### 測試
- `backend/tests/test_comprehension_predict.py`（16 個 unit）：normalize 5 案 / generate 成功 + 4 種 fallback / grade exact / normalize match / semantic 通過 / semantic 不通過 / LLM unavailable + exception fallback
- `backend/tests/test_comprehension_predict_route.py`（11 個 HTTP 整合）：401 / generate 持久化 + hide expected / 清空舊 / 422 非 coding / 503 LLM 失敗 / 跨使用者 404 / 400 未先 generate / exact 通過 / mismatch fallback / 跨使用者 grade 404
- 全套 270 tests 全綠（243 → 270，+27 個新測試，零 regression）

### 設計關鍵
- **題型限制**：predict_output 只對 coding 有意義（其他 → 422 PREDICT_OUTPUT_NOT_APPLICABLE），避免「對 MC 預測輸出」這種無意義操作
- **expected 不洩漏**：generate response 只回 `test_input`；server 把 `{"input", "expected"}` 用 JSON 編碼存入 `comprehension_prompt`，grade 時解出比對
- **expected 對學生實際程式**：LLM 推理時被告知「對學生這份程式（含可能的 bug）」的輸出，而非題目正解 — 教學目標是「能否預測自己程式行為」
- **兩階段比對**：先嚴格 normalize（trim + 折疊空白）→ 不通過再 LLM 語意 → 任一通過即 passed=True；學生友善（容忍 `1, 2, 3` vs `1 2 3`）但保留精確性（順序 / 數值錯誤一律不過）
- **LLM 失敗對稱**：generate → 503；grade Stage 2 失敗 → fallback 用 Stage 1 結果（mismatch passed=False，不擋學生流程）
- **expected 即時回前端**：grade response 帶 `expected_output`，學生答完可自我對照學習

---

## [2026-05-05] — Phase 2-6b：EPL 驗證（LLM 出題 + 評分學生回答）

### 新增（Service）
- `backend/services/comprehension/epl.py`（159 行）— LLM 客戶端 + dataclass + async 流程：
  - `EplGenerationResult` / `EplGradeResult` dataclass（frozen）
  - `generate_epl_prompt(question, student_answer)` — 出 EPL 題；失敗回 prompt=None
  - `grade_epl_answer(question, student_answer, epl_prompt, epl_answer)` — 評分；失敗回 fallback
  - 評分 3 面向：conceptual_correctness / specificity / causality；passed = (avg ≥ 0.6)
- `backend/services/comprehension/epl_prompts.py`（111 行）— 純 prompt 模板獨立檔（避免 epl.py 超過 250 行硬性限制）：
  - `format_student_answer` — 題型決定格式（coding 出 code block / MC 解析選項文字 / fill_blank 列出填空）
  - `build_generate_prompt` — 生成 EPL 題的 system prompt
  - `build_grade_prompt` — 評分學生 EPL 回答的 system prompt
- `backend/services/comprehension/orchestrator.py`（106 行）— 整合 LLM + DB：
  - `start_epl_for_answer` — 取作答 + 題目 → LLM → 寫 type/prompt + 清空舊 answer/passed
  - `submit_epl_for_answer` — 校驗已 generate → LLM → 寫 answer/passed
  - LLM 失敗：generate → 503；grade → 200 但 passed=None（不擋學生）

### API
- `backend/api/routes/comprehension.py`（174 行）：
  - `POST /comprehension/{student_answer_id}/epl/generate` — 出題（重置語意）
  - `POST /comprehension/{student_answer_id}/epl/grade` — 評分，body `{epl_answer: str}`
  - `EplGenerateOut` / `EplGradeOut` response schemas（細項分數即時回傳，不入庫）

### 測試
- `backend/tests/test_comprehension_epl.py`（16 個 unit）：format / prompt building / LLM 成功 / fallback (no client / exception / invalid JSON / empty prompt / ValidationError) / 通過閾值 / 不通過 / feedback 空字串正規化
- `backend/tests/test_comprehension_epl_route.py`（9 個 HTTP 整合）：401 / generate 持久化 + 清空舊 / generate LLM 失敗 503 / generate 跨使用者 404 / grade 未先 generate 400 / grade 成功 / grade LLM 失敗 200 但 passed=None / grade 跨使用者 404
- 全套 243 tests 全綠（218 → 243，+25 個新測試，零 regression）

### 設計關鍵
- **重置語意**：generate 每次都清空 `comprehension_answer/passed`，避免新 prompt 搭配舊回答的資料錯亂
- **順序強制**：grade 必須先 generate（無 prompt → 400 EPL_NOT_STARTED），確保 LLM 評分時有完整脈絡
- **失敗策略不對稱**：generate 失敗 503（前端可重試）；grade 失敗 200 + passed=None（學生回答仍持久化方便重試評分，不擋流程）
- **細項分數不入庫**：schema 只有 `comprehension_passed: bool`；conceptual/specificity/causality 屬即時回饋，前端顯示一次即可，不需歷史追蹤
- **拆檔對齊 250 行限制**：epl.py 原 264 行 → 拆出 epl_prompts.py（純字串模板）後 159 行，符合 CLAUDE.md 硬性門檻

---

## [2026-05-05] — Phase 2-6a：Post-Solution Comprehension Check 持久化基礎

### 新增（Schema / Migration）
- `backend/alembic/versions/b8c9d0e1f2a3_add_comprehension_to_student_answers.py`（66 行）— `student_answers` 表加 4 個 nullable 欄位：
  - `comprehension_type` (varchar 20, nullable) — `epl` / `predict_output` / `variation`
  - `comprehension_prompt` (text, nullable) — 系統出的驗證題目
  - `comprehension_answer` (text, nullable) — 學生回答
  - `comprehension_passed` (boolean, nullable) — 是否通過驗證
  - CHECK constraint：`comprehension_type IS NULL OR ∈ enum`

### ORM
- `backend/models/quiz.py`：`StudentAnswer` 加 4 欄位 + `ComprehensionType(str, Enum)`（EPL / PREDICT_OUTPUT / VARIATION）
- `backend/models/__init__.py`：export `ComprehensionType`

### Service
- `backend/services/comprehension/__init__.py` + `crud.py`（79 行）：
  - `get_comprehension(db, student_answer_id, user_id)` — 擁有權檢查（非本人 → 404）
  - `upsert_comprehension(db, student_answer_id, user_id, payload)` — partial upsert，未提供欄位保留原值
  - `ComprehensionUpdate` dataclass

### API
- `backend/api/routes/comprehension.py`（108 行）：
  - `GET /comprehension/{student_answer_id}` — 讀取 4 欄位狀態
  - `PUT /comprehension/{student_answer_id}` — partial upsert
  - 422 type 非法 / 404 跨使用者或不存在
- `backend/main.py`：註冊 `comprehension_router`

### 測試
- `backend/tests/test_comprehension_route.py`（10 個整合測試）：401 未登入 / GET 初始狀態 null / 完整 PUT / partial PUT 保留欄位 / 422 type 非法 / 404 跨使用者 / 404 不存在
- 全套 218 tests 全綠（208 → 218，+10 個新測試，零 regression）

### 設計關鍵
- **nullable + 同表擴充**：comprehension 為「解題後選擇性驗證」，多數作答不觸發；nullable 欄位比 1:1 副表省一個 join
- **404 而非 403**：跨使用者一律回 STUDENT_ANSWER_NOT_FOUND，避免列舉攻擊揭露存在性（與 reflection / chat 服務一致）
- **partial PUT**：未提供欄位保留原值，方便分階段寫入（例：先存 prompt，學生答完再寫 answer + passed）
- **Service 不做 LLM**：本層僅持久化；EPL / 預測輸出 / 變體題的 LLM 生成與評分屬 2-6b/c/d
- **不加 `comprehension_completed_at`**：嚴格對齊 db-schema.md 4 欄位規格；2-6e 動態觸發頻率需要時再 migrate

---

## [2026-05-04] — Phase 2-5 Pre-Coding Reflection：教學設計與容錯

**PRIMM 對齊的流程修正**：原本「拿題目 → 立刻彈反思 modal」，學生**還沒看到題目**就被要求
反思，違反 PRIMM「反思必須針對具體題目」。改為多一個 `preview` 階段：題目先顯示、
學生讀完主動點「開始反思」才彈窗；取消反思回到 preview 而非丟棄已生成的題目。

**三面向獨立評分而非單一分數**：`understanding` / `plan_quality` / `concept_recall` 各自 0–1，
`quality_score` 取三者平均（簡單可解釋，不加權）。分開的理由是**追問要挑最弱的面向**，
單一總分做不到。

**追問的三道防線**（避免反思從教學工具變成負擔）
- `QUALITY_THRESHOLD = 0.6`，高於門檻時**強制清空** LLM 多嘴生出的 followup ——
  門檻行為由程式碼保證，不靠 prompt 約束
- `MAX_FOLLOWUP_ROUNDS = 2`，第二輪後給「已盡力，直接看題」放行，不無限 loop
- **LLM 失敗（quality_score=null）一律視為通過** —— OpenAI 抖動不能擋住學生做題

**反思注入 EDF 分兩個版本**：Evidence 收**簡短版**（步驟 + 預期概念），避免反思內容稀釋
程式碼分析；Feedback 收**詳細版**（含品質分數），讓 AI 能引用學生計畫做蘇格拉底式提問。
格式化 helper 內建「**嚴禁直接幫學生補完計畫**」規則 —— 否則 AI 會變成代寫工具。
prompt 順序 `preamble → persona → strategy → context → reflection → rag` 由測試強制保證。

**權限隔離用 404 而非 403**：他人的 reflection 一律回「不存在」，避免 ID 列舉攻擊揭露存在性。
載入失敗（DB 異常／不存在／非本人）都不擋教學流程，與 mastery / RAG 同一套容錯哲學。

**side panel 的持久化用 sessionStorage 不擴後端**：省下 list / latest 端點。
`storage` event 預設只在**其他** tab 觸發，所以另外發 `CustomEvent` 補同 tab 場景；
反思被刪除時 404 自動清掉 sessionStorage，UI 退回空狀態而不是顯示錯誤。

**`source_id` 用 polymorphic UUID 不建 FK**：指向 `questions.id` 或 `learning_units.id`
（後者當時還沒建表），由 service 層依 `source_type` 決定驗不驗。
`(user_id, source_type, source_id)` UNIQUE ——同一學生對同一題只能有一份反思。
`quality_score` / `followup_question` 保持 nullable，讓 LLM 評分能後補而不動 schema。

## [2026-05-04] — Phase 2-4 智慧出題：Select → Generate → Validate 的設計

**enum 從此改用 `String + CHECK`**：踩過三次 PG ENUM 的坑後，`questions.type` / `source`
等新欄位一律字串 + CHECK 約束，ORM 端保留字串列舉維持型別語意。
`concept_tags` 用 JSON 而非 PG `text[]` —— 避免 PG-only 型別讓 SQLite 測試壞掉；
題庫規模 < 1000 全表掃可接受，需要 GIN index 再 migrate。
`content` / `answer` 也用 JSON：三種題型的形狀不同，shape 驗證交給 application 層。

**Select 的中心度加權**：`score = (1 - confidence) × (1 + 0.2 × out_degree)`。
foundation 概念（如 `syntax-basic` 有 5 個後續依賴）若是弱項，補強價值高於孤立弱項。
兩條刻意的邊界：
- **只在已有 mastery row 且 confidence < 0.4 中挑** —— 前置概念沒 row 表示學生根本沒接觸，
  主動測試只會擾亂他
- **cold-start 回空 list** —— 本層只負責「弱項」語意，「怎麼開始」交給 Generate 決定

**Generate 的 content 二次驗證**：LLM 即使遵循 prompt 仍會漏欄位，三種題型各有 Pydantic
模型驗證後才寫 DB（MC 還加 `field_validator` 確保 `answer_index < len(options)`）。
用 `json_object` 而非 `json_schema` strict —— strict 對 output 限制較嚴，可能誤拒合理題目。

**Validate 回報告而非拋例外**：LLM 生出爛題是**正常情境**不是錯誤，caller 需要看 issues
決定 retry 還是丟棄；只有「LLM 不可用」才 raise。三面向 AND：答案正確性 / 概念吻合 /
Bloom 不超標，任一不過就列 issue。
**retry 上限 2 次**，連續失敗回 503 而非無限呼叫 LLM。

**答案 mask 在 route 層**：`_mask_content_for_student()` 讓 GET 端點不下發答案欄位
（避免 DOM 洩漏），submit 後才回完整 content。

**generate / validate 共用 transaction**：service 一律不 commit，讓 validate 能在同一個
transaction 內補標 `validated=True`。

## [2026-05-04] — Phase 2 智慧功能：RAG／知識圖譜／BKT 的設計決策

> 建置明細查 `git log --since=2026-05-04 --until=2026-05-05 --stat`。

**踩了三次才根除的 PG ENUM bug**（值得單獨記）
`sa.Enum(...)` 預設送 `enum.name` 而 Postgres 欄位接的是 `enum.value` → 500
`InvalidTextRepresentation`。修法是每個 Enum 欄位加
`values_callable=lambda x: [e.value for e in x]`。
**為什麼會踩三次**（UserRole → MessageRole → EdgeType）：測試走 SQLite，SQLite 沒有 ENUM 型別，
所以本機全綠、一上 PG 才爆。`concept_edges` 更晚才暴露——表空的時候根本不會讀到 enum。
→ 後續 `student_mastery.bloom_level` 直接改用 `SmallInteger + CHECK`，不再碰 PG ENUM。
另一個相關陷阱：`op.create_table` 會自動 `CREATE TYPE`，**不可**再預先 `enum.create()`，否則
`DuplicateObjectError`。

**Auth.js v5 的 HKDF info 字串變了**
從 `"NextAuth.js Generated Encryption Key"` 改為
`"Auth.js Generated Encryption Key (cookie_name)"`，且 cookie_name 與 salt 需從 request
動態取得（dev / prod 的 cookie 名不同 → 衍生出不同 key）。不改就是 401 INVALID_TOKEN。

**BKT 的 OSS 合規路徑**（守則 8）
pyBKT 已列為宣告依賴，但 `Model.fit()` / `Roster` 需要歷史資料，cold-start 無從用起。
決策：**冷啟動用標準 BKT Bayes 公式**（Corbett & Anderson 1995 的公開教科書數學，
**不是移植 OATutor 的 JS 實作**）；等 Phase 5 有真實資料後跑 `fit()` 學 per-concept 參數，
只換 `BKTParams` 的數值，**演算法本身不動**。
⚠ `scikit-learn` 必須 `<1.7` —— pyBKT 1.4.1 與 1.7+ 的 `_log_loss` API 不相容。

**mastery 資料表用 lazy 建列**：學生實際互動時才建 row，避免 user × concept 的笛卡兒積空白列。

**RAG 一律失敗安全**：`fetch_rag_chunks_safe` 吞掉所有異常回 `[]` —— RAG 掛掉只是少了教材引用，
不能因此讓學生拿不到教學回應。同一個 try/except 模式後來也用在 mastery 更新上。
（當時 RAG 觸發沿用 Decision 層的 `hint≥2 且 bloom≥ANALYZE`，**已於 K4b 改為內容相關性檢索**。）
刻意**不做 BM25 reranking**——最小可用，等召回品質實測不足再補。

**API 以 `tag` 而非 UUID 作識別**：`/concepts/pointer-arithmetic` 比 UUID 穩定且 URL 友善。

**RAG 管線參數**（LlamaIndex `IngestionPipeline`，全程不自寫 chunking／embedding）：
`SentenceSplitter` chunk 512 / overlap 64 → `text-embedding-3-small`（1536d）→ pgvector
表 `data_codedge_rag`。檢索結果用自家 `RetrievedChunk` 包一層，
**避免 LlamaIndex 型別擴散到 EDF 上層**。

**知識圖譜的視覺取捨**（定調 Obsidian 風：ellipse 圓點 + 細 bezier 曲線 + 標籤外置）
- 用 Cytoscape `underlay-*` 而非 `outline-*` 畫精熟度：underlay 在節點底層產生光暈感，
  與 ellipse 風格協調；outline 邊緣太硬
- **顏色走兩個獨立通道**：fill ＝ 學科分類，underlay ＝ 精熟度。兩者色域重疊（綠/紅）
  但實測不會誤讀
- **未互動的概念不畫圈**：否則新使用者一進來看到整張紅圖會被嚇到
- hover 時 `closedNeighborhood()` 高亮、其餘 `.faded`；`syntax-basic` 自然成為中央放射樞紐
- fetch 上提到 page 層（mastery 要同時餵 graph 與 panel），graph 元件降為 presentational

**API 契約細節**：`/concepts/graph` 直接回 Cytoscape 慣例格式（`source`/`target` 而非
`source_id`）省去前端轉換；鄰居明確標 `incoming` / `outgoing`，前端才能顯示「先修」vs「進階」。
service 回 ORM、route 層做 Pydantic serialization，兩層邊界保持乾淨。

**20 個 ConceptTag 是 authoritative**，但 category / difficulty / name_zh 為 AI 暫定值。
初始 23 條 concept edge 同樣是 AI 暫定，**後於 K1a 由 curated DAG 全面取代為 90 條多對多邊**。

## [2026-04-29] — 本機開發環境工具選型

- **Colima 取代 Docker Desktop**：brew cask 安裝需要 sudo TTY，非互動環境過不去
- **uv 取代 brew Python**：brew 的 Python 3.12 在 macOS Tahoe 有 expat 動態連結 bug；
  uv 自帶 portable CPython 繞開
- **本機 `docker-compose.dev.yml` 不進部署路徑**（部署走 `zeabur.json`），但 image 對齊
  `pgvector/pgvector:pg16`，確保本機與生產跑同一份 migration
- **chunks 與向量表交給 LlamaIndex `IngestionPipeline` 自動建**，不寫進 migration
  ——後果是它不在 alembic 管轄內，7-1a-3 生產播種時必須另外 pg_dump 搬

## [2026-04-29] — OSS 重用策略 + Roadmap 重排

**OSS 決策矩陣正本在 `docs/references.md` §1**（4 Tier）與 §2（授權黑名單）；
同日寫入 `CLAUDE.md` 執行守則 #8：開發前必查矩陣，新增 dependency 須列出 license。
關鍵禁令：**PM4Py 因 AGPL 禁用**（改 prefixspan）、**BKT 必用 pyBKT 不得 port OATutor**、
學習路徑用拓撲排序不採 EduAdapt-AI RL。

**Roadmap 重排（部署延後至 Phase 4）的理由**：API 串接 + Zeabur 反覆卡關，
與其邊做功能邊修部署，不如先把學生端做完、一次性處理部署。

## [2026-04-29] — 品牌命名：Codedge 平台 + Coddy AI 助教

- **Codedge** ＝ `Code` + `Edge` 字母融合（共享 `e`），三層意義：cutting-edge 程式前沿／
  edge case 邊界案例（CS 核心術語）／"have the edge" 取得優勢
- **Coddy** ＝ AI 助教名，承襲 `Cod-` 字頭與品牌呼應
- **副標「會思考的學習，從會提問的 AI 開始」** — 點出與 ChatGPT 直接給答案的差異化；
  取代原 slogan「Coddy 陪你寫 C++，磨穿每個 edge case」（受苦感、未體現雙關）
- **login hero 不放「Code with Edge」**：h1 `Codedge` 已等同拆解後的字面，並列即重複。
  但 `<title>` 保留 —— browser tab / SEO 場景單獨出現時，它才是揭示雙關的地方
- 歷史條目中的「C++ Tutor」「AI 導師」保留原貌不回溯修改

## [2026-04-29] — R8 反 AI 感規則的由來

**觸發**：使用者指出截圖中「右上 chat icon 半透明 halo + 紫色圓 bot 頭像 + `⚠` emoji」
＝廉價 AI 感；專業工具（Linear / Stripe / Vercel）皆無此風格。

**規則正本在 `.claude/rules/frontend.md` R8.1–R8.5**：禁半透明色背景／禁 emoji 符號字／
禁圓形彩色 halo 頭像／禁裝飾性彩色／active 狀態用 border 不用色背景。
例外白名單：灰階淡化 `text-text-muted/N`、shadcn 基礎元件、lucide 線條 icon、實線 border。

## [2026-04-29] — Chat 開關的兩次反覆（最終：極簡優先）

先把 toggle 改成「僅收合時顯示」，同日再整個移除。**最終狀態：Chat 只能靠 `Ctrl+B`
或面板內收合鈕開關，關閉後沒有視覺按鈕可重新開啟** —— 依使用者要求保持極簡。
若日後發現學生找不到入口，加回浮動按鈕即可（這是刻意接受的取捨，不是疏漏）。

## [2026-04-29] — Phase 1-6 介面精修：六項設計決策

**執行順序決策**：UI 統一精修先於部署——避免上線後再大幅改 UI。
（同時把原 Phase 1-6 部署順延為 1-7，因 API 串接 golden path 尚未通過。）

- **唯一視覺基本元素＝GitHub Dark token**：6 份外部借鑑（Cursor / Warp / Linear / Claude /
  Vercel / Raycast）**只貢獻結構模式**，不貢獻 color / font / shadow / border / radius / spacing。
  這條是後來 R1–R8 的源頭
- **兩處唯一視覺例外**：AI 訊息氣泡 ring（purple alpha）、`.kbd` 鍵帽多層 inset 陰影
- **導覽從 VSCode 左側欄改為 GitHub 頂部橫向**（180px sidebar → 48px top nav）：
  釋出水平空間給 Editor + Chat。這是 `ui-ux-spec.md` 後來大量失真的起點——
  它寫的 Activity Bar 從此不存在
- **訊息氣泡以 border 而非背景色區分角色**：User / AI 同 `bg-surface-1`，
  靠 border 顏色分辨——這是 R3「邊框唯一例外」的來由
- **Output 改 Run Block 列表**（仿 Warp）：新 block 置頂並自動收合舊 block，
  取代原本單次輸出的 tab UI
- **queued listener pattern**：chat 收合時點 block 的「詢問 AI」會先排隊，
  等 chat 掛載後再 drain——否則注入會靜默失敗
- **Surface token 採疊加而非取代**：`--surface-0/1/2/inset` 疊在既有 `--bg-*` 上，
  既有元件零影響

## [2026-04-29] — Google OAuth 本機驗證通過

Google Cloud Console redirect URI＝`http://localhost:3000/api/auth/callback/google`；
測試使用者需手動加入白名單（OAuth 測試模式限制，後來成為 100 人上限的伏筆）。
`AUTH_SECRET` 由 `openssl rand -base64 33` 產生，必須與後端 `NEXTAUTH_SECRET` 同值。

## [2026-04-13] — Phase 1 建置期的設計決策

> 建置本身（檔案、端點、測試）查 `git log --since=2026-04-13 --until=2026-04-14 --stat`。
> 以下只留當時做過、且影響至今的取捨。

**EDF 三層管線的原始設計**
- Evidence 用 **LLM JSON mode 而非 AST**：直接讓 LLM 輸出錯誤分類 + ConceptTag + Bloom，
  省下自建「AST 特徵 → 概念」規則工程（此決策於 K2c 重新檢視後維持，見 tech-debt E3）
- Decision 原為 **6×6 Bloom × Hint Ladder 矩陣（36 格）**，RAG 觸發條件＝`hint≥2 且 bloom≥ANALYZE`
  → 兩者都已被推翻：K4b 改為內容相關性檢索、7-C2a 改為累積式揭露階梯
- Feedback 分層組裝順序 **preamble → persona → strategy → context**，preamble 5 條不可覆寫

**三層輸入防護（正本見 `.claude/rules/backend.md`）**
Regex 偵測 injection → XML 標籤隔離（`<student_input>` / `<student_code>`）→ System Preamble；
輸出端 `validate_output()` 阻擋 >8 行且無 TODO 的完整程式碼。**四道防線缺一不可**：
Regex 擋已知樣式、XML 擋 LLM 混淆使用者輸入與系統指令、preamble 擋前兩者漏掉的。

**其他仍生效的取捨**
- **stdin 前端 UI 移除，但後端保留 `stdin` 參數** —— 供未來 test case 機制用
  （7-R 互動終端上線後此決策才真正兌現）
- **`WorkspaceContext` 用 ref 共享程式碼**，不用 state：避免每次鍵入觸發整棵樹 re-render
- **測試改 SQLite file-based 取代 in-memory**：in-memory 會綁定事件迴圈，async 測試取不到同一個 DB
- **前端一律走 Next.js API proxy**（`web/app/api/[...path]/route.ts`）不直連後端 ——
  同源避開 CORS，且 token 不落到瀏覽器可見的跨網域請求

## [2026-04-13] — 兩個跨模組教學機制的設計

- **Pre-Coding Reflection（解題前反思閘門）**：採**方案 B ＝ 只給一次追問機會**，
  不無限追問——反思是為了降低認知外包，本身不該變成負擔（後續 U2h 進一步寬容化）
- **Post-Solution Comprehension Check**：三型（EPL 自我解釋／預測輸出／變體挑戰），
  驗證的是「能不能遷移」而非「能不能重複」

## [2026-04-12] — 文檔架構重構：為 AI 上下文效率而設計

把 7 個舊文件重組為 8 份 docs + 3 份 `.claude/rules/`。**核心決策是引入 `.claude/rules/`**：
依 glob 自動注入（`web/**` → frontend.md、`backend/**` → backend.md、
`backend/services/edf/**` → edf-pipeline.md），讓規則在「要用到的時候」才進上下文，
而不是全部塞進 CLAUDE.md。這條決策至今仍是文檔分層的基礎。

## [2026-04-11] — 專案初始化
