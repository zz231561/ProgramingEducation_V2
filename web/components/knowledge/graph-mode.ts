/**
 * 語意縮放模式切換（overview 全覽 / detail 概念級）。
 *
 * 兩種模式顯示同一批概念節點：overview 把節點與字體放大（`.ov` 樣式）
 * 並重排為緊湊網格（overview-layout.ts），讓 zoom out 後名稱仍可讀；
 * detail 回到蛇形星系佈局。切換由 viewport zoom 門檻驅動，
 * 節點位置以動畫過渡、尺寸靠 style transition 平滑變化。
 */

import type { Core } from "cytoscape";

import type { NodePosition } from "./graph-layout";

export type ViewMode = "overview" | "detail";

export type ModeLayouts = {
  detail: Map<string, NodePosition>;
  overview: Map<string, NodePosition>;
};

/** 低於此 zoom 切換 overview（全覽 fit ≈ 0.3、單章 fit ≥ 0.6）。 */
export const OVERVIEW_ZOOM_THRESHOLD = 0.45;
/** 佈局切換的位置動畫時長（underlay 軌道 crossfade 同步此值）。 */
export const MODE_TRANSITION_MS = 320;

export function modeForZoom(zoom: number): ViewMode {
  return zoom < OVERVIEW_ZOOM_THRESHOLD ? "overview" : "detail";
}

/** 套用模式：toggle `.ov` 樣式 + 概念節點移至對應佈局座標。 */
export function applyMode(
  cy: Core,
  mode: ViewMode,
  layouts: ModeLayouts,
  animate: boolean,
): void {
  const isOverview = mode === "overview";
  const target = isOverview ? layouts.overview : layouts.detail;
  cy.elements().toggleClass("ov", isOverview);
  cy.nodes("[tag]").forEach((node) => {
    const pos = target.get(node.id());
    if (!pos) return;
    node.stop();
    if (animate) {
      node.animate({
        position: { ...pos },
        duration: MODE_TRANSITION_MS,
        easing: "ease-in-out",
      });
    } else {
      node.position({ ...pos });
    }
  });
}
