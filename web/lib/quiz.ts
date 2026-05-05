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
