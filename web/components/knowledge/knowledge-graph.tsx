"use client";

/**
 * Knowledge Graph — Cytoscape.js + fcose layout 視覺化全部 Concept 節點與 Edge。
 *
 * 對應 roadmap 2-2c。串接後端 GET /concepts/graph，依 category 著色、
 * 依 difficulty_level 調整節點大小，邊樣式依 edge_type 區分。
 *
 * 視覺規格 / 色票 / 違和感 7 條檢核 → `knowledge-graph-style.ts`
 */

import cytoscape, { type Core, type EventObject } from "cytoscape";
import fcose from "cytoscape-fcose";
import { useEffect, useMemo, useRef, useState } from "react";

import { ApiRequestError, api } from "@/lib/api";

import {
  STYLESHEET,
  TOKEN,
  toElements,
} from "./knowledge-graph-style";
import type { GraphData } from "./knowledge-graph-types";

// 註冊 fcose layout（idempotent，多次呼叫無害）
cytoscape.use(fcose);

export type KnowledgeGraphProps = {
  /** 點擊節點時觸發；接收 concept tag 供上層查詳情。*/
  onNodeClick?: (tag: string) => void;
};

export function KnowledgeGraph({ onNodeClick }: KnowledgeGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const [data, setData] = useState<GraphData | null>(null);
  const [error, setError] = useState<string | null>(null);

  // 初次載入：抓全圖
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const result = await api<GraphData>("/concepts/graph");
        if (!cancelled) setData(result);
      } catch (e) {
        if (cancelled) return;
        const msg =
          e instanceof ApiRequestError ? e.body.message : "無法載入知識圖譜";
        setError(msg);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const elements = useMemo(
    () => (data ? toElements(data) : []),
    [data],
  );

  // Cytoscape lifecycle — data 可用後才初始化
  useEffect(() => {
    if (!containerRef.current || !data) return;

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: STYLESHEET,
      layout: {
        name: "fcose",
        // quality=default 適合 < 50 節點；節點數成長後可改 proof
        quality: "default",
        animate: false,
        nodeRepulsion: () => 8000,
        idealEdgeLength: () => 100,
        padding: 24,
      } as cytoscape.LayoutOptions,
      wheelSensitivity: 0.2,
      minZoom: 0.4,
      maxZoom: 2.5,
    });

    cy.on("tap", "node", (evt: EventObject) => {
      const tag = evt.target.data("tag") as string;
      onNodeClick?.(tag);
    });

    cyRef.current = cy;
    return () => {
      cy.destroy();
      cyRef.current = null;
    };
  }, [data, elements, onNodeClick]);

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-sm text-text-secondary">{error}</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-sm text-text-secondary">載入知識圖譜中…</p>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="h-full w-full"
      style={{ backgroundColor: TOKEN.bgCanvas }}
    />
  );
}
