"use client";

/**
 * Learn 頁面（roadmap 3-1c）— 學習路徑視覺化 + 進度條。
 *
 * 三模式：
 * - list：所有路徑卡片 + 「+ 生成新路徑」按鈕
 * - detail：點選某條後顯示 unit 列表
 * - generating：modal 表單填寫並送出
 *
 * 點擊 unit 進入學習單元頁屬於 3-1d 範圍。
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { BookOpen, Loader2, Plus } from "lucide-react";

import { GeneratePathDialog } from "@/components/learn/generate-path-dialog";
import { PathCard } from "@/components/learn/path-card";
import { PathDetailView } from "@/components/learn/path-detail";
import { UnitContent } from "@/components/learn/unit-content";
import { ApiRequestError } from "@/lib/api";
import {
  GeneratePathPayload,
  PathDetail,
  PathSummary,
  Unit,
  deletePath,
  generatePath,
  getPath,
  listPaths,
  updateUnitStatus,
} from "@/lib/learning";

type View =
  | { mode: "list" }
  | { mode: "detail"; detail: PathDetail }
  | { mode: "loading-detail" }
  | { mode: "unit"; detail: PathDetail; unitIndex: number };

export default function LearnPage() {
  const [paths, setPaths] = useState<PathSummary[] | null>(null);
  const [listError, setListError] = useState<string | null>(null);
  const [view, setView] = useState<View>({ mode: "list" });
  const [dialogOpen, setDialogOpen] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [generateError, setGenerateError] = useState<string | null>(null);

  const refreshList = useCallback(async () => {
    setListError(null);
    try {
      setPaths(await listPaths());
    } catch (e) {
      setListError(humanizeError(e));
    }
  }, []);

  useEffect(() => {
    refreshList();
  }, [refreshList]);

  const handleSelect = useCallback(async (pathId: string) => {
    setView({ mode: "loading-detail" });
    try {
      const detail = await getPath(pathId);
      setView({ mode: "detail", detail });
    } catch (e) {
      setView({ mode: "list" });
      setListError(humanizeError(e));
    }
  }, []);

  const handleBack = useCallback(() => {
    setView({ mode: "list" });
    refreshList();
  }, [refreshList]);

  const handleSelectUnit = useCallback((unit: Unit) => {
    setView((prev) => {
      if (prev.mode !== "detail") return prev;
      const idx = prev.detail.units.findIndex((u) => u.id === unit.id);
      if (idx < 0) return prev;
      return { mode: "unit", detail: prev.detail, unitIndex: idx };
    });
  }, []);

  const handleBackToDetail = useCallback(async () => {
    setView((prev) => {
      if (prev.mode !== "unit") return prev;
      return { mode: "detail", detail: prev.detail };
    });
  }, []);

  const handleDelete = useCallback(
    async (pathId: string) => {
      if (!window.confirm("確定要刪除這條學習路徑嗎？此操作不可復原。")) return;
      try {
        await deletePath(pathId);
        await refreshList();
      } catch (e) {
        setListError(humanizeError(e));
      }
    },
    [refreshList],
  );

  const handleGenerate = useCallback(
    async (payload: GeneratePathPayload) => {
      setGenerating(true);
      setGenerateError(null);
      try {
        const detail = await generatePath(payload);
        setDialogOpen(false);
        setView({ mode: "detail", detail });
        await refreshList();
      } catch (e) {
        setGenerateError(humanizeError(e));
      } finally {
        setGenerating(false);
      }
    },
    [refreshList],
  );

  if (view.mode === "loading-detail") {
    return (
      <div className="flex h-full items-center justify-center text-text-secondary">
        <Loader2 className="mr-2 size-5 animate-spin" />
        載入路徑...
      </div>
    );
  }

  if (view.mode === "detail") {
    return (
      <div className="h-full overflow-y-auto px-6 py-8">
        <PathDetailView
          detail={view.detail}
          onBack={handleBack}
          onSelectUnit={handleSelectUnit}
        />
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
        />
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto px-6 py-8">
      <div className="mx-auto w-full max-w-3xl space-y-6">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-medium text-text-primary">
              學習路徑
            </h1>
            <p className="mt-1 text-sm text-text-secondary">
              依概念依賴關係 + 你的精熟度動態安排的學習順序
            </p>
          </div>
          <button
            type="button"
            onClick={() => {
              setGenerateError(null);
              setDialogOpen(true);
            }}
            className="inline-flex h-8 items-center gap-1.5 rounded-md bg-btn-primary-bg px-3 text-sm font-medium text-white hover:bg-btn-primary-hover"
          >
            <Plus className="size-4" />
            生成新路徑
          </button>
        </header>

        {listError && (
          <div className="rounded-md border-l-2 border-accent-red bg-surface-2 px-3 py-2 text-xs text-accent-red">
            {listError}
          </div>
        )}

        {paths === null ? (
          <div className="flex items-center justify-center py-12 text-text-secondary">
            <Loader2 className="mr-2 size-4 animate-spin" />
            載入中...
          </div>
        ) : paths.length === 0 ? (
          <EmptyState onGenerate={() => setDialogOpen(true)} />
        ) : (
          <div className="space-y-3">
            {paths.map((p) => (
              <PathCard
                key={p.id}
                summary={p}
                onSelect={handleSelect}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}
      </div>

      <GeneratePathDialog
        open={dialogOpen}
        loading={generating}
        error={generateError}
        onClose={() => setDialogOpen(false)}
        onSubmit={handleGenerate}
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
}: {
  detail: PathDetail;
  unitIndex: number;
  onBackToDetail: () => void;
  onAfterStatusChange: (detail: PathDetail, newIndex: number) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const unit = detail.units[unitIndex];

  const navByOffset = useMemo(() => {
    return (offset: number) => {
      const target = unitIndex + offset;
      if (target < 0 || target >= detail.units.length) return null;
      // 鎖定單元不可導航
      if (detail.units[target].status === "locked") return null;
      return () => onAfterStatusChange(detail, target);
    };
  }, [detail, unitIndex, onAfterStatusChange]);

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

function EmptyState({ onGenerate }: { onGenerate: () => void }) {
  return (
    <div className="rounded-md border border-border-default bg-surface-1 px-6 py-12 text-center">
      <BookOpen className="mx-auto size-10 text-text-muted/60" />
      <p className="mt-4 text-sm text-text-primary">尚未建立學習路徑</p>
      <p className="mt-1 text-xs text-text-secondary">
        點擊上方「生成新路徑」依你目前的精熟度建立第一條
      </p>
      <button
        type="button"
        onClick={onGenerate}
        className="mt-4 inline-flex h-8 items-center gap-1.5 rounded-md border border-btn-default-border bg-btn-default-bg px-3 text-sm text-text-primary hover:bg-surface-2"
      >
        <Plus className="size-4" />
        立即生成
      </button>
    </div>
  );
}

function humanizeError(e: unknown): string {
  if (e instanceof ApiRequestError) {
    if (e.status === 422 && e.body.error === "LEARNING_PATH_EMPTY") {
      return e.body.message || "找不到符合條件的概念，請先建立或選擇其他分類。";
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
