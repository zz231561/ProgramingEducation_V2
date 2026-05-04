"use client";

import { useState } from "react";

import { KnowledgeGraph } from "@/components/knowledge/knowledge-graph";

/**
 * Knowledge 頁面 — 知識圖譜全圖視覺化（roadmap 2-2c）。
 *
 * 點擊節點目前僅紀錄選取狀態；2-2d 將以此狀態驅動 Concept Detail Panel。
 */
export default function KnowledgePage() {
  const [selectedTag, setSelectedTag] = useState<string | null>(null);

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center justify-between border-b border-border-default px-4 py-3">
        <div>
          <h1 className="text-base font-medium text-text-primary">
            Knowledge Graph
          </h1>
          <p className="text-xs text-text-secondary">
            節點顏色依分類，大小依難度（1-5）；邊類型：實線箭頭 = 先修、虛線 = 包含、點線 = 特化、細線 = 相關
          </p>
        </div>
        {selectedTag ? (
          <span className="text-xs text-text-secondary">
            選取：<span className="text-text-primary">{selectedTag}</span>
          </span>
        ) : null}
      </header>
      <div className="flex-1">
        <KnowledgeGraph onNodeClick={setSelectedTag} />
      </div>
    </div>
  );
}
