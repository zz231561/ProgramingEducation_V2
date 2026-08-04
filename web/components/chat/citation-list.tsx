"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, ExternalLink, Quote } from "lucide-react";
import type { Citation } from "@/lib/chat-types";

/**
 * Coddy 回應的教材出處清單（防幻覺第三層）。
 *
 * 設計意圖：讓學生「當場可核對」——展開即見 transcript 原文，不必先跳出去聽影片
 * 才知道 Coddy 有沒有亂講。後端已用 `strip_ungrounded_citations` 攔掉不存在的引用，
 * 這裡呈現的必然是真實檢索結果。
 */
export function CitationList({ citations }: { citations: Citation[] }) {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  if (citations.length === 0) return null;

  return (
    <div className="mt-2 rounded-md border border-border-default bg-surface-1 p-2.5">
      <h4 className="flex items-center gap-1.5 text-xs font-medium text-text-secondary">
        <Quote className="size-3" />
        教材出處（展開可看原文）
      </h4>
      <ul className="mt-1.5 space-y-1">
        {citations.map((c, idx) => (
          <CitationRow
            key={`${c.url}-${idx}`}
            citation={c}
            expanded={openIndex === idx}
            onToggle={() => setOpenIndex(openIndex === idx ? null : idx)}
          />
        ))}
      </ul>
    </div>
  );
}

function CitationRow({
  citation,
  expanded,
  onToggle,
}: {
  citation: Citation;
  expanded: boolean;
  onToggle: () => void;
}) {
  return (
    <li>
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={expanded}
        className="flex w-full items-center gap-1.5 rounded-sm px-1 py-0.5 text-left text-xs text-text-secondary hover:bg-surface-2 hover:text-text-primary"
      >
        {expanded ? (
          <ChevronDown className="size-3 shrink-0" />
        ) : (
          <ChevronRight className="size-3 shrink-0" />
        )}
        <span className="truncate">{citation.title}</span>
        <span className="ml-auto shrink-0 font-mono text-text-link">
          {citation.timestamp}
        </span>
      </button>

      {expanded && (
        <div className="mt-1 ml-4 rounded-sm border-l border-border-muted bg-bg-inset px-2.5 py-2">
          <p className="text-xs leading-relaxed text-text-secondary">
            {citation.excerpt}
          </p>
          <a
            href={citation.url}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-1.5 inline-flex items-center gap-1 text-xs text-text-link hover:underline"
          >
            在 YouTube 開啟此段
            <ExternalLink className="size-3" />
          </a>
        </div>
      )}
    </li>
  );
}
