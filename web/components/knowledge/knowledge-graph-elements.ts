/**
 * GraphData → Cytoscape elements 轉換（K5b 自 knowledge-graph-style.ts 拆出）。
 *
 * 單一元素集（2026-07-05 語意縮放改版）：
 * - concept 節點（填色 = 熟練度）+ 分章 compound parent（無填色，僅章名標籤）
 * - overview / detail 共用同一批節點，zoom out 只切換 `.ov` 尺寸
 *   （ov_size）與佈局座標，由 graph-mode.ts 驅動
 * - K5c overlay：path_status（current/completed ring）+ remedial（紅 ring）
 * - 跨章邊標記 cross=true（detail 聚焦時淡出以降低視覺凌亂）
 */

import type { ElementDefinition } from "cytoscape";

import { computeChapterAnchors } from "./graph-layout";
import { MASTERY_COLOR } from "./knowledge-graph-style";
import type {
  GraphData,
  MasteryEntry,
  PathOverlay,
} from "./knowledge-graph-types";
import { getMasteryBand } from "./knowledge-graph-types";

/** 章節 parent 節點 id 前綴（與 concept uuid 區隔）。 */
export const CHAPTER_ID_PREFIX = "chapter:";

// overview 模式的節點放大倍率（配合 overview-style.ts 字體 30px）
const OVERVIEW_SIZE_SCALE = 1.7;

export function toElements(
  data: GraphData,
  masteryMap?: Map<string, MasteryEntry>,
  pathOverlay?: PathOverlay,
): ElementDefinition[] {
  // 分章 compound parents（依課綱順序；標籤只用分類名）
  const anchors = computeChapterAnchors(data);
  const parents: ElementDefinition[] = anchors.map(({ category }) => ({
    data: {
      id: `${CHAPTER_ID_PREFIX}${category}`,
      label: category,
      category,
    },
  }));

  const nodes: ElementDefinition[] = data.nodes.map((n) => {
    const mastery = masteryMap?.get(n.tag);
    const band = getMasteryBand(mastery?.confidence);
    // Obsidian 比例：18 base + 4 per difficulty (1-5 → 22-38 px)
    const size = 18 + n.difficulty_level * 4;
    return {
      data: {
        id: n.id,
        parent: `${CHAPTER_ID_PREFIX}${n.category}`,
        tag: n.tag,
        label: n.name_zh,
        color: MASTERY_COLOR[band],
        size,
        ov_size: Math.round(size * OVERVIEW_SIZE_SCALE),
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
