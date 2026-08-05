"use client";

import { useState, useCallback } from "react";
import { ChevronUp, ChevronDown, Trash2 } from "lucide-react";
import { useWorkspace } from "./workspace-context";
import type { RunRecord } from "./types";
import { RunBlock, classifyStatus, STATUS_META } from "./run-block";

interface OutputPanelProps {
  /** 是否收合為單行 status bar */
  collapsed?: boolean;
  /** 收合/展開切換 */
  onToggleCollapse?: () => void;
}

/**
 * Output Panel — 以 Run Block 列表呈現執行歷史（新到舊）。
 * 歷史記錄存於 WorkspaceContext（AppShell 層），面板開合不會清空；
 * 本元件只持有「哪一則展開」的檢視狀態。
 * 視覺規格：design-plan.md §2.3
 */
export function OutputPanel({ collapsed = false, onToggleCollapse }: OutputPanelProps) {
  const { runs, clearRuns, requestChatInjection } = useWorkspace();
  const latestBlock = runs[0];
  // 預設只展開最新一則（仿 Warp）；這裡只記使用者手動翻過的例外，
  // 因此新結果進來時自動展開、舊的自動收合，不需要 effect 重設狀態。
  const [overrides, setOverrides] = useState<Record<number, boolean>>({});
  const isExpanded = (id: number) => overrides[id] ?? id === latestBlock?.id;

  const toggleBlock = useCallback(
    (id: number, expanded: boolean) =>
      setOverrides((prev) => ({ ...prev, [id]: !expanded })),
    [],
  );

  /* 收合狀態：單行 status bar 顯示最新 block 摘要 */
  if (collapsed) {
    return (
      <button
        onClick={onToggleCollapse}
        className="flex h-7 w-full items-center gap-2 border-t border-border-default bg-bg-inset px-3 text-xs text-text-secondary hover:text-text-primary transition-colors body-ui"
      >
        <ChevronUp className="size-3.5" />
        <CollapsedStatusContent latest={latestBlock} />
      </button>
    );
  }

  return (
    <div className="flex h-full flex-col border-t border-border-default bg-bg-canvas">
      {/* Panel Header */}
      <div className="flex h-8 items-center gap-2 border-b border-border-muted px-3">
        <span className="text-xs font-medium text-text-secondary body-ui">Output</span>
        {runs.length > 0 && (
          <span className="rounded-pill bg-surface-2 px-2 py-0.5 text-[10px] text-text-muted">
            {runs.length}
          </span>
        )}

        <div className="flex-1" />

        {runs.length > 0 && (
          <button
            onClick={clearRuns}
            className="flex h-6 items-center gap-1 rounded px-2 text-xs text-text-muted hover:text-text-primary hover:bg-surface-2 transition-colors body-ui"
            title="清空執行歷史"
          >
            <Trash2 className="size-3" />
            清空
          </button>
        )}
        <button
          onClick={onToggleCollapse}
          className="flex size-6 items-center justify-center rounded text-text-muted hover:text-text-secondary hover:bg-surface-2 transition-colors"
          title="收合 Output"
          aria-label="收合 Output"
        >
          <ChevronDown className="size-3.5" />
        </button>
      </div>

      {/* Block 列表 */}
      <div className="flex-1 overflow-auto p-2 space-y-2">
        {runs.length === 0 ? (
          <div className="flex h-full items-center justify-center">
            <p className="text-xs text-text-muted body-reading">執行程式碼後，輸出結果會以 block 顯示在這裡。</p>
          </div>
        ) : (
          runs.map((block) => (
            <RunBlock
              key={block.id}
              block={block}
              expanded={isExpanded(block.id)}
              index={block.id}
              onToggle={() => toggleBlock(block.id, isExpanded(block.id))}
              onSendToChat={() => requestChatInjection(block.result)}
            />
          ))
        )}
      </div>
    </div>
  );
}

/** Collapsed status bar 內容 — 用 lucide icon 取代 emoji 符號（R8.2） */
function CollapsedStatusContent({ latest }: { latest?: RunRecord }) {
  if (!latest) return <span>Output</span>;
  const status = classifyStatus(latest.result);
  const meta = STATUS_META[status];
  const time = latest.result.time ? ` (${parseFloat(latest.result.time).toFixed(2)}s)` : "";
  return (
    <span className="flex items-center gap-1.5">
      <span>Run #{latest.id}</span>
      <meta.Icon className={`size-3 ${meta.textClass}`} />
      <span className={meta.textClass}>{meta.label}{time}</span>
    </span>
  );
}
