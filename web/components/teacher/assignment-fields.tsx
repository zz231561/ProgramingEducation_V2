"use client";

/**
 * 作業內容欄位（5-5a-3）— 標題 / 內容 / 截止時間，建立與編輯共用。
 * datetime-local 與後端 ISO 之間的轉換 helper 一併導出。
 */

import { CalendarClock } from "lucide-react";

export interface AssignmentFieldValues {
  title: string;
  description: string;
  dueLocal: string; // datetime-local 值（本地時間，可空）
}

/** ISO（UTC）→ datetime-local 輸入值（本地時區）。 */
export function isoToLocalInput(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(
    d.getHours(),
  )}:${pad(d.getMinutes())}`;
}

/** datetime-local 值 → ISO（UTC）；空值回 null。 */
export function localInputToIso(local: string): string | null {
  if (!local) return null;
  const d = new Date(local);
  return Number.isNaN(d.getTime()) ? null : d.toISOString();
}

const inputCls =
  "h-8 w-full rounded-md border border-border-default bg-bg-canvas px-3 text-sm text-text-primary placeholder:text-text-muted focus:border-accent-blue focus:outline-none";

export function AssignmentFields({
  values,
  onChange,
}: {
  values: AssignmentFieldValues;
  onChange: (patch: Partial<AssignmentFieldValues>) => void;
}) {
  return (
    <div className="space-y-3">
      <input
        value={values.title}
        onChange={(e) => onChange({ title: e.target.value })}
        placeholder="作業標題"
        maxLength={200}
        className={inputCls}
      />
      <textarea
        value={values.description}
        onChange={(e) => onChange({ description: e.target.value })}
        placeholder="作業內容說明（可貼上題目、繳交要求…）"
        rows={4}
        className="w-full resize-y rounded-md border border-border-default bg-bg-canvas px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-accent-blue focus:outline-none"
      />
      <label className="flex flex-wrap items-center gap-2 text-xs text-text-muted">
        <CalendarClock className="size-3.5" />
        截止時間（可留空）
        <input
          type="datetime-local"
          value={values.dueLocal}
          onChange={(e) => onChange({ dueLocal: e.target.value })}
          className="h-8 rounded-md border border-border-default bg-bg-canvas px-2 text-sm text-text-primary focus:border-accent-blue focus:outline-none [color-scheme:dark]"
        />
      </label>
    </div>
  );
}
