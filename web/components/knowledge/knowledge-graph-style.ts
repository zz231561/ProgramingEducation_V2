/**
 * Knowledge Graph 視覺樣式 — Cytoscape stylesheet + tokens。
 *
 * 風格參考：Obsidian Graph View（小圓點 + 細曲線 + hover 點亮鄰居）。
 * 所有色票必須來自 GitHub Dark token（frontend.md），不可引入外來 hex。
 * 顏色僅用於功能性語意（category / edge_type），符合 R8.4。
 */

import type { ElementDefinition, StylesheetCSS } from "cytoscape";

import type { GraphData } from "./knowledge-graph-types";

// === Design tokens（與 frontend.md 對齊） ===

export const TOKEN = {
  bgCanvas: "#0D1117",
  borderDefault: "#30363D",
  borderEmphasis: "#6E7681",
  textPrimary: "#E6EDF3",
  textSecondary: "#8B949E",
} as const;

// category → 節點背景色（語意：分類，非裝飾）— Detail Panel 也共用同一表
export const CATEGORY_COLOR: Record<string, string> = {
  "基礎語法": "#58A6FF", // blue
  "記憶體": "#F85149",   // red
  "物件導向": "#3FB950", // green
  STL: "#BC8CFF",        // purple
  "演算法": "#D29922",   // orange
  "進階": "#8B949E",     // text-secondary
};

export const DEFAULT_CATEGORY_COLOR = TOKEN.borderEmphasis;

// === Stylesheet (Obsidian-style) ===

export const STYLESHEET: StylesheetCSS[] = [
  // --- Node base ---
  {
    selector: "node",
    css: {
      "background-color": "data(color)",
      "border-color": TOKEN.borderDefault,
      "border-width": 1,
      shape: "ellipse",
      width: "data(size)",
      height: "data(size)",
      label: "data(label)",
      color: TOKEN.textSecondary,
      "font-size": "11px",
      "font-family": "Inter, 'Noto Sans TC', sans-serif",
      // 標籤外置於節點下方（Obsidian 風）
      "text-valign": "bottom",
      "text-halign": "center",
      "text-margin-y": 6,
      "text-wrap": "wrap",
      "text-max-width": "100px",
      "transition-property": "opacity, border-color, border-width, color",
      "transition-duration": 120,
    },
  },
  {
    selector: "node:selected",
    css: {
      "border-color": TOKEN.borderEmphasis,
      "border-width": 2,
    },
  },
  // --- Hover 鄰居高亮（label 變亮 + 邊框轉強）---
  {
    selector: "node.highlighted",
    css: {
      "border-color": TOKEN.borderEmphasis,
      "border-width": 2,
      color: TOKEN.textPrimary,
    },
  },
  // --- 淡化非鄰居（hover 時其他元素降透明度）---
  {
    selector: ".faded",
    css: { opacity: 0.18 },
  },

  // --- Edge base ---
  {
    selector: "edge",
    css: {
      "line-color": TOKEN.borderDefault,
      width: 1,
      opacity: 0.55,
      "curve-style": "bezier",
      "control-point-step-size": 30,
      "target-arrow-color": TOKEN.borderDefault,
      "arrow-scale": 0.75,
      "transition-property": "opacity, line-color, width",
      "transition-duration": 120,
    },
  },
  {
    selector: 'edge[edge_type = "prerequisite"]',
    css: {
      "line-style": "solid",
      "target-arrow-shape": "triangle",
    },
  },
  {
    selector: 'edge[edge_type = "contains"]',
    css: { "line-style": "dashed" },
  },
  {
    selector: 'edge[edge_type = "specialization"]',
    css: {
      "line-style": "dotted",
      "target-arrow-shape": "triangle",
    },
  },
  {
    selector: 'edge[edge_type = "related"]',
    css: { "line-style": "solid", width: 0.5, opacity: 0.4 },
  },
  // --- Edge hover 高亮 ---
  {
    selector: "edge.highlighted",
    css: {
      "line-color": TOKEN.borderEmphasis,
      "target-arrow-color": TOKEN.borderEmphasis,
      width: 1.5,
      opacity: 0.95,
    },
  },
];

// === GraphData → Cytoscape elements ===

export function toElements(data: GraphData): ElementDefinition[] {
  const nodes: ElementDefinition[] = data.nodes.map((n) => ({
    data: {
      id: n.id,
      tag: n.tag,
      label: n.name_zh,
      color: CATEGORY_COLOR[n.category] ?? DEFAULT_CATEGORY_COLOR,
      // Obsidian 比例：18 base + 4 per difficulty (1-5 → 22-38 px)
      size: 18 + n.difficulty_level * 4,
      category: n.category,
      difficulty_level: n.difficulty_level,
    },
  }));
  const edges: ElementDefinition[] = data.edges.map((e) => ({
    data: {
      id: e.id,
      source: e.source,
      target: e.target,
      edge_type: e.edge_type,
      weight: e.weight,
    },
  }));
  return [...nodes, ...edges];
}
