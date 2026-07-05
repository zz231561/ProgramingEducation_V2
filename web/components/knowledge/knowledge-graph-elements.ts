/**
 * GraphData → Cytoscape elements 轉換（K5b 自 knowledge-graph-style.ts 拆出）。
 *
 * 雙層視圖（2026-07-05 五驗定案）：
 * - Detail 層：concept 節點（填色 = 熟練度）+ 分章 compound parent（星雲背景）
 * - Overview 層：每章一顆大型星系節點（星雲背景 + 可讀章名）+ 章間聚合依賴邊
 *   —— zoom out 的「最適排版」，由 graph-mode.ts 依 zoom 門檻切換顯示
 * - K5c overlay：path_status（current/completed ring）+ remedial（紅 ring）
 * - 跨章邊標記 cross=true（detail 聚焦時淡出以降低視覺凌亂）
 */

import type { ElementDefinition } from "cytoscape";

import { galaxyDataUri } from "./galaxy-backgrounds";
import { RADIUS_STEP, computeChapterAnchors } from "./graph-layout";
import { MASTERY_COLOR } from "./knowledge-graph-style";
import type {
  GraphData,
  MasteryEntry,
  PathOverlay,
} from "./knowledge-graph-types";
import { getMasteryBand } from "./knowledge-graph-types";

/** 章節 parent 節點 id 前綴（與 concept uuid 區隔）；星系導覽 fit 也用它定位。 */
export const CHAPTER_ID_PREFIX = "chapter:";
/** Overview 星系節點 id 前綴。 */
export const GALAXY_ID_PREFIX = "galaxy:";

/** Overview 星系節點 + 章間聚合依賴邊。 */
function overviewElements(data: GraphData): ElementDefinition[] {
  const anchors = computeChapterAnchors(data);
  const categoryById = new Map(data.nodes.map((n) => [n.id, n.category]));
  const countByCategory = new Map<string, number>();
  for (const n of data.nodes) {
    countByCategory.set(n.category, (countByCategory.get(n.category) ?? 0) + 1);
  }

  const galaxies: ElementDefinition[] = anchors.map(({ category, x, y }, i) => {
    const count = countByCategory.get(category) ?? 0;
    // 星系大小貼齊 detail cluster 的實際範圍，crossfade 時視覺連續
    const clusterRadius = RADIUS_STEP * Math.sqrt(Math.max(0, count - 1)) + 60;
    return {
      data: {
        id: `${GALAXY_ID_PREFIX}${category}`,
        label: `${category}\n${count} 個概念`,
        category,
        galaxy: galaxyDataUri(i),
        size: Math.round(clusterRadius * 1.8),
        overview: true,
      },
      position: { x, y },
    };
  });

  // 章間聚合依賴邊（任一跨章 prerequisite 即畫一條，去重）
  const seen = new Set<string>();
  const chapterEdges: ElementDefinition[] = [];
  for (const e of data.edges) {
    const a = categoryById.get(e.source);
    const b = categoryById.get(e.target);
    if (!a || !b || a === b) continue;
    const key = `${a}→${b}`;
    if (seen.has(key)) continue;
    seen.add(key);
    chapterEdges.push({
      data: {
        id: `gedge:${key}`,
        source: `${GALAXY_ID_PREFIX}${a}`,
        target: `${GALAXY_ID_PREFIX}${b}`,
        overview: true,
      },
    });
  }
  return [...galaxies, ...chapterEdges];
}

export function toElements(
  data: GraphData,
  masteryMap?: Map<string, MasteryEntry>,
  pathOverlay?: PathOverlay,
): ElementDefinition[] {
  // 分章 compound parents（依課綱順序；index 決定星雲樣式；標籤只用分類名）
  const anchors = computeChapterAnchors(data);
  const parents: ElementDefinition[] = anchors.map(({ category }, i) => ({
    data: {
      id: `${CHAPTER_ID_PREFIX}${category}`,
      label: category,
      category,
      galaxy: galaxyDataUri(i),
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

  return [...parents, ...nodes, ...edges, ...overviewElements(data)];
}
