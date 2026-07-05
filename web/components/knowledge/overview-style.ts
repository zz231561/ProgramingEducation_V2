/**
 * Overview（全覽）語意縮放樣式 — `.ov` 類別由 graph-mode.ts 切換。
 *
 * zoom out 後仍顯示全部概念節點與名稱：節點與字體改用放大的世界座標
 * 尺寸（font 30px × 全覽 zoom ≈ 0.3 → 螢幕約 9-10px 可讀），
 * cell 間距由 overview-layout.ts 配合此處尺寸設計，標籤互不重疊。
 */

import type { StylesheetCSS } from "cytoscape";

import { TOKEN } from "./knowledge-graph-style";

export const OVERVIEW_STYLES: StylesheetCSS[] = [
  // 概念節點：放大節點（ov_size = size × 1.7）與字體，文字轉主色提高對比
  {
    selector: "node[tag].ov",
    css: {
      width: "data(ov_size)",
      height: "data(ov_size)",
      "font-size": "30px",
      "text-max-width": "240px",
      "text-margin-y": 8,
      color: TOKEN.textPrimary,
    },
  },
  // 章節容器標籤同步放大，維持章名可讀
  {
    selector: "node:parent.ov",
    css: {
      "font-size": "48px",
      "text-margin-y": -16,
      color: TOKEN.textSecondary,
    },
  },
  // 邊與箭頭等比加粗，避免 zoom out 後細到不可見
  {
    selector: "edge.ov",
    css: {
      width: 3,
      "arrow-scale": 2,
    },
  },
  // 跨章依賴邊在全覽時是有效資訊，比 detail 的 0.18 略提高
  {
    selector: "edge[?cross].ov",
    css: { opacity: 0.3 },
  },
];
