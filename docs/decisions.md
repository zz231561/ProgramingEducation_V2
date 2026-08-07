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

## [2026-08-08] — 文件契約 drift 的三層防線

### 為什麼採 AST inventory + fingerprint

method/path、table/column、env、page route 與 service name 適合直接列出差集；request/response、
status、auth dependencies 及 DB constraints 的完整展開量很大，若把 83 筆 OpenAPI 或 SQLAlchemy
metadata 複製進 Markdown，文件會重新變成難以閱讀的機械快照。因此保留人類可讀的 endpoint／schema
摘要，並以 normalized signature fingerprint 偵測細節變更；drift 時必須先更新文件，再更新 fingerprint。

### 否決方案

- **只靠規則提醒**：無法阻止漏跑，故接入 GitHub CI。
- **把完整 OpenAPI / metadata JSON commit 到 docs**：diff 噪音大、AI 讀取成本高，且與
  `api-spec.md`／`db-schema.md` 重複。
- **解析自然語言判斷所有架構敘述**：容易誤判；敘述性內容維持人工核對，機械 gate 只處理
  可建立明確 inventory 的契約。

## [2026-08-08] — Runner 30 並行容量實測

### 實測數據與結論

B 機以 30 支不同 C++ 程式強制避開 binary cache，同時呼叫 `POST /run`：30/30 成功，
全批 3.491 秒，latency p95 3.428 秒，queue p95 495 ms；runner peak 178.17% CPU、
74.96 MiB RAM。2-slot gate 成功把編譯壓力限制於兩核心內，結果優於 server-plan 原估的
最後一人約 6 秒，因此維持 2C2G 與 gate=2，不升級 4C4G。

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

### Rule set 校準依據
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

### 實際健檢結果：程式碼比預期乾淨
使用者關切的三類問題實測幾乎不存在——**低效寫法 2 個**、**被註解掉的程式碼 0 個**
（原 2 個是欄位說明註解的誤判）、jscpd 重複率 **0.28%**。
真正的債是「44 個未使用 import」與「lint 從沒跑過」本身。

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

### 實測數據（本次決策依據，非引用）
- jscpd 全專案重複率 **0.28%**（276 檔）——遠低於業界 3–5% 警戒值，
  「vibe coding 必然產生大量重複」在本專案**不成立**
- 但預設門檻漏掉 tech-debt C3：`--min-lines 5 --min-tokens 30` 才抓到 `_get_client`
  跨 14 檔的 7 行 near-duplicate。**那 14 檔全部通過行數檢查**——已回填 C3

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

## [2026-08-06] — 7-C3 Comprehension 前端 UI（2-6 後端完整但學生一直碰不到）

### 待觀察（7-C4）
- 觸發頻率：後端規則是通過率 ≥ 0.8 才不觸發，冷啟動必觸發 EPL。多題連續作答時
  可能每答對一題就彈一次（每次 2 次 LLM 呼叫）——**刻意先不加前端節流**，
  以免未經討論就削弱 2-6e 的自適應設計；7-C4 用實際頻率數據裁決
- 規格線框寫的是 emoji 標題（🧠），實作改用 lucide `Brain`（frontend.md R8.2 禁 emoji）

---

## [2026-08-06] — 7-C2b 其餘 P1 修正（NZEC 語意 / 逾時文案 / 說明規則 / 429 顯示）

### 實測驗證（P1 重跑）
RULE-7 生效：由基準的「評測平台**通常**會視為異常結束」變成
「**本平台的判定**：我這邊會把非零結束狀態判成 Runtime Error」，第 4 輪並自動分成三層陳述。
⚠ 觀察：LLM 在散文中仍會把「非零＝失敗」講成 C++ 標準的規定（嚴格說那是實作定義）——
機械文案本身正確，此為 prose 精確度問題，記入 7-C4 觀察

## [2026-08-06] — 7-C2a'' 收尾：B8 消除 + 「我卡住了」按鈕 + Evidence 容錯 + 七型全驗

### 決策依據與證據
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

## [2026-08-06] — 7-C2a' 選層輸入改寫：persistence（追問次數）→ need（需求量估計）

> 使用者要求「跳脫現有規則構思最接近完美的解法」後的重寫。**核心主張：堅持不等於值得。**
> 舊的 persistence 是「同脈絡追問了幾次」，實測顯示它把三種完全不同的學生混為一談——
> 認真卡住的、在對話中一直有進展的、單純施壓索答的，全都是 +1。

### 實測對照（真實 LLM，同一組 persona 腳本）

| persona | 舊 persistence | 新 need |
|---|---|---|
| P1 迷惘新手（真卡住） | reveal 2→3→**5**→5（第 3 輪就封頂） | 2→3→**4**→4（穩定爬升） |
| P3 答案索取型（四輪施壓） | 1→1→2→**4**（施壓有效） | **1→1→0→0**（need 恆 0，施壓無效） |
| P2 按部就班型 | — | comprehension 兩輪皆 understood → need 0、reveal 0 |

P3 停在 base **不是靠關鍵字黑名單擋的**，是因為他從未付出可觀測的努力、也從未表示不理解。
P2 證實不需要脆弱的「致謝歸零」規則：理解訊號本身就會把 need 壓住。

## [2026-08-06] — 7-C2a 實作：Decision 層改累積式揭露階梯 + 動態選層（方案 B）

> 同日設計定案（見下一節）的實作。行為驗證（`eval_coddy` 七型重跑對照）屬 7-C4，尚未執行。

### 決策依據與證據
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

### 矛盾的解法：移除離群值而非新增裁決
- 明文原則：**RULE-1／RULE-2 是階梯之上的不變量，任何等級都不得突破；
  L5 的「完整」指解釋完整、非程式碼完整**
- 依據＝`modules.md` 引用的 CodeAid 研究（不給直接程式碼的 AI 學習效果更好）是整個設計的證據基礎，
  為了階梯好看而破例會拆掉地基
- 附帶發現：edf-pipeline.md 寫 L5「僅在反覆失敗 5+ 次後觸發」，**此門檻從未被任何程式碼實作**

## [2026-08-06] — docs：8-1d 自檢 script + roadmap 重排（技術債納入排程）+ 全域文件同步

> 使用者要求：重整現況、重排 roadmap（以現在進行的事為主）、技術債清理排在**功能之後驗收之前**、
> 確保文檔與現況一致無幻覺，並新增「小問題當輪直接修」守則。

### 決策依據與證據
- 依性質重編為 A 功能缺口 / B Coddy 品質 / C 測試與工程 / D 部署 / E 內容視覺，每項給編號供 roadmap 引用
- **關閉兩條已失去現實對應的項目**：7-R 過渡期 stdin 兩缺陷（R4/R5d 已上線，回退前提不可能成立）、
  Zeabur PREBUILT schema 未實測（實際部署走 dashboard 手動建 service，未用該 template 路徑）
- 已消除項集中到底部並補上 7-C 系列 9 項；表頭聲明「機械事實一律以 doc_selfcheck.py 產出為準」
- C2 檔案大小更新為**實測 8 個超硬上限**（原記 4-5 個，且遺漏 variation/comprehension/quiz-feedback）

### 決策依據與證據
- `CLAUDE.md`：新增**守則 9「當場修小問題」**（範圍小＋根因明確＋不需設計裁決＝當輪直接修，
  只有擴散性改動 / 架構或教學設計取捨 / 根因未定才需討論）；當前狀態改寫為 7-C 主線 + 兩項工具指引
- `docs/acceptance-checklist.md`：標題區註明對應 7-E、開始時機為 7-C+7-D 完成後，並列出待增補的新驗收點

## [2026-08-06] — feat(eval) + fix(coddy)：7-C1' 七型學生模擬驗收 harness + 診斷輪修復 9 項

> 使用者指示：扮演多型學生與 Coddy 真實對話、同步白盒檢測後台、驗證 RAG，確認機制符合設計。
> 兩輪模擬（診斷輪 r1 → 修復 → 驗證輪 r2/r3），約 60 次真實 LLM 互動（成本 < $0.2）。

### 決策依據與證據
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

## [2026-08-06] — fix(coddy)：7-C1 P0 批次——接通 Hint Ladder + Evidence 補執行狀態

> 起因：使用者實測 return 1 對話，Coddy 連續反問不升級。審計證實兩個結構性斷線（詳見 tech-debt / roadmap 7-C）。

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

## [2026-08-06] — feat(chat)：7-U6 Coddy 分階段進度（`/chat/interact` 改 SSE）

> 原本從頭到尾只有一個不動的「Coddy思考中…」。使用者要「像主流 LLM 那樣有進度感」，
> 但**拒絕假進度**——所以做的是後端真實推播 EDF 三層管線的所在階段。

### 決策依據與證據
- `services/chat.py`：`interact()` 新增 `on_stage` 回呼，在 Evidence 前 / K-Graph+RAG 前 / Feedback 前各推一次（`analyzing` / `retrieving` / `composing`）。**None 時完全不呼叫**，非串流呼叫端零開銷
- `api/routes/chat.py`：`/chat/interact` 改回 `StreamingResponse`（`text/event-stream`），事件序 `stage`×3 → `done`(InteractResponse)；帶 `X-Accel-Buffering: no` 防代理層把事件壓到最後一起送
- **錯誤處理的真實取捨**：串流一開始 HTTP header 就送出，途中失敗無法再改 status → 改發 `error` 事件。rate limit / 認證屬前置檢查，仍維持正常 429 / 401
- 為何不做逐字串流：現行輸出防護（阻擋 AI 直接給完整程式碼）是拿到完整回應才檢查，一旦逐字吐出，洩漏的程式碼學生已經看到了。分階段狀態不動這條防線，且資訊量更高（學生知道它在查教材）

## [2026-08-06] — feat(editor)：7-U5 C++ 靜態補全（VSCode 式，不接 LSP）

### 鍵位設計
- `{ key: "Tab", run: acceptCompletion }` 排在 `indentWithTab` **之前**：有候選時 Tab 接受、沒候選時 handler 回傳 false 才輪到縮排，兩者不打架
- Enter 亦可接受（VSCode 行為）；Esc 關閉

### 決策記錄
- **不接 clangd LSP**：B 機 2GB，clangd 每實例 300MB 起跳，30 人同時上課必爆（與不自架 Judge0 同一資源理由）。要做得先升硬體

## [2026-08-06] — feat(learn)：7-U3 教材出處移除 + 時間戳改句尾註腳式播放標記

### 教材出處 UI：只供模型使用
- LEARN 概念說明的「影片出處（點擊跳轉）」清單移除
- Coddy 回應下方的「教材出處（展開可看原文）」移除，`components/chat/citation-list.tsx` 刪除
- **citations 資料本身保留**：後端照常檢索、注入 prompt、隨回應傳回並存 DB，只是不再呈現給學生
- ⚠ 副作用：K4e 防幻覺從三層變**兩層**（機械攔截未 grounded 引用 + 誠實說教材沒提仍在；失去「學生當場核對原文」那層）

## [2026-08-06] — feat(learn)：7-U1 單元導航收斂 + 7-U2 課程全解鎖；修 schema 漂移

### 課程全解鎖：推翻循序鎖定
- `generator.py`：新路徑所有 unit 皆 `available`（原為第一個 available、其餘 locked）
- migration **`u7d8e9f0a1b2`**：既有使用者的 `locked` → `available`（downgrade 不可逆，僅還原初始語義）
- 前端移除 **ghostUnlock 整條線路**：`learn/page.tsx` / `path-detail.tsx` / `unit-content.tsx` 的 prop、`hooks/use-dev-mode.ts` 的 `useGhostUnlock`、`lib/dev-mode.ts` 的旗標讀寫、`components/settings/dev-unlock-card.tsx`（DEV 設定卡）、以及 5-6b「教師全開」特例——全解鎖後這些例外全部多餘
- 學習引導改由 K-Graph 前置依賴 / 弱項診斷 / 補救路徑負責，不再用鎖擋人；順序仍以編號與狀態圖示呈現為建議路徑
- 3 個測試改為斷言新語義（generator 全 available / route status / progress summary available_units 3）

## [2026-08-06] — feat(runner)：R5c-2 生產互動終端上線 + R5d 移除 stdin 預填 UI

