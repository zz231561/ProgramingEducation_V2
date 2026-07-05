"use client";

/**
 * Knowledge Graph — Cytoscape.js 視覺化全部 Concept 節點與 Edge。
 *
 * Presentational 元件 — 由 KnowledgePage 傳入 graphData + masteryMap + pathOverlay，
 * 自己只負責 Cytoscape 生命週期與互動。
 * 視覺規格 / 色票 → `knowledge-graph-style.ts`；elements 轉換 → `knowledge-graph-elements.ts`
 * 太陽系主題：preset 蛇形軌道佈局（graph-layout.ts）+ NASA 行星容器（planet-theme.ts）
 *            + 軌道弧線/星空 underlay（orbit-scene.ts，隨 viewport 同步 transform）
 * 鏡頭：進場 zoom 至目前進度星球（上限 ZOOM_CAP 避免過大）；GalaxyNav 左右切換
 * K5c：focusTags（補救跳轉）優先於 currentTag 進度聚焦
 */

import cytoscape, {
  type Core,
  type EventObject,
  type NodeCollection,
} from "cytoscape";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { GalaxyNav } from "./galaxy-nav";
import { computeChapterAnchors, computePositions } from "./graph-layout";
import { CHAPTER_ID_PREFIX, toElements } from "./knowledge-graph-elements";
import { STYLESHEET, TOKEN } from "./knowledge-graph-style";
import type {
  GraphData,
  MasteryEntry,
  PathOverlay,
} from "./knowledge-graph-types";
import { buildOrbitPath, buildStars } from "./orbit-scene";
import { planetFor } from "./planet-theme";

const FIT_PADDING = 72;
const NAV_ANIMATION_MS = 350;
// 鏡頭放大上限：小章節 fit 後不再貼臉（使用者回饋「放太大」）
const ZOOM_CAP = 1.0;

export type KnowledgeGraphProps = {
  data: GraphData;
  masteryMap: Map<string, MasteryEntry>;
  /** K5c 路徑高亮 overlay（省略 = 無 ring）。 */
  pathOverlay?: PathOverlay;
  /** 目前進度 concept（進場鏡頭 zoom 至其所屬星球）。 */
  currentTag?: string | null;
  /** K5c：補救跳轉聚焦 tags；優先於 currentTag。 */
  focusTags?: string[];
  /** 點擊節點時觸發；接收 concept tag 供上層查詳情。*/
  onNodeClick?: (tag: string) => void;
};

