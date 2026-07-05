"use client";

/**
 * 概念選擇器（dev 工具共用）— 章節下拉 + 概念下拉，選定後回傳 tag。
 *
 * 資料來自 fetchConceptGraph（module 快取）；診斷模擬卡與題庫檢視卡共用。
 */

import { useEffect, useMemo, useState } from "react";

import type { GraphData } from "@/components/knowledge/knowledge-graph-types";
import { fetchConceptGraph } from "@/lib/dev-mode";

export const SELECT_CLASS =
  "h-8 rounded-md border border-border-default bg-surface-0 px-2 text-sm text-text-primary";

export function DevConceptSelect({
  value,
  onChange,
}: {
  value: string;
  onChange: (tag: string) => void;
}) {
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [category, setCategory] = useState("");

  useEffect(() => {
    let cancelled = false;
    fetchConceptGraph().then(
      (data) => {
        if (cancelled) return;
        setGraph(data);
        setCategory((prev) => prev || (data.nodes[0]?.category ?? ""));
      },
      () => undefined,
    );
    return () => {
      cancelled = true;
    };
  }, []);

  const categories = useMemo(
    () => [...new Set(graph?.nodes.map((n) => n.category) ?? [])],
    [graph],
  );
  const concepts = useMemo(
    () => graph?.nodes.filter((n) => n.category === category) ?? [],
    [graph, category],
  );

  return (
    <>
      <select
        aria-label="章節"
        value={category}
        onChange={(e) => {
          setCategory(e.target.value);
          onChange("");
        }}
        className={SELECT_CLASS}
      >
        {categories.map((c) => (
          <option key={c} value={c}>{c}</option>
        ))}
      </select>
      <select
        aria-label="概念"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={`${SELECT_CLASS} max-w-64`}
      >
        <option value="">選擇概念…</option>
        {concepts.map((n) => (
          <option key={n.tag} value={n.tag}>{n.name_zh}</option>
        ))}
      </select>
    </>
  );
}
