/**
 * 根源弱點診斷 API helpers（roadmap K3e）。
 *
 * 對應後端 `GET /concepts/{tag}/diagnosis`（K3d）與
 * `POST /concepts/{tag}/diagnosis/remediate`（K4c）；schema 與
 * `backend/api/routes/diagnosis.py` 一致。
 */

import { api } from "./api";

export interface Suspect {
  tag: string;
  name_zh: string;
  /** 距目標的回溯層數（1 = 直接前置）。 */
  depth: number;
  /** null = 從未曝光（盲區）。 */
  confidence: number | null;
  exposure_count: number;
  /** 題庫診斷題；無題為 null。 */
  question_id: string | null;
}

export interface DiagnosisResponse {
  target_tag: string;
  triggered: boolean;
  recent_failure_streak: number;
  suspects: Suspect[];
}

export interface RemedialUnit {
  unit_id: string;
  concept_tag: string;
  name_zh: string;
  order_index: number;
  previous_status: string;
  status: string;
}

export interface RemediateResponse {
  target_tag: string;
  /** order_index 升冪 = 建議補救順序。 */
  remedial_units: RemedialUnit[];
}

export async function getDiagnosis(tag: string): Promise<DiagnosisResponse> {
  return api<DiagnosisResponse>(`/concepts/${encodeURIComponent(tag)}/diagnosis`);
}

export async function remediate(tag: string): Promise<RemediateResponse> {
  return api<RemediateResponse>(
    `/concepts/${encodeURIComponent(tag)}/diagnosis/remediate`,
    { method: "POST" },
  );
}
