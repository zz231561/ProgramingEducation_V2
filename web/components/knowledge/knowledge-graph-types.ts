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

/** confidence → band 對應；undefined（無 row）= unseen。 */
export function getMasteryBand(confidence: number | undefined): MasteryBand {
  if (confidence === undefined) return "unseen";
  if (confidence >= 0.8) return "mastered";
  if (confidence >= 0.4) return "learning";
  return "struggling";
}
