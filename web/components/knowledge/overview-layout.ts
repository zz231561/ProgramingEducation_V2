/**
 * Overview（全覽）語意縮放佈局 — 純函式。
 *
 * 與 detail 蛇形星系不同：zoom out 後仍顯示全部概念節點與名稱，
 * 可讀性是第一優先。章節排 3 欄網格（9 章 → 3×3），章內節點排
 * 緊湊 cell 網格；cell 尺寸配合 overview 放大後的節點與字體
 * （overview-style.ts），在全覽 fit zoom（≈0.3）下標籤互不重疊。
 */

import type { ChapterAnchor, NodePosition } from "./graph-layout";
import { orderedCategories, sortWithinChapter } from "./graph-layout";
import type { GraphData } from "./knowledge-graph-types";

// cell 尺寸依 overview 樣式推算：節點 ≤65 + 最多 3 行標籤（font 30）
const CELL_W = 260;
const CELL_H = 180;
const CHAPTER_COLS = 3; // 章節網格欄數（9 章 → 3×3）
const CHAPTER_GAP = 220; // 章節區塊間距（另含 compound parent padding）

export type OverviewLayout = {
  positions: Map<string, NodePosition>;
  /** 章節錨點，已依蛇形（奇數列反向）排序 — 直接餵 buildOrbitPath。 */
  orbitAnchors: ChapterAnchor[];
};

type ChapterBlock = {
  category: string;
  cols: number;
  w: number;
  h: number;
};

/** 章內網格欄數（近方形區塊）。 */
function gridCols(count: number): number {
  return Math.max(1, Math.ceil(Math.sqrt(count)));
}

export function computeOverviewLayout(data: GraphData): OverviewLayout {
  const categories = orderedCategories(data.nodes);
  const membersByCategory = new Map(
    categories.map((c) => [
      c,
      sortWithinChapter(data.nodes.filter((n) => n.category === c)),
    ]),
  );

  const blocks: ChapterBlock[] = categories.map((category) => {
    const count = membersByCategory.get(category)!.length;
    const cols = gridCols(count);
    return {
      category,
      cols,
      w: cols * CELL_W,
      h: Math.ceil(count / cols) * CELL_H,
    };
  });

  // 兩段式定位：欄寬 = 該欄最寬區塊、列高 = 該列最高區塊
  const rowsCount = Math.ceil(blocks.length / CHAPTER_COLS);
  const colWidths = Array<number>(CHAPTER_COLS).fill(0);
  const rowHeights = Array<number>(rowsCount).fill(0);
  blocks.forEach((b, i) => {
    const col = i % CHAPTER_COLS;
    const row = Math.floor(i / CHAPTER_COLS);
    colWidths[col] = Math.max(colWidths[col], b.w);
    rowHeights[row] = Math.max(rowHeights[row], b.h);
  });

  // 各欄／列中心座標（累加前綴 + 間距）
  const colX: number[] = [];
  const rowY: number[] = [];
  let acc = 0;
  colWidths.forEach((w) => {
    colX.push(acc + w / 2);
    acc += w + CHAPTER_GAP;
  });
  acc = 0;
  rowHeights.forEach((h) => {
    rowY.push(acc + h / 2);
    acc += h + CHAPTER_GAP;
  });

  const positions = new Map<string, NodePosition>();
  const anchors: ChapterAnchor[] = blocks.map((b, i) => {
    const x = colX[i % CHAPTER_COLS];
    const y = rowY[Math.floor(i / CHAPTER_COLS)];
    membersByCategory.get(b.category)!.forEach((node, k) => {
      positions.set(node.id, {
        x: x - b.w / 2 + CELL_W * (k % b.cols) + CELL_W / 2,
        y: y - b.h / 2 + CELL_H * Math.floor(k / b.cols) + CELL_H / 2,
      });
    });
    return { category: b.category, x, y };
  });

  // 軌道弧線用蛇形順序（奇數列反向），視覺延續太陽系主題
  const orbitAnchors: ChapterAnchor[] = [];
  for (let r = 0; r < rowsCount; r++) {
    const row = anchors.slice(r * CHAPTER_COLS, (r + 1) * CHAPTER_COLS);
    orbitAnchors.push(...(r % 2 === 1 ? row.reverse() : row));
  }
  return { positions, orbitAnchors };
}
