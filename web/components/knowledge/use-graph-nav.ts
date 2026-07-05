"use client";

/**
 * useGraphNav — 知識圖譜的章節游標 + 鏡頭動作 hook。
 *
 * 自 knowledge-graph.tsx 拆出（tech-debt：主元件超過 250 行硬性門檻）。
 * 職責：章節索引 state（含進場聚焦推導）、章節 fit、上一/下一章導航、
 * 點章 zoom in、全覽 zoom out。Cytoscape 實例由主元件透過 cyRef 共享。
 */

import type { Core } from "cytoscape";
import { useCallback, useMemo, useState, type RefObject } from "react";

import { animateToBounds, boundsOf } from "./graph-camera";
import type { ChapterAnchor, NodePosition } from "./graph-layout";
import type { OverviewLayout } from "./overview-layout";
import type { GraphData } from "./knowledge-graph-types";

// fit 目標包圍盒外擴：detail 章節（節點 + 下方標籤）/ overview 全覽（cell 半格）
const CHAPTER_FIT_MARGIN = 130;
const OVERVIEW_FIT_MARGIN = 150;

type UseGraphNavOptions = {
  data: GraphData;
  positions: Map<string, NodePosition>;
  anchors: ChapterAnchor[];
  overview: OverviewLayout;
  cyRef: RefObject<Core | null>;
  /** 目前進度 concept（進場鏡頭 zoom 至其所屬章節）。 */
  currentTag?: string | null;
  /** K5c：補救跳轉聚焦 tags；優先於 currentTag。 */
  focusTags?: string[];
};

export function useGraphNav({
  data,
  positions,
  anchors,
  overview,
  cyRef,
  currentTag,
  focusTags,
}: UseGraphNavOptions) {
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
    [chapterIdx, anchors.length, fitChapter, cyRef],
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
  }, [overview, cyRef]);

  const navLabel = `${anchors[chapterIdx]?.category ?? ""}（${chapterIdx + 1}/${anchors.length}）`;

  return {
    chapterIdx,
    initialChapterIdx,
    fitChapter,
    handleNav,
    zoomToCategory,
    handleOverview,
    navLabel,
  };
}
