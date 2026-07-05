/**
 * 軌道弧線 + 星空 underlay 的純資料生成（太陽系主題）。
 *
 * 產出以「圖模型座標」表示的 SVG path 與星點——由 KnowledgeGraph 掛在
 * cytoscape canvas 底下的 <svg><g> 內，隨 viewport（pan/zoom）同步 transform，
 * 星空與軌道因此跟著世界移動，背景色保持單一 #0D1117。
 */

import { mulberry32 } from "./galaxy-backgrounds";
import type { ChapterAnchor } from "./graph-layout";

const STAR_COUNT = 140;
const SCENE_MARGIN = 520; // 星空超出章節範圍的外擴距離

export type Star = { x: number; y: number; r: number; opacity: number };

/**
 * Catmull-Rom 轉 cubic bezier：貫穿全部章節錨點的平滑軌道弧線。
 * 回傳 SVG path d 字串（模型座標）。
 */
export function buildOrbitPath(anchors: ChapterAnchor[]): string {
  if (anchors.length < 2) return "";
  const pts = anchors.map((a) => ({ x: a.x, y: a.y }));
  let d = `M ${pts[0].x.toFixed(1)} ${pts[0].y.toFixed(1)}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(0, i - 1)];
    const p1 = pts[i];
    const p2 = pts[i + 1];
    const p3 = pts[Math.min(pts.length - 1, i + 2)];
    const c1x = p1.x + (p2.x - p0.x) / 6;
    const c1y = p1.y + (p2.y - p0.y) / 6;
    const c2x = p2.x - (p3.x - p1.x) / 6;
    const c2y = p2.y - (p3.y - p1.y) / 6;
    d += ` C ${c1x.toFixed(1)} ${c1y.toFixed(1)}, ${c2x.toFixed(1)} ${c2y.toFixed(1)}, ${p2.x.toFixed(1)} ${p2.y.toFixed(1)}`;
  }
  return d;
}

/** 世界座標星空（seed 固定 → 每次渲染一致）。 */
export function buildStars(anchors: ChapterAnchor[]): Star[] {
  if (anchors.length === 0) return [];
  const xs = anchors.map((a) => a.x);
  const ys = anchors.map((a) => a.y);
  const minX = Math.min(...xs) - SCENE_MARGIN;
  const maxX = Math.max(...xs) + SCENE_MARGIN;
  const minY = Math.min(...ys) - SCENE_MARGIN;
  const maxY = Math.max(...ys) + SCENE_MARGIN;

  const rand = mulberry32(42);
  const stars: Star[] = [];
  for (let i = 0; i < STAR_COUNT; i++) {
    stars.push({
      x: minX + rand() * (maxX - minX),
      y: minY + rand() * (maxY - minY),
      r: 0.6 + rand() * 1.4,
      opacity: 0.15 + rand() * 0.45,
    });
  }
  return stars;
}
