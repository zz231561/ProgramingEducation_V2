"use client";

/**
 * 學生作業頁（5-5b-3）— /assignments。教師以 /teacher/assignments 管理。
 */

import { StudentAssignments } from "@/components/assignments/student-assignments";

export default function AssignmentsPage() {
  return (
    <div className="h-full overflow-y-auto px-6 py-8">
      <StudentAssignments />
    </div>
  );
}
