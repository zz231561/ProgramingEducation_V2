/**
 * 雙層視圖模式切換（overview 章節級 / detail 概念級）。
 *
 * 由 zoom 門檻驅動：鏡頭動畫每 frame 觸發 viewport 事件，穿越門檻的
 * 瞬間切換 `.mode-hidden` 類別，搭配 220ms opacity transition 形成
 * 「縮放中自然 crossfade」的平滑過場。
 */

import type { Core } from "cytoscape";

export type ViewMode = "overview" | "detail";

/** 低於此 zoom 顯示章節級 overview（全覽 fit ≈ 0.25-0.3、單章 fit ≥ 0.6）。 */
export const OVERVIEW_ZOOM_THRESHOLD = 0.45;

export function modeForZoom(zoom: number): ViewMode {
  return zoom < OVERVIEW_ZOOM_THRESHOLD ? "overview" : "detail";
}

/** 套用視圖模式：只顯示對應層，另一層淡出並停用互動。 */
export function applyMode(cy: Core, mode: ViewMode): void {
  cy.batch(() => {
    const overview = cy.elements("[?overview]");
    const detail = cy.elements().difference(overview);
    if (mode === "overview") {
      overview.removeClass("mode-hidden");
      detail.addClass("mode-hidden");
    } else {
      overview.addClass("mode-hidden");
      detail.removeClass("mode-hidden");
    }
  });
}
