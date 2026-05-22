"use client";

/**
 * 範例程式 tab（Phase 6-2d）— grounded code examples 渲染 + 「在 Workspace 開啟」轉場。
 *
 * 三種狀態優先順序（與 ConceptTab 一致）：
 * 1. 6-2 新 grounded 形狀（unit.content.code_examples）→ 卡片列表
 * 2. 6-2 標註 needs_more_source → 顯示原因
 * 3. 舊形狀（unit.content.examples: string[]）→ legacy fallback（仍渲染為純程式碼塊）
 * 4. 都沒有 → placeholder
 *
 * 設計取捨：
 * - 範例 tab 不嵌 YT player（避免每 tab 各跑一個 IFrame）；citation 改為「靜態時間戳 + 節錄」標籤
 *   讓使用者知道出處，但 jump 仍須回 concept tab 點 citation。
 * - 「在 Workspace 開啟」復用 sessionStorage pattern（pending-workspace-code.ts），
 *   不走 URL query（C++ source 太長）。
 */

import Link from "next/link";
import { ArrowUpRight, FileCode2 } from "lucide-react";

import { CodeExample, Unit } from "@/lib/learning";
import { setPendingWorkspaceCode } from "@/lib/pending-workspace-code";

interface Props {
  unit: Unit;
}

export function ExamplesTab({ unit }: Props) {
  const grounded = unit.content.code_examples;
  const legacy = unit.content.examples ?? [];

  if (grounded && grounded.needs_more_source) {
    return <NeedsMoreSourceNotice reason={grounded.reason} />;
  }

  if (grounded && grounded.examples.length > 0) {
    return (
      <div className="space-y-3">
        {grounded.examples.map((example, idx) => (
          <ExampleCard key={`${example.title}-${idx}`} example={example} />
        ))}
      </div>
    );
  }

  if (legacy.length > 0) {
    return (
      <div className="space-y-3">
        {legacy.map((code, idx) => (
          <LegacyCodeBlock key={idx} code={code} />
        ))}
      </div>
    );
  }

  return <EmptyNotice unitName={unit.concept_name_zh} />;
}

function ExampleCard({ example }: { example: CodeExample }) {
  const handleOpenInWorkspace = () => {
    setPendingWorkspaceCode(example.code);
  };

  return (
    <div className="rounded-md border border-border-default bg-surface-1">
      <header className="flex items-start justify-between gap-3 border-b border-border-default px-4 py-3">
        <div className="flex items-start gap-2">
          <FileCode2 className="mt-0.5 size-4 shrink-0 text-text-secondary" />
          <h3 className="text-sm font-medium text-text-primary">
            {example.title}
          </h3>
        </div>
        <Link
          href="/workspace"
          onClick={handleOpenInWorkspace}
          className="inline-flex h-7 shrink-0 items-center gap-1 rounded-md border border-border-default bg-btn-default-bg px-2.5 text-xs text-text-secondary hover:text-text-primary"
        >
          在 Workspace 開啟
          <ArrowUpRight className="size-3" />
        </Link>
      </header>

      <pre className="overflow-x-auto bg-bg-inset px-4 py-3 font-mono text-[0.8125rem] leading-relaxed text-text-primary">
        {example.code}
      </pre>

      {example.explanation && (
        <p className="border-t border-border-default px-4 py-3 text-sm leading-relaxed text-text-secondary">
          {example.explanation}
        </p>
      )}

      {example.citation && (
        <CitationLabel
          timestamp={example.citation.timestamp}
          excerpt={example.citation.text_excerpt}
        />
      )}
    </div>
  );
}

function CitationLabel({
  timestamp,
  excerpt,
}: {
  timestamp: string;
  excerpt: string;
}) {
  return (
    <div className="flex items-start gap-2 border-t border-border-default bg-surface-2 px-4 py-2 text-xs">
      <span className="font-mono text-text-link">{timestamp}</span>
      <span className="text-text-muted">{excerpt}</span>
    </div>
  );
}

function LegacyCodeBlock({ code }: { code: string }) {
  return (
    <pre className="overflow-x-auto rounded-md border border-border-default bg-bg-inset p-3 font-mono text-sm text-text-primary">
      {code}
    </pre>
  );
}

function NeedsMoreSourceNotice({ reason }: { reason: string }) {
  return (
    <div className="rounded-md border border-border-default bg-surface-1 p-4">
      <h3 className="text-sm font-medium text-text-primary">範例尚未就緒</h3>
      <p className="mt-2 text-sm leading-relaxed text-text-secondary">
        本單元的影片字幕內容不足以生成程式範例。
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
      「{unitName}」的程式範例尚未匯入（待 6-2 批次生成 + promote）。
    </div>
  );
}