### 決策依據與證據
- Zeabur：backend 綁公開子網域 + `RUNNER_BACKEND/RUNNER_URL/RUNNER_TOKEN` + web `NEXT_PUBLIC_TERMINAL_WS_URL` + redeploy
- **唯一卡點＝backend 需重啟才會讀入環境變數**（web 已 redeploy 但 backend 未重啟時，批次與互動都不會打到 B 機——判斷依據：B 機日誌完全沒有來自 A 機的連線）。已寫入 deployment.md §E 疑難排解
- **A 機出口 IP 實測為 `43.153.167.105`**，與 R5a 依生產 DB 連線字串的推測值一致 → 防火牆規則無需調整，`ufw logging` 探測法未被用上（保留於文件備用）

## [2026-08-05] — feat(runner)：R5a/b 部署產物 + 本機 Docker 實測（修 3 個容器內才會爆的缺陷）

### 決策依據與證據
- `runner/docker-compose.yml`：`cap_add: SYS_ADMIN` + apparmor/seccomp unconfined（nsjail 建 namespace 必需）；**容器層天花板** mem 1400m / pids 512 / cpus 1.8（個別程式限制歸 nsjail，這層防「全部 session 加總拖垮 2C2G 主機」）；`/tmp` tmpfs（學生寫檔不落地、重啟自清）；healthcheck
- `runner/bootstrap.sh`：swap 2G + `vm.swappiness=10` / docker / ufw 僅放行 22 與 A 機→8080 / **補 `DOCKER-USER` iptables 規則**（docker 會繞過 ufw，常見疏漏）/ 禁 SSH 密碼登入 / 清重複公鑰。冪等
- `runner/deploy.sh`：build → up → 等 healthy → 冒煙測試；`.env.example`（token 產生方式）；`.gitignore`
- `docs/deployment.md` **§E 完整 SOP**：含「**來源 IP 探測法**」（用 ufw DENY 日誌讀出 A 機真實出口 IP，不需開放全網）、Zeabur 三個環境變數 + `NEXT_PUBLIC_*` 需 redeploy 提醒、驗收表、**一行回滾**（`RUNNER_BACKEND=judge0`）、疑難排解

### 本機 Docker 實測揭露的三項限制
1. **PCH 目錄未綁入 jail** → `fatal error: /opt/pch/std.h: No such file or directory`；jail 是全新 mount namespace，只有顯式綁定的路徑存在（順帶補 `/etc/ld.so.cache` 與 `TMPDIR=/box`，GCC 需暫存目錄）
2. **nsjail 以 execve 啟動子行程、不做 PATH 查找** → 傳 `g++` 靜默失敗，且 `--really_quiet` 把錯誤吃掉只剩 "compile failed"；改為 `shutil.which` 解析絕對路徑，並讓失敗訊息帶上 sandbox rc 以便診斷
3. 🔴 **nsjail 以 `128+signal` 回報，無窮迴圈被誤判成 `Runtime Error (NZEC)`** → 學生會收到錯誤的 Coddy 主動說明（該講逾時卻講執行期錯誤）；`classify_exit` 改為同時處理負數（直接子行程）與 128+N（nsjail）兩種慣例，SIGKILL/SIGXCPU 歸 Time Limit

## [2026-08-05] — feat(runner)：R4 前端互動終端 — xterm 嵌入 Output 面板

### 決策依據與證據
- **`lib/terminal-theme.ts`**：xterm 主題；bg/fg/cursor 直接對應既有 token（`--bg-inset` / `--text-primary` / `--text-link`），ANSI 16 色採 GitHub 官方 dark 色盤（frontend.md R8 白名單核准例外，僅限終端畫布）
- **`lib/terminal-protocol.ts`**：frame 型別（與 `runner/app/terminal.py` docstring 同一份契約）+ `terminalWsUrl()`（讀 `NEXT_PUBLIC_TERMINAL_WS_URL`，未設退同源）+ `frameToExecutionResult()`（exit/compile_error → 既有 ExecutionResult 語意）
- **`use-terminal-session.ts`**：ticket → WS → frame 分派；**任何錯誤（RUNNER_BUSY / SESSION_LIMIT / ticket 503 / 連線失敗）一律退回批次執行**，學生不會卡住
- **`terminal-view.tsx`**：xterm 動態 import（避 SSR）+ ResizeObserver fit + **不做 local echo**（PTY 端 kernel 行規範已處理回顯）；回呼以 ref 持有，避免 prop 變動重建終端機清空畫面
- **`terminal-pane.tsx`**：狀態列（排隊中／編譯中／互動中）+ 畫布；排隊時顯示「前面還有 N 位」

### 決策依據與證據
- `use-run-code.ts`：改為**優先互動終端**，退回批次；xterm 動態載入期間的首批輸出先 buffer、attach 時 flush（避免掉字）
- `output-panel.tsx`：session 進行中以終端畫布取代歷史列表，結束後自動收回 RunBlock（`STATUS_META` 圖示／「詢問 Coddy」／執行歷史選單全部沿用）
- `stdin-panel.tsx`：降級為「**進階：預先餵入**」，預設收合、移除 `codeNeedsInput` 與「程式在等待輸入」提示（互動模式下程式真的會停下來等，提示無意義）→ **tech-debt 記錄的 A12 兩缺陷（提示不即時 / Run 不攔截）就此消滅**
- `.env.example` 加 `NEXT_PUBLIC_TERMINAL_WS_URL`；新增 `@xterm/xterm` + `@xterm/addon-fit`
- ⚠ `output-panel.tsx` 163 行（R4 +25，>150 提醒線未達硬線）已記 tech-debt

## [2026-08-05] — feat(runner)：R1 runner service — 沙箱編譯執行 + PCH + 快取 + 並行閘

### 決策依據與證據
- **`POST /run`**：批次編譯執行，回應七欄位逐字對齊 `ExecutionResult`、狀態字串沿用 Judge0 慣例（"Accepted" / "Compilation Error" / "Time Limit Exceeded" / "Runtime Error (SIGXXX/NZEC)"）→ R2 映射與前端 `classifyStatus` / `run_help` 零改動；`GET /healthz`（queue/cache 觀測，不驗 token）
- **模組**（9 檔，皆 <150 行）：`config`（env 參數，server-plan 定案值）/ `models` / `sandbox`（nsjail 旗標包裝，`none` 模式供本機測試）/ `gate`（並行閘 2 + 排隊位置回報 API 供 R3 WS 推送 + 排隊逾時 503 RUNNER_BUSY）/ `cache`（sha256 LRU 256 條，逐出刪檔）/ `compiler`（PCH `-include` 自動偵測 + 快取入庫）/ `executor`（argv shlex + 訊號翻譯 + hardlink 進 workdir）/ `proc`（**串流封頂讀取**——不用 `communicate()` 防 `while(1) cout` 在截斷前 OOM runner；stdin feed + 孫行程佔 pipe 寬限 2s）/ `main`
- **Dockerfile**：multi-stage——nsjail 自 source 建（不在 apt 庫）+ **PCH 預編 15 個常用標準庫標頭**（旗標與 config 一致否則 g++ 拒用）；`RUNNER_SANDBOX=nsjail` 烘入映像
- **待 R5 實測**：Dockerfile 建置（本機 docker 未啟動）、nsjail 旗標路徑（`sandbox.py` 集中，B 機微調）

## [2026-08-05] — docs(runner)：7-R 自建互動執行引擎定案（R0），推翻 Batch Terminal 決策

> 起因：使用者驗收 A12（stdin 預填）體驗極差——「貼上按 Run 直接跳結果、必須一次填完 input 不符邏輯」。追根究柢是 Judge0 批次判題天生做不到互動；加上 RapidAPI 50 次/天不敷課堂、自架 Judge0 需 GRUB 切 cgroup v1，整條 Judge0 路線一併重新評估後推翻。

### 自建互動 runner 決策
- **推翻「Terminal：Batch 模式」**（原始決策）與「Judge0 上線後自架」（2026-07-12）兩條
- 新路線：**自建互動 runner**——nsjail 沙箱（不自造輪子）+ **PTY**（stdout 行緩衝，`cout` 提示字即時出現；一併修掉 V1 pipe 緩衝缺陷）+ WebSocket；一律互動終端，`POST /run` 批次僅供題庫驗證/教材健檢/實作題判定
- 拓撲：Browser `wss` → A 機 backend（需綁公開子網域；Next.js Route Handler 不支援 WS proxy）中繼 → B 機 runner；防火牆僅放行 A 機 + `X-Runner-Token` 縱深；B 機不持有 credential；`ExecutionResult` 欄位不變（EDF / analytics / run_help 零改動）
- UI：終端機**嵌入 Output 面板**（拒絕 V1 的 modal——寫程式時看不到程式碼）；`@xterm/xterm`；**ANSI 16 色例外核准**（GitHub 官方 dark 色盤，僅限終端畫布，frontend.md R8 白名單）
- 費用：B 機另租 +$3/月（總 $12），PokerNote 原機不動（避免 DB 搬遷風險與失去 Zeabur 託管）；不再需要 Judge0 付費訂閱（比原路線省 $7+/月）

### 決策依據與證據
- **B 機已租用並實測全綠**：`43.133.7.93`（2C2G/40G Tokyo；cgroup v2 齊全不需動 GRUB；`ubuntu@` 金鑰登入 + 免密碼 sudo；純裸 VM 無 k3s）；實測 OS 為 24.04（面板顯示 22.04，以實測為準）
- 資源參數定案：並行編譯閘 2 / swap 2G / 編譯 CPU 10s·RAM 512M / 執行 RAM 256M·pids 64·輸出 8M / session idle 60s·硬上限 300s·同時 40；PCH 加速（本機實測編譯 0.25s→0.09s）
- roadmap 新增 **7-R 節（R0✅~R6）**；server-plan.md 全文改寫為 Runner 專用機；architecture.md 新增執行引擎節；backend.md 加 `RUNNER_BACKEND/RUNNER_URL/RUNNER_TOKEN`；tech-debt 記「stdin 預填 UI 兩缺陷不修（R4 取代，含回退條款）」

## [2026-08-05] — chore(security)：清除設定檔明文 DB 密碼 + 權限收斂 + 正式環境硬擋 hook

> 起因：巡檢 Claude Code 權限設定時，發現 `.claude/settings.local.json` 有一條同時包含**正式環境 DB 明文密碼**與 `.venv/bin/python *` 萬用字元的 allow 規則——等於「連著正式資料庫的任意 Python 執行，永不詢問」。

### 評估後不採用 — 正式主機硬擋 hook
- 曾實作 PreToolUse hook 攔截含正式主機的 Bash 指令（實測可攔），**同日評估後移除**
- 原因：① 只擋得住寫死的那一台，換主機或改從 `.env` 讀連線字串就失效，安全感不實 ② 正式環境測試是常態需求，硬擋反而礙事
- **實際防線**：含密碼的 allow 規則已刪除，故連正式 DB 的指令會回到逐次確認，由人眼判斷

## [2026-08-05] — feat(scripts)：教材程式碼健檢工具 + 每日 20 次配額 + session 開場提醒

> 承 v41 `extern` 事件：**沒有任何機制會驗證教材裡的程式碼真的能編譯**，錯了兩個月沒人發現。

### 教材健檢的兩層成本設計
1. **靜態掃描（免費、每次都跑）**：拿 `corrections.json` 的 `global_replacements` 當「已知錯誤拼法字典」掃 questions / staging / learning_units。**不另外維護第二份清單**——修正配置本身就是規格
2. **Judge0 編譯（有配額）**：把 coding 題的 `starter_code`（**125 支**）送去真的編譯。**每天上限 20 次**（免費額度 50/天），未驗過或內容變動的優先、其次最久沒驗的 → 約 7 天跑完一輪，之後自動輪替
- 狀態寫 `data/teaching_content/snippet_check_state.json`（哪天跑過 / 每支的 hash + 結果 + 時間）；**只有真的編譯過才算「今天跑過」**，靜態掃描不會消掉提醒
- 教材本身沒有 code fence（U2g 移除範例程式後概念說明是純文字），所以可編譯的實體只有 starter_code

