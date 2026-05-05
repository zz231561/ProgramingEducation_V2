/**
 * Learning Path（結構化學習路徑）型別 + API helpers — Phase 3-1c。
 *
 * 對應後端 `/learning/paths` endpoints；schema 與 backend `models/learning.py` +
 * `api/routes/learning.py` 一致。
 */

import { api } from "./api";

export type UnitStatus = "locked" | "available" | "in_progress" | "completed";

export interface UnitContent {
  summary?: string;
  examples?: string[];
  exercise_question_ids?: string[];
}

export interface Unit {
  id: string;
  concept_id: string;
  concept_tag: string;
  concept_name_zh: string;
  concept_difficulty: number;
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

export interface PathSummary {
  id: string;
  title: string;
  description: string;
  total_units: number;
  completed_units: number;
  available_units: number;
  created_at: string;
  updated_at: string;
}

export interface GeneratePathPayload {
  title: string;
  description?: string;
  category?: string;
  skip_mastered_threshold?: number;
}

export async function listPaths(): Promise<PathSummary[]> {
  const data = await api<{ paths: PathSummary[] }>("/learning/paths");
  return data.paths;
}

export async function getPath(pathId: string): Promise<PathDetail> {
  return api<PathDetail>(`/learning/paths/${pathId}`);
}

export async function generatePath(
  payload: GeneratePathPayload,
): Promise<PathDetail> {
  return api<PathDetail>("/learning/paths", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function deletePath(pathId: string): Promise<void> {
  await api<void>(`/learning/paths/${pathId}`, { method: "DELETE" });
}

/** 計算進度百分比（0-100，無單元時為 0）。 */
export function progressPercent(summary: PathSummary): number {
  if (summary.total_units === 0) return 0;
  return Math.round((summary.completed_units / summary.total_units) * 100);
}
