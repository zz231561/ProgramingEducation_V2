"use client";

/**
 * Workspace 反思側邊欄（Phase 2-5d）。
 *
 * 持續顯示當前作答的反思計畫，學生可隨時對照、編輯：
 * - planned_steps、expected_concepts、problem_understanding
 * - 編輯後 PATCH /reflection/{id}（觸發後端重新評分 + is_modified=true）
 *
 * 顯示模式 ↔ 編輯模式切換；無 active reflection 時顯示空狀態提示。
 *
 * 拆檔（控制 250 行硬性線）：
 * - reflection-sidebar-view.tsx — 顯示模式
 * - reflection-sidebar-edit.tsx — 編輯模式
 * - use-active-reflection.ts — sessionStorage + GET 訂閱 hook
 */

import { useCallback, useState } from "react";
import { Loader2, X } from "lucide-react";

import { Reflection } from "@/lib/reflection";
import { ReflectionSidebarEdit } from "./reflection-sidebar-edit";
import { ReflectionSidebarView } from "./reflection-sidebar-view";
import { useActiveReflection } from "./use-active-reflection";

interface ReflectionSidebarProps {
  /** 收合時呼叫（caller 控制 layout）。 */
  onCollapse: () => void;
}

export function ReflectionSidebar({ onCollapse }: ReflectionSidebarProps) {
  const { reflection, loading, error, clear, setReflection } = useActiveReflection();
  const [editing, setEditing] = useState(false);

  const handleSaved = useCallback(
    (updated: Reflection) => {
      setReflection(updated);
      setEditing(false);
    },
    [setReflection],
  );

  return (
    <aside className="flex h-full flex-col border-r border-border-default bg-surface-1">
      <Header onCollapse={onCollapse} />
      <div className="min-h-0 flex-1 overflow-y-auto">
        {loading && (
          <CenteredHint icon={<Loader2 className="size-4 animate-spin" />} text="載入反思中..." />
        )}
        {!loading && error && <CenteredHint text={error} tone="error" />}
        {!loading && !error && !reflection && <EmptyState />}
        {!loading && !error && reflection && !editing && (
          <ReflectionSidebarView
            reflection={reflection}
            onEdit={() => setEditing(true)}
            onClear={clear}
          />
        )}
        {!loading && !error && reflection && editing && (
          <ReflectionSidebarEdit
            reflection={reflection}
            onCancel={() => setEditing(false)}
            onSaved={handleSaved}
          />
        )}
      </div>
    </aside>
  );
}

function Header({ onCollapse }: { onCollapse: () => void }) {
  return (
    <div className="flex items-center justify-between border-b border-border-default px-3 py-2">
      <span className="text-sm font-medium text-text-primary">反思計畫</span>
      <button
        type="button"
        onClick={onCollapse}
        className="flex size-6 items-center justify-center rounded-md text-text-muted hover:bg-bg-subtle hover:text-text-primary"
        aria-label="收合反思側邊欄"
      >
        <X className="size-3.5" />
      </button>
    </div>
  );
}

function CenteredHint({
  icon,
  text,
  tone = "default",
}: {
  icon?: React.ReactNode;
  text: string;
  tone?: "default" | "error";
}) {
  const color = tone === "error" ? "text-accent-red" : "text-text-muted";
  return (
    <div className={`flex h-full flex-col items-center justify-center gap-2 px-4 text-xs ${color}`}>
      {icon}
      <p className="text-center">{text}</p>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-2 px-4 text-center text-xs text-text-muted">
      <p className="font-medium text-text-secondary">尚無進行中的反思</p>
      <p className="leading-5">
        從 Quiz 或 Learn 頁開題並完成反思後，計畫會在此處顯示。
      </p>
    </div>
  );
}