### 決策依據與證據
- 依使用者指示**今天先不實測**，只完成程式；靜態掃描已跑過一次：**0 個已知錯誤拼法**（v41 修完後全庫乾淨）


## [2026-08-05] — fix(content)：章節 41 `extern` 錯字修正（含兩支批次 script 語法損壞）

### 查證 — 「v17/v41 題庫掛零」是過期記錄
- tech-debt 那筆寫於 2026-07-06 上午的批次；**同日晚間 6-3c 知識點驅動批次已補**。實查：**v17 有 8 題（7 MC + 1 coding），健康**；v41 只有 2 題
- **但 v41 的 2 題全都寫成 `external`**（其中 coding 題直接要求「利用 external 宣告」）→ 學生照做**必定編譯失敗**，等於 0 題可用。全庫掃描確認錯誤只在 v41
- 覆蓋率最低的其餘章節：v03 安裝教學 1 題（無可考點，屬預期）、v61 5 題、v45 6 題

## [2026-08-05] — feat(edf)：時區提醒 + 端點正名 run-help；發現章節 41 教材把 `extern` 寫成 `external`

### UTC 時區提醒採機械判定
- 伺服器時鐘是 UTC，比台灣慢 8 小時 → 學生在章節 45 印出「現在時間」會看到差 8 小時的結果，且**看不出是環境問題還是自己寫錯**
- `uses_local_time()` 偵測 `localtime` / `strftime` / `asctime` / `ctime`（**只認會轉成「人看的當地時間」的函式**；`time(NULL)` 印 epoch、`clock()` 算 CPU 時間都不受時區影響，不觸發）
- 執行**成功**時才提醒（編譯失敗/逾時另有路徑），每個 session 一次；文案說明這是雲端環境常態並反問「加多少秒會變成台灣時間」，不直接給答案

## [2026-08-05] — fix(chat)：收合聊天不再遺失對話 + 平板補 chat + 執行語言鎖死（A1/A2/A3）

> 上一則問題總結中查證出的三個缺陷，全部修掉。

### 決策依據與證據
- **根因**：`app-shell.tsx` 的 `{chatOpen && <ChatPanel/>}` 是條件掛載 → 收合即 unmount，而訊息列表、session id、執行結果訂閱**全都住在 ChatPanel 裡**。資料其實在 DB，但畫面空白，學生得自己從歷史選單撈回來
- **修法**（與 Output 執行歷史同一套）：新增 `components/chat/chat-runtime.tsx`，把 `useChat` / `useSessions` 與三個 workspace 訂閱提到 `ChatRuntimeProvider`（掛在 `WorkspaceProvider` 內、`ShellLayout` 外＝永遠掛載）；`ChatPanel` 降為純呈現層（145 → 95 行）
- **一併修好的副作用**：① 聊天收合時執行程式，結果卡片不再被丟掉（原本 `onExecutionComplete` 沒有 queue，直接消失）② 編譯錯誤去重簽章不再隨面板開合重置（不會重複花每日配額）

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

### 逾時說明採零成本機械路徑
- `compile_error.py` 加 `is_timeout()` + `_TIMEOUT_TEMPLATE`：固定文案指出兩大主因（迴圈沒有結束條件 / 用 `cin` 但沒給輸入），**並肯定「正在練習無窮迴圈這章的話，這個結果是正確的」**
- 前端觸發條件擴到 `Time Limit Exceeded`，以狀態字串當去重簽章；session 標題改「執行問題引導」

## [2026-08-05] — feat(workspace)：補上標準輸入介面（`cin` 無處可輸入）+ 修 kickoff fail-open

> 使用者寫了含 `std::cin >> userInput` 的程式，**畫面上沒有任何地方可以輸入**。

### 決策依據與證據
- Output 面板頂端的「輸入」摺疊列：多行 textarea（上限 10,000 字，與後端一致）、顯示目前行數
- **偵測到程式會讀輸入時自動展開並標示「程式在等待輸入」**（`codeNeedsInput()` 比對 `cin >>` / `getline` / `scanf` / `cin.get`，純字串比對零成本）
- 明說批次執行的限制：「程式是一次跑完的，不能邊跑邊打字——請先在這裡填好所有 `cin` 要讀的內容，再按 Run」（roadmap 既有決策：Judge0 批次模式，不做即時互動 terminal）

## [2026-08-05] — feat(edf)：編譯失敗時 Coddy 主動說明（平台限制直說 / 學生錯誤引導）

> 使用者提問「預設函式庫有哪些、想引用別的怎麼辦」+ 定案「編譯錯誤本來就該由 Coddy 主動分析；系統錯誤直說，學生自己出錯要引導」。
> **背景事實**：`judge0.py:13` 寫死 `CPP_LANGUAGE_ID=54`，只送單一 `main.cpp` → 可用的僅 C++ 標準函式庫；沙箱無顯示裝置也無網路，Qt 這類 GUI 函式庫**裝了也跑不動**。

### 決策依據與證據
- **兩類錯誤刻意不同處理**：
  - **平台限制**（`fatal error: X: No such file or directory` 且 X 不在標準標頭白名單）→ **機械判定 + 固定文案，完全不呼叫 LLM**（零成本；也避免 LLM 亂編「你可以裝一下」這種做不到的建議）。文案說明「不是你寫錯」＋環境只有標準函式庫＋無畫面沙箱＋改用 `cin` 的具體出路
  - **學生自己的錯誤**（漏分號、型別不符…）→ LLM 引導：白話翻譯錯誤訊息 + 指出從哪裡查起，**prompt 明令不可給修好的程式碼、不可說「第 N 行改成 XXX」**
- **標準標頭白名單**涵蓋 STL / C 標頭 / 常見 POSIX；`iostream` 找不到會被判為環境異常而非平台限制（不對學生說謊）
- 訊息寫入現有 session（非另開），保留在對話歷史可回看；LLM 失敗 fail-open 回固定文案

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

### 決策依據與證據
- **根因**：`globals.css` 從未宣告 `color-scheme`，也沒有任何滾動條樣式 → 瀏覽器一律給淺色預設，在純 Dark Mode 介面上就是一條白槓
- `html { color-scheme: dark }` — 讓所有原生元件（滾動條、select、日期選擇器）跟著深色，不只滾動條受益
- 自訂滾動條（使用者選 10px + 透明軌道）：拇指 `--border-default`、hover 轉 `--border-emphasis`、`border: 2px solid transparent` + `background-clip: content-box` 內縮 → **視覺 6px 細、實際 10px 好抓**；軌道與 corner 全透明；Firefox 以 `scrollbar-width: thin` + `scrollbar-color` 對應
- 全部走既有 token，未引入新色（R1 通過）

## [2026-08-05] — fix(workspace)：檔名鎖定 .cpp 尾綴 + 點檔名改名 + 首次草稿併發修復（U2e 驗收回饋）

> 使用者生產環境驗收回報三點：①「點資料夾剛開始跳錯誤、之後正常」②「存成 main.md 也能執行，副檔名形同虛設」③「最上方檔名點不動、無法改名」。

### 副檔名策略：鎖尾綴而非靜默改寫
- **確認副檔名完全無作用**：`services/judge0.py:13` 寫死 `CPP_LANGUAGE_ID = 54`，前端執行時只送 code 不送檔名 → `main.md` / `main` / `main.txt` 都以 C++ 編譯。後端原本只驗長度 1–100
- **後端 `normalize_file_name()`**（`services/workspace_files.py`）：`.cpp` 結尾（不分大小寫）保持原樣，否則**補上**（不改寫既有副檔名——使用者明確表示 `main.md → main.cpp` 的靜默轉換很怪）；補完超長回 422。`save_file` / `rename_file` 皆走此規則，API 直呼也繞不過
- **前端 `.cpp` 為鎖定尾綴**（新元件 `file-name-input.tsx`）：輸入框只編輯主檔名，尾綴以固定灰字呈現於框內、無法刪改；另存對話框 / 側欄儲存 / 改名列三處共用。另存對話框補一行「程式一律以 C++ 編譯執行」
- 存檔後**以伺服器回傳的檔名為準**（原本沿用送出的字串，補副檔名後會與 DB 不一致）；實作題 handoff 自動命名同步改為「{單元} 程式實作題.cpp」，維持反思按鈕的檔名比對成立

## [2026-08-05] — docs：生產庫播種狀態複驗（7-1a-4 收尾，無待補項）

> 承接「concepts 影片 ID 待補」的掛帳。開公網後以 `--dry-run --force` 查驗，結果**該項在上個 session 修完 script 後就已執行完畢**，只是狀態文件未同步 → 本次為純狀態修正，**未對生產庫做任何寫入**（dry-run 已 rollback）。

## [2026-08-05] — perf(llm)：模型全面升級 gpt-5.6 + 每日配額 + 離題分流（成本控制三層）

> 上線前防濫用盤點：rate limit（10 次/分）與 prompt injection 防護已有，但**主題範圍限制完全沒有**（RULE-1~5 只管程式碼洩漏/語言/字數/收尾）、`off_topic` 只是欄位（`dialogue.py:53` 明寫「暫不主動判定」）、**沒有每日總量上限**（理論上一人一天可打 14,400 次）。
> **業界基準**：CS50.ai（架構幾乎相同——GPT-4o + 講座字幕 RAG + 教學護欄）實測 **$1.90/學生/月、$0.05/prompt**。

### 模型選型：實測後全面升級
| 用途 | 舊 | 新 | 單價變化 |
|---|---|---|---|
| 對話 + 分析 | `gpt-5.4-mini` | **`gpt-5.6-luna`** | $0.75/$4.50 → **$0.20/$1.20** |
| 生成（Quiz/Hint） | `gpt-5-mini` | **`gpt-5.6-luna`** | $0.25/$2.00 → **$0.20/$1.20** |
| 審查 / 內容批次 | `gpt-5.4` | **`gpt-5.6-terra`** | $2.50/$15 → **$2.00/$12** |

- **每項都更便宜且更新世代，無取捨**。實測單次互動成本 **$0.00316 → $0.00081（省 74%）**；100 人×80 則/月：**$25.3 → $6.5**
- **修 `core/llm_params.py`**：gpt-5.6 世代拒收自訂 `temperature`**也拒收 `reasoning_effort`**（原判斷只認 `gpt-5-` 前綴 → luna 直接 502）。拆出 `_accepts_custom_temperature()`；預設 `reasoning_tokens=0` 無須壓制
- `config.py` 的 `LLM_MODEL` 預設由 `gpt-4o` 改為 `gpt-5.6-luna`（生產漏設時的 fallback 不該是 2024 世代）

### 決策依據與證據
- `RATE_LIMIT_LLM_PER_DAY=60`：**只掛 `scope="llm"`**，`/code/execute` 等不受影響。UTC 日期分 key、26 小時 TTL 涵蓋任何時區；超額回 429 `DAILY_QUOTA_EXCEEDED` 並明示「明天重新計算，仍可寫程式/執行/讀教材」；設 0 停用。+3 tests
- **決策：不做上課日/非上課日分級配額**——正常使用僅 $6.5/月，分級省的是最壞情況的一部分（該由 OpenAI 帳號硬上限擋），卻要付出教師端課表 UI + 時區處理的複雜度，且**會傷害週末複習/考前衝刺的學習體驗**

## [2026-08-05] — feat(edf)：Coddy 防幻覺三層機制（NotebookLM 式可驗證引用）

> 承上一條：把正確 metadata 餵給 LLM 只解決「它沒資料可用」，**不保證它聽話**。本次補上不依賴 LLM 自律的機制。原 `validate_output()` 只檢查程式碼洩漏，對「內容是否真的來自教材」零檢查。

### 已知限制（誠實記錄）
- **幻覺無法 100% 消除**：出處已鎖死，但 LLM 仍可能曲解教材內容（老師說 A 講成 B）。驗證這個需第二次 LLM 呼叫比對，成本與延遲翻倍 → **不常態開啟**，日後可做抽樣稽核工具（原方案④）

---

## [2026-08-05] — fix(edf)：Coddy 影片引用改為真實出處 + 可點擊時間連結（K4d 驗收回饋）

### 決策依據與證據
- 本機真實 LLM 實測：輸出 `[C++的break與continue 04:05](...&t=245s)`、`[C++的while迴圈 07:04](...&t=424s)`，章節名稱與秒數換算皆正確（245s=04:05、424s=07:04）且來自真實 metadata

