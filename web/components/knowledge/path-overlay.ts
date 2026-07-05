/**
 * K5c 個人化路徑 overlay 衍生邏輯（純函式）。
 *
 * 由 default learning path 的 units 推導每個 concept 的路徑狀態：
 * - in_progress → current（目前單元；可能多個）
 * - completed → completed
 * - 無 in_progress 時，order_index 最小的 available → current（建議下一步）
 */

import type { Unit } from "@/lib/learning";

import type { PathNodeStatus, PathOverlay } from "./knowledge-graph-types";

export function buildPathOverlay(
  units: Unit[],
  remedialTags: string[],
): PathOverlay {
  const statusByTag = new Map<string, PathNodeStatus>();

  for (const u of units) {
    if (u.status === "completed") statusByTag.set(u.concept_tag, "completed");
    else if (u.status === "in_progress") statusByTag.set(u.concept_tag, "current");
  }

  const hasCurrent = [...statusByTag.values()].includes("current");
  if (!hasCurrent) {
    const nextAvailable = units
      .filter((u) => u.status === "available")
      .sort((a, b) => a.order_index - b.order_index)[0];
    if (nextAvailable) statusByTag.set(nextAvailable.concept_tag, "current");
  }

  return { statusByTag, remedialTags: new Set(remedialTags) };
}

/** 解析 /knowledge?remedial=tag1,tag2 query 參數（無參數 → 空陣列）。 */
export function parseRemedialParam(raw: string | null): string[] {
  if (!raw) return [];
  return raw
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}
