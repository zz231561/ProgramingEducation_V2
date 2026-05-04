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
