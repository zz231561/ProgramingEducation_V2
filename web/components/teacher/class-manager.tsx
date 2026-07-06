"use client";

/**
 * 班級管理主體（5-1c-1）— 建立表單 + 班級列表狀態管理。
 */

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

import { ApiRequestError } from "@/lib/api";
import { ClassInfo, listClasses } from "@/lib/classroom";

import { ClassCard } from "./class-card";
import { CreateClassForm } from "./create-class-form";

type View =
  | { mode: "loading" }
  | { mode: "error"; message: string }
  | { mode: "ready"; classes: ClassInfo[] };

export function ClassManager() {
  const [view, setView] = useState<View>({ mode: "loading" });

  useEffect(() => {
    let cancelled = false;
    listClasses().then(
      (classes) => {
        if (!cancelled) setView({ mode: "ready", classes });
      },
      (e) => {
        if (!cancelled) {
          const msg =
            e instanceof ApiRequestError ? e.body.message : "載入班級失敗";
          setView({ mode: "error", message: msg });
        }
      },
    );
    return () => {
      cancelled = true;
    };
  }, []);

  const handleCreated = (klass: ClassInfo) => {
    setView((prev) =>
      prev.mode === "ready"
        ? { mode: "ready", classes: [klass, ...prev.classes] }
        : prev,
    );
  };

  const handleUpdated = (updated: ClassInfo) => {
    setView((prev) =>
      prev.mode === "ready"
        ? {
            mode: "ready",
            classes: prev.classes.map((c) =>
              c.id === updated.id ? updated : c,
            ),
          }
        : prev,
    );
  };

  return (
    <div className="mt-6 space-y-6">
      <div className="rounded-md border border-border-default bg-surface-1 p-4">
        <h2 className="text-sm font-medium text-text-primary">建立新班級</h2>
        <p className="mt-1 mb-3 text-xs text-text-muted">
          建立後系統會產生 6 位數字邀請碼，分享給學生即可加入。
        </p>
        <CreateClassForm onCreated={handleCreated} />
      </div>

      {view.mode === "loading" && (
        <div className="flex items-center gap-2 text-sm text-text-muted">
          <Loader2 className="size-4 animate-spin" />
          載入班級…
        </div>
      )}

      {view.mode === "error" && (
        <p className="text-sm text-accent-red">{view.message}</p>
      )}

      {view.mode === "ready" && view.classes.length === 0 && (
        <p className="text-sm text-text-muted">
          尚未建立任何班級。從上方建立第一個班級開始。
        </p>
      )}

      {view.mode === "ready" && view.classes.length > 0 && (
        <div className="space-y-3">
          {view.classes.map((c) => (
            <ClassCard key={c.id} klass={c} onUpdated={handleUpdated} />
          ))}
        </div>
      )}
    </div>
  );
}