/** fit 目標並套用 ZOOM_CAP（cap 時改用置中）。 */
function fitWithCap(cy: Core, eles: NodeCollection, animate: boolean): void {
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

export function KnowledgeGraph({
  data,
  masteryMap,
  pathOverlay,
  currentTag,
  focusTags,
  onNodeClick,
}: KnowledgeGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const underlayRef = useRef<SVGGElement>(null);
  const cyRef = useRef<Core | null>(null);

  const elements = useMemo(
    () => toElements(data, masteryMap, pathOverlay),
    [data, masteryMap, pathOverlay],
  );
  const positions = useMemo(() => computePositions(data), [data]);
  const anchors = useMemo(() => computeChapterAnchors(data), [data]);
  const orbitPath = useMemo(() => buildOrbitPath(anchors), [anchors]);
  const stars = useMemo(() => buildStars(anchors), [anchors]);

  // 進場聚焦章節：補救 tags > 目前進度 > 第一章（太陽）
  const initialChapterIdx = useMemo(() => {
    const anchorTag = focusTags?.[0] ?? currentTag;
    if (!anchorTag) return 0;
    const category = data.nodes.find((n) => n.tag === anchorTag)?.category;
    const idx = category
      ? anchors.findIndex((a) => a.category === category)
      : -1;
    return idx >= 0 ? idx : 0;
  }, [data, anchors, currentTag, focusTags]);

  // derived-state 調整：initialChapterIdx 變動（如 path 載入完成）時重設游標
  const [chapterIdx, setChapterIdx] = useState(initialChapterIdx);
  const [prevInitialIdx, setPrevInitialIdx] = useState(initialChapterIdx);
  if (prevInitialIdx !== initialChapterIdx) {
    setPrevInitialIdx(initialChapterIdx);
    setChapterIdx(initialChapterIdx);
  }

  const fitChapter = useCallback(
    (cy: Core, idx: number, animate: boolean) => {
      const parent = cy.getElementById(
        `${CHAPTER_ID_PREFIX}${anchors[idx]?.category ?? ""}`,
      );
      fitWithCap(cy, parent, animate);
    },
    [anchors],
  );

  const handleNav = useCallback(
    (dir: -1 | 1) => {
      const next = Math.min(anchors.length - 1, Math.max(0, chapterIdx + dir));
      setChapterIdx(next);
      if (cyRef.current) fitChapter(cyRef.current, next, true);
    },
    [chapterIdx, anchors.length, fitChapter],
  );

  // Cytoscape lifecycle
  useEffect(() => {
    if (!containerRef.current) return;

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: STYLESHEET,
      layout: {
        // 確定性佈局：座標由 graph-layout.ts 預先算好（parent 由子節點自動推導）
        name: "preset",
        positions: (node: { id: () => string }) =>
          positions.get(node.id()) ?? undefined,
        fit: false,
        animate: false,
      } as unknown as cytoscape.LayoutOptions,
      wheelSensitivity: 0.2,
      minZoom: 0.12,
      maxZoom: 3,
    });

    cy.on("tap", "node[tag]", (evt: EventObject) => {
      const tag = evt.target.data("tag") as string;
      onNodeClick?.(tag);
    });

    // Obsidian 風 hover 高亮：點亮鄰居 + 淡化其他（章節容器不參與）
    cy.on("mouseover", "node[tag]", (evt: EventObject) => {
      const node = evt.target;
      const neighborhood = node.closedNeighborhood();
      cy.elements().difference(neighborhood).addClass("faded");
      neighborhood.addClass("highlighted");
    });
    cy.on("mouseout", "node[tag]", () => {
      cy.elements().removeClass("faded highlighted");
    });

    // 軌道/星空 underlay 與 viewport 同步（直接寫 DOM transform，避免 re-render）
    const syncUnderlay = () => {
      underlayRef.current?.setAttribute(
        "transform",
        `translate(${cy.pan().x} ${cy.pan().y}) scale(${cy.zoom()})`,
      );
    };
    cy.on("viewport", syncUnderlay);

    // 進場鏡頭：補救 tags 直接框住嫌疑鏈，否則 zoom 至進度所在星球
    if (focusTags && focusTags.length > 0) {
      const targets = cy.nodes().filter((n) => focusTags.includes(n.data("tag")));
      if (targets.length > 0) fitWithCap(cy, targets, false);
    } else {
      fitChapter(cy, initialChapterIdx, false);
    }
    syncUnderlay();

    cyRef.current = cy;
    return () => {
      cy.destroy();
      cyRef.current = null;
    };
  }, [elements, positions, onNodeClick, focusTags, initialChapterIdx, fitChapter]);

  const navLabel = `${planetFor(chapterIdx).body} · ${
    anchors[chapterIdx]?.category ?? ""
  }（${chapterIdx + 1}/${anchors.length}）`;

  return (
    <div
      className="relative h-full w-full overflow-hidden"
      style={{ backgroundColor: TOKEN.bgCanvas }}
    >
      <svg
        className="pointer-events-none absolute inset-0 h-full w-full"
        aria-hidden
      >
        <g ref={underlayRef}>
          <path
            d={orbitPath}
            fill="none"
            stroke={TOKEN.borderDefault}
            strokeWidth={2}
            strokeDasharray="2 10"
            opacity={0.6}
          />
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
      <div ref={containerRef} className="relative h-full w-full" />
      <GalaxyNav
        label={navLabel}
        canPrev={chapterIdx > 0}
        canNext={chapterIdx < anchors.length - 1}
        onPrev={() => handleNav(-1)}
        onNext={() => handleNav(1)}
      />
    </div>
  );
}
