/** Knowledge Graph 共用型別 — 與後端 GET /concepts/graph 回應對齊。 */

export type ConceptNode = {
  id: string;
  tag: string;
  name_zh: string;
  name_en: string;
  description: string;
  difficulty_level: number;
  category: string;
};

export type ConceptEdge = {
  id: string;
  source: string;
  target: string;
  edge_type: "prerequisite" | "contains" | "specialization" | "related";
  weight: number;
};

export type GraphData = {
  nodes: ConceptNode[];
  edges: ConceptEdge[];
};

/** 與後端 ConceptDetailOut 對齊。direction 標示邊相對於 center 的方向。*/
export type NeighborRecord = {
  direction: "incoming" | "outgoing";
  edge: ConceptEdge;
  concept: ConceptNode;
};

export type ConceptDetailData = {
  concept: ConceptNode;
  neighbors: NeighborRecord[];
};

/** 與後端 MasteryEntryOut 對齊。 */
export type MasteryEntry = {
  tag: string;
  confidence: number;
  exposure_count: number;
  success_count: number;
  error_count: number;
  bloom_level: number | null;
};

/** 精熟度視覺分群（前端衍生）。 */
export type MasteryBand = "mastered" | "learning" | "struggling" | "unseen";

/** K5c 個人化路徑節點狀態（由 default path units 衍生）。 */
export type PathNodeStatus = "current" | "completed";

/** K5c 路徑高亮 overlay — 疊加在 mastery 著色之上的 ring 語意。 */
export type PathOverlay = {
  /** concept tag → 路徑狀態；不在 map 內 = 無 ring。 */
  statusByTag: Map<string, PathNodeStatus>;
  /** 診斷補救嫌疑節點（來自 /knowledge?remedial= query param）。 */
  remedialTags: Set<string>;
};

/** confidence → band 對應；undefined（無 row）= unseen。 */
export function getMasteryBand(confidence: number | undefined): MasteryBand {
  if (confidence === undefined) return "unseen";
  if (confidence >= 0.8) return "mastered";
  if (confidence >= 0.4) return "learning";
  return "struggling";
}
