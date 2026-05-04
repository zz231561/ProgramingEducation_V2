"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { ConceptDetailPanel } from "@/components/knowledge/concept-detail-panel";
import { KnowledgeGraph } from "@/components/knowledge/knowledge-graph";
import type {
  GraphData,
  MasteryEntry,
} from "@/components/knowledge/knowledge-graph-types";
import { ApiRequestError, api } from "@/lib/api";

/**
 * Knowledge 頁面 — 知識圖譜全圖 + Concept Detail Panel + 精熟度著色
 * （roadmap 2-2c + 2-2d + 2-3c）。
 *
 * 由 page 層 fetch 圖譜資料與精熟度（一次性平行請求），下傳給
 * presentational 子元件。Detail Panel 也共用 masteryMap 顯示「我的精熟度」。
 */
export default function KnowledgePage() {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [masteryEntries, setMasteryEntries] = useState<MasteryEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [selectedTag, setSelectedTag] = useState<string | null>(null);

  const handleClose = useCallback(() => setSelectedTag(null), []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [graph, mastery] = await Promise.all([
          api<GraphData>("/concepts/graph"),
          api<MasteryEntry[]>("/concepts/mastery"),
        ]);
        if (cancelled) return;
        setGraphData(graph);
        setMasteryEntries(mastery);
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

  const masteryMap = useMemo(
    () => new Map(masteryEntries.map((m) => [m.tag, m])),
    [masteryEntries],
  );

  return (
    <div className="flex h-full flex-col">
      <header className="border-b border-border-default px-4 py-3">
        <h1 className="text-base font-medium text-text-primary">
          Knowledge Graph
        </h1>
        <p className="text-xs text-text-secondary">
          節點顏色依分類，大小依難度（1-5）；外圈：綠 = 已掌握 / 黃 = 學習中 / 紅 = 需加強 / 無圈 = 尚未互動
        </p>
      </header>
      <div className="flex flex-1 overflow-hidden">
        <div className="min-w-0 flex-1">
          {error ? (
            <div className="flex h-full items-center justify-center">
              <p className="text-sm text-text-secondary">{error}</p>
            </div>
          ) : !graphData ? (
            <div className="flex h-full items-center justify-center">
              <p className="text-sm text-text-secondary">載入知識圖譜中…</p>
            </div>
          ) : (
            <KnowledgeGraph
              data={graphData}
              masteryMap={masteryMap}
              onNodeClick={setSelectedTag}
            />
          )}
        </div>
        {selectedTag ? (
          <ConceptDetailPanel
            tag={selectedTag}
            mastery={masteryMap.get(selectedTag)}
            onClose={handleClose}
            onSelectTag={setSelectedTag}
          />
        ) : null}
      </div>
    </div>
  );
}