---

## [2026-08-05] — perf(deploy)：生產環境「頁面載入十秒」根因排除 — DNS threadpool + HTTP/3

> 使用者回報 Learn / Knowledge / 首次登入皆需 10 秒以上（一次錄製達 3 分鐘）。逐層量測後確認是**兩個獨立的生產環境問題疊加**，本機開發（localhost）兩者皆不會出現。

### 量測基線（先排除的部分）
- 後端 13 個端點 ×5 次（真實 PostgreSQL，62 概念 / 628 題 / 861 chunks）：**2–10ms，最慢 40ms，無慢查詢**
- lazy-seed 首次產生 62 units：**0.02 秒**；backend 冷啟動 import 0.92 秒
- 生產 health check ×20：130–337ms 穩定無尖峰；SSR `/login` 330ms
- 前端交付：HTTP/2 + `cache-control: immutable` + gzip，9 個 chunk，各頁只打 1 個 API（Knowledge 用 `Promise.all`），**無瀑布**
- Performance trace（499MB / 699,950 事件）：**≥100ms 的任務只有 1 個**，總耗時 8.5 秒 → **主執行緒幾乎完全閒置，前端零阻塞**

### 決策依據與證據
- **證據**：Network 顯示 `/api/auth/session` 首次 **2.2 分鐘**，期間 `health` ×5 全部 5.00 秒逾時（前端 AbortController 上限）；session 一完成，health 立刻回到 86–472ms → **兩者共用同一瓶頸資源**
- **機制**：Next.js 為單一 Node process，DNS 查詢走 libuv threadpool（預設僅 4 執行緒）。容器內 Node 18+ IPv6 優先而 Zeabur 容器 IPv6 無法路由外網 → 解析逾時佔滿 threadpool → proxy 要解析 `*.zeabur.internal` 時排隊
- **修法**：web service 加 `NODE_OPTIONS=--dns-result-order=ipv4first` + `UV_THREADPOOL_SIZE=32`（**不在版控，已記入 deployment.md Step 2**）
- **結果**：`workspace?_rsc` 304ms、`draft` 491ms — API 全數恢復

### 決策依據與證據
- **證據**：修好 DNS 後靜態資源仍極慢——137KB 花 **18.50 秒**（約 7 KB/s），但同機同時 curl 測**序列 633 KB/s、15 個混合並行 0.71 秒全完成**。回應帶 `alt-svc: h3=":443"; ma=3600` → Chromium 系瀏覽器切 HTTP/3（QUIC over UDP），curl 走 TCP 不受影響
- **修法**：`next.config.ts` 加 `Alt-Svc: clear`（RFC 7838），讓瀏覽器清除記錄並留在 HTTP/2。**拒絕「要使用者自行關閉 QUIC」的方案**——校園 / 企業 / 部分 ISP 對 UDP 443 限速或丟包很常見，2027-01 評估時學生多在校園網路
- **結果**（使用者實測 43 筆請求全為 `h2`）：同一檔案 **18.50 秒 → 166ms（111 倍）**；靜態資源普遍 15–22ms、API 70–350ms

## [2026-08-05] — fix(deploy)：生產環境影片 ID 全 NULL — 播種 script 補 concepts metadata 同步

### 決策依據與證據
- **生產 Learn 概念說明只顯示 placeholder**（使用者實測回報）：根因**不是**教材沒灌成功，而是 `concepts.video_youtube_id` 在生產庫全為 NULL——migration `e1f2a3b4c5d6:134` 把它 seed 成 `None`，62 個真實影片 ID 是 6-1d 用 `patch_video_metadata.py` 寫進**本機** DB 的，屬「本機有、migration 沒有」的第三類缺口（前兩類＝concept UUID 隨機、`data_codedge_rag` 執行期建表）
- **放大效應**：`web/components/learn/concept-tab.tsx:32` 在 `video_youtube_id` 為 null 時**整個 tab early return placeholder**，連已經灌好的 grounded 教材都不渲染 → 症狀看起來像「播種失敗」，實際只差影片 ID
- **修法**：`seed_production_content.py` 新增 `sync_concept_metadata()`，以 tag 為鍵 UPDATE 生產庫的 `video_youtube_id` / `video_duration_seconds`

## [2026-08-05] — feat(scripts)：測試/生產環境隔離防護 + 生產播種實機完成

### 決策依據與證據
- **`backend/scripts/_db_guard.py`**：所有 script 共用 `core.database` 讀 `settings.DATABASE_URL`，而對生產庫做維護時 `export DATABASE_URL=<生產>` 會**殘留在同一個終端機**——之後跑任何 script 都會誤寫生產庫（本次部署過程中就已具備此條件）。兩級防護：
  - `require_local_db()` — **無覆寫選項，非本機一律中止**。掛 `seed_fake_students`（假帳號污染實驗資料）/ `generate_unit_content` / `generate_unit_questions` / `ingest_transcripts_rag` / `rereview_questions`（本機生成、之後用播種搬運，沒有對生產跑的理由）
  - `confirm_remote_db()` — 允許但需互動輸入 `yes`（非互動環境用 `ALLOW_PRODUCTION_WRITE=1`）。掛 `promote_unit_content` / `patch_video_metadata`（生產庫的合法維護操作）
  - 訊息一律遮蔽密碼（`postgres:***@host`），並提示「這通常是變數殘留，請開新終端機或 unset」

### 決策記錄
- DEV 工具安全性複查（使用者提問）：`/dev/reset`·`/dev/mastery`·`/dev/role`·`/dev/simulate-failures` **全部已限定 `user.id`**（`services/dev_tools.py` 每條 delete 都帶 user_id 條件），`/dev/questions` 唯讀、幽靈解鎖純前端 → **無需修改**；生產開啟 DEV 僅需 `DEV_MODE_ENABLED=true` + email 白名單

---

## [2026-08-04] — feat(deploy)：生產資料播種 script（7-1a-3）+ Judge0 RapidAPI 鏈路實測

### 決策依據與證據
- **本機建 `prod_test` 庫完整演練**：跑完整 alembic → 確認 concept UUID 與本機不同（`bb615138…` vs `0e660c1e…`）→ pg_dump 搬 RAG 表 → 執行 script → **62 教材 / 628 題（503 MC + 125 coding）/ 861 chunks / 64 documents 全數寫入，0 孤兒、tag 對應與本機完全一致**
- **Judge0 RapidAPI 端到端實測**（此鏈路首次真正跑通）：正常執行（stdin `3 4` → `stdout='sum=7\n'`、0.003s / 1140KB）/ 編譯錯誤（g++ 訊息完整回傳）/ 服務不可用（`AppError 503 JUDGE0_UNAVAILABLE`）三路徑皆符合 `backend.md` 規範

## [2026-07-21] — fix(workspace)：我的程式碼刪除修正 + 反思 modal 提交按鈕遮蔽

### 決策依據與證據
- **刪除檔案誤報「操作失敗」**（根因 `lib/api.ts`）：後端 DELETE 回 204 No Content，`api()` 無條件 `res.json()` 對空 body 解析失敗拋錯 → 被 catch 誤判失敗；實際已刪除（重整後列表重抓才看到消失）。加 `res.status === 204 → return undefined`；**同時修好「未立即刪除」**——樂觀 `setFiles` filter 原本在 throw 後永遠沒執行到，現正常即時移除
- **刪到當前開啟檔案無提示**（`code-files-sidebar.tsx` + `use-named-file.ts`）：刪除時偵測 `f.name === currentName`，跳出專屬確認「此為目前開啟檔案，刪除後將移除並跳回預設程式」；確認後呼叫新抽出的 `resetToDefault`（從 `newFile` 抽離、不含未存確認）重設編輯器為預設範本並清檔名關聯
- **反思計畫過長時提交按鈕消失**（`reflection-flow.tsx` + `reflection-flow-parts.tsx`）：modal Popup 原為 `max-h-[85vh] overflow-hidden` 但內部 header/題目(22vh)/body(60vh)/footer 直向堆疊無 flex 約束，總高超過即把 footer 裁出可視區且無法捲動觸及；改 Popup 為 `flex flex-col`、body 改 `min-h-0 flex-1` 吸收剩餘高度並內捲、header/題目/footer 加 `shrink-0` 固定 → 提交按鈕永遠可見（側欄編輯版本身已有 `overflow-y-auto`，不受影響）

## [2026-07-18] — fix(tech-debt)：低風險技術債清償——Judge0 自架 authn / lazy-seed 空骨架 / pyproject / uv.lock

### 決策依據與證據
- **Judge0 自架 authn header**（`services/judge0.py`）：`_build_headers` 加 authn 分支——URL 含 rapidapi 網域 → `X-RapidAPI-Key`（現狀不變）；自架 + key → `X-Auth-Token`；無 key 不帶 auth header。新增可選 `JUDGE0_AUTH_MODE` 環境變數（rapidapi / self-hosted）顯式覆蓋自動判斷，供邊角情境救援；消除「切自架開 authn 會 401」技術債（生產實測仍待 Phase 7）
- **lazy-seed 空骨架**（`services/learning/generator.py`）：`generate_learning_path` seed units 時讀 `unit_content_staging`（status=approved）直接帶入 content，無 approved 才寫空骨架——promote 後才註冊的新帳號（含 DEV ghost user）概念說明 tab 不再落 pending fallback；與 promote script 整包覆蓋行為對齊（單一真相來源，讀取端零改動）
- **pyproject.toml hatchling packages**：補 `[tool.hatch.build.targets.wheel] packages`（flat layout 顯式列 api/core/models/services/scripts），`pip install -e .` 不再失敗；hatchling 隔離環境驗證 wheel target 可解析（151 files）

### 決策依據與證據
- **`.gitignore` 加 `uv.lock`**：依賴鎖定正本維持 `requirements.lock`（Dockerfile 亦用它）；uv.lock 為先前 uv 指令副產品，不進版控避免雙鎖定檔 drift
- **git user.name/email 技術債關閉**：確認已設定（曾冠豪 / abbyabby41@gmail.com）

### 決策記錄
- OpenAI client ×9 重複：維持刻意延後（抽共用需連動 9 檔 + 大量測試 monkeypatch，收益不成比例）
- 429 toast / OpenAI 降級快取 / 6-4b 題庫補生：本輪不做（使用者裁決）

---

## [2026-07-16] — fix(workspace)：U2e 回饋修訂——側欄化 + 近實時存檔 + 游標跳行 + Enter 縮排

### 決策依據與證據
- **打字游標跳到第一行**：兩個根因——(1) CodeEditor 以父層 onChange 為重建依賴，父層 callback identity 每 render 變動 → 編輯器整個重建、游標重設；改 onChange 走 ref、重建僅依賴 `initialValue`。(2) 草稿還原 effect 以整個 autosave hook 物件為依賴 → 每 render 重抓草稿並覆寫存檔基準；改解構穩定 callback 為依賴
- **Enter 換行不對齊上一行**：CodeMirror `indentUnit` 預設 2 空格與 4 空格程式碼錯位（換行後需再按 Tab）；加 `indentUnit.of("    ")` 統一 4 空格，並保留語法感知縮排（`{` 後自動加深）

## [2026-07-16] — feat(workspace)：U2e 程式碼存檔（DB 草稿自動存 + 我的程式碼多檔管理）

### 決策依據與證據
- **`code_files` 表**（migration `r4a5b6c7d8e9`，up/down 可逆驗證）：單表兩用——草稿（name IS NULL，partial unique 每人一份）+ 命名檔案（UNIQUE(user_id,name) 同名覆蓋；上限 50；code CHECK ≤ 100k 字元）
- **API**（`services/workspace_files.py` + `api/routes/code_files.py`）：`GET/PUT /code/draft`（還原/upsert）+ `GET/PUT /code/files`（列表 meta / 同名覆蓋儲存）+ `GET/DELETE /code/files/{id}`；一律限本人（他人 404）
- **自動存檔**（`lib/use-draft-autosave.ts`）：停止輸入 2 秒 PUT 草稿 + Toolbar「儲存中…/已自動儲存」指示；beforeunload 與 SPA 卸載時 keepalive 搶救未存變更；內容未變不重複打 API
- **進 Workspace 還原草稿**：載入完成前不掛編輯器（避免預設範本閃現）；404/失敗 fail-open 用預設範本
- **Toolbar「我的程式碼」選單**（`code-files-menu.tsx`）：另存命名檔案（同名覆蓋）+ 列表（名稱+時間）載入/刪除；載入後 Toolbar 檔名同步

