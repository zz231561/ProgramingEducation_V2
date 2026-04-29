"use client";

import { useEffect, useState, useCallback } from "react";
import { ChevronUp, ChevronDown, Trash2 } from "lucide-react";
import { useWorkspace } from "./workspace-context";
import { RunBlock, type RunBlockData, classifyStatus, STATUS_META } from "./run-block";

interface OutputPanelProps {
  /** 是否收合為單行 status bar */
  collapsed?: boolean;
  /** 收合/展開切換 */
  onToggleCollapse?: () => void;
}

/**
 * Output Panel — 以 Run Block 列表呈現所有執行結果。
 * 訂閱 WorkspaceContext.onExecutionComplete，每次 Run 自動加入新 block 於頂部。
 * 視覺規格：design-plan.md §2.3
 */
export function OutputPanel({ collapsed = false, onToggleCollapse }: OutputPanelProps) {
  const { onExecutionComplete, requestChatInjection } = useWorkspace();
  const [blocks, setBlocks] = useState<RunBlockData[]>([]);

  // 訂閱新執行結果
  useEffect(() => {
    return onExecutionComplete((result) => {
      setBlocks((prev) => {
        const newBlock: RunBlockData = {
          id: prev.length === 0 ? 1 : prev[0].id + 1,
          timestamp: Date.now(),
          result,
          expanded: true,
        };
        // 新 block 置頂；舊 block 自動收合（仿 Warp）
        return [newBlock, ...prev.map((b) => ({ ...b, expanded: false }))];
      });
    });
  }, [onExecutionComplete]);

  const toggleBlock = useCallback((id: number) => {
    setBlocks((prev) => prev.map((b) => (b.id === id ? { ...b, expanded: !b.expanded } : b)));
  }, []);

  const handleClearAll = useCallback(() => setBlocks([]), []);

  const latestBlock = blocks[0];

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
        {blocks.length > 0 && (
          <span className="rounded-pill bg-surface-2 px-2 py-0.5 text-[10px] text-text-muted">
            {blocks.length}
          </span>
        )}

        <div className="flex-1" />

        {blocks.length > 0 && (
          <button
            onClick={handleClearAll}
            className="flex h-6 items-center gap-1 rounded px-2 text-xs text-text-muted hover:text-text-primary hover:bg-surface-2 transition-colors body-ui"
            title="清空所有 block"
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
        {blocks.length === 0 ? (
          <div className="flex h-full items-center justify-center">
            <p className="text-xs text-text-muted body-reading">執行程式碼後，輸出結果會以 block 顯示在這裡。</p>
          </div>
        ) : (
          blocks.map((block) => (
            <RunBlock
              key={block.id}
              block={block}
              index={block.id}
              onToggle={() => toggleBlock(block.id)}
              onSendToChat={() => requestChatInjection(block.result)}
            />
          ))
        )}
      </div>
    </div>
  );
}

/** Collapsed status bar 內容 — 用 lucide icon 取代 emoji 符號（R8.2） */
function CollapsedStatusContent({ latest }: { latest?: RunBlockData }) {
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
