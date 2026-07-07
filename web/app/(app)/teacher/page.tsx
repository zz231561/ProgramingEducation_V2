"use client";

/**
 * 教師班級管理頁（roadmap 5-1c-1；導航改造後為 /teacher 的班級分頁）。
 * 角色 gating 在 teacher/layout.tsx。
 */

import { School } from "lucide-react";

import { ClassManager } from "@/components/teacher/class-manager";

export default function TeacherClassesPage() {
  return (
    <>
      <div className="flex items-center gap-2">
        <School className="size-5 text-text-secondary" />
        <h1 className="text-xl font-medium text-text-primary">班級管理</h1>
      </div>
      <ClassManager />
    </>
  );
}
