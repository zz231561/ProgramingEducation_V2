"use client";

import { useCallback, useState } from "react";

import { ConceptDetailPanel } from "@/components/knowledge/concept-detail-panel";
import { KnowledgeGraph } from "@/components/knowledge/knowledge-graph";

/**
 * Knowledge 頁面 — 知識圖譜全圖 + Concept Detail Panel（roadmap 2-2c + 2-2d）。
 *
 * 點節點 → 右側 panel 顯示詳情；panel 內點鄰居 → 切換到該 concept 的詳情。
 */
export default function KnowledgePage() {
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const handleClose = useCallback(() => setSelectedTag(null), []);

  return (
    <div className="flex h-full flex-col">
      <header className="border-b border-border-default px-4 py-3">
        <h1 className="text-base font-medium text-text-primary">
          Knowledge Graph
        </h1>
        <p className="text-xs text-text-secondary">
          節點顏色依分類，大小依難度（1-5）；邊類型：實線箭頭 = 先修、虛線 = 包含、點線 = 特化、細線 = 相關
        </p>
      </header>
      <div className="flex flex-1 overflow-hidden">
        <div className="min-w-0 flex-1">
          <KnowledgeGraph onNodeClick={setSelectedTag} />
        </div>
        {selectedTag ? (
          <ConceptDetailPanel
            tag={selectedTag}
            onClose={handleClose}
            onSelectTag={setSelectedTag}
          />
        ) : null}
      </div>
    </div>
  );
}
