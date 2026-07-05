"use client";

/**
 * Learn 頁面（roadmap 3-1c+ 簡化版）— 直接顯示使用者的預設學習路徑。
 *
 * 設計轉變：原 3-1c 含「list / 生成新路徑 / 刪除」介面，但 concept graph 重建為固定
 * 59 影片線性鏈後，每位學生「生成」結果完全相同，路徑列表只有 1 條，新增/刪除按鈕無意義。
 * → 改為自動 lazy seed 預設「C++ 完整課程」+ 進入頁面直接顯示 detail。
 *
 * 兩模式：
 * - detail：59 unit 列表（預設視圖）
 * - unit：點選某 unit 後的單元內容頁（4 tab）
 *
 * 後端 POST /paths / DELETE /paths / GET /paths 仍保留，供未來教師端 / 自訂路徑使用。
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { Loader2 } from "lucide-react";

import { PathDetailView } from "@/components/learn/path-detail";
import { UnitContent } from "@/components/learn/unit-content";
import { useGhostUnlock } from "@/hooks/use-dev-mode";
import { ApiRequestError } from "@/lib/api";
import {
  PathDetail,
  Unit,
  getDefaultPath,
  getPath,
  updateUnitStatus,
} from "@/lib/learning";

type View =
  | { mode: "loading" }
  | { mode: "error"; message: string }
  | { mode: "detail"; detail: PathDetail }
  | { mode: "unit"; detail: PathDetail; unitIndex: number };

export default function LearnPage() {
  const [view, setView] = useState<View>({ mode: "loading" });
  const ghostUnlock = useGhostUnlock();

  const loadDefault = useCallback(async () => {
    setView({ mode: "loading" });
    try {
      const detail = await getDefaultPath();
      setView({ mode: "detail", detail });
    } catch (e) {
      setView({ mode: "error", message: humanizeError(e) });
    }
  }, []);

  useEffect(() => {
    // 初次載入：fetch 預設路徑（loadDefault 內含 setView 是必要的初始化，
    // 屬「effect → external state」典型場景，故停用 react-hooks/set-state-in-effect）
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadDefault();
  }, [loadDefault]);

  const handleSelectUnit = useCallback((unit: Unit) => {
    setView((prev) => {
      if (prev.mode !== "detail") return prev;
      const idx = prev.detail.units.findIndex((u) => u.id === unit.id);
      if (idx < 0) return prev;
      return { mode: "unit", detail: prev.detail, unitIndex: idx };
    });
  }, []);

  const handleBackToDetail = useCallback(() => {
    setView((prev) => {
      if (prev.mode !== "unit") return prev;
      return { mode: "detail", detail: prev.detail };
    });
  }, []);

  if (view.mode === "loading") {
    return (
      <div className="flex h-full items-center justify-center text-text-secondary">
        <Loader2 className="mr-2 size-5 animate-spin" />
        載入學習路徑...
      </div>
    );
  }

  if (view.mode === "error") {
    return (
      <div className="flex h-full items-center justify-center px-6 text-center">
        <div className="max-w-md rounded-md border-l-2 border-accent-red bg-surface-2 px-4 py-3 text-sm text-accent-red">
          {view.message}
        </div>
      </div>
    );
  }

  if (view.mode === "unit") {
    return (
      <div className="h-full overflow-y-auto px-6 py-8">
        <UnitView
          detail={view.detail}
          unitIndex={view.unitIndex}
          onBackToDetail={handleBackToDetail}
          onAfterStatusChange={(updatedDetail, newIndex) =>
            setView({ mode: "unit", detail: updatedDetail, unitIndex: newIndex })
          }
          ghostUnlock={ghostUnlock}
        />
      </div>
    );
  }

  // detail 模式
  return (
    <div className="h-full overflow-y-auto px-6 py-8">
      <PathDetailView
        detail={view.detail}
        onSelectUnit={handleSelectUnit}
        ghostUnlock={ghostUnlock}
      />
    </div>
  );
}

/**
 * 學習單元 view 包裝 — 處理 status transition + path detail 同步刷新。
 *
 * status 變動後從 server 重 fetch 整個 path detail（含所有 units 狀態），
 * 確保解鎖的下一單元也即時可見。
 */
function UnitView({
  detail,
  unitIndex,
  onBackToDetail,
  onAfterStatusChange,
  ghostUnlock,
}: {
  detail: PathDetail;
  unitIndex: number;
  onBackToDetail: () => void;
  onAfterStatusChange: (detail: PathDetail, newIndex: number) => void;
  ghostUnlock?: boolean;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const unit = detail.units[unitIndex];

  const navByOffset = useMemo(() => {
    return (offset: number) => {
      const target = unitIndex + offset;
      if (target < 0 || target >= detail.units.length) return null;
      // DEV-4 幽靈解鎖：locked 也可導航（僅瀏覽，狀態轉移仍受後端限制）
      if (detail.units[target].status === "locked" && !ghostUnlock) return null;
      return () => onAfterStatusChange(detail, target);
    };
  }, [detail, unitIndex, onAfterStatusChange, ghostUnlock]);

  const refreshAndStay = useCallback(async () => {
    const fresh = await getPath(detail.id);
    onAfterStatusChange(fresh, unitIndex);
  }, [detail.id, unitIndex, onAfterStatusChange]);

  const transition = useCallback(
    async (target: "in_progress" | "completed") => {
      setBusy(true);
      setError(null);
      try {
        await updateUnitStatus(unit.id, target);
        await refreshAndStay();
      } catch (e) {
        setError(humanizeError(e));
      } finally {
        setBusy(false);
      }
    },
    [unit.id, refreshAndStay],
  );

  return (
    <>
      <UnitContent
        unit={unit}
        pathTitle={detail.title}
        totalUnits={detail.units.length}
        onBack={onBackToDetail}
        onPrev={navByOffset(-1)}
        onNext={navByOffset(1)}
        onStart={() => transition("in_progress")}
        onComplete={() => transition("completed")}
        busy={busy}
      />
      {error && (
        <div className="mx-auto mt-4 max-w-3xl rounded-md border-l-2 border-accent-red bg-surface-2 px-3 py-2 text-xs text-accent-red">
          {error}
        </div>
      )}
    </>
  );
}

function humanizeError(e: unknown): string {
  if (e instanceof ApiRequestError) {
    if (e.status === 422 && e.body.error === "LEARNING_PATH_EMPTY") {
      return e.body.message || "課程尚未建立（請聯絡管理員 seed concepts）。";
    }
    if (e.status === 404 && e.body.error === "LEARNING_PATH_NOT_FOUND") {
      return "找不到此學習路徑（可能已被刪除）。";
    }
    if (e.status === 404 && e.body.error === "LEARNING_UNIT_NOT_FOUND") {
      return "找不到此學習單元（可能已被刪除）。";
    }
    if (e.status === 422 && e.body.error === "LEARNING_UNIT_INVALID_TRANSITION") {
      return e.body.message || "目前狀態不允許此操作。";
    }
    if (e.status === 401) return "請先登入。";
    return e.body.message || "操作失敗。";
  }
  return e instanceof Error ? e.message : "未知錯誤";
}
