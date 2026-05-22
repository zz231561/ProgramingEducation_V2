"use client";

/**
 * 摘要 tab（Phase 6-2e）— grounded key_points bullet + citation 標籤。
 *
 * 狀態優先順序（與 ConceptTab / ExamplesTab 一致）：
 * 1. content.summary 為 grounded object 且 needs_more_source → 顯示原因
 * 2. content.summary 為 grounded object 且 key_points 非空 → bullet list + citations
 * 3. content.summary 為 legacy 非空 string → 純文字 fallback（3-1d lazy seed 形狀）
 * 4. 都沒有 → placeholder
 *
 * 設計取捨：
 * - 摘要與概念說明不重複嵌 YT player（避免每 tab 各跑 IFrame）；citation
 *   仍以靜態時間戳 + 節錄呈現，跳轉請回概念 tab 點 citation。
 * - 後端 Pydantic 限制 key_points ≤ 7、每項短句，故 UI 不需虛擬滾動 / 折疊。
 */

import { Citation, SummaryContent, Unit } from "@/lib/learning";

interface Props {
  unit: Unit;
}

export function SummaryTab({ unit }: Props) {
  const summary = unit.content.summary;

  if (isGroundedSummary(summary)) {
    if (summary.needs_more_source) {
      return <NeedsMoreSourceNotice reason={summary.reason} />;
    }
    if (summary.key_points.length > 0) {
      return (
        <GroundedSummary
          keyPoints={summary.key_points}
          citations={summary.citations}
        />
      );
    }
  }

  if (typeof summary === "string" && summary.trim().length > 0) {
    return <LegacySummary text={summary} />;
  }

  return <EmptyNotice unitName={unit.concept_name_zh} />;
}

function isGroundedSummary(
  value: string | SummaryContent | undefined,
): value is SummaryContent {
  return typeof value === "object" && value !== null && "key_points" in value;
}

function GroundedSummary({
  keyPoints,
  citations,
}: {
  keyPoints: string[];
  citations: Citation[];
}) {
  return (
    <div className="space-y-3">
      <div className="rounded-md border border-border-default bg-surface-1 p-4">
        <h3 className="text-sm font-medium text-text-primary">重點摘要</h3>
        <ul className="mt-3 list-disc space-y-1.5 pl-5 text-sm leading-relaxed text-text-secondary">
          {keyPoints.map((point, idx) => (
            <li key={`${idx}-${point.slice(0, 10)}`}>{point}</li>
          ))}
        </ul>
      </div>
      {citations.length > 0 && <CitationList citations={citations} />}
    </div>
  );
}

function CitationList({ citations }: { citations: Citation[] }) {
  return (
    <div className="rounded-md border border-border-default bg-surface-1 p-3">
      <h4 className="text-xs font-medium text-text-secondary">
        影片出處（請至概念說明 tab 點擊跳轉）
      </h4>
      <ul className="mt-2 space-y-1.5">
        {citations.map((c, idx) => (
          <li
            key={`${c.timestamp}-${idx}`}
            className="flex items-start gap-2 px-1.5 py-1 text-xs"
          >
            <span className="font-mono text-text-link">{c.timestamp}</span>
            <span className="text-text-secondary">{c.text_excerpt}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function LegacySummary({ text }: { text: string }) {
  return (
    <div className="rounded-md border border-border-default bg-surface-1 p-4 text-sm leading-relaxed text-text-secondary">
      {text}
    </div>
  );
}

function NeedsMoreSourceNotice({ reason }: { reason: string }) {
  return (
    <div className="rounded-md border border-border-default bg-surface-1 p-4">
      <h3 className="text-sm font-medium text-text-primary">摘要尚未就緒</h3>
      <p className="mt-2 text-sm leading-relaxed text-text-secondary">
        本單元的影片字幕內容不足以生成重點摘要。
      </p>
      {reason && (
        <p className="mt-2 text-xs text-text-muted">說明：{reason}</p>
      )}
    </div>
  );
}

function EmptyNotice({ unitName }: { unitName: string }) {
  return (
    <div className="rounded-md border border-border-default bg-surface-1 px-6 py-12 text-center text-sm text-text-secondary">
      「{unitName}」的重點摘要尚未匯入（待 6-2 批次生成 + promote）。
    </div>
  );
}
