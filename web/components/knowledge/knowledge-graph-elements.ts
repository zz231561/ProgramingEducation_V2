/**
 * GraphData → Cytoscape elements 轉換（K5b 自 knowledge-graph-style.ts 拆出）。
 *
 * - 節點填色 = 熟練度 band（MASTERY_COLOR）
 * - 分章 cluster：每個 category 產生一個 compound parent（背景 = NASA 行星影像）
 * - K5c overlay：path_status（current/completed ring）+ remedial（紅 ring）
 * - 跨章邊標記 cross=true（聚焦時淡出以降低視覺凌亂）
 */

import type { ElementDefinition } from "cytoscape";

import { orderedCategories } from "./graph-layout";
import { MASTERY_COLOR } from "./knowledge-graph-style";
import { planetBackgroundFor } from "./planet-theme";
import type {
  GraphData,
  MasteryEntry,
  PathOverlay,
} from "./knowledge-graph-types";
import { getMasteryBand } from "./knowledge-graph-types";

/** 章節 parent 節點 id 前綴（與 concept uuid 區隔）；星系導覽 fit 也用它定位。 */
export const CHAPTER_ID_PREFIX = "chapter:";

export function toElements(
  data: GraphData,
  masteryMap?: Map<string, MasteryEntry>,
  pathOverlay?: PathOverlay,
): ElementDefinition[] {
  // 分章 compound parents（依課綱順序；index 決定星球背景樣式）
  // 標籤只用原分類名——星球是介面主題非主角（2026-07-05 使用者定案）
  const categories = orderedCategories(data.nodes);
  const parents: ElementDefinition[] = categories.map((category, i) => ({
    data: {
      id: `${CHAPTER_ID_PREFIX}${category}`,
      label: category,
      planet: planetBackgroundFor(i),
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

  const categoryById = new Map(data.nodes.map((n) => [n.id, n.category]));
  const edges: ElementDefinition[] = data.edges.map((e) => ({
    data: {
      id: e.id,
      source: e.source,
      target: e.target,
      edge_type: e.edge_type,
      weight: e.weight,
      // 跨章依賴邊：預設淡出（聚焦單章時畫面才不凌亂），hover 高亮不受影響
      cross: categoryById.get(e.source) !== categoryById.get(e.target),
    },
  }));

  return [...parents, ...nodes, ...edges];
}
