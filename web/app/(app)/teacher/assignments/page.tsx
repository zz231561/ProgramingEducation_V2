"use client";

/**
 * 教師作業頁（roadmap 5-5a-3；/teacher/assignments）。
 * 角色 gating 在 teacher/layout.tsx。
 */

import { ClipboardList } from "lucide-react";

import { AssignmentManager } from "@/components/teacher/assignment-manager";

export default function TeacherAssignmentsPage() {
  return (
    <>
      <div className="flex items-center gap-2">
        <ClipboardList className="size-5 text-text-secondary" />
        <h1 className="text-xl font-medium text-text-primary">作業</h1>
      </div>
      <AssignmentManager />
    </>
  );
}
