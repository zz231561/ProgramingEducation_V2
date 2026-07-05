"use client";

/**
 * Knowledge Graph — Cytoscape.js 視覺化全部 Concept 節點與 Edge。
 *
 * Presentational 元件 — 由 KnowledgePage 傳入 graphData + masteryMap + pathOverlay，
 * 自己只負責 Cytoscape 生命週期與互動。
 * 視覺規格 / 色票 → `knowledge-graph-style.ts`；elements 轉換 → `knowledge-graph-elements.ts`
 * K5b 改版二：preset layout（`graph-layout.ts` 確定性座標，取代 fcose 隨機結果）
 *            + 章節星系背景（`galaxy-backgrounds.ts`），parent 可拖曳整章移動
 * K5c：focusTags 有值時 layout 完成後 fit 至補救節點
 */

import cytoscape, { type Core, type EventObject } from "cytoscape";
import { useEffect, useMemo, useRef } from "react";

import { computePositions } from "./graph-layout";
import { toElements } from "./knowledge-graph-elements";
import { STYLESHEET, TOKEN } from "./knowledge-graph-style";
import type {
  GraphData,
  MasteryEntry,
  PathOverlay,
} from "./knowledge-graph-types";

export type KnowledgeGraphProps = {
  data: GraphData;
  masteryMap: Map<string, MasteryEntry>;
  /** K5c 路徑高亮 overlay（省略 = 無 ring）。 */
  pathOverlay?: PathOverlay;
  /** K5c：初次渲染後鏡頭聚焦到這些 concept tags（補救路徑跳轉用）。 */
  focusTags?: string[];
  /** 點擊節點時觸發；接收 concept tag 供上層查詳情。*/
  onNodeClick?: (tag: string) => void;
};

export function KnowledgeGraph({
  data,
  masteryMap,
  pathOverlay,
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
        fit: true,
        padding: 48,
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

    // K5c：補救路徑跳轉 — 鏡頭聚焦嫌疑節點
    if (focusTags && focusTags.length > 0) {
      const targets = cy.nodes().filter((n) => focusTags.includes(n.data("tag")));
      if (targets.length > 0) cy.fit(targets, 80);
    }

    cyRef.current = cy;
    return () => {
      cy.destroy();
      cyRef.current = null;
    };
  }, [elements, positions, onNodeClick, focusTags]);

  return (
    <div
      ref={containerRef}
      className="h-full w-full"
      style={{ backgroundColor: TOKEN.bgCanvas }}
    />
  );
}
