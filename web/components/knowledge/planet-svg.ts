/**
 * 程序生成行星 SVG（data URI）— 取代 NASA 影像（2026-07-05 使用者四驗定案：
 * 真實照片無法融入背景且搶走視覺焦點）。
 *
 * 低飽和 token 色相 + 柔和明暗漸層球體，特徵（光暈/環/條紋/隕石坑/陸塊）
 * 依 spec 組合；seed 固定 → 每次渲染完全一致。
 * ⚠ SVG 必須帶 width/height 屬性——canvas rasterize 對 viewBox-only SVG
 * 會退回 300×150 預設尺寸（headless 實驗證實的前車之鑑）。
 */

import { mulberry32 } from "./prng";

const SIZE = 480;
const C = SIZE / 2;
const R = 150; // 球體半徑

export type PlanetSpec = {
  hue: string;
  accent?: string;
  glow?: boolean; // 太陽光暈
  ring?: boolean; // 土星環
  bands?: number; // 橫向條紋數
  craters?: number; // 隕石坑數
  patches?: number; // 陸塊斑塊數（地球）
};

function bands(count: number, accent: string, rand: () => number): string {
  let out = "";
  for (let i = 0; i < count; i++) {
    const y = C - R * 0.7 + ((R * 1.4) / (count + 1)) * (i + 1);
    const h = 10 + rand() * 16;
    out += `<rect x="${C - R}" y="${(y - h / 2).toFixed(1)}" width="${R * 2}" height="${h.toFixed(1)}" fill="${accent}" opacity="${(0.14 + rand() * 0.1).toFixed(2)}"/>`;
  }
  return out;
}

function spots(
  count: number,
  fill: string,
  maxR: number,
  rand: () => number,
): string {
  let out = "";
  for (let i = 0; i < count; i++) {
    const angle = rand() * Math.PI * 2;
    const dist = rand() * R * 0.62;
    const x = C + dist * Math.cos(angle);
    const y = C + dist * Math.sin(angle);
    out += `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${(6 + rand() * maxR).toFixed(1)}" fill="${fill}" opacity="${(0.16 + rand() * 0.12).toFixed(2)}"/>`;
  }
  return out;
}

/** 依 spec 生成行星 data URI（seed 保證同章永遠同圖）。 */
export function planetDataUri(spec: PlanetSpec, seed: number): string {
  const rand = mulberry32(seed + 7);
  const accent = spec.accent ?? spec.hue;

  const glow = spec.glow
    ? `<circle cx="${C}" cy="${C}" r="${R * 1.5}" fill="url(#glow)"/>`
    : "";
  const ring = spec.ring
    ? `<ellipse cx="${C}" cy="${C}" rx="${R * 1.45}" ry="${R * 0.36}" fill="none" stroke="${accent}" stroke-width="13" opacity="0.3" transform="rotate(-16 ${C} ${C})"/>`
    : "";
  const features =
    (spec.bands ? bands(spec.bands, accent, rand) : "") +
    (spec.craters ? spots(spec.craters, "#010409", 14, rand) : "") +
    (spec.patches ? spots(spec.patches, accent, 22, rand) : "");

  const svg =
    `<svg xmlns="http://www.w3.org/2000/svg" width="${SIZE}" height="${SIZE}" viewBox="0 0 ${SIZE} ${SIZE}">` +
    `<defs>` +
    `<radialGradient id="glow"><stop offset="0.4" stop-color="${spec.hue}" stop-opacity="0.32"/><stop offset="1" stop-color="${spec.hue}" stop-opacity="0"/></radialGradient>` +
    `<radialGradient id="body" cx="0.36" cy="0.34" r="0.9"><stop offset="0" stop-color="${spec.hue}" stop-opacity="0.66"/><stop offset="0.65" stop-color="${spec.hue}" stop-opacity="0.4"/><stop offset="1" stop-color="${spec.hue}" stop-opacity="0.2"/></radialGradient>` +
    `<radialGradient id="shade" cx="0.32" cy="0.3" r="1.05"><stop offset="0.62" stop-color="#010409" stop-opacity="0"/><stop offset="1" stop-color="#010409" stop-opacity="0.55"/></radialGradient>` +
    `<clipPath id="clip"><circle cx="${C}" cy="${C}" r="${R}"/></clipPath>` +
    `</defs>` +
    glow +
    `<circle cx="${C}" cy="${C}" r="${R}" fill="url(#body)"/>` +
    `<g clip-path="url(#clip)">${features}</g>` +
    `<circle cx="${C}" cy="${C}" r="${R}" fill="url(#shade)"/>` +
    ring +
    `</svg>`;

  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}
