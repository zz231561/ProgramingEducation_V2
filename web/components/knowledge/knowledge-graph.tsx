"use client";

/**
 * Knowledge Graph — Cytoscape.js 視覺化全部 Concept 節點與 Edge。
 *
 * Presentational 元件 — 由 KnowledgePage 傳入 graphData + masteryMap + pathOverlay，
 * 自己只負責 Cytoscape 生命週期與互動。
 * 語意縮放（2026-07-05 改版）：overview / detail 顯示同一批概念節點；
 * zoom < 門檻時節點與字體放大並重排為緊湊網格（overview-layout.ts），
 * 讓全覽時所有節點名稱仍可讀；切換由 graph-mode.ts 依 viewport zoom 驅動。
 * 點擊概念節點 zoom in 至該章（並開詳情面板）。
 * K5c：focusTags（補救跳轉）優先於 currentTag 進度聚焦。
 */

import cytoscape, { type Core, type EventObject } from "cytoscape";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { GalaxyNav } from "./galaxy-nav";
import { animateToBounds, boundsOf, fitWithCap } from "./graph-camera";
import {
  computeChapterAnchors,
  computePositions,
  type NodePosition,
} from "./graph-layout";
import {
  applyMode,
  modeForZoom,
  type ModeLayouts,
  type ViewMode,
} from "./graph-mode";
import { toElements } from "./knowledge-graph-elements";
import { STYLESHEET, TOKEN } from "./knowledge-graph-style";
import type {
  GraphData,
  MasteryEntry,
  PathOverlay,
} from "./knowledge-graph-types";
import { buildOrbitPath, buildStars } from "./orbit-scene";
import { computeOverviewLayout } from "./overview-layout";
import { OVERVIEW_STYLES } from "./overview-style";
import { OrbitUnderlay } from "./orbit-underlay";

// fit 目標包圍盒外擴：detail 章節（節點 + 下方標籤）/ overview 全覽（cell 半格）
const CHAPTER_FIT_MARGIN = 130;
const OVERVIEW_FIT_MARGIN = 150;

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
  const [viewMode, setViewMode] = useState<ViewMode>("detail");

  const elements = useMemo(
    () => toElements(data, masteryMap, pathOverlay),
    [data, masteryMap, pathOverlay],
  );
  const positions = useMemo(() => computePositions(data), [data]);
  const anchors = useMemo(() => computeChapterAnchors(data), [data]);
  const overview = useMemo(() => computeOverviewLayout(data), [data]);
  const layouts: ModeLayouts = useMemo(
    () => ({ detail: positions, overview: overview.positions }),
    [positions, overview],
  );
  const orbitPath = useMemo(() => buildOrbitPath(anchors), [anchors]);
  const overviewOrbitPath = useMemo(
    () => buildOrbitPath(overview.orbitAnchors),
    [overview],
  );
  // 星空覆蓋兩種佈局的聯集範圍
  const stars = useMemo(
    () => buildStars([...anchors, ...overview.orbitAnchors]),
    [anchors, overview],
  );

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

  // 章節 fit 一律瞄準 detail 佈局座標（overview 點章 zoom in 時，
  // 節點會在鏡頭動畫中移回 detail 位置，故不能拿元素現況當目標）
  const fitChapter = useCallback(
    (cy: Core, idx: number, animate: boolean) => {
      const category = anchors[idx]?.category;
      if (!category) return;
      const pts = data.nodes
        .filter((n) => n.category === category)
        .map((n) => positions.get(n.id))
        .filter((p): p is NodePosition => p !== undefined);
      if (pts.length === 0) return;
      animateToBounds(cy, boundsOf(pts, CHAPTER_FIT_MARGIN), animate);
    },
    [anchors, data, positions],
  );

  const handleNav = useCallback(
    (dir: -1 | 1) => {
      const next = Math.min(anchors.length - 1, Math.max(0, chapterIdx + dir));
      setChapterIdx(next);
      if (cyRef.current) fitChapter(cyRef.current, next, true);
    },
    [chapterIdx, anchors.length, fitChapter],
  );

  // 點擊章節容器 / 概念節點 → zoom in 至該章
  const zoomToCategory = useCallback(
    (cy: Core, category: string) => {
      const idx = anchors.findIndex((a) => a.category === category);
      if (idx < 0) return;
      setChapterIdx(idx);
      fitChapter(cy, idx, true);
    },
    [anchors, fitChapter],
  );

  // 全覽：zoom out 至 overview 佈局範圍（跨過門檻後節點自動放大重排）
  const handleOverview = useCallback(() => {
    const cy = cyRef.current;
    if (!cy) return;
    const pts = [...overview.positions.values()];
    if (pts.length === 0) return;
    animateToBounds(cy, boundsOf(pts, OVERVIEW_FIT_MARGIN), true);
  }, [overview]);

  // Cytoscape lifecycle
  useEffect(() => {
    if (!containerRef.current) return;

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: [...STYLESHEET, ...OVERVIEW_STYLES],
      layout: {
        // 確定性佈局：detail 座標由 graph-layout.ts 算好（overview 由模式切換動畫移位）
        name: "preset",
        positions: (node: { id: () => string }) =>
          positions.get(node.id()) ?? undefined,
        fit: false,
        animate: false,
      } as unknown as cytoscape.LayoutOptions,
      // wheelSensitivity 維持預設：自訂值會被 Cytoscape 警告在不同滑鼠/OS 上縮放不自然
      minZoom: 0.12,
      maxZoom: 3,
    });

    // 統一點擊：parent / 概念節點都帶 category → zoom in 該章
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

    // viewport 同步：underlay transform + 語意縮放模式切換（初次套用不做動畫）
    let mode: ViewMode | null = null;
    const syncViewport = () => {
      underlayRef.current?.setAttribute(
        "transform",
        `translate(${cy.pan().x} ${cy.pan().y}) scale(${cy.zoom()})`,
      );
      const next = modeForZoom(cy.zoom());
      if (next !== mode) {
        applyMode(cy, next, layouts, mode !== null);
        mode = next;
        setViewMode(next);
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
    layouts,
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
      <OrbitUnderlay
        groupRef={underlayRef}
        detailPath={orbitPath}
        overviewPath={overviewOrbitPath}
        stars={stars}
        mode={viewMode}
      />
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