## [2026-07-08] — feat(teacher)：5-6b Learn 教師全開 + 5-6c 單元題庫檢視

### 決策依據與證據
- **5-6c 教師題庫檢視**：
  - 後端 `GET /quiz/bank?tag=`（`require_roles(TEACHER)`）回完整 content（含正解 answer_index）+ 解析，僅 validated；複用 `list_questions_by_tag`；+2 tests（教師看得到正解 / 學生 403）
  - 前端 `TeacherQuestionBank` 元件 + `unit-content` 教師專屬「題庫（教師）」tab：列該單元 concept 題目，**解答預設隱藏 + 顯示/隱藏一鍵切換**（避免示範露答案），正解以綠框標示 + 解析
## [2026-07-07] — feat(teacher)：5-5a-1 作業 3 表 migration + models

### 決策依據與證據
- **作業指派 schema**（migration `q3f4a5b6c7d8` + `models/assignment.py`）：TronClass 式文件繳交
  - `assignments`：教師建立、指派整班（title/description/due_at/is_active）
  - `assignment_submissions`：學生繳交（text/score/feedback/graded_at）；UNIQUE(assignment_id, student_id) 每生每作業一份重繳覆蓋；score CHECK >= 0
  - `attachments`：多型附件（owner_type assignment/submission）檔案內容存 **bytea**（Zeabur 容器 fs ephemeral）；單檔 CHECK ≤ 10MB（`MAX_ATTACHMENT_BYTES`）
  - db-schema.md §Module 8 同步 3 表
- **設計決策（2026-07-07 使用者定案）**：作業＝文件繳交非題庫 quiz；指派整班；檔案存 Postgres；教師可評分+評語；學生雙入口（作業 tab + Dashboard 卡片）；**原 5-5b 熱力圖/錯誤統計改隸 5-4**（與文件繳交無關）

## [2026-07-07] — feat(dev)：DEV-E 假學生資料 seeder

### 決策依據與證據
- **假學生 seeder**（`services/dev_seed/` package + CLI `scripts/seed_fake_students.py`）：供教師端 / 行為分析本機開發
  - 三行為原型（主動 / 被動 / 掙扎）塑形資料，讓 5-2d 聚合與 5-3 群聚分析有可跑樣本
  - 每位學生：profile + 班級成員 + coding_events（成功/錯誤/hint）+ chat_messages（含 dialogue_act）+ student_mastery（confidence 依原型 gauss 抖動）
  - 可辨識 email 後綴 `@seed.dev`；一律先 purge 舊 seed 學生（顯式刪子表跨 SQLite/PG 一致）→ 可重現、不撞號
  - demo 教師 `seed-teacher@seed.dev` + demo 班級 get-or-create（reuse，purge 不動）；`--class-id` 可併入既有班級
  - seeded Random（`seed` 參數）保證可重現
  - **拆分**：`generators.py`（純 builder，130 行）+ `seeder.py`（編排，158 行）避免單檔逾 250 行門檻
- CLI 實機驗證：對 Postgres dev DB 生成 6 位（原型 2/2/2 均衡）

## [2026-07-07] — feat(analytics)：5-2d 行為指標聚合 service

### 決策依據與證據
- **行為指標聚合 service**（`services/analytics/aggregate.py` `aggregate_user_behavior` + `BehaviorMetrics` dataclass）：
  - 從 coding_events + chat_messages 計算單一使用者指標：execution_count / success_count / success_rate / hint_request_count / avg_fix_duration_seconds / hint_distribution / dialogue_act_distribution
  - **修復時間**：時序配對「首次未解錯誤 → 下一次成功」的間隔平均（無配對回 None）
  - **dialogue_act 分布**：DB group_by（chat_messages join session；比照 6-R8 func.count），NULL 不計入
  - 支援 `since`/`until` 時間窗過濾
- **設計決策**：compute-on-read，**不建 `behavior_aggregates` 預聚合表 / 不排程**——初期 < 100 人查詢壓力低；預聚合屬效能優化，留待 5-3/5-4 有真實資料 + 查詢壓力再評估
- **範圍取捨**：concept_error_counts / active_seconds 暫不計（現有事件資料無乾淨來源，避免臆測）；API 端點屬 5-3d（延後至真實資料）

## [2026-07-07] — feat(auth)：5-1d-3/4 身分選擇 onboarding + 設定重置卡（前端，UI 驗收通過）

### 決策依據與證據
- **待使用者 UI 驗收**（既有帳號 role_selected=false → 下次登入先見身分選擇頁）

---

## [2026-07-07] — feat(auth)：5-1d-1/2 身分自選 + 切換全清（後端）

### 決策依據與證據
- **`users.role_selected`**（migration `n0c1d2e3f4a5`，server_default false）：區分「onboarding 已主動選身分」vs 首登預設；`/users/me`·`/auth/me` 回傳；既有帳號下次登入將被引導選身分
- **`POST /users/role`**（`services/identity.py`）：自選 student/teacher（admin 不可自選 → 422）；**首次選擇只設定不清資料；已選過再改＝重置**——全清 mastery/progress/quiz/chat（reuse `reset_user_data`）+ profile + 班級成員關係 + 教師擁有的 classes（顯式先刪成員）；回傳 `did_reset`

## [2026-07-07] — feat(teacher)：5-1b-1 學生身分 profile 表 + 需求擴充決策

### 決策依據與證據
- **student_profiles 表**（migration `m9b0c1d2e3f4` + `models/student_profile.py`）：學生首次登入補填 school / department / student_id / real_name；`user_id` 當 PK（1:1 天然去重）；email 沿用 users
- **需求擴充決策**（AskUserQuestion 三裁決）：① profile 存獨立表（非 users 加欄位）② 首次登入強制引導填寫（僅 role=student，gate 由前端執行）③ 學號不做唯一約束（跨校撞號）；邀請碼定為 6 位數字
- 5-1b 拆為 5-1b-1（本次）/ 5-1b-2 班級 CRUD / 5-1b-3 加入班級+profile API

## [2026-07-06] — feat(quiz)：6-3d QUIZ 弱項綜合測驗組 + 程式題強模型 + 題庫淨化

### 決策依據與證據
- **多概念綜合出題**：`generate_question` 加 `extra_concepts`——system prompt 要求綜合測驗目標 + 相關概念（需綜合運用才可解），`concept_tags` 記錄全部概念
- **藍圖 + 節點選擇**（`weakness_set_plan.py`，不呼叫 LLM）：`compute_blueprint` 依題數 + 整體掌握度算配額（掌握度低→偏單節點；回升→提高綜合題比例）；`mastery_snapshot` 以 effective confidence 分弱項/已掌握；`plan_questions` 單節點 MC / 綜合 MC（弱項+前置）/ coding（弱項+已掌握鷹架）
- **組裝**（`weakness_set.py`）：題庫優先重用 ≤30% + 缺口並行生成（`asyncio.gather` + semaphore 6 併發，各自獨立 session，coding 用強模型）
- **端點** `POST /quiz/weakness-set?count=10|25`：回傳整組（mask 答案）+ `no_weakness` 旗標
- **前端** QUIZ 頁改弱項測驗：選 10/25 → 一次生成（動畫進度）→ 逐題作答（重用 MC/coding/hint/result）→ 總結；無弱項提示先去 LEARN；DEV 深連結 `?question=` 仍走舊 runner
- **文獻標注** references.md §5.1：Bjork 交錯/適欲難度、Vygotsky ZPD/鷹架、CAT content balancing、概念圖 GNN+RL 多跳

## [2026-07-06] — feat(quiz)：6-3c 知識點驅動題庫 + LEARN 整組作答 + 審查加「考點有意義」

### 決策依據與證據
- **知識點萃取**（`services/quiz/knowledge_points.py`）：LLM（分析組 gpt-5.4-mini）讀該影片全部字幕 → 萃取 3-8 個重要知識點，明確排除操作細節（安裝步驟 / 介面位置 / 左上右下等畫面資訊）
- **題量依知識量**：批次改為每知識點 1 題觀念選擇題（`content.knowledge_point` 記錄對應點供覆蓋追溯）+ 每單元固定 1 題 coding（課程介紹單元 0 題）
- **題目來源分流**：新增 `QuestionSource.BATCH`（migration `k7f8a9b0c1d2`）——LEARN 單元題組只列 batch 預生成題；QUIZ 弱項現生題（`generated`）不列入
- **LEARN 整組作答 API**：`GET /quiz/unit-set`（`list_unit_question_set`）回傳某概念全部 batch 題 + 該生作答進度（answered/total）
- **`GET /quiz/generate` 加 knowledge_point / source 參數**；generate prompt 加「考點必須有意義」規則

## [2026-07-06] — feat(learn)：U2g tab 重構 + 範例程式移除 + 62 部內容全量上線

### 決策依據與證據
- **LEARN 單元 tab 改為「概念說明 / 程式實作題 / 觀念題」**：練習題兩面板升為獨立 tab（`ExercisesTab` 加 `category` prop 由 tab 指定題型）；課程介紹單元（v01-03）隱藏程式實作題 tab；移除練習題/Quiz 入口的「優先從題庫取題」開發者導向提示字樣
- **內容上線流程改使用者回饋制**（使用者決策）：6-4a 正式抽查移除；新增 `scripts/promote_unit_content.py` 全量 approve + promote **62 concepts → learning_units**（promote 時剝除 summary/code_examples 殘留 key）；品質問題待實際操作回饋（6-4b 局部重跑）

## [2026-07-06] — docs(planning)：U2g/6-3c 定案——LEARN tab 重構、範例程式移除、知識點驅動題量

### 四項介面決策
- **U2g（遞補原第 6 批）**：LEARN tab 改「概念說明 / 程式實作題 / 觀念題」；觀念題＝選擇題（**簡答題型不做**）；v01-03 課程介紹隱藏程式實作題 tab；範例程式全面移除（前端 + 管線 skip examples call，staging 資料留存不 promote）
- **6-3c（接 U2g）**：題量改依影片知識量——批次前置 LLM 知識點萃取（3-8 點/影片）→ 每知識點 1 題觀念題（JSON 記錄知識點供覆蓋追溯）；程式題固定 1 題（intro 0 題）；既有 138 題保留只補缺；估 $3-6

## [2026-07-06] — fix(learn)：練習題題型分類 + 反思僅限程式題 + 反思視窗置頂題目

### 決策依據與證據
- **反思誤套非程式題**：題庫混題型後（6-3a-3），LEARN 練習 tab 抽到選擇題仍被強制進反思流程（反思設計僅適用「先想解題思路再寫程式」的情境）；現改題型分類入口
- **反思視窗看不到題目**：學生填反思需關窗回看題目；`ReflectionFlow` 加 `questionStem` prop，題幹固定顯示於視窗頂部（獨立捲動區，不隨表單捲動）

### 決策依據與證據
- **練習題入口改題型卡**（`exercises-tab-views.tsx`）：「程式實作題」（讀題 → 反思 gating → Workspace）/「觀念選擇題」（直接作答 + 立即對錯回饋，重用 Quiz 頁 `MCQuestion` + `submitAnswer`，答題驅動 BKT）；from-bank / generate 均帶 `question_type` 過濾
- 檔案拆分守規：`exercises-tab.tsx` 233 → 148 行；新增 `exercises-coding-panel.tsx`（原 QuestionPanel + 反思摘要搬出）與 `exercises-mc-panel.tsx`（MC 作答 + 結果）

---

## [2026-07-06] — feat(content)：第 5 批實機批次——6-2b content 62 部 + 6-3a-3 題庫 138 題

