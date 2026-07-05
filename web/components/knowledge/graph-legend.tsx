/**
 * Knowledge Graph 圖例（K5b/c）。
 *
 * 填色 = 熟練度（K2 state）、外圈 ring = 路徑狀態。
 * 純灰階文字 + 功能性色點（R8.4：顏色僅語意用途）。
 */

import { MASTERY_COLOR, TOKEN } from "./knowledge-graph-style";

const MASTERY_ITEMS = [
  { color: MASTERY_COLOR.mastered, label: "已掌握" },
  { color: MASTERY_COLOR.learning, label: "學習中" },
  { color: MASTERY_COLOR.struggling, label: "需加強" },
  { color: MASTERY_COLOR.unseen, label: "尚未互動" },
] as const;

const RING_ITEMS = [
  { color: TOKEN.blue, label: "目前單元" },
  { color: TOKEN.green, label: "已完成" },
  { color: TOKEN.red, label: "補救路徑" },
] as const;

export function GraphLegend({ showRemedial }: { showRemedial: boolean }) {
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-text-secondary">
      <span className="text-text-muted">填色＝熟練度</span>
      {MASTERY_ITEMS.map((item) => (
        <LegendDot key={item.label} color={item.color} label={item.label} />
      ))}
      <span className="ml-2 text-text-muted">外圈＝路徑</span>
      {RING_ITEMS.filter((i) => showRemedial || i.label !== "補救路徑").map(
        (item) => (
          <LegendRing key={item.label} color={item.color} label={item.label} />
        ),
      )}
    </div>
  );
}

function LegendDot({ color, label }: { color: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span
        className="inline-block size-2.5 rounded-full"
        style={{ backgroundColor: color }}
      />
      {label}
    </span>
  );
}

function LegendRing({ color, label }: { color: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span
        className="inline-block size-3 rounded-full border-2"
        style={{ borderColor: color }}
      />
      {label}
    </span>
  );
}
