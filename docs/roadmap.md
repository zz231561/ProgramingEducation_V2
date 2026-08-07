# Roadmap

> **狀態：活躍｜進度唯一真相來源。** 本檔只回答「現在做什麼、接著做什麼、卡在哪裡」。
> 完成歷史見 [`roadmap-archive.md`](roadmap-archive.md)，設計取捨見 [`decisions.md`](decisions.md)，
> 工程問題見 [`tech-debt.md`](tech-debt.md)，變更明細查 `git log`。
>
> **狀態規則**：`[ ]` 只代表已排程且有明確完成條件的工作；等人、等環境或條件式工作放在專區。
> 完成 milestone 在本檔留一行索引，細節不回填。既有任務 ID 保留，避免破壞歷史引用。

## 下一個接手點

| 欄位 | 內容 |
|------|------|
| 當前 milestone | **7-E 使用者驗收** |
| 下一個 Checkbox | **7-E0 驗收前準備** |
| 操作文件 | [`acceptance-checklist.md`](acceptance-checklist.md) §0 |
| 完成條件 | 環境、帳號、角色與 API 額度確認完成，可開始逐段真人驗收 |
| 驗證方式 | 能機器驗收的項目由 agent 執行；只有視覺、語氣與真實操作感受交給使用者 |

> 下一輪不論由 Codex 或 Claude Code 接手，都從 **7-E0** 開始；一次只做一個 Roadmap Checkbox。
> 發現小問題依「當場修小問題」守則處理；需要設計裁決的問題另排 Checkbox，不擴大當輪範圍。

## 執行順序

| 順序 | Milestone | 開始條件 | 狀態 |
|------|-----------|----------|------|
| 1 | **7-E 使用者驗收** | 7-C、7-D 已完成 | 🎯 現在 |
| 2 | **Phase 8 專案整理** | 7-E 無阻斷問題 | 待辦 |
| 3 | **7-2 監控與告警** | Phase 8 完成 | 待辦 |
| 4 | **7-3 效能 baseline** | 監控資料可取得 | 待辦 |
| 5 | **5-3／5-4 行為分析** | 已累積足夠真實學生資料 | 待條件 |

## 已排程工作

### 7-E 使用者驗收

> 逐段依 [`acceptance-checklist.md`](acceptance-checklist.md) 操作；已個別通過的案例仍保留在清單中，
> 所屬段落完成後才勾本檔。K1d、K4d、K5d 不再散落於舊 Phase，統一在對應驗收段完成。

- [ ] 7-E0 **驗收前準備**：確認 production、測試帳號、學生／教師角色與 LLM 額度
- [ ] 7-E1 **Workspace 執行與互動終端**：包含已通過的互動終端案例
- [ ] 7-E2 **Workspace 編輯器與檔案操作**
- [ ] 7-E3 **LEARN 課程動線**
- [ ] 7-E4 **Coddy 對話品質**：揭露階梯、NZEC／錯誤文案、「我卡住了」與 K4d 語氣／鷹架
- [ ] 7-E5 **QUIZ 與理解驗證**：含 Modal、AI 鎖與觸發頻率是否干擾學習
- [ ] 7-E6 **知識圖譜**：多對多渲染、個人進度與弱項可讀性（原 K1d／K5d）
- [ ] 7-E7 **教師端**：帳號、班級、作業與行為資料 production 端到端驗證（原 7-1c）
- [ ] 7-E8 **安全與設定**
- [ ] 7-E9 **持續回饋機制**：確認問題分流、回歸方式與後續新功能盤點入口

### Phase 8 專案整理

> 7-E 完成且無阻斷問題後開始；先盤點、後刪除。已前移完成的 8-1、8-3a 不再保留假待辦。

- [ ] 8-0a **新功能盤點**：依 7-E 回饋決定是否新增功能，未確認前不預設需求
- [ ] 8-2b **Git repository 維護**：評估並執行 `git gc`，前後量測但不手抄進文件
- [ ] 8-2c **死程式碼與孤兒檔案盤點**：只提出清單與處置建議，不自行刪除
- [ ] 8-2d **本機 ScreenShot 資料夾裁決**：確認用途後決定保留或移除
- [ ] 8-3b **前端測試下一層評估**：依 7-E 風險決定是否導入 React component tests／Playwright

### 7-2 監控與告警

- [ ] 7-2a **Sentry SDK**：前後端初始化、DSN 與異常捕捉
- [ ] 7-2b **結構化日誌**：request ID 與可查詢的 production log context
- [ ] 7-2c **健康檢查分層**：`/health/live` 與 `/health/ready`
- [ ] 7-2d **部署後告警鏈路驗證**：機器觸發並確認 issue、日誌與 health alert 可追蹤

### 7-3 效能 baseline

- [ ] 7-3a **前端體感**：量測 TTFB／LCP
- [ ] 7-3b **LLM 延遲**：量測 EDF、Quiz 與 Comprehension p95
- [ ] 7-3c **Runner 容量**：量測成功率、queue wait 與 production latency
- [ ] 7-3d **基準固化**：建立 `docs/performance-baseline.md`，記錄量測方法與可重跑結果

## 等外部條件

| ID | 條件 | 條件成立後移往 |
|----|------|----------------|
| 7-D8 E-WIN | 有可操作的 Windows PowerShell／Codex 環境 | 建立獨立驗收 Checkbox；不阻擋 7-D 或 7-E |
| 5-3 | production 已累積足夠真實學生行為與學習成效資料 | 行為相關性、分群、PrefixSpan 與 API |
| 5-4 | 5-3 產出可信分析結果 | 教師端行為分析視覺化 |

條件成立後仍沿用原 ID：5-3a 相關性、5-3b KMeans 分群、5-3c PrefixSpan、5-3d API；
5-4a 散佈／熱力圖、5-4b 時序／Hint 分布、5-4c 群聚／精熟度趨勢。

## 持續性工作

- **6-4b 教材品質修補**：使用者回報特定 unit 問題時，調整 grounded prompt、局部重跑；
  source 品質不足才重做 transcript。這是事件觸發規則，不是阻擋主線的未完成 Checkbox。
- **7-C4 驗收觀察**：在 7-E4 觀察弱學生是否因理解驗證過密而受干擾；若確認有問題，
  再建立「理解驗證間隔」Checkbox，不預先增加機制。
- **7-E9 production 回饋**：小問題當輪修；架構、教學設計或範圍擴散問題另排 Roadmap。

## 已完成 Milestones

| Milestone | 結果 |
|-----------|------|
| Phase 1–4 | MVP、智慧功能、學習體驗與部署配置完成 |
| Phase 5（5-1／5-2／5-5／5-6） | 班級、資料收集、作業與教師端完成；5-3／5-4 等真實資料 |
| Phase 6／6-K／6-U | Grounded 教材、題庫、自適應學習與學生端體驗完成；品質修補改事件觸發 |
| 7-1／7-R／7-U | Zeabur、互動 Runner 與上線後體驗完成；教師端真人驗收併入 7-E7 |
| 7-C | Coddy 教學品質修復與七型模擬完成；真人感受併入 7-E4／7-E5 |
| 7-D | 技術債、文件契約、教材健檢、錯誤 toast 與註解規範完成 |
| 7-D8 | Claude Code／Codex canonical source、雙端 adapters、CI drift check、macOS bootstrap 完成；Windows 實機驗收不阻擋結案 |

> 早期完成細節依 phase 查凍結的 [`roadmap-archive.md`](roadmap-archive.md)；近期變更以
> `git log --grep=<task-id>` 查詢。決策不得再複製回本檔。
