"use client";

/**
 * Knowledge Graph — Cytoscape.js 視覺化全部 Concept 節點與 Edge。
 *
 * Presentational 元件 — 由 KnowledgePage 傳入 graphData + masteryMap + pathOverlay，
 * 自己只負責 Cytoscape 生命週期與互動。
 * 視覺規格 / 色票 → `knowledge-graph-style.ts`；elements 轉換 → `knowledge-graph-elements.ts`
 * K5b 改版二：preset layout（`graph-layout.ts` 確定性座標）+ 章節星系背景
 * K5 調整三：進場鏡頭 zoom 至目前進度星系；GalaxyNav 左右鍵切換星系
 * K5c：focusTags（補救跳轉）優先於 currentTag 進度聚焦
 */

import cytoscape, { type Core, type EventObject } from "cytoscape";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { GalaxyNav } from "./galaxy-nav";
import { computePositions, orderedCategories } from "./graph-layout";
import { CHAPTER_ID_PREFIX, toElements } from "./knowledge-graph-elements";
import { STYLESHEET, TOKEN } from "./knowledge-graph-style";
import type {
  GraphData,
  MasteryEntry,
  PathOverlay,
} from "./knowledge-graph-types";

const FIT_PADDING = 60;
const NAV_ANIMATION_MS = 350;

export type KnowledgeGraphProps = {
  data: GraphData;
  masteryMap: Map<string, MasteryEntry>;
  /** K5c 路徑高亮 overlay（省略 = 無 ring）。 */
  pathOverlay?: PathOverlay;
  /** 目前進度 concept（進場鏡頭 zoom 至其所屬星系）。 */
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
  const cyRef = useRef<Core | null>(null);

  const elements = useMemo(
    () => toElements(data, masteryMap, pathOverlay),
    [data, masteryMap, pathOverlay],
  );
  const positions = useMemo(() => computePositions(data), [data]);
  const chapters = useMemo(() => orderedCategories(data.nodes), [data]);

  // 進場聚焦章節：補救 tags > 目前進度 > 第一章
  const initialChapterIdx = useMemo(() => {
    const anchorTag = focusTags?.[0] ?? currentTag;
    if (!anchorTag) return 0;
    const category = data.nodes.find((n) => n.tag === anchorTag)?.category;
    const idx = category ? chapters.indexOf(category) : -1;
    return idx >= 0 ? idx : 0;
  }, [data, chapters, currentTag, focusTags]);

  // derived-state 調整：initialChapterIdx 變動（如 path 載入完成）時重設游標
  const [chapterIdx, setChapterIdx] = useState(initialChapterIdx);
  const [prevInitialIdx, setPrevInitialIdx] = useState(initialChapterIdx);
  if (prevInitialIdx !== initialChapterIdx) {
    setPrevInitialIdx(initialChapterIdx);
    setChapterIdx(initialChapterIdx);
  }

  const fitChapter = useCallback(
    (cy: Core, idx: number, animate: boolean) => {
      const parent = cy.getElementById(`${CHAPTER_ID_PREFIX}${chapters[idx]}`);
      if (parent.empty()) return;
      if (animate) {
        cy.animate({
          fit: { eles: parent, padding: FIT_PADDING },
          duration: NAV_ANIMATION_MS,
          easing: "ease-in-out",
        });
      } else {
        cy.fit(parent, FIT_PADDING);
      }
    },
    [chapters],
  );

  const handleNav = useCallback(
    (dir: -1 | 1) => {
      const next = Math.min(chapters.length - 1, Math.max(0, chapterIdx + dir));
      setChapterIdx(next);
      if (cyRef.current) fitChapter(cyRef.current, next, true);
    },
    [chapterIdx, chapters.length, fitChapter],
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
      minZoom: 0.2,
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

    // 進場鏡頭：補救 tags 直接框住嫌疑鏈，否則 zoom 至進度所在星系
    if (focusTags && focusTags.length > 0) {
      const targets = cy.nodes().filter((n) => focusTags.includes(n.data("tag")));
      if (targets.length > 0) cy.fit(targets, 80);
    } else {
      fitChapter(cy, initialChapterIdx, false);
    }

    cyRef.current = cy;
    return () => {
      cy.destroy();
      cyRef.current = null;
    };
  }, [elements, positions, onNodeClick, focusTags, initialChapterIdx, fitChapter]);

  return (
    <div className="relative h-full w-full">
      <div
        ref={containerRef}
        className="h-full w-full"
        style={{ backgroundColor: TOKEN.bgCanvas }}
      />
      <GalaxyNav
        label={`${chapters[chapterIdx] ?? ""}（${chapterIdx + 1}/${chapters.length}）`}
        canPrev={chapterIdx > 0}
        canNext={chapterIdx < chapters.length - 1}
        onPrev={() => handleNav(-1)}
        onNext={() => handleNav(1)}
      />
    </div>
  );
}
