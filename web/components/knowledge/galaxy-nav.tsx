"use client";

/**
 * 星系切換導覽（K5 視覺調整二）— 半透明左右按鈕 + 章名指示 + 全覽。
 *
 * 疊在圖譜 canvas 上（absolute），灰階半透明符合 R8 白名單；
 * 切換/全覽動畫由父層 KnowledgeGraph 操作 cytoscape 鏡頭。
 */

import { ChevronLeft, ChevronRight, Maximize } from "lucide-react";

interface Props {
  /** 目前章節顯示名（含進度序），如「運算子（4/10）」。 */
  label: string;
  canPrev: boolean;
  canNext: boolean;
  onPrev: () => void;
  onNext: () => void;
  /** 全覽：zoom out 看到所有節點。 */
  onOverview: () => void;
}

const BUTTON_CLASS =
  "absolute top-1/2 z-10 flex size-9 -translate-y-1/2 items-center justify-center " +
  "rounded-pill border border-border-default bg-surface-1/70 text-text-secondary " +
  "transition-colors hover:bg-surface-2 hover:text-text-primary " +
  "disabled:pointer-events-none disabled:opacity-40";

export function GalaxyNav({
  label,
  canPrev,
  canNext,
  onPrev,
  onNext,
  onOverview,
}: Props) {
  return (
    <>
      <button
        type="button"
        aria-label="上一章"
        disabled={!canPrev}
        onClick={onPrev}
        className={`${BUTTON_CLASS} left-3`}
      >
        <ChevronLeft className="size-5" />
      </button>
      <button
        type="button"
        aria-label="下一章"
        disabled={!canNext}
        onClick={onNext}
        className={`${BUTTON_CLASS} right-3`}
      >
        <ChevronRight className="size-5" />
      </button>
      <div className="absolute bottom-3 left-1/2 z-10 flex -translate-x-1/2 items-center gap-2">
        <div className="rounded-pill border border-border-default bg-surface-1/70 px-3 py-1 text-xs text-text-secondary">
          {label}
        </div>
        <button
          type="button"
          aria-label="全覽所有節點"
          title="全覽"
          onClick={onOverview}
          className="flex size-7 items-center justify-center rounded-pill border border-border-default bg-surface-1/70 text-text-secondary transition-colors hover:bg-surface-2 hover:text-text-primary"
        >
          <Maximize className="size-3.5" />
        </button>
      </div>
    </>
  );
}
