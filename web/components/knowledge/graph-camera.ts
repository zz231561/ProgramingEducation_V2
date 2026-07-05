/** 鏡頭工具 — fit + zoom 上限（自 knowledge-graph.tsx 拆出控制檔案大小）。 */

import type { Core, NodeCollection } from "cytoscape";

export const FIT_PADDING = 72;
export const NAV_ANIMATION_MS = 350;
// 鏡頭放大上限：小章節 fit 後不再貼臉（使用者回饋「放太大」）
export const ZOOM_CAP = 1.0;

/** fit 目標並套用 ZOOM_CAP（cap 生效時改為置中該目標）。 */
export function fitWithCap(
  cy: Core,
  eles: NodeCollection,
  animate: boolean,
): void {
  if (eles.empty()) return;
  const bb = eles.boundingBox();
  const fitZoom = Math.min(
    (cy.width() - FIT_PADDING * 2) / bb.w,
    (cy.height() - FIT_PADDING * 2) / bb.h,
  );
  const zoom = Math.min(ZOOM_CAP, fitZoom);
  if (animate) {
    cy.animate({
      zoom,
      center: { eles },
      duration: NAV_ANIMATION_MS,
      easing: "ease-in-out",
    });
  } else {
    cy.zoom(zoom);
    cy.center(eles);
  }
}
