"use client";

/**
 * Knowledge Graph — Cytoscape.js 視覺化全部 Concept 節點與 Edge。
 *
 * Presentational 元件 — 由 KnowledgePage 傳入 graphData + masteryMap + pathOverlay，
 * 自己只負責 Cytoscape 生命週期與互動。
 * 雙層視圖：zoom < 門檻顯示章節級星系（overview-style.ts），否則顯示概念級
 * detail；切換由 graph-mode.ts 依 viewport zoom 驅動，crossfade 平滑過場。
 * 點擊星系 / 章節容器 / 概念節點一律鏡頭 zoom in 至該章（概念另開詳情面板）。
 * K5c：focusTags（補救跳轉）優先於 currentTag 進度聚焦。
 */

import cytoscape, { type Core, type EventObject } from "cytoscape";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { GalaxyNav } from "./galaxy-nav";
import { fitWithCap } from "./graph-camera";
import { computeChapterAnchors, computePositions } from "./graph-layout";
import { applyMode, modeForZoom, type ViewMode } from "./graph-mode";
import { CHAPTER_ID_PREFIX, toElements } from "./knowledge-graph-elements";
import { STYLESHEET, TOKEN } from "./knowledge-graph-style";
import type {
  GraphData,
  MasteryEntry,
  PathOverlay,
} from "./knowledge-graph-types";
import { buildOrbitPath, buildStars } from "./orbit-scene";
import { OVERVIEW_STYLES } from "./overview-style";

export type KnowledgeGraphProps = {
  data: GraphData;
  masteryMap: Map<string, MasteryEntry>;
  /** K5c 路徑高亮 overlay（省略 = 無 ring）。 */
  pathOverlay?: PathOverlay;
  /** 目前進度 concept（進場鏡頭 zoom 至其所屬章節）。 */
  currentTag?: string | null;
  /** K5c：補救跳轉聚焦 tags；優先於 currentTag。 */
  focusTags?: string[];
  /** 點擊節點時觸發；接收 concept tag 供上層查詳情。*/
  onNodeClick?: (tag: string) => void;
};

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

  // 進場聚焦章節：補救 tags > 目前進度 > 第一章
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

  // 點擊星系 / 章節容器 / 概念節點 → zoom in 至該章
  const zoomToCategory = useCallback(
    (cy: Core, category: string) => {
      const idx = anchors.findIndex((a) => a.category === category);
      if (idx < 0) return;
      setChapterIdx(idx);
      fitChapter(cy, idx, true);
    },
    [anchors, fitChapter],
  );

  // 全覽：zoom out 至章節級視圖（overview 層自動接手，章名維持可讀）
  const handleOverview = useCallback(() => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.animate({
      fit: { eles: cy.elements("node[?overview]"), padding: 48 },
      duration: 500,
      easing: "ease-in-out",
    });
  }, []);

  // Cytoscape lifecycle
  useEffect(() => {
    if (!containerRef.current) return;

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: [...STYLESHEET, ...OVERVIEW_STYLES],
      layout: {
        // 確定性佈局：概念座標由 graph-layout.ts 算好；星系節點自帶 position
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

    // 統一點擊：星系 / parent / 概念節點都帶 category → zoom in 該章
    cy.on("tap", "node[category]", (evt: EventObject) => {
      const target = evt.target;
      const tag = target.data("tag") as string | undefined;
      if (tag) onNodeClick?.(tag);
      zoomToCategory(cy, target.data("category") as string);
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

    // viewport 同步：underlay transform + 雙層模式切換（crossfade 過場）
    let mode: ViewMode | null = null;
    const syncViewport = () => {
      underlayRef.current?.setAttribute(
        "transform",
        `translate(${cy.pan().x} ${cy.pan().y}) scale(${cy.zoom()})`,
      );
      const next = modeForZoom(cy.zoom());
      if (next !== mode) {
        mode = next;
        applyMode(cy, next);
      }
    };
    cy.on("viewport", syncViewport);

    // 進場鏡頭：補救 tags 直接框住嫌疑鏈，否則 zoom 至進度所在章節
    if (focusTags && focusTags.length > 0) {
      const targets = cy.nodes().filter((n) => focusTags.includes(n.data("tag")));
      if (targets.length > 0) fitWithCap(cy, targets, false);
    } else {
      fitChapter(cy, initialChapterIdx, false);
    }
    syncViewport();

    cyRef.current = cy;
    return () => {
      cy.destroy();
      cyRef.current = null;
    };
  }, [
    elements,
    positions,
    onNodeClick,
    focusTags,
    initialChapterIdx,
    fitChapter,
    zoomToCategory,
  ]);

  const navLabel = `${anchors[chapterIdx]?.category ?? ""}（${chapterIdx + 1}/${anchors.length}）`;

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
        onOverview={handleOverview}
      />
    </div>
  );
}
