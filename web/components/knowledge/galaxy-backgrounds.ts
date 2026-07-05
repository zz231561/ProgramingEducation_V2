/**
 * K5 章節星系背景 — 程序生成低透明度星雲/星系 SVG（data URI）。
 *
 * 2026-07-05 五驗定案：太陽系行星太搶視覺，恢復此星雲設計為正式方案。
 * 每章以 chapterIndex 為 seed（mulberry32）：樣式獨特但每次渲染完全一致。
 * 色相僅取 GitHub Dark token（藍/紫/灰）。
 * ⚠ SVG 必須帶 width/height 屬性——canvas rasterize 對 viewBox-only SVG
 * 會退回 300×150 預設尺寸導致幾乎不可見（headless 實驗證實的前車之鑑）。
 */

import { mulberry32 } from "./prng";

const GALAXY_HUES = ["#58A6FF", "#BC8CFF", "#8B949E"] as const;
const CANVAS = 480;

function nebulaEllipses(rand: () => number, hue: string): string {
  const cx = CANVAS / 2;
  const count = 3 + Math.floor(rand() * 2);
  let out = "";
  for (let i = 0; i < count; i++) {
    const ox = (cx + (rand() - 0.5) * 130).toFixed(1);
    const oy = (cx + (rand() - 0.5) * 130).toFixed(1);
    const rx = (90 + rand() * 100).toFixed(1);
    const ry = (36 + rand() * 55).toFixed(1);
    const rot = (rand() * 180).toFixed(1);
    const op = (0.18 + rand() * 0.14).toFixed(2);
    out += `<ellipse cx="${ox}" cy="${oy}" rx="${rx}" ry="${ry}" fill="${hue}" opacity="${op}" transform="rotate(${rot} ${ox} ${oy})" filter="url(#b)"/>`;
  }
  return out;
}

function starDots(rand: () => number): string {
  let out = "";
  for (let i = 0; i < 46; i++) {
    const x = (rand() * CANVAS).toFixed(1);
    const y = (rand() * CANVAS).toFixed(1);
    const r = (0.5 + rand() * 1.1).toFixed(2);
    const op = (0.25 + rand() * 0.55).toFixed(2);
    out += `<circle cx="${x}" cy="${y}" r="${r}" fill="#E6EDF3" opacity="${op}"/>`;
  }
  return out;
}

/** 產生指定章節的星系背景 data URI（同 index 永遠同圖）。 */
export function galaxyDataUri(chapterIndex: number): string {
  const rand = mulberry32(chapterIndex + 1);
  const hue = GALAXY_HUES[chapterIndex % GALAXY_HUES.length];
  const c = CANVAS / 2;

  const svg =
    `<svg xmlns="http://www.w3.org/2000/svg" width="${CANVAS}" height="${CANVAS}" viewBox="0 0 ${CANVAS} ${CANVAS}">` +
    `<defs>` +
    `<filter id="b" x="-50%" y="-50%" width="200%" height="200%">` +
    `<feGaussianBlur stdDeviation="20"/></filter>` +
    `<radialGradient id="g"><stop offset="0" stop-color="${hue}" stop-opacity="0.5"/>` +
    `<stop offset="0.55" stop-color="${hue}" stop-opacity="0.2"/>` +
    `<stop offset="1" stop-color="${hue}" stop-opacity="0"/></radialGradient>` +
    `</defs>` +
    `<circle cx="${c}" cy="${c}" r="${c * 0.8}" fill="url(#g)"/>` +
    nebulaEllipses(rand, hue) +
    starDots(rand) +
    `</svg>`;

  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}
