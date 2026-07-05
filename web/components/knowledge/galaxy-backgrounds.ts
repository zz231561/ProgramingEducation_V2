/**
 * K5 章節星系背景 — 程序生成低透明度星雲/星系 SVG（data URI）。
 *
 * 每章以 chapterIndex 為 seed（mulberry32）：樣式獨特但每次渲染完全一致。
 * 色相僅取 GitHub Dark token（藍/紫/灰），內部 opacity 0.1-0.2 + cytoscape
 * background-image-opacity 再壓一層，維持「低透明度美化」不搶節點主體。
 */

const GALAXY_HUES = ["#58A6FF", "#BC8CFF", "#8B949E"] as const;
const CANVAS = 480;

/** 決定性 PRNG — 同 seed 永遠產生同序列。 */
function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

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
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${CANVAS} ${CANVAS}">` +
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