### 決策依據與證據
- **gpt-5 世代參數不相容**：全系列拒收 `max_tokens`（須 `max_completion_tokens`）；`gpt-5-mini` reasoning 系拒收自訂 temperature 且預設把預算燒在內部推理回空內容（實測 `reasoning_effort="minimal"` → 0 reasoning tokens 正常輸出）。新增 `core/llm_params.py` 相容層純函式 `chat_model_kwargs()`，13 個呼叫點統一切換；gpt-5.4 系 / gpt-4o 行為不變；+5 tests
- **quiz batch `MissingGreenlet`**：validate 失敗的 rollback 會 expire session 內全部 concept（不只當前），下一輪迴圈屬性存取觸發同步 lazy-load 崩潰；`generate_all` 每輪 `db.refresh(concept)`；+1 回歸測試（未修復狀態精準重現）；後端全量 **614 passed**

### 實機批次數據
- **6-2b content 批次（gpt-5.4）**：62/62 成功入 `unit_content_staging`（pending）；僅 v05 語法規則、v62 static 成員標 `needs_more_source`；抽查品質良好（v08 grounded markdown + 11 citations + 3 範例）
- **6-3a-3 題庫批次（gpt-5-mini 生成 + gpt-5.4 審查 cascade）**：62 concept 首輪 42 滿額 / 15 partial / 2 全滅 + 缺題 15 部補跑一輪 → 題庫 **138 題 validated**（MC + coding 約各半）；57/62 concept 滿額 2+ 題；v17/v41 兩輪全滅 + v11/v53/v61 各缺 1 題記 tech-debt 待 6-4b prompt 調整
- 費用實測遠低於預估（單 concept content 約 15-20 秒 × 2 call，總計約 $3-5，餘額充足）

---

## [2026-07-06] — feat(llm)：6-M1 分組模型環境變數（任務導向路由落地）

### 決策依據與證據
- **`core/config.py` 三組模型變數**：`LLM_MODEL_GENERATE` / `LLM_MODEL_VALIDATE` / `LLM_MODEL_CONTENT`，各配 lowercase fallback property（未設定 → `LLM_MODEL`，單一模型時代行為不變）；不抽共用 client（tech-debt 既有決策）
- **呼叫點切換**（依 6-M 選型表分流）：生成組 `llm_model_generate` = quiz/generate、quiz/hint、comprehension 出題（epl / predict_output / variation generate）；審查組 `llm_model_validate` = quiz/validate；內容組 `llm_model_content` = learning/content_generator（batch_generator `model_used` 記錄同步）；對話 + 分析組維持 `LLM_MODEL` 預設（edf/feedback、edf/evidence、reflection/evaluate、quiz/feedback、comprehension 評分）
- **variation `_call_llm_json` 加 `model` 參數**：出題與評分共用 helper，由 caller 分流
- **.env 套用選型**：`LLM_MODEL=gpt-5.4-mini`、`GENERATE=gpt-5-mini`、`VALIDATE=gpt-5.4`、`CONTENT=gpt-5.4`；`.env.example` 同步

## [2026-07-06] — feat(mastery)：第 3 批 K6a/b/c 熟練度演算法 v2 + knowledge-graph 拆檔

### 決策依據與證據
- **K6a 訊號分級**：`BKT_CHAT_PARAMS(learn=0.05, slip=0.3, guess=0.4)`——chat「程式碼無錯」是弱證據（學生常帶寫到一半的碼求助），以 BKT 參數本身表達通道雜訊；`update_mastery` 加 `params` 參數，chat 傳弱證據、quiz/comprehension 沿用強證據預設；測試驗證雙向更新幅度皆顯著小於 quiz
- **K6b 遺忘衰減**：新模組 `services/mastery/decay.py`——`effective = floor + (stored−floor)×exp(−ln2×days/half_life)`；floor=0.25、基準半衰期 14 天、每次成功練習 +50%（FSRS 穩定度）、上限 180 天；惰性計算不改 DB、BKT 更新仍以 stored 為 prior（衰減=提取強度下降，非習得倒退）。套用點：mastery summary（K4 鷹架自動連動）、quiz Select（衰減回弱項重新被選中=遺忘驅動複習）、K3 診斷（久未練習的前置概念可成嫌疑）
- **K6c 事件級透明化**：`/concepts/mastery` 加 `raw_confidence`/`days_since_practiced`/`due_for_review`；detail panel 顯示「已 N 天未練習，掌握度自 X% 回落至 Y%——建議複習」（due 用 accent-orange）與輕量提示（差 ≥5% 才顯示避免雜訊）；圖譜 band 色以 effective confidence 驅動、衰減自然變暗；不做逐筆帳本

## [2026-07-06] — feat(learn)：第 2 批 U2b 移除摘要 + U2c 拔課程介紹範例

### 決策依據與證據
- **`concept_category` 直通**：`UnitWithConcept` + `UnitOut` + 前端 `Unit` 型別加欄位；課程介紹單元（video 1-3）前端隱藏「範例程式」tab（含 activeTab 防呆退回概念說明）
- **批次生成跳過**：`generate_unit_content` 對 category=課程介紹 concept 不呼叫 examples LLM call，回空 examples 且不標 needs_more_source（避免 6-4 抽查誤判待補）

## [2026-07-06] — fix(workspace)：第 1 批 U1a/b/c — 首登誤顯、反思側欄比例、反思 handoff gating

### 決策依據與證據
- **U1a**：根路由 `/`（`app/(app)/page.tsx`）原為 Phase 1「程式碼編輯器將在後續任務中實作」placeholder——首次登入 OAuth callback 偶爾落在 `/`（NextAuth callbackUrl 遺失時預設值）即誤顯此畫面；改為 server-side `redirect("/workspace")`
- **U1b**：反思側欄被壓成細縫的根因＝react-resizable-panels **v4 裸數字解讀為 px 而非 %**（`maxSize={40}` = 最大 40 像素）；workspace 頁全部 Panel size props 改百分比字串（`"28%"`/`"40%"` 等，含 editor/output 垂直組）
- **U1c**：反思顯示 gating——`setActiveReflectionId`（僅「前往 Workspace」按鈕呼叫）同步寫 `active_reflection_handoff` 標記；Workspace 進入改用 `getHandedOffReflectionId()`：標記不符（直接 navigate 的殘留）→ 自動清除不顯示；同 tab 重新整理仍保留（非一次性消費，保住「當下解題脈絡」語意）；舊 session 殘留無標記 → 下次進 Workspace 自動清

---

## [2026-07-06] — docs(planning)：實作順序 + LLM 模型選型 v2 定案（任務導向路由）

### 決策依據與證據
- **roadmap 6-M LLM 模型選型 v2**（與使用者三輪討論定案，取代原論文指定的單一 GPT-4o）：任務導向路由——對話組（EDF Feedback）/ 分析組（Evidence、Reflection、Comprehension 評分）= `gpt-5.4-mini`；生成組（Quiz generate / Hint / Comprehension 出題）= `gpt-5-mini`；審查組（Quiz validate）= `gpt-5.4`（cascade：弱生成 + 強把關）；Unit content 6-2b 批次 = `gpt-5.4`（教科書品質優先）；Embedding 維持 text-embedding-3-small。6-M1 實作 = 分組環境變數（GENERATE/VALIDATE/CONTENT，fallback LLM_MODEL），不抽共用 client
- **費用估算**（依 2026-07 官方定價網查）：一次性批次 ≈ $6.6（content $4 + 生成 $1 + 審查 $1.6），儲值 $10；上線後即時互動 ≈ $35-40/月（100 學生，比 GPT-4o 省逾半）；不採 OpenAI Batch API（省 <$1.5 不值非同步改寫）
- **references.md §5.1 補論文文獻**：FrugalGPT（arXiv:2305.05176）+ RouteLLM（arXiv:2406.18665）——cascade / 模型路由設計依據
- **實作執行順序 10 批定案**（roadmap 已確認決策節）：U1 bugs → U2b/c 移除類 → k-graph 拆分 + K6 → quiz 模組（U2d/U2a/重複曝光） → 6-M1 + 實機批次 → U2f → 教師端（5-1→5-2→DEV-E→5-5） → U2e + 監控 → Phase 7 部署 → 5-3/5-4（待真實資料，Phase 5 資料策略註記同步修訂）

## [2026-07-06] — docs(planning)：session 規劃定案 — K6 熟練度演算法 v2 + Phase 6-U 學生端修正清單 + 文檔重整

### 決策依據與證據
- **roadmap K6 熟練度演算法 v2**（2026-07-06 與使用者 AskUserQuestion 裁決）：K6a 訊號分級 BKT 參數（quiz 強證據沿用現參數 / chat 弱證據 guess↑ learn↓，以 slip/guess 表達觀察通道雜訊、不外掛權重係數）+ K6b 遺忘曲線惰性衰減（`floor + (conf−floor)·exp(−λ·days)`，半衰期隨練習次數成長＝FSRS 穩定度概念，floor 防歸零，讀取端套用不需排程）+ K6c 事件級透明化（OLM；語意化事件不給逐筆帳本，衰減 framing 為複習提示接 K-Graph 節點變暗）
- **roadmap Phase 6-U 學生端修正**：U1a 首登誤顯 Workspace 待製作畫面 / U1b 反思 UI 比例 / U1c 反思顯示 gating（sessionStorage 殘留）/ U2a QUIZ 美化 / U2b 移除 LEARN 摘要 tab / U2c 拔除 1-3 章範例程式 / U2d QUIZ tab 改題庫優先 / U2e Workspace 程式碼存檔 / U2f 範例程式製作（低優先）；教師端＝既有 Phase 5 不另立項
- **references.md §5.1 論文關鍵文獻標注**（使用者論文引用需求）：BKT（Corbett & Anderson 1995）/ BKT+Forgetting（Khajah et al. 2016）/ Ebbinghaus 指數衰減 / FSRS 記憶穩定度 / Duolingo HLR（Settles & Meeker 2016）/ contextual guess-slip（Baker et al. 2008）/ OLM（Bull & Kay + 2020 系統性回顧）/ 生成式學習（Fiorella & Mayer 2015）
- tech-debt 新增：unit content 生成管線 `summary` 欄位閒置（U2b 移除 tab 後，6-4 批次重跑前評估從 prompt 移除以省 token）

### Decisions（第一區現狀確認 + 第二區裁決）
- **題庫成本**：不採 NotebookLM（無公開 API、輸出對不齊題目 schema/citation）；批次 grounded 生成 + 題庫優先已是解方，QUIZ tab 補上題庫優先（U2d）即完整
- **題目入庫**：即時生成題 validated=True 後永久入庫且會被 from-bank 重複抽用（現行機制確認保留）
- **代碼存儲**：chat 快照 + 作答記錄入 DB；編輯器本身無存檔（重整即失）→ 列 U2e
- **反思粒度**：現行即「每題一份」（quiz source + question id），符合預期不改
- **LEARN 摘要**：直接移除（生成式學習研究：提供現成摘要效益低 + 冗餘效應）

---

## [2026-07-05] — feat(K5-太陽系主題)：NASA 行星影像 + 蛇形軌道佈局（與使用者共同定案）

### 決策依據與證據
- **星系背景隱形根因**：程序生成 SVG 缺 `width`/`height` 屬性，canvas rasterize 退回 300×150 預設尺寸 → cover 錯位成角落污漬（headless Edge 對照實驗證實）；NASA 影像為 JPG 無此問題，`galaxy-backgrounds.ts` 保留為備援並註記此坑
- **zoom 過大**：`fitWithCap` 取代裸 fit——fit zoom 與 `ZOOM_CAP=1.0` 取小，小章節不再貼臉
- **節點過密**：phyllotaxis 步距 52→74；章距 380→700、行距 680（蛇形 2×5）
- **線條凌亂**：跨章依賴邊預設 opacity 0.18 淡出（`edge[?cross]`），hover 高亮恢復；章內邊維持 0.7

---

## [2026-07-05] — feat(K5+K3e)：知識圖譜視覺改版 + 診斷前端入口

