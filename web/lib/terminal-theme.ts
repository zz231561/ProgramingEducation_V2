/**
 * xterm 主題 — GitHub Dark。
 *
 * 前 6 項（bg/fg/cursor/selection）直接對應既有 design token；
 * ANSI 16 色採 GitHub 官方 dark 色盤，屬 frontend.md R8 白名單核准例外
 * **僅限終端機畫布內**，供學生程式自行輸出的色碼渲染。
 */

/** @returns xterm ITheme 相容物件 */
export const TERMINAL_THEME = {
  background: "#010409", // --bg-inset（同 Code Block 規格）
  foreground: "#E6EDF3", // --text-primary
  cursor: "#58A6FF", // --text-link
  cursorAccent: "#010409",
  selectionBackground: "#264F78",

  // ANSI 標準 8 色
  black: "#484F58",
  red: "#FF7B72",
  green: "#3FB950",
  yellow: "#D29922",
  blue: "#58A6FF",
  magenta: "#BC8CFF",
  cyan: "#39C5CF",
  white: "#B1BBC4",

  // ANSI bright 8 色
  brightBlack: "#6E7681",
  brightRed: "#FFA198",
  brightGreen: "#56D364",
  brightYellow: "#E3B341",
  brightBlue: "#79C0FF",
  brightMagenta: "#D2A8FF",
  brightCyan: "#56D4DD",
  brightWhite: "#E6EDF3",
} as const;

export const TERMINAL_FONT =
  '"JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace';
export const TERMINAL_FONT_SIZE = 14;
