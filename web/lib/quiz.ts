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

/**
 * Phase 6-3b：從題庫隨機抽 validated grounded 題目（不呼叫 LLM）。
 *
 * - conceptTag 指定 → 抽該概念（Learn 練習 tab）
 * - conceptTag 省略 → U2d 弱項模式：後端沿用 Select 邏輯挑最弱概念（Quiz 頁）
 * - questionType 可選：依使用者選的題型過濾
 * - 後端一律排除已答過的題；命中 → < 1 秒回題；無題 → 拋
 *   ApiRequestError(404, "QUESTION_BANK_EMPTY")，caller fallback 至 generateQuestion。
 */
export async function getQuestionFromBank(
  conceptTag?: string,
  questionType?: QuestionType,
): Promise<Question> {
  const params = new URLSearchParams();
  if (conceptTag) params.set("concept_tag", conceptTag);
  if (questionType) params.set("question_type", questionType);
  const qs = params.toString();
  return api<Question>(`/quiz/from-bank${qs ? `?${qs}` : ""}`);
}

/**
 * K3e：以 id 直取題目（診斷嫌疑鏈微測驗入口）。
 * 僅 validated 題可取；不存在 → ApiRequestError(404, "QUESTION_NOT_FOUND")。
 */
export async function getQuestionById(questionId: string): Promise<Question> {
  return api<Question>(`/quiz/questions/${questionId}`);
}

/** 6-3c：LEARN 單元題組單題（含該學生作答狀態）。 */
export interface UnitQuestionItem {
  question: Question;
  is_answered: boolean;
  is_correct: boolean;
}

/** 6-3c：LEARN 單元題組回應。 */
export interface UnitSetResponse {
  concept_tag: string;
  items: UnitQuestionItem[];
  total: number;
  answered: number;
}

/**
 * 6-3c：取某概念的預生成題組（source='batch'）+ 作答進度。
 * LEARN 逐題作答用；不呼叫 LLM。QUIZ 弱項現生題不列入。
 */
export async function getUnitQuestionSet(
  conceptTag: string,
  questionType?: QuestionType,
): Promise<UnitSetResponse> {
  const params = new URLSearchParams({ concept_tag: conceptTag });
  if (questionType) params.set("question_type", questionType);
  return api<UnitSetResponse>(`/quiz/unit-set?${params.toString()}`);
}

/** 6-3d：弱項綜合測驗組回應。 */
export interface WeaknessSetResponse {
  questions: Question[];
  total: number;
  /** 無弱項（cold-start / 已全數掌握）→ true，前端提示先去 LEARN 練習 */
  no_weakness: boolean;
}

/**
 * 6-3d：一次生成弱項綜合測驗組（10 或 25 題）。
 * 題庫優先重用 + 缺口並行現生；單/綜合 MC 依掌握度自適應 + 1-2 綜合 coding。
 */
export async function getWeaknessSet(count: 10 | 25): Promise<WeaknessSetResponse> {
  return api<WeaknessSetResponse>(`/quiz/weakness-set?count=${count}`, {
    method: "POST",
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
  /** 3-2c：供前端 fetch /quiz/answers/{id}/feedback */
  answer_id: string;
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

// === 3-2c 作答後 EDF 回饋 ===

export interface ConceptMasteryItem {
  concept_tag: string;
  concept_name_zh: string;
  /** 0.0-1.0；未練過視為 0 */
  confidence: number;
}

export interface RecommendedUnit {
  unit_id: string;
  path_id: string;
  concept_tag: string;
  concept_name_zh: string;
  video_order: number | null;
  status: "locked" | "available" | "in_progress" | "completed";
}

export interface QuizFeedbackResponse {
  concept_mastery: ConceptMasteryItem[];
  suggestion: string;
  /** true = LLM 失敗用了固定 fallback 模板 */
  suggestion_fallback: boolean;
  recommended_units: RecommendedUnit[];
}

export async function getQuizFeedback(
  answerId: string,
): Promise<QuizFeedbackResponse> {
  return api<QuizFeedbackResponse>(`/quiz/answers/${answerId}/feedback`);
}
