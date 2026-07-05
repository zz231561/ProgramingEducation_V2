/**
 * GraphData → Cytoscape elements 轉換（K5b 自 knowledge-graph-style.ts 拆出）。
 *
 * - 節點填色 = 熟練度 band（MASTERY_COLOR）
 * - 分章 cluster：每個 category 產生一個 compound parent 節點
 * - K5c overlay：path_status（current/completed ring）+ remedial（紅 ring）
 */

import type { ElementDefinition } from "cytoscape";

import { MASTERY_COLOR } from "./knowledge-graph-style";
import type {
  GraphData,
  MasteryEntry,
  PathOverlay,
} from "./knowledge-graph-types";
import { getMasteryBand } from "./knowledge-graph-types";

/** 章節 parent 節點 id 前綴（與 concept uuid 區隔）。 */
const CHAPTER_ID_PREFIX = "chapter:";

export function toElements(
  data: GraphData,
  masteryMap?: Map<string, MasteryEntry>,
  pathOverlay?: PathOverlay,
): ElementDefinition[] {
  // 分章 compound parents（只為實際出現的 category 建立）
  const categories = [...new Set(data.nodes.map((n) => n.category))];
  const parents: ElementDefinition[] = categories.map((category) => ({
    data: {
      id: `${CHAPTER_ID_PREFIX}${category}`,
      label: category,
    },
  }));

  const nodes: ElementDefinition[] = data.nodes.map((n) => {
    const mastery = masteryMap?.get(n.tag);
    const band = getMasteryBand(mastery?.confidence);
    return {
      data: {
        id: n.id,
        parent: `${CHAPTER_ID_PREFIX}${n.category}`,
        tag: n.tag,
        label: n.name_zh,
        color: MASTERY_COLOR[band],
        // Obsidian 比例：18 base + 4 per difficulty (1-5 → 22-38 px)
        size: 18 + n.difficulty_level * 4,
        category: n.category,
        difficulty_level: n.difficulty_level,
        mastery_band: band,
        confidence: mastery?.confidence ?? null,
        // K5c：路徑狀態 ring（無狀態 → null 不命中 selector）
        path_status: pathOverlay?.statusByTag.get(n.tag) ?? null,
        remedial: pathOverlay?.remedialTags.has(n.tag) ?? false,
      },
    };
  });

  const edges: ElementDefinition[] = data.edges.map((e) => ({
    data: {
      id: e.id,
      source: e.source,
      target: e.target,
      edge_type: e.edge_type,
      weight: e.weight,
    },
  }));

  return [...parents, ...nodes, ...edges];
}
