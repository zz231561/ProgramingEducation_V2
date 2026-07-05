/**
 * Knowledge Graph 視覺樣式 — Cytoscape stylesheet + tokens。
 *
 * 風格參考：Obsidian Graph View（小圓點 + 細曲線 + hover 點亮鄰居）。
 * K5b 改版：節點填色 = 熟練度（K2 state）、分章 compound cluster、
 *           prerequisite 邊箭頭強化；章節 cluster 用灰階容器（R8.4 顏色僅功能性）。
 * K5c 疊加：underlay ring = 路徑狀態（目前 / 已完成 / 補救）。
 * 所有色票必須來自 GitHub Dark token（frontend.md），不可引入外來 hex。
 *
 * GraphData → elements 轉換 → `knowledge-graph-elements.ts`
 */

import type { StylesheetCSS } from "cytoscape";

import type { MasteryBand } from "./knowledge-graph-types";

// === Design tokens（與 frontend.md 對齊） ===

export const TOKEN = {
  bgCanvas: "#0D1117",
  bgDefault: "#161B22",
  borderDefault: "#30363D",
  borderMuted: "#21262D",
  borderEmphasis: "#6E7681",
  textPrimary: "#E6EDF3",
  textSecondary: "#8B949E",
  textMuted: "#6E7681",
  green: "#3FB950",
  orange: "#D29922",
  red: "#F85149",
  blue: "#58A6FF",
} as const;

// K5b：mastery band → 節點填色（語意：知識狀態，非裝飾）— 圖例與 Detail Panel 共用
export const MASTERY_COLOR: Record<MasteryBand, string> = {
  mastered: TOKEN.green,
  learning: TOKEN.orange,
  struggling: TOKEN.red,
  unseen: TOKEN.borderDefault, // 灰 = 尚未互動
};

// category → 分類色（Detail Panel badge 沿用；K5b 起節點填色改用 MASTERY_COLOR）
export const CATEGORY_COLOR: Record<string, string> = {
  "基礎語法": "#58A6FF", // blue
  "記憶體": "#F85149",   // red
  "物件導向": "#3FB950", // green
  STL: "#BC8CFF",        // purple
  "演算法": "#D29922",   // orange
  "進階": "#8B949E",     // text-secondary
};

export const DEFAULT_CATEGORY_COLOR = TOKEN.borderEmphasis;

// === Stylesheet (Obsidian-style + K5b/c) ===

export const STYLESHEET: StylesheetCSS[] = [
  // --- Concept 節點（有 tag data；章節 parent 不會命中）---
  {
    selector: "node[tag]",
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
    selector: "node[tag]:selected",
    css: {
      "border-color": TOKEN.borderEmphasis,
      "border-width": 2,
    },
  },
  // --- 章節容器（compound parent，detail 層）---
  // 背景與畫布一致（無填色無邊框），以低透明度星雲 SVG 區隔章節；
  // 拖曳 parent 可整體移動該章（cytoscape compound 原生行為）。
  {
    selector: "node:parent",
    css: {
      shape: "ellipse",
      "background-opacity": 0,
      "border-width": 0,
      "background-image": "data(galaxy)",
      "background-fit": "cover",
      "background-clip": "node",
      "background-image-opacity": 0.8,
      label: "data(label)",
      color: TOKEN.textMuted,
      "font-size": "13px",
      "font-family": "Inter, 'Noto Sans TC', sans-serif",
      "text-valign": "top",
      "text-halign": "center",
      "text-margin-y": -8,
      padding: "48px",
      "transition-property": "opacity",
      "transition-duration": 220,
    },
  },
  // --- Hover 鄰居高亮（label 變亮 + 邊框轉強）---
  {
    selector: "node[tag].highlighted",
    css: {
      "border-color": TOKEN.borderEmphasis,
      "border-width": 2,
      color: TOKEN.textPrimary,
    },
  },
  // --- 淡化非鄰居（hover 時其他元素降透明度；章節容器不淡化避免視覺跳動）---
  {
    selector: "node[tag].faded, edge.faded",
    css: { opacity: 0.18 },
  },

  // --- K5c 路徑狀態 ring（underlay）— 語意：目前單元 / 已完成 / 補救路徑 ---
  {
    selector: 'node[path_status = "completed"]',
    css: {
      "underlay-color": TOKEN.green,
      "underlay-padding": 4,
      "underlay-opacity": 0.4,
      "underlay-shape": "ellipse",
    },
  },
  {
    selector: 'node[path_status = "current"]',
    css: {
      "underlay-color": TOKEN.blue,
      "underlay-padding": 5,
      "underlay-opacity": 0.9,
      "underlay-shape": "ellipse",
    },
  },
  // 補救嫌疑節點（診斷跳轉）：紅 ring，優先級最高（宣告在後者勝出）
  {
    selector: "node[?remedial]",
    css: {
      "underlay-color": TOKEN.red,
      "underlay-padding": 6,
      "underlay-opacity": 0.9,
      "underlay-shape": "ellipse",
      "border-color": TOKEN.borderEmphasis,
    },
  },

  // --- Edge base（K5b：箭頭放大 + 提高不透明度讓依賴方向可讀）---
  {
    selector: "edge",
    css: {
      "line-color": TOKEN.borderDefault,
      width: 1.2,
      opacity: 0.7,
      "curve-style": "bezier",
      "control-point-step-size": 30,
      "target-arrow-color": TOKEN.borderDefault,
      "arrow-scale": 1,
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
  // 跨章依賴邊：預設淡出降噪（聚焦單一星球時視野乾淨），hover 高亮時恢復
  {
    selector: "edge[?cross]",
    css: { opacity: 0.18 },
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
      width: 1.8,
      opacity: 0.95,
    },
  },
];
