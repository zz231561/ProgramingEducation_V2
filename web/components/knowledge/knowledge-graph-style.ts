/**
 * Knowledge Graph 視覺樣式 — Cytoscape stylesheet + tokens。
 *
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
} as const;

// category → 節點背景色（語意：分類，非裝飾）
const CATEGORY_COLOR: Record<string, string> = {
  "基礎語法": "#58A6FF", // blue
  "記憶體": "#F85149",   // red
  "物件導向": "#3FB950", // green
  STL: "#BC8CFF",        // purple
  "演算法": "#D29922",   // orange
  "進階": "#8B949E",     // text-secondary
};

const DEFAULT_CATEGORY_COLOR = TOKEN.borderEmphasis;

// === Stylesheet ===

export const STYLESHEET: StylesheetCSS[] = [
  {
    selector: "node",
    css: {
      "background-color": "data(color)",
      "border-color": TOKEN.borderDefault,
      "border-width": 1,
      label: "data(label)",
      color: TOKEN.textPrimary,
      "font-size": "11px",
      "font-family": "Inter, 'Noto Sans TC', sans-serif",
      "text-valign": "center",
      "text-halign": "center",
      "text-wrap": "wrap",
      "text-max-width": "80px",
      width: "data(size)",
      height: "data(size)",
      shape: "round-rectangle",
    },
  },
  {
    selector: "node:selected",
    css: {
      "border-color": TOKEN.borderEmphasis,
      "border-width": 2,
    },
  },
  {
    selector: "edge",
    css: {
      "line-color": TOKEN.borderDefault,
      width: 1,
      "curve-style": "bezier",
      "target-arrow-color": TOKEN.borderDefault,
      opacity: 0.7,
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
    css: { "line-style": "solid", width: 0.5 },
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
      // 30 base + 6 per difficulty (1-5 → 36-60 px)
      size: 30 + n.difficulty_level * 6,
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
