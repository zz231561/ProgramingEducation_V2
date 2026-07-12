"use client";

/**
 * 作業管理主體（5-5a-3）— 載入班級 + 作業，渲染建立表單與作業列表。
 */

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

import { ApiRequestError } from "@/lib/api";
import { AssignmentInfo, listAssignments } from "@/lib/assignments";
import { ClassInfo, listClasses } from "@/lib/classroom";

import { AssignmentCard } from "./assignment-card";
import { CreateAssignmentForm } from "./create-assignment-form";
import { TeacherAssignmentDetail } from "./teacher-assignment-detail";

type View =
  | { mode: "loading" }
  | { mode: "error"; message: string }
  | { mode: "ready"; classes: ClassInfo[]; assignments: AssignmentInfo[] };

export function AssignmentManager() {
  const [view, setView] = useState<View>({ mode: "loading" });
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([listClasses(), listAssignments()]).then(
      ([classes, assignments]) =>
        !cancelled && setView({ mode: "ready", classes, assignments }),
      (e) =>
        !cancelled &&
        setView({
          mode: "error",
          message: e instanceof ApiRequestError ? e.body.message : "載入失敗",
        }),
    );
    return () => {
      cancelled = true;
    };
  }, []);

  const onCreated = (a: AssignmentInfo) =>
    setView((p) =>
      p.mode === "ready" ? { ...p, assignments: [a, ...p.assignments] } : p,
    );
  const onUpdated = (a: AssignmentInfo) =>
    setView((p) =>
      p.mode === "ready"
        ? { ...p, assignments: p.assignments.map((x) => (x.id === a.id ? a : x)) }
        : p,
    );
  const onDeleted = (id: string) =>
    setView((p) =>
      p.mode === "ready"
        ? { ...p, assignments: p.assignments.filter((x) => x.id !== id) }
        : p,
    );

  const nameOf = (id: string) =>
    view.mode === "ready"
      ? view.classes.find((c) => c.id === id)?.name
      : undefined;

  const selected =
    view.mode === "ready" && selectedId
      ? view.assignments.find((a) => a.id === selectedId)
      : undefined;
  if (selected)
    return (
      <TeacherAssignmentDetail
        assignment={selected}
        className={nameOf(selected.class_id)}
        onBack={() => setSelectedId(null)}
      />
    );

  return (
    <div className="mt-6 space-y-6">
      <div className="rounded-md border border-border-default bg-surface-1 p-4">
        <h2 className="text-sm font-medium text-text-primary">建立新作業</h2>
        <p className="mt-1 mb-3 text-xs text-text-muted">
          選擇班級、填寫內容與截止時間，可附加教材檔案（word / pdf / pptx / 程式碼）。
        </p>
        {view.mode === "ready" && (
          <CreateAssignmentForm classes={view.classes} onCreated={onCreated} />
        )}
      </div>

      {view.mode === "loading" && (
        <div className="flex items-center gap-2 text-sm text-text-muted">
          <Loader2 className="size-4 animate-spin" />
          載入作業…
        </div>
      )}

      {view.mode === "error" && (
        <p className="text-sm text-accent-red">{view.message}</p>
      )}

      {view.mode === "ready" && view.assignments.length === 0 && (
        <p className="text-sm text-text-muted">
          尚未建立任何作業。從上方建立第一份作業開始。
        </p>
      )}

      {view.mode === "ready" && view.assignments.length > 0 && (
        <div className="space-y-3">
          {view.assignments.map((a) => (
            <AssignmentCard
              key={a.id}
              assignment={a}
              className={nameOf(a.class_id)}
              onOpen={setSelectedId}
              onUpdated={onUpdated}
              onDeleted={onDeleted}
            />
          ))}
        </div>
      )}
    </div>
  );
}