### 決策依據與證據
- **K5a 套件決策記錄**（`docs/references.md` §1）：維持 Cytoscape.js + fcose——fcose 是唯一同時支援 compound node + constraint 的 force-directed layout；dagre 不支援 compound（無法分章 cluster）；React Flow 定位 workflow editor、遷移需重寫全部 graph 程式碼無決定性優勢；D3 手刻本已禁用
- **K5b 熟練度視覺**：節點填色改為 mastery band（綠=已掌握 / 橙=學習中 / 紅=需加強 / 灰=尚未互動，取代原 category 填色 + underlay 外圈）；每個 category 產生 compound parent 形成分章 cluster（fcose `nestingFactor: 0.15`）；prerequisite 邊箭頭放大（arrow-scale 0.75→1）+ 不透明度提高（0.55→0.7）；`toElements` 自 style 檔拆至 `knowledge-graph-elements.ts` 控制檔案大小
- **K5c 路徑高亮**：underlay ring 改承載路徑語意——藍 ring=目前單元（in_progress，無則取 order 最小 available）/ 綠 ring=已完成 / 紅 ring=補救嫌疑；overlay 由 `/learning/paths/default` 衍生（`path-overlay.ts` 純函式，載入失敗不擋圖譜主體）；`/knowledge?remedial=tag1,tag2` query 觸發紅 ring + 鏡頭聚焦（K3e 跳轉入口）；header 圖例改共用 `graph-legend.tsx`
- **K3e 診斷前端入口**：quiz 結果頁答錯自動查 `GET /concepts/{tag}/diagnosis`（未觸發或失敗自動隱藏，符合 K3d 設計）；觸發時顯示嫌疑鏈（depth / 熟練度 / 盲區標示）+ 每節點「微測驗」按鈕（新端點 `GET /quiz/questions/{id}` 直取 K3c 附掛的題庫診斷題，僅 validated）+「開放補救路徑」（POST remediate → 顯示重開單元順序 + Learn 連結）+「在知識圖譜查看嫌疑鏈」（`?remedial=` 跳轉）

## [2026-07-04] — feat(K4a/b)：Coddy 自適應提示 — K-Graph 鷹架 + RAG 相關性觸發

### 決策依據與證據
- **K4b（原 6-5a）** RAG 觸發改內容相關性：`TeachingStrategy` 移除 `use_rag` 欄位與 `hint>=2 && bloom>=ANALYZE` 寫死規則；`fetch_rag_chunks_safe` 每次互動都檢索、只注入 cosine >= `RAG_MIN_SCORE`（0.40 初始值，K4d 實測調參）的 chunks，全低於門檻回空（該查就查、不相關不硬塞）
- **K4a（原 6-5b）** persona 語氣改寫：Coddy 具名、先肯定再引導、提問具體到程式碼、小事直接回答；RULE-5 從「永遠以提問結尾」放寬為「自然的下一步收尾（提問或行動建議），不必刻意反問」
- `.claude/rules/edf-pipeline.md` 同步：RAG 觸發規範改為相關性分數、prompt 組裝順序加 kgraph 層、persona 描述更新
- 既有 decision / feedback 測試配合 `use_rag` 移除改寫

---

## [2026-07-04] — feat(K3)：根源弱點定位器後端（圖回溯認知診斷）

### 決策依據與證據
- `services/diagnosis/root_cause.py`：**K3a** stateless 觸發判定（該 concept 最近作答連續失敗 streak，遇答對截斷，>= 3 觸發）+ **K3b** closure（max_depth=3）回溯嫌疑排序（已曝光低 confidence 優先 → 未曝光盲區；高 confidence 前置排除；上限 3）+ **K3c** 每個嫌疑附題庫 validated 診斷題 question_id
- **K3d-API** `GET /concepts/{tag}/diagnosis`（獨立 route 檔避免 concepts.py 破 250 行；純 DB 讀取不掛 rate limit；未觸發回 triggered=false 供前端隱藏入口）
- 新增 K3e（前端入口）追蹤項，建議與 K5 視覺改版一併設計

## [2026-07-04] — feat(K2)：動態知識狀態追蹤 — EDF 對話重新驅動 BKT

### 決策依據與證據
- **K2a** migration `j6e7f8a9b0c1`：`concepts.edf_parent_tag` 欄位 + index + mapping seed（EDF 20 粗 tag 中 10 個對映 59 個影片 concept；課程介紹 3 個 NULL；STL/template/concurrency 等課綱未涵蓋 tag 照舊跳過）
- **K2a** `services/mastery/resolve.py`：三層 fan-out 解析（① tag 直接命中 → ② parent group 只更新該生已曝光組員 → ③ 全未曝光只更新組內 video_order 最小的入門 concept）——讓 Workspace 對話重新驅動 BKT，同時防止粗 tag 對話噪音淹沒 quiz / comprehension 精準信號；消除 tech-debt「EDF Mastery 連動暫時退場」
- **K2b** `GET /concepts/mastery` 加 `last_practiced_at`（K4 Coddy prompt 的時序信號；缺口分析後改為擴充既有端點、不新建 k-state API）
- **K2c 決策記錄**：暫不引入真 AST（tree-sitter/libclang）——LLM Evidence 已輸出等效信號；Phase 5 有行為資料後重評（記 tech-debt）

## [2026-07-04] — feat(K1)：K-Graph 自適應學習引擎啟動 — 跨章多對多依賴 DAG

### 決策依據與證據
- `docs/roadmap.md`：**移除 6-5 / 6-6 段**（內容完整整併至 K4 / K1+K5，留整併說明）；已確認決策更新（知識圖譜重構決議標記完成、新增 Phase 6-K 決策）
- `docs/tech-debt.md`：「跨章節 PREREQUISITE 邊未標」✅ 消除（K1a）；「EDF Mastery 連動退場」cross-ref K2a；「Learn 頁 graph 版」併入 K5
- `docs/modules.md` Module 5 升級為 K-Graph 引擎描述；`docs/db-schema.md` 補邊資料現況注記
- 可行性檢查結論：schema 原生支援多對多（unique triple）、拓撲排序已處理 DAG、quiz select 的出度中心性加權在 DAG 下才真正生效（線性鏈時全部 out_degree=1 無區分度）——K1 為資料工程而非架構重寫

---

## [2026-05-22] — Phase 6-3b ExercisesTab 題庫優先（GET /quiz/from-bank + 前端分流 fallback）

### 決策依據與證據
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

### 決策依據與證據
- **為什麼 endpoint 用 GET 而非 POST**：抽題是冪等讀取操作（每次隨機抽 1 題；非建立資源），語意上 GET 更合適；URL 中 `concept_tag=` 也便於除錯 / 觀察。
- **為什麼 random.choice 在 Python 端而非 SQL `ORDER BY RANDOM()`**：JSON contains（`concept_tags @> [tag]`）跨 SQLite/Postgres 寫法差異大；既然候選量 n ≤ 數十，先撈出再 Python random 是可攜的低成本選擇。未來流量大或 dedup 需要更複雜邏輯時可升級。

## [2026-05-22] — 設計反轉：video_order 1-3（課程介紹）加回學習路徑

### 決策依據與證據
- **新 alembic migration `h4c5d6e7f8a9_seed_intro_video_prerequisites.py`**：補 3 條 PREREQUISITE 邊
  - `cpp-01-language-intro` → `cpp-02-cpp-overview`
  - `cpp-02-cpp-overview` → `cpp-03-devcpp-install`
  - `cpp-03-devcpp-install` → `cpp-04-first-program`
  - 完整鏈：1→2→3→4→...→62（共 61 條 prerequisite 邊）
- **`backend/services/learning/generator.py`**：移除 `EXCLUDED_FROM_PATH_CATEGORIES` 常數與 `notin_` 過濾條件；`_fetch_concepts` 改為純 `select(Concept)` + optional category filter
- **`backend/services/learning/batch_generator.py`**：移除 EXCLUDED 過濾；`list_target_concepts` 改為只過濾 `video_order IS NULL`；docstring 更新「涵蓋全部 62 部（含 1-3）」
- **保留 `category="課程介紹"` 不變**：未來知識圖譜頁可用此 category 做 styling 區分（不再做路徑過濾用途）
- **`docs/roadmap.md`**：6-1c 條目 + 「已確認決策」段 1-3 處理方式 + Phase 6 開頭「Concept 範圍」說明 — 三處同步修訂

## [2026-05-13] — chore(web): middleware → proxy 遷移（Next.js 16 deprecation）

### 決策依據與證據
`npm run dev` 出現 deprecation 警告 `The "middleware" file convention is deprecated. Please use "proxy" instead.`。Next.js 官方理由：避免與 Express middleware 概念混淆，且明確標示其位於 Edge Runtime 上的 proxy 性質。

## [2026-05-08] — Phase 6-2b 程式碼完成：grounded 批次生成 + staging table + retry + promote helper（待使用者實機驗證）

### 決策依據與證據
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

## [2026-05-08] — Phase 6-1e 完成：Whisper 全 62 部 transcript + 二次審核 + 861 chunks 入 RAG（NotebookLM 核心就緒）

### 決策依據與證據
原計畫 A（yt-dlp 抓 zh-Hant 自動字幕）**徹底失敗**——6/6 樣本影片皆 "no automatic captions, no subtitles"（教授頻道未開或 YT 未生成）。改採 B1（OpenAI Whisper API），實測品質高（教授名「黃國豪」抓對；C++/devc++/Cout 等術語多數正確），唯一系統性錯辨「黃國昊」（同音字 hào），由二次審核 corrections.json 全域替換解決。

### 設計亮點
- **不破壞原始**：raw transcripts 永不修改；錯誤定位 + 重跑 apply 都很方便；可重複迭代 corrections
- **Timestamp markers 嵌入 chunk text**：LLM 在 6-2 生成時可直接抽出 `[mm:ss]` 做 citation，不用查 metadata（雖然 metadata 也保留 start/end_time_seconds）
- **二次審核機制**：global 解決系統性錯誤（一條 fix 多影片）；per_video 留給 6-4 抽查階段針對性修
- **Reset & re-ingest 高效**：發現「黃國華」漏網後，加 1 條 global → re-apply → --reset + re-ingest 全程 < 2 min

## [2026-05-07] — Phase 6 升級為 NotebookLM grounded 模式 + 6-1a/b 完成

### 決策依據與證據
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

## [2026-05-07] — Roadmap 新增 Phase 6 教學內容建構，原上線實測順延 Phase 7

### 決策依據與證據
- **原 Phase 6 上線實測 → Phase 7**：6-1/6-2/6-3 整段順延為 7-1/7-2/7-3，所有子任務同步重編號（cross-ref 註解保留歷史軌跡：原 4-3a → 6-1 → 7-1）
- **Phase 5 ⇄ Phase 6 平行關係**：執行策略 / 已確認決策最後一條同步調整為「兩者可平行 / 先後皆可，依教授資料準備進度而定」
- **Phase 7 前置條件加強**：除原 Zeabur + VPS 就緒外，新增「Phase 6 至少 6-1 + 6-2b 完成」（避免部署後 Learn 頁面仍空殼）

## [2026-05-07] — Roadmap 重整 follow-up：修正其他 doc 殘留舊 Phase 標號

### 決策依據與證據
- **`docs/design-plan.md` §4.5**：`1-7c 上線驗證` → `Phase 6 上線實測（原 1-7c → 4-3a → 6-1b Golden path）`，保留歷史演進 cross-reference
- **`docs/modules.md` Module 8 / 9**：Phase 4 → **Phase 5**（教師 Dashboard / 學習行為分析屬教師端，非部署）
- **`docs/db-schema.md` chat_messages 擴充欄位註記**：Phase 4-2c → **Phase 5-2c**（dialogue_act 屬行為資料收集，原本就在 5-2c，4-2c 為誤標）
- **`docs/roadmap.md` Phase 1 結尾註記**：「部署原 1-7 已移至 Phase 4」補完為「Phase 4（容器化 / 配置層）+ Phase 6（上線實測）」反映當前兩段切分

## [2026-05-07] — Roadmap 重整：上線實測類任務集中至 Phase 6

### 決策依據與證據
- **`docs/roadmap.md` 結構調整**：將「需要實際部署到 Zeabur / VPS 才能驗證」的工作集中到新的 **Phase 6 上線實測**
  - 原 `Phase 4-3 上線驗證`（4-3a/b/c）整段移至 Phase 6
  - 4-3a Golden path → **6-1**（拆成 6-1a 部署 / 6-1b Golden path / 6-1c 教師端 e2e 三步驟）
  - 4-3b 監控 → **6-2**（拆出 6-2a/b/c 程式碼可本機完成 + 6-2d 須實際部署驗證告警鏈路）
  - 4-3c 效能 baseline → **6-3**（拆成 6-3a TTFB/LCP / 6-3b LLM p95 / 6-3c Judge0 / 6-3d 寫入 baseline 文件）
