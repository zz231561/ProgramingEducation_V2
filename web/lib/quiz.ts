/**
 * Quiz API helpers — Phase 3-1e（Learn 練習 tab 取題）。
 *
 * 對應後端 `/quiz/generate`；schema 與 `backend/api/routes/quiz.py` 一致。
 * 完整 Quiz UI（含作答提交）屬 Phase 3-2；此 lib 僅 generate 部分。
 */

import { api } from "./api";

export type QuestionType = "multiple_choice" | "fill_blank" | "coding";

export interface CodingContent {
  stem: string;
  starter_code?: string;
}

export interface MultipleChoiceContent {
  stem: string;
  options: string[];
}

export interface FillBlankContent {
  stem: string;
}

export type QuestionContent =
  | CodingContent
  | MultipleChoiceContent
  | FillBlankContent;

export interface Question {
  id: string;
  type: QuestionType;
  concept_tags: string[];
  bloom_level: number;
  difficulty: number;
  content: QuestionContent;
}

export interface GenerateQuestionPayload {
  type: QuestionType;
  bloom_level?: number;
  /** 3-1e：指定 concept 出題；省略則走後端弱項補強邏輯。 */
  concept_tag?: string;
}

export async function generateQuestion(
  payload: GenerateQuestionPayload,
): Promise<Question> {
  return api<Question>("/quiz/generate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// === 3-2a 作答提交 ===

/** 學生作答 payload — 形狀依 question.type 決定。 */
export type SubmitAnswer =
  | { selected_index: number }      // multiple_choice
  | { code: string }                // coding
  | { answers: string[] };          // fill_blank

export interface SubmitQuestionPayload {
  question_id: string;
  answer: SubmitAnswer;
  time_spent_seconds?: number | null;
  /** 0-5；3-2b 提示系統未實作前一律 0 */
  hint_level_used?: number;
}

/** 提交後 server 回傳 — 含完整 content（含答案）+ feedback + explanation。 */
export interface SubmitResponse {
  is_correct: boolean;
  feedback: string;
  /** 完整題目內容（已含 answer_index / answers / 等揭露欄位）。 */
  correct_content: Record<string, unknown>;
  explanation: string;
}

export async function submitAnswer(
  payload: SubmitQuestionPayload,
): Promise<SubmitResponse> {
  return api<SubmitResponse>("/quiz/submit", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// === 3-2b 提示系統 ===

export interface HintRequestPayload {
  question_id: string;
  hint_level: number; // 1-5
  student_attempt?: string;
}

export interface HintResponse {
  level: number;
  hint: string;
  /** true = LLM 失敗用了固定 fallback 句 */
  fallback: boolean;
}

export async function requestHint(
  payload: HintRequestPayload,
): Promise<HintResponse> {
  return api<HintResponse>("/quiz/hint", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
