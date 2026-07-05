/**
 * 太陽系主題對應（2026-07-05 與使用者討論定案）。
 *
 * 十個章節依課程順序 = 離太陽距離：學習之旅從太陽出發航向外太陽系，
 * 越遠越進階。影像為 NASA public domain（見 public/planets/CREDITS.md），
 * 行星視覺大小由章節概念數決定（cluster 越大 parent 越大，影像 cover 跟隨）。
 */

export type PlanetBody = {
  /** 天體中文名（章節標籤與導覽指示用）。 */
  body: string;
  /** public/ 下的影像路徑。 */
  file: string;
};

const PLANETS: PlanetBody[] = [
  { body: "太陽", file: "/planets/sun.jpg" },
  { body: "水星", file: "/planets/mercury.jpg" },
  { body: "金星", file: "/planets/venus.jpg" },
  { body: "地球", file: "/planets/earth.jpg" },
  { body: "火星", file: "/planets/mars.jpg" },
  { body: "木星", file: "/planets/jupiter.jpg" },
  { body: "土星", file: "/planets/saturn.jpg" },
  { body: "天王星", file: "/planets/uranus.jpg" },
  { body: "海王星", file: "/planets/neptune.jpg" },
  { body: "冥王星", file: "/planets/pluto.jpg" },
];

/** 取章節對應天體（超出 10 章時輪替，避免 undefined）。 */
export function planetFor(chapterIndex: number): PlanetBody {
  return PLANETS[chapterIndex % PLANETS.length];
}