- **Phase 4 改名**：「部署上線」→「部署準備（容器化 + 配置層，本機可完成）」標記 ✅，明確區分本機可完成與須實際部署
- **Phase 5 前置條件放寬**：原「Phase 4 部署完成」→「Phase 4 配置層完成」，加註資料策略：5-1/5-2/5-5 純本機可完成；5-3/5-4 程式碼可先用合成資料寫，部署後以實測資料調校
- **執行策略 / 已確認決策**：頂部與底部同步更新為 Phase 2→3→4→5→6 新順序

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

### 設計關鍵
- **單次 outerjoin 而非 N+1**：59 concepts 只 1 個 query，不是 60+
- **教學順序排序**：concept video_order ASC / category 依 earliest video_order
- **MASTERED_THRESHOLD = 0.8 共用**：與 generator / dashboard.queries 一致；單一語意
- **全展開 vs 摺疊**：60 rows 一覽比 click ladder 直觀

## [2026-05-05] — Phase 3-3b：Dashboard 最近活動時間線

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

### 設計關鍵
- **submit 與 feedback 分離**：submit 立即回對錯（快）；feedback async fetch（LLM 慢，UI loading state 不擋畫面）
- **不重做 EDF Evidence**：quiz answer 結構化已知（is_correct + concept_tags），不需 LLM 拆解錯誤類型；EDF Evidence Pipeline 仍服務 chat 場景（學生提問時用）
- **未練概念視為 0**：`outerjoin` + 預設 0.0 — 顯示完整 concept_tags 不留空白，cold start 學生看到 0% 也比看到「無資料」直覺
- **推薦過濾三層**：同 user 的 path × 未完成 × concept_tag 匹配；避免推已學完的 unit 或他人路徑的 unit
- **獨立 route 檔**：`quiz_feedback.py` 拆出避免主 quiz.py 超 250 行（schema 定義較長）
- **LLM 失敗 fallback 對稱**：與 hint / EPL / Comprehension 設計一致；`suggestion_fallback` flag 讓前端顯示「離線」狀態
- **RecommendedUnit 連結到 /learn**：MVP 直接導向學習路徑首頁；未來可加深 deep-link 直跳特定 unit

## [2026-05-05] — Phase 3-2b：Quiz 計時器 + 5 級提示系統

### 決策依據與證據
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

### 設計關鍵
- **Hint Ladder 對齊 EDF Pipeline 規則**：`_ladder_description` 直接引用 `.claude/rules/edf-pipeline.md` 5 級定義；保證 hint 風格與 chat 評估的「直接給答案」防護一致
- **LLM 失敗 fallback 不擋學生**：類似 EPL/Comprehension 設計；fallback 句子分 5 個 level 預先寫好，前端用 `fallback` flag 提示「離線」狀態
- **強制遞增不可跳級**：教學原則防止學生直接看 level 5；後端不限制（接收 1-5 任何值），由前端 UX 控制
- **Hint 不寫入 DB**：純即時生成；`hint_level_used` 已透過 `/quiz/submit` 持久化（quiz history 可分析學生提示依賴度）
- **Timer 純前端**：不影響 submit 流程；submit 時 caller 仍從 startedAt 計算 time_spent_seconds（與 3-2a 邏輯一致）
- **MC 也支援 hint**：UI 統一；雖然 MC hint 教學意義較弱，但保留選擇權

---

## [2026-05-05] — Phase 3-2a：Quiz 頁面 — 選擇題 + 程式撰寫題正式版

### 設計關鍵
- **設計分工釐清**：Quiz 頁面 = 純測驗（取題 → 作答 → 結果），無反思流程；Learn 練習 tab（3-1e）= 學習場景含 Pre-Coding Reflection。避免在 Quiz 頁面強制反思打斷測驗節奏
- **Coding 題目前 is_correct=False**：`backend/services/quiz/grade.py` 的 coding 分支永遠回 False（Judge0 整合屬 Phase 4）；UI 提示這點，避免使用者困惑
- **Discriminated union for SubmitAnswer**：對應後端 `answer: dict` 但 TS 端用 union 強制型別 — 防止 caller 對 MC 傳 code 等錯誤
- **time_spent_seconds 自動計**：runner 在 question 模式記錄 `startedAt`，submit 時計算秒差送 server（為 3-2b 計時器顯示鋪路）
- **hint_level_used = 0 hardcoded**：3-2b 提示系統未實作前一律 0；submit API 已支援 0-5 範圍
- **coding 不揭露答案**：Phase 4 Judge0 整合後改用實際執行結果判分；3-2a 階段保留學生再思考空間
- **fill_blank UI 未做**：roadmap 明列 3-2a 為「選擇題 + 程式撰寫題」；fill_blank 在 result-view 已支援揭露答案邏輯，UI 待後續任務（顯示 `UnsupportedTypeNote` placeholder）
- **CodeEditor 復用**：直接 import 現有元件（守則 #7 不重複造輪子）；CodeMirror 6 + cpp + oneDark 已調整為 GitHub Dark token 對齊

## [2026-05-05] — Phase 3-1e：練習 tab 嵌入 Pre-Coding Reflection 觸發點（Phase 3-1 完成 🎉）

### 設計關鍵
- **「觸發點」非「完整作答」**：3-1e 範圍嚴格限於「在練習 tab 內取題 + 觸發反思」；完整 coding 作答 UI（編輯器 + Judge0 提交 + 判分回饋）屬 Phase 3-2 Quiz 完整版
- **向後相容的 quiz/generate**：新增 `concept_tag` 為 optional，原 cold-start fallback / 弱項補強邏輯不變
- **復用 ReflectionFlow 而非重寫**：對齊「不重複造輪子」（CLAUDE.md 守則 #7）；reflection 元件已成熟，直接 import 即可
- **Workspace 導引**：反思 approve 後的「在 Workspace 作答」連結會配合 Phase 2-5d 的 `setActiveReflectionId`（reflection_id 寫 sessionStorage）— 學生跳到 /workspace 寫程式時 AI Tutor 自動帶入此反思（EDF Pipeline 注入），完整閉環
- **題型固定 coding**：教學影片內容多為 coding 練習；MC/fill_blank 對「練習」概念意義較弱，3-1e 不暴露選擇

## [2026-05-05] — Phase 3-1c+ 簡化：onboarding 自動 seed 預設路徑（移除無意義的「生成路徑」UX）

### 重新評估
- 3-1c 原設計含「+ 生成新路徑」按鈕 + EmptyState + 多路徑列表，預期學生會手動建立多條路徑
- 但 3-1c+ concept graph 重建為固定 59 影片線性鏈後，每位學生「生成」結果完全相同
  → category filter 是唯一變數但 99% 學生會學完整課程
  → 「生成」變無意義儀式，違反「不為不存在的需求設計」原則（YAGNI / CLAUDE.md 守則 #7）
- 結論：移除手動生成 UI，改為 onboarding 自動 seed

### 設計關鍵
- **「ensure 而非 default-named」語意**：`ensure_default_path_exists` 回任何已存在路徑（不檢驗 title），避免使用者手動建立非預設 title 後又被自動建一條重複的
- **Backend endpoints 完全保留**：POST/DELETE/GET list 仍在；schema 完全保留；前端不暴露但 schema 仍支援多 path（為未來教師端 / 複習路徑預留）
- **無 list 視圖反而更簡潔**：原 path-card.tsx 在只有 1 條路徑時是視覺噪音；直接顯示 detail 更直覺
- **path-detail 移除 onBack**：detail 變主畫面，無「返回」目的地；unit-content 內仍有「返回路徑：xxx」按鈕（unit → detail 的返回有意義）
- **不刪除 schema/migration**：方案 A 純 UX 簡化，零 schema 變動；未來真有教師端再 git revert 復活 path-card / generate-dialog 即可

---

## [2026-05-05] — Phase 3-1d：學習單元內容頁（4 tab + status transition + 自動解鎖）

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

### 設計關鍵
- **方案 B（完全替換）vs A（共存）/ C（替換+對應）**：選 B 因為 chat-driven mastery 本來噪音多，真正可信信號來自 quiz/comprehension；簡化 99% 複雜度，符合 YAGNI 原則
- **線性 PREREQUISITE 鏈為主**：跨章節依賴（如 47 遞迴 ← 29 for）等教授後續標註；MVP 先簡單可用
- **Migration 不可重跑（destructive）**：alembic 只跑一次此 revision，OK；dev/prod 都會清掉舊 concept；目前未上線無真實學生資料風險
- **學習路徑生成可立即運作**：拓撲排序在 59 個 concept + 58 條線性邊上產生有意義路徑；弱項補強仍能依 BKT 信心度排序
- **YT player 整合延後**：`video_youtube_id` 已在 schema，等教授補資料後 3-1d 學習單元頁實作

## [2026-05-05] — Phase 3-1c：Learn 頁面 — 路徑視覺化 + 進度條

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

### 設計關鍵
- **passed=None 不觸碰 mastery**：BKT 演算法對「答錯」與「未評分」應有差別 — fallback 不該被當作扣分，否則 LLM 偶發失敗會誤傷學生信心度
- **trigger 純規則 + DB 查詢**：可預測、易測；不引入隨機性 / RL（避免過度工程，符合守則 #7「不過度設計」）
- **threshold 集中常數**：`HIGH_PASS_THRESHOLD` / `MID_HIGH_PASS_THRESHOLD` / `MID_LOW_PASS_THRESHOLD` 提到 module 頂端，方便未來 A/B test 調參
- **`_decide` 獨立函式**：12 個 unit test 直接覆蓋規則矩陣，不需 DB；`decide_trigger` 只負責 fetch + dispatch
- **route 拆獨立檔**：trigger endpoint 放 `comprehension_trigger.py`，主 `comprehension.py` 維持 242 行不超 250

## [2026-05-05] — Phase 2-6d：變體挑戰（LLM 生變體題 + 評分學生新解）

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

### 設計關鍵
- **題型限制**：predict_output 只對 coding 有意義（其他 → 422 PREDICT_OUTPUT_NOT_APPLICABLE），避免「對 MC 預測輸出」這種無意義操作
- **expected 不洩漏**：generate response 只回 `test_input`；server 把 `{"input", "expected"}` 用 JSON 編碼存入 `comprehension_prompt`，grade 時解出比對
- **expected 對學生實際程式**：LLM 推理時被告知「對學生這份程式（含可能的 bug）」的輸出，而非題目正解 — 教學目標是「能否預測自己程式行為」
- **兩階段比對**：先嚴格 normalize（trim + 折疊空白）→ 不通過再 LLM 語意 → 任一通過即 passed=True；學生友善（容忍 `1, 2, 3` vs `1 2 3`）但保留精確性（順序 / 數值錯誤一律不過）
- **LLM 失敗對稱**：generate → 503；grade Stage 2 失敗 → fallback 用 Stage 1 結果（mismatch passed=False，不擋學生流程）
- **expected 即時回前端**：grade response 帶 `expected_output`，學生答完可自我對照學習

---

## [2026-05-05] — Phase 2-6b：EPL 驗證（LLM 出題 + 評分學生回答）

### 設計關鍵
- **重置語意**：generate 每次都清空 `comprehension_answer/passed`，避免新 prompt 搭配舊回答的資料錯亂
- **順序強制**：grade 必須先 generate（無 prompt → 400 EPL_NOT_STARTED），確保 LLM 評分時有完整脈絡
- **失敗策略不對稱**：generate 失敗 503（前端可重試）；grade 失敗 200 + passed=None（學生回答仍持久化方便重試評分，不擋流程）
- **細項分數不入庫**：schema 只有 `comprehension_passed: bool`；conceptual/specificity/causality 屬即時回饋，前端顯示一次即可，不需歷史追蹤
- **拆檔對齊 250 行限制**：epl.py 原 264 行 → 拆出 epl_prompts.py（純字串模板）後 159 行，符合 CLAUDE.md 硬性門檻

---

## [2026-05-05] — Phase 2-6a：Post-Solution Comprehension Check 持久化基礎

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
