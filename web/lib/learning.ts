/**
 * Learning Path（結構化學習路徑）型別 + API helpers — Phase 3-1c。
 *
 * 對應後端 `/learning/paths` endpoints；schema 與 backend `models/learning.py` +
 * `api/routes/learning.py` 一致。
 */

import { api } from "./api";

export type UnitStatus = "locked" | "available" | "in_progress" | "completed";

/**
 * 6-2a Grounded citation — LLM 標註的 transcript 出處（mm:ss / mm:ss-mm:ss）。
 */
export interface Citation {
  timestamp: string;
  text_excerpt: string;
}

/**
 * 6-2a `concept_explanation` section — Markdown + citations，可能 needs_more_source。
 * Note：6-2b 完成批次生成前，learning_units.content 仍可能是舊形狀（無此欄位），故 optional。
 */
export interface ConceptExplanation {
  needs_more_source: boolean;
  reason: string;
  markdown: string;
  citations: Citation[];
}

/**
 * 6-2a `code_examples` section — 1-3 個程式範例，每個附 optional citation。
 */
export interface CodeExample {
  title: string;
  code: string;
  explanation: string;
  citation: Citation | null;
}

export interface CodeExamples {
  needs_more_source: boolean;
  reason: string;
  examples: CodeExample[];
}

/**
 * 6-2a `summary` section — 3-7 個 key_points + citations，可能 needs_more_source。
 * Note：舊 lazy-seed content.summary 是 string；promote 後變成此 object。
 *       SummaryTab 透過 typeof 判斷哪一種形狀。
 */
export interface SummaryContent {
  needs_more_source: boolean;
  reason: string;
  key_points: string[];
  citations: Citation[];
}

export interface UnitContent {
  // 舊形狀（3-1d）— 6-2b promote 後 summary 會被新 grounded object 形狀取代
  summary?: string | SummaryContent;
  examples?: string[];
  exercise_question_ids?: string[];
  // 6-2a/b 新 grounded 形狀（promote 後 staging → learning_units.content）
  concept_explanation?: ConceptExplanation;
  code_examples?: CodeExamples;
}

export interface Unit {
  id: string;
  concept_id: string;
  concept_tag: string;
  concept_name_zh: string;
  concept_difficulty: number;
  // 6-2c：嵌入 YT IFrame player 與 citation 跳轉所需
  video_youtube_id: string | null;
  video_duration_seconds: number | null;
  order_index: number;
  status: UnitStatus;
  completed_at: string | null;
  content: UnitContent;
}

export interface PathDetail {
  id: string;
  title: string;
  description: string;
  units: Unit[];
  created_at: string;
  updated_at: string;
}

/** 取（並 lazy seed）使用者的預設學習路徑 — Learn 頁面進入時的唯一入口。 */
export async function getDefaultPath(): Promise<PathDetail> {
  return api<PathDetail>("/learning/paths/default");
}

/** 重 fetch 已知 ID 的路徑（unit status 變動後同步用）。 */
export async function getPath(pathId: string): Promise<PathDetail> {
  return api<PathDetail>(`/learning/paths/${pathId}`);
}

// === 3-1d unit status transitions ===

export type WritableUnitStatus = "available" | "in_progress" | "completed";

export interface UnitBasic {
  id: string;
  order_index: number;
  status: UnitStatus;
  completed_at: string | null;
}

export interface UnitTransitionResult {
  unit: UnitBasic;
  next_unlocked_unit: UnitBasic | null;
}

export async function updateUnitStatus(
  unitId: string,
  status: WritableUnitStatus,
): Promise<UnitTransitionResult> {
  return api<UnitTransitionResult>(`/learning/units/${unitId}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}
