/**
 * Overview 層樣式（zoom out 的章節級「最適排版」）+ 雙層 crossfade 類別。
 *
 * 星系節點：星雲背景 + 大字章名（font 52px × overview zoom ≈ 0.3 → 螢幕上
 * 約 15px 可讀）；章間聚合依賴邊粗線大箭頭。`.mode-hidden` 以 opacity
 * transition 隱藏另一層，鏡頭縮放動畫穿越門檻時形成平滑 crossfade。
 */

import type { StylesheetCSS } from "cytoscape";

import { TOKEN } from "./knowledge-graph-style";

export const OVERVIEW_STYLES: StylesheetCSS[] = [
  {
    selector: "node[?overview]",
    css: {
      shape: "ellipse",
      width: "data(size)",
      height: "data(size)",
      "background-opacity": 0,
      "border-width": 0,
      "background-image": "data(galaxy)",
      "background-fit": "cover",
      "background-clip": "node",
      "background-image-opacity": 0.95,
      label: "data(label)",
      color: TOKEN.textPrimary,
      "font-size": "52px",
      "font-family": "Inter, 'Noto Sans TC', sans-serif",
      "text-valign": "center",
      "text-halign": "center",
      "text-wrap": "wrap",
      "text-max-width": "460px",
      "line-height": 1.35,
      "transition-property": "opacity",
      "transition-duration": 220,
    },
  },
  {
    selector: "edge[?overview]",
    css: {
      "line-color": TOKEN.borderEmphasis,
      width: 5,
      opacity: 0.45,
      "curve-style": "bezier",
      "control-point-step-size": 80,
      "target-arrow-shape": "triangle",
      "target-arrow-color": TOKEN.borderEmphasis,
      "arrow-scale": 2.2,
      "transition-property": "opacity",
      "transition-duration": 220,
    },
  },
  // 雙層切換：隱藏層透明化 + 停用互動（宣告在最後，優先級最高）
  {
    selector: ".mode-hidden",
    css: {
      opacity: 0,
      events: "no",
    },
  },
];
