/**
 * 太陽系主題對應（2026-07-05 與使用者討論定案；同日四驗改程序生成 SVG）。
 *
 * 十個章節依課程順序 = 離太陽距離；星球僅是介面主題非主角——
 * 章節標籤只顯示原分類名，天體名不出現在 UI 文字。
 * 色相全部取 GitHub Dark token（R8 白名單登記之裝飾例外）。
 */

import { planetDataUri, type PlanetSpec } from "./planet-svg";

// token: blue #58A6FF / purple #BC8CFF / green #3FB950 / orange #D29922
//        red #F85149 / gray #8B949E
const SPECS: PlanetSpec[] = [
  { hue: "#D29922", glow: true },                            // 太陽
  { hue: "#8B949E", craters: 5 },                            // 水星
  { hue: "#D29922", accent: "#8B949E", bands: 2 },           // 金星
  { hue: "#58A6FF", accent: "#3FB950", patches: 4 },         // 地球
  { hue: "#F85149", craters: 3 },                            // 火星
  { hue: "#D29922", accent: "#F85149", bands: 4 },           // 木星
  { hue: "#D29922", accent: "#8B949E", bands: 2, ring: true }, // 土星
  { hue: "#58A6FF", bands: 1 },                              // 天王星
  { hue: "#58A6FF", accent: "#BC8CFF", bands: 2 },           // 海王星
  { hue: "#BC8CFF", accent: "#8B949E", craters: 4 },         // 冥王星
];

/** 取章節對應星球背景 data URI（超出 10 章時輪替）。 */
export function planetBackgroundFor(chapterIndex: number): string {
  return planetDataUri(SPECS[chapterIndex % SPECS.length], chapterIndex);
}
