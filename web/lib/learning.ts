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
