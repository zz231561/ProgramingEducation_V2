"use client";

/**
 * 學習路徑詳細頁 — unit 列表 + 進度（roadmap 3-1c/d）。
 *
 * 3-1d 起：unit 變可點，locked 不可點。
 * 3-1c+ 簡化：Learn 頁面直接以此頁為主畫面（無 list 模式可返），故不顯示「返回」按鈕。
 */

import { PathDetail, Unit } from "@/lib/learning";

import { UnitStatusIcon, statusLabel } from "./unit-status-icon";

interface Props {
  detail: PathDetail;
  onSelectUnit: (unit: Unit) => void;
}

export function PathDetailView({ detail, onSelectUnit }: Props) {
  const total = detail.units.length;
  const completed = detail.units.filter((u) => u.status === "completed").length;
  const percent = total === 0 ? 0 : Math.round((completed / total) * 100);

  return (
    <div className="mx-auto w-full max-w-3xl space-y-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-medium text-text-primary">
          {detail.title}
        </h1>
        {detail.description && (
          <p className="text-sm text-text-secondary">{detail.description}</p>
        )}
        <div className="flex items-center gap-3 text-xs text-text-muted">
          <span>
            <span className="text-text-primary">{completed}</span> / {total} 完成
          </span>
          <span>·</span>
          <span>{percent}%</span>
        </div>
      </header>

      <ol className="space-y-2">
        {detail.units.map((unit, index) => (
          <UnitRow
            key={unit.id}
            unit={unit}
            index={index}
            onSelect={() => onSelectUnit(unit)}
          />
        ))}
      </ol>

      {total === 0 && (
        <div className="rounded-md border border-border-default bg-surface-1 px-4 py-6 text-center text-sm text-text-secondary">
          此路徑沒有任何單元。
        </div>
      )}
    </div>
  );
}

function UnitRow({
  unit,
  index,
  onSelect,
}: {
  unit: Unit;
  index: number;
  onSelect: () => void;
}) {
  const clickable = unit.status !== "locked";
  return (
    <li
      role={clickable ? "button" : undefined}
      tabIndex={clickable ? 0 : undefined}
      onClick={clickable ? onSelect : undefined}
      onKeyDown={(e) => {
        if (clickable && (e.key === "Enter" || e.key === " ")) onSelect();
      }}
      className={`flex items-start gap-3 rounded-md border border-border-default bg-surface-1 px-3 py-2.5 transition-colors ${
        clickable
          ? "cursor-pointer hover:border-border-emphasis"
          : "opacity-60"
      }`}
    >
      <UnitStatusIcon status={unit.status} className="mt-0.5 size-4" />
      <div className="min-w-0 flex-1">
        <div className="flex items-baseline gap-2">
          <span className="font-mono text-xs text-text-muted">
            {String(index + 1).padStart(2, "0")}
          </span>
          <span className="text-sm text-text-primary">
            {unit.concept_name_zh}
          </span>
          <span className="rounded-pill border border-border-default px-1.5 text-[10px] text-text-muted">
            難度 {unit.concept_difficulty}
          </span>
        </div>
        <div className="mt-0.5 text-xs text-text-muted">
          {unit.concept_tag} · {statusLabel(unit.status)}
        </div>
      </div>
    </li>
  );
}
