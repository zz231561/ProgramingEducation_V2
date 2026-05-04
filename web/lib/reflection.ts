/**
 * Reflection（解題前反思）型別 + API helper — Phase 2-5c。
 *
 * 對應後端 `/reflection` endpoints；schema 與 backend `models/reflection.py` 一致。
 * UI 流程：填表單 → POST → 若有 followup_question 顯示追問 → PATCH followup_answer → 再評分。
 */

import { api } from "./api";

export type ReflectionSourceType = "quiz" | "learning_unit";

export interface Reflection {
  id: string;
  user_id: string;
  source_type: ReflectionSourceType;
  source_id: string;
  problem_understanding: string;
  planned_steps: string[];
  expected_concepts: string;
  quality_score: number | null;
  followup_question: string | null;
  followup_answer: string | null;
  is_modified: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateReflectionPayload {
  source_type: ReflectionSourceType;
  source_id: string;
  problem_understanding: string;
  planned_steps: string[];
  expected_concepts: string;
}

export interface PatchReflectionPayload {
  planned_steps?: string[];
  expected_concepts?: string;
  followup_answer?: string;
  problem_understanding?: string;
}

/** 後端品質門檻 — 與 `services/reflection/evaluate.py` `QUALITY_THRESHOLD` 同步。 */
export const QUALITY_THRESHOLD = 0.6;

export async function createReflection(
  payload: CreateReflectionPayload,
): Promise<Reflection> {
  return api<Reflection>("/reflection", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function patchReflection(
  id: string,
  payload: PatchReflectionPayload,
): Promise<Reflection> {
  return api<Reflection>(`/reflection/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}
