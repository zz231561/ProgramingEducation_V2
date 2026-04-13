"use client";

import { useState } from "react";
import { ChevronUp, ChevronDown } from "lucide-react";

type OutputTab = "stdout" | "stderr" | "compile";

export interface OutputData {
  stdout: string;
  stderr: string;
  compile: string;
}

interface OutputPanelProps {
  /** 輸出資料 */
  output?: OutputData;
  /** 是否收合 */
  collapsed?: boolean;
  /** 收合/展開切換 */
  onToggleCollapse?: () => void;
  /** 最近一次執行狀態摘要 */
  statusText?: string;
}

const EMPTY_OUTPUT: OutputData = { stdout: "", stderr: "", compile: "" };

const TAB_LABELS: Record<OutputTab, string> = {
  stdout: "stdout",
  stderr: "stderr",
  compile: "compile",
};

/**
 * Output Panel — stdout / stderr / compile tabs，可收合為單行 status bar
 */
export function OutputPanel({
  output = EMPTY_OUTPUT,
  collapsed = false,
  onToggleCollapse,
  statusText,
}: OutputPanelProps) {
  const [activeTab, setActiveTab] = useState<OutputTab>("stdout");

  const hasStderr = output.stderr.length > 0;
  const content = output[activeTab];

  /* 收合狀態：單行 status bar */
  if (collapsed) {
    return (
      <button
        onClick={onToggleCollapse}
        className="flex h-7 w-full items-center gap-2 border-t border-border-default bg-bg-inset px-3 text-xs text-text-secondary hover:text-text-primary transition-colors"
      >
        <ChevronUp className="size-3.5" />
        <span>{statusText ?? "Output"}</span>
      </button>
    );
  }

  return (
    <div className="flex h-full flex-col border-t border-border-default bg-bg-inset">
      {/* Tab bar */}
      <div className="flex h-8 items-center gap-1 border-b border-border-muted px-2">
        {(Object.keys(TAB_LABELS) as OutputTab[]).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`relative flex h-full items-center px-2.5 text-xs transition-colors ${
              activeTab === tab
                ? "text-text-primary"
                : "text-text-muted hover:text-text-secondary"
            }`}
          >
            {TAB_LABELS[tab]}
            {/* stderr 有內容時顯示紅點 */}
            {tab === "stderr" && hasStderr && (
              <span className="ml-1.5 size-1.5 rounded-full bg-accent-red" />
            )}
            {/* active 底線 */}
            {activeTab === tab && (
              <span className="absolute bottom-0 left-0 h-0.5 w-full bg-accent-orange" />
            )}
          </button>
        ))}

        <div className="flex-1" />

        {/* 收合按鈕 */}
        <button
          onClick={onToggleCollapse}
          className="flex size-6 items-center justify-center rounded text-text-muted hover:text-text-secondary transition-colors"
          title="收合 Output"
        >
          <ChevronDown className="size-3.5" />
        </button>
      </div>

      {/* 輸出內容 */}
      <div className="flex-1 overflow-auto p-3">
        {content ? (
          <pre
            className={`whitespace-pre-wrap font-mono text-xs leading-relaxed ${
              activeTab === "stderr" ? "text-accent-red" : "text-text-primary"
            }`}
          >
            {content}
          </pre>
        ) : (
          <p className="text-xs text-text-muted">
            {activeTab === "stdout" && "執行程式碼後，輸出結果會顯示在這裡。"}
            {activeTab === "stderr" && "標準錯誤輸出會顯示在這裡。"}
            {activeTab === "compile" && "編譯器訊息會顯示在這裡。"}
          </p>
        )}
      </div>
    </div>
  );
}
