"use client";

/**
 * 教師作業詳情（5-5b-4 動線修訂）— 作業資訊 + 交件情況與批改。
 * 由作業列表點卡片進入；作業管理操作（編輯/停用/刪除）留在列表卡。
 */

import { ArrowLeft, CalendarClock } from "lucide-react";

import { formatDue } from "@/lib/assignment-format";
import { AssignmentInfo } from "@/lib/assignments";

import { SubmissionsPanel } from "./submissions-panel";

export function TeacherAssignmentDetail({
  assignment,
  className,
  onBack,
}: {
  assignment: AssignmentInfo;
  className?: string;
  onBack: () => void;
}) {
  return (
    <div className="mt-6 space-y-4">
      <button
        type="button"
        onClick={onBack}
        className="inline-flex items-center gap-1.5 text-sm text-text-secondary hover:text-text-primary"
      >
        <ArrowLeft className="size-4" />
        返回作業列表
      </button>

      <header className="space-y-1">
        <h2 className="text-lg font-medium text-text-primary">
          {assignment.title}
        </h2>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-text-muted">
          {className && <span>{className}</span>}
          <span className="flex items-center gap-1.5">
            <CalendarClock className="size-3.5" />
            截止 {formatDue(assignment.due_at)}
          </span>
        </div>
        {assignment.description && (
          <p className="whitespace-pre-wrap text-sm text-text-secondary">
            {assignment.description}
          </p>
        )}
      </header>

      <div className="rounded-md border border-border-default bg-surface-1 pb-2">
        <h3 className="border-b border-border-muted px-4 py-3 text-sm font-medium text-text-primary">
          交件情況
        </h3>
        <SubmissionsPanel assignmentId={assignment.id} />
      </div>
    </div>
  );
}
