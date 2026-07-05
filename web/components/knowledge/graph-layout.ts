/**
 * K5 確定性佈局（純函式）— 取代 fcose 隨機 force-directed 結果。
 *
 * 太陽系主題（2026-07-05 定案）：章節（天體）呈 2×5 蛇形軌道排列——
 * 上排太陽→火星左至右、下排木星→冥王星左至右，行間微幅弧線起伏；
 * 章內節點以 phyllotaxis（向日葵螺旋，黃金角 137.5°）繞章心展開，
 * 落在行星盤面上——零重疊、輸入相同時輸出永遠相同。
 *
 * 排序依據：章節序 = 章內最小 video_order；章內序 = video_order。
 * null video_order 一律排最後（以 tag 字典序保證穩定）。
 */

import type { ConceptNode, GraphData } from "./knowledge-graph-types";

// 蛇形軌道與螺旋參數（依 10 章 × 最多 12 節點/章 調校）
const COLS = 5;
const CHAPTER_SPACING_X = 700;
const ROW_GAP = 680;
const ARC_LIFT = 60; // 每排的弧線起伏幅度
const RADIUS_STEP = 74; // phyllotaxis r = step * sqrt(k)（原 52，依使用者回饋放寬）
const GOLDEN_ANGLE = 2.399963; // rad ≈ 137.5°

export type NodePosition = { x: number; y: number };
export type ChapterAnchor = { category: string; x: number; y: number };

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

/** 章節錨點（蛇形 2×COLS + 弧線起伏）；軌道 underlay 也用同一組座標。 */
export function computeChapterAnchors(data: GraphData): ChapterAnchor[] {
  return orderedCategories(data.nodes).map((category, i) => {
    const row = Math.floor(i / COLS);
    const col = i % COLS;
    return {
      category,
      x: col * CHAPTER_SPACING_X,
      y: row * ROW_GAP + ARC_LIFT * Math.sin((col / (COLS - 1)) * Math.PI),
    };
  });
}

/** 計算全部 concept 節點的固定座標（key = node id）。 */
export function computePositions(data: GraphData): Map<string, NodePosition> {
  const positions = new Map<string, NodePosition>();

  computeChapterAnchors(data).forEach(({ category, x, y }, chapterIndex) => {
    // 每章螺旋起始角錯開，避免所有星團第一顆星朝同方向
    const startAngle = chapterIndex * 1.7;
    const members = sortWithinChapter(
      data.nodes.filter((n) => n.category === category),
    );
    members.forEach((node, k) => {
      const r = RADIUS_STEP * Math.sqrt(k);
      const theta = startAngle + k * GOLDEN_ANGLE;
      positions.set(node.id, {
        x: x + r * Math.cos(theta),
        y: y + r * Math.sin(theta),
      });
    });
  });

  return positions;
}
