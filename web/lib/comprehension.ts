/**
 * Post-Solution Comprehension（2-6）API client — 7-C3 前端接線。
 *
 * 流程：答對 → `getTriggerSuggestion` 判斷要不要驗、驗哪一種 →
 * 對應 type 的 `generate` 出題 → 學生作答 → `grade` 評分（後端已串 BKT 回寫）。
 *
 * 三種 type 的 generate/grade 契約各不相同，所以不做過度抽象的共用介面。
 */

import { api } from "@/lib/api";

export type ComprehensionType = "epl" | "predict_output" | "variation";

export interface TriggerDecision {
  student_answer_id: string;
  should_trigger: boolean;
  suggested_type: ComprehensionType | null;
  pass_rate: number | null;
  sample_size: number;
  reason: string;
}

export interface EplGenerated {
  comprehension_prompt: string;
}

export interface EplGrade {
  comprehension_passed: boolean | null;
  conceptual_correctness: number | null;
  specificity: number | null;
  causality: number | null;
  feedback: string | null;
}

export interface PredictGenerated {
  test_input: string;
}

export interface PredictGrade {
  comprehension_passed: boolean;
  expected_output: string;
  /** exact / semantic / mismatch — 前端只用來說明「怎麼算你答對的」 */
  match_method: string;
  feedback: string | null;
}

export interface VariationTestCase {
  input: string;
  expected: string;
}

export interface VariationGenerated {
  stem: string;
  starter_code: string;
  test_cases: VariationTestCase[];
  concept_focus: string;
}

export interface VariationGrade {
  comprehension_passed: boolean;
  feedback: string | null;
}

export function getTriggerSuggestion(answerId: string): Promise<TriggerDecision> {
  return api<TriggerDecision>(`/comprehension/trigger-suggestion/${answerId}`);
}

function post<T>(path: string, body?: unknown): Promise<T> {
  return api<T>(path, {
    method: "POST",
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
}

export function generateEpl(answerId: string) {
  return post<EplGenerated>(`/comprehension/${answerId}/epl/generate`);
}

export function gradeEpl(answerId: string, eplAnswer: string) {
  return post<EplGrade>(`/comprehension/${answerId}/epl/grade`, {
    epl_answer: eplAnswer,
  });
}

export function generatePredict(answerId: string) {
  return post<PredictGenerated>(`/comprehension/${answerId}/predict_output/generate`);
}

export function gradePredict(answerId: string, predictedOutput: string) {
  return post<PredictGrade>(`/comprehension/${answerId}/predict_output/grade`, {
    predicted_output: predictedOutput,
  });
}

export function generateVariation(answerId: string) {
  return post<VariationGenerated>(`/comprehension/${answerId}/variation/generate`);
}

export function gradeVariation(answerId: string, studentCode: string) {
  return post<VariationGrade>(`/comprehension/${answerId}/variation/grade`, {
    student_code: studentCode,
  });
}
