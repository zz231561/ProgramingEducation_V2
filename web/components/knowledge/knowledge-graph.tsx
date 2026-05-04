"use client";

/**
 * Knowledge Graph — Cytoscape.js + fcose layout 視覺化全部 Concept 節點與 Edge。
 *
 * Presentational 元件 — 由 KnowledgePage 傳入 graphData + masteryMap，
 * 自己只負責 Cytoscape 生命週期與互動。
 * 視覺規格 / 色票 / 違和感 7 條檢核 → `knowledge-graph-style.ts`
 */

import cytoscape, { type Core, type EventObject } from "cytoscape";
import fcose from "cytoscape-fcose";
import { useEffect, useMemo, useRef } from "react";

import {
  STYLESHEET,
  TOKEN,
  toElements,
} from "./knowledge-graph-style";
import type {
  GraphData,
  MasteryEntry,
} from "./knowledge-graph-types";

// 註冊 fcose layout（idempotent，多次呼叫無害）
cytoscape.use(fcose);

export type KnowledgeGraphProps = {
  data: GraphData;
  masteryMap: Map<string, MasteryEntry>;
  /** 點擊節點時觸發；接收 concept tag 供上層查詳情。*/
  onNodeClick?: (tag: string) => void;
};

export function KnowledgeGraph({
  data,
  masteryMap,
  onNodeClick,
}: KnowledgeGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);

  const elements = useMemo(
    () => toElements(data, masteryMap),
    [data, masteryMap],
  );

  // Cytoscape lifecycle
  useEffect(() => {
    if (!containerRef.current) return;

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: STYLESHEET,
      layout: {
        name: "fcose",
        // quality=default 適合 < 50 節點；節點較小且 label 外置，間距放大避免標籤撞到鄰居
        quality: "default",
        animate: false,
        nodeRepulsion: () => 12000,
        idealEdgeLength: () => 130,
        padding: 32,
      } as cytoscape.LayoutOptions,
      wheelSensitivity: 0.2,
      minZoom: 0.3,
      maxZoom: 3,
    });

    cy.on("tap", "node", (evt: EventObject) => {
      const tag = evt.target.data("tag") as string;
      onNodeClick?.(tag);
    });

    // Obsidian 風 hover 高亮：點亮鄰居 + 淡化其他
    cy.on("mouseover", "node", (evt: EventObject) => {
      const node = evt.target;
      const neighborhood = node.closedNeighborhood();
      cy.elements().difference(neighborhood).addClass("faded");
      neighborhood.addClass("highlighted");
    });
    cy.on("mouseout", "node", () => {
      cy.elements().removeClass("faded highlighted");
    });

    cyRef.current = cy;
    return () => {
      cy.destroy();
      cyRef.current = null;
    };
  }, [elements, onNodeClick]);

  return (
    <div
      ref={containerRef}
      className="h-full w-full"
      style={{ backgroundColor: TOKEN.bgCanvas }}
    />
  );
}
