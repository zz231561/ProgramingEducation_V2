"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useMemo, useState } from "react";

import { ConceptDetailPanel } from "@/components/knowledge/concept-detail-panel";
import { GraphLegend } from "@/components/knowledge/graph-legend";
import { KnowledgeGraph } from "@/components/knowledge/knowledge-graph";
import type {
  GraphData,
  MasteryEntry,
} from "@/components/knowledge/knowledge-graph-types";
import {
  buildPathOverlay,
  parseRemedialParam,
} from "@/components/knowledge/path-overlay";
import { getDefaultPath, type Unit } from "@/lib/learning";
import { ApiRequestError, api } from "@/lib/api";

/**
 * Knowledge 頁面 — 知識圖譜全圖 + Concept Detail Panel（roadmap 2-2c/d + K5b/c）。
 *
 * K5b：節點填色 = 熟練度、分章 cluster；K5c：路徑 ring（目前/已完成/補救）。
 * 補救高亮由 /knowledge?remedial=tag1,tag2 觸發（K3e 診斷跳轉）。
 * useSearchParams 需 Suspense boundary（Next.js CSR bailout 規範）。
 */
export default function KnowledgePage() {
  return (
    <Suspense fallback={null}>
      <KnowledgePageInner />
    </Suspense>
  );
}

function KnowledgePageInner() {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [masteryEntries, setMasteryEntries] = useState<MasteryEntry[]>([]);
  const [pathUnits, setPathUnits] = useState<Unit[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [selectedTag, setSelectedTag] = useState<string | null>(null);

  const searchParams = useSearchParams();
  const remedialTags = useMemo(
    () => parseRemedialParam(searchParams.get("remedial")),
    [searchParams],
  );

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
      // K5c：路徑 overlay 為 best-effort — 失敗不擋圖譜主體
      try {
        const path = await getDefaultPath();
        if (!cancelled) setPathUnits(path.units);
      } catch (e) {
        console.warn("載入學習路徑失敗，路徑高亮停用", e);
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

  const pathOverlay = useMemo(
    () => buildPathOverlay(pathUnits, remedialTags),
    [pathUnits, remedialTags],
  );

  // 目前進度 concept（進場鏡頭 zoom 至其星系）
  const currentTag = useMemo(() => {
    for (const [tag, status] of pathOverlay.statusByTag) {
      if (status === "current") return tag;
    }
    return null;
  }, [pathOverlay]);

  return (
    <div className="flex h-full flex-col">
      <header className="space-y-1.5 border-b border-border-default px-4 py-3">
        <h1 className="text-base font-medium text-text-primary">
          Knowledge Graph
        </h1>
        <GraphLegend showRemedial={remedialTags.length > 0} />
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
              pathOverlay={pathOverlay}
              currentTag={currentTag}
              focusTags={remedialTags}
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
