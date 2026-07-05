/**
 * K5 確定性佈局（純函式）— 取代 fcose 隨機 force-directed 結果。
 *
 * 設計：章節（星系）沿左→右 S 曲線排列呈現學習進程；章內節點以
 * phyllotaxis（向日葵螺旋，黃金角 137.5°）繞章心展開——形似星團、
 * 零重疊、且輸入相同時輸出永遠相同。
 *
 * 排序依據：章節序 = 章內最小 video_order；章內序 = video_order。
 * null video_order 一律排最後（以 tag 字典序保證穩定）。
 */

import type { ConceptNode, GraphData } from "./knowledge-graph-types";

// S 曲線與螺旋參數（依 10 章 × 最多 12 節點/章 調校）
const CHAPTER_SPACING_X = 380;
const WAVE_AMPLITUDE = 170;
const WAVE_STEP = 0.9; // rad per chapter
const RADIUS_STEP = 52; // phyllotaxis r = step * sqrt(k)
const GOLDEN_ANGLE = 2.399963; // rad ≈ 137.5°

export type NodePosition = { x: number; y: number };

/** 章節依課綱順序排列（章內最小 video_order 升冪；無 video 章節殿後）。 */
export function orderedCategories(nodes: ConceptNode[]): string[] {
  const minOrder = new Map<string, number>();
  for (const n of nodes) {
    const order = n.video_order ?? Number.MAX_SAFE_INTEGER;
    const prev = minOrder.get(n.category);
    if (prev === undefined || order < prev) minOrder.set(n.category, order);
  }
  return [...minOrder.keys()].sort((a, b) => {
    const diff = minOrder.get(a)! - minOrder.get(b)!;
    return diff !== 0 ? diff : a.localeCompare(b);
  });
}

/** 章內節點排序（video_order 升冪、null 殿後、tag 決勝）。 */
function sortWithinChapter(nodes: ConceptNode[]): ConceptNode[] {
  return [...nodes].sort((a, b) => {
    const ao = a.video_order ?? Number.MAX_SAFE_INTEGER;
    const bo = b.video_order ?? Number.MAX_SAFE_INTEGER;
    return ao !== bo ? ao - bo : a.tag.localeCompare(b.tag);
  });
}

/** 計算全部 concept 節點的固定座標（key = node id）。 */
export function computePositions(data: GraphData): Map<string, NodePosition> {
  const categories = orderedCategories(data.nodes);
  const positions = new Map<string, NodePosition>();

  categories.forEach((category, chapterIndex) => {
    const anchorX = chapterIndex * CHAPTER_SPACING_X;
    const anchorY = WAVE_AMPLITUDE * Math.sin(chapterIndex * WAVE_STEP);
    // 每章螺旋起始角錯開，避免所有星團第一顆星朝同方向
    const startAngle = chapterIndex * 1.7;

    const members = sortWithinChapter(
      data.nodes.filter((n) => n.category === category),
    );
    members.forEach((node, k) => {
      const r = RADIUS_STEP * Math.sqrt(k);
      const theta = startAngle + k * GOLDEN_ANGLE;
      positions.set(node.id, {
        x: anchorX + r * Math.cos(theta),
        y: anchorY + r * Math.sin(theta),
      });
    });
  });

  return positions;
}
