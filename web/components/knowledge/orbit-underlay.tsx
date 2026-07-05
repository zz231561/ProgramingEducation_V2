"use client";

/**
 * 星空 + 軌道弧線 underlay — 掛在 cytoscape canvas 底下，
 * <g> 由父層依 viewport（pan/zoom）同步 transform。
 *
 * detail / overview 佈局不同，各有一條軌道弧線，依模式 crossfade
 * （時長對齊 graph-mode.ts 的節點移位動畫）。
 */

import type { RefObject } from "react";

import { MODE_TRANSITION_MS, type ViewMode } from "./graph-mode";
import { TOKEN } from "./knowledge-graph-style";
import type { Star } from "./orbit-scene";

type Props = {
  /** 父層持有的 <g> ref，viewport 事件時直接改 transform。 */
  groupRef: RefObject<SVGGElement | null>;
  detailPath: string;
  overviewPath: string;
  stars: Star[];
  mode: ViewMode;
};

export function OrbitUnderlay({
  groupRef,
  detailPath,
  overviewPath,
  stars,
  mode,
}: Props) {
  const paths = [
    { d: detailPath, visible: mode === "detail" },
    { d: overviewPath, visible: mode === "overview" },
  ];
  return (
    <svg
      className="pointer-events-none absolute inset-0 h-full w-full"
      aria-hidden
    >
      <g ref={groupRef}>
        {paths.map((p, i) => (
          <path
            key={i}
            d={p.d}
            fill="none"
            stroke={TOKEN.borderDefault}
            strokeWidth={2}
            strokeDasharray="2 10"
            style={{
              opacity: p.visible ? 0.6 : 0,
              transition: `opacity ${MODE_TRANSITION_MS}ms ease-in-out`,
            }}
          />
        ))}
        {stars.map((s, i) => (
          <circle
            key={i}
            cx={s.x}
            cy={s.y}
            r={s.r}
            fill={TOKEN.textPrimary}
            opacity={s.opacity}
          />
        ))}
      </g>
    </svg>
  );
}
