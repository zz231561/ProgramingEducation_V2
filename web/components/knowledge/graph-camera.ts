/** 鏡頭工具 — fit + zoom 上限（自 knowledge-graph.tsx 拆出控制檔案大小）。 */

import type { Core, NodeCollection } from "cytoscape";

import type { NodePosition } from "./graph-layout";

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

export type WorldBounds = { x1: number; y1: number; x2: number; y2: number };

/** 一組座標點的包圍盒（外擴 margin 容納節點與標籤）。 */
export function boundsOf(points: NodePosition[], margin: number): WorldBounds {
  const xs = points.map((p) => p.x);
  const ys = points.map((p) => p.y);
  return {
    x1: Math.min(...xs) - margin,
    y1: Math.min(...ys) - margin,
    x2: Math.max(...xs) + margin,
    y2: Math.max(...ys) + margin,
  };
}

/**
 * 鏡頭移至指定包圍盒（fit + ZOOM_CAP）。
 * 目標與元素現況解耦：模式切換（節點移位）動畫進行中，仍能瞄準最終佈局。
 */
export function animateToBounds(
  cy: Core,
  b: WorldBounds,
  animate: boolean,
): void {
  const w = b.x2 - b.x1;
  const h = b.y2 - b.y1;
  if (w <= 0 || h <= 0) return;
  const fitZoom = Math.min(
    (cy.width() - FIT_PADDING * 2) / w,
    (cy.height() - FIT_PADDING * 2) / h,
  );
  const zoom = Math.min(ZOOM_CAP, fitZoom);
  const pan = {
    x: cy.width() / 2 - zoom * (b.x1 + w / 2),
    y: cy.height() / 2 - zoom * (b.y1 + h / 2),
  };
  if (animate) {
    cy.animate({ zoom, pan, duration: 500, easing: "ease-in-out" });
  } else {
    cy.zoom(zoom);
    cy.pan(pan);
  }
}
