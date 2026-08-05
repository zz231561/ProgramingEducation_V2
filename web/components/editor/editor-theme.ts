/**
 * CodeMirror 主題 — 覆蓋 One Dark 以匹配 frontend.md Design Tokens。
 * 自 code-editor.tsx 抽出（7-U5 補全彈窗樣式讓該檔超過 150 行提醒線）。
 */

import { EditorView } from "@codemirror/view";

export const editorTheme = EditorView.theme({
  "&": {
    height: "100%",
    fontSize: "14px",
    fontFamily: "'JetBrains Mono', monospace",
  },
  ".cm-content": {
    padding: "8px 0",
    caretColor: "#58A6FF",
  },
  ".cm-gutters": {
    backgroundColor: "#0D1117",
    borderRight: "1px solid #21262D",
    color: "#6E7681",
  },
  ".cm-activeLineGutter": {
    backgroundColor: "#1C2128",
    color: "#E6EDF3",
  },
  ".cm-activeLine": {
    backgroundColor: "#1C212844",
  },
  "&.cm-focused .cm-cursor": {
    borderLeftColor: "#58A6FF",
  },
  "&.cm-focused .cm-selectionBackground, ::selection": {
    backgroundColor: "#264F78",
  },
  ".cm-scroller": {
    overflow: "auto",
  },
  // 補全彈窗（7-U5）— 對齊 frontend.md 的 Card / Input 規格
  ".cm-tooltip.cm-tooltip-autocomplete": {
    border: "1px solid #30363D",
    borderRadius: "6px",
    backgroundColor: "#161B22",
    boxShadow: "0 16px 48px rgba(0,0,0,0.5)",
    overflow: "hidden",
  },
  ".cm-tooltip-autocomplete > ul": {
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: "13px",
    maxHeight: "16em",
  },
  ".cm-tooltip-autocomplete > ul > li": {
    padding: "3px 8px",
    color: "#E6EDF3",
  },
  ".cm-tooltip-autocomplete > ul > li[aria-selected]": {
    backgroundColor: "#1C2128",
    color: "#E6EDF3",
  },
  ".cm-completionDetail": {
    marginLeft: "8px",
    color: "#8B949E",
    fontStyle: "normal",
  },
  ".cm-completionInfo": {
    border: "1px solid #30363D",
    borderRadius: "6px",
    backgroundColor: "#161B22",
    color: "#8B949E",
    padding: "6px 8px",
    fontFamily: "'Inter', 'Noto Sans TC', sans-serif",
    fontSize: "12px",
    maxWidth: "260px",
  },
  ".cm-completionMatchedText": {
    color: "#58A6FF",
    textDecoration: "none",
  },
});
