"use client";

/**
 * K3 診斷模擬卡（DEV-8）— 注入指定 concept 連續答錯 N 次，立即觸發診斷。
 *
 * 注入後顯示嫌疑鏈摘要 + 知識圖譜補救高亮連結；之後在 Quiz 該概念
 * 答錯一次也會走到相同的 K3e 診斷 UI。
 */

import Link from "next/link";
import { useState } from "react";

import { type DevSimulateResult, devSimulateFailures } from "@/lib/dev-mode";

import { DevConceptSelect } from "./dev-concept-select";

export function DevDiagnosisCard() {
  const [tag, setTag] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<DevSimulateResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleInject = async () => {
    setBusy(true);
    setResult(null);
    setError(null);
    try {
      setResult(await devSimulateFailures(tag, 3));
    } catch {
      setError("注入失敗");
    } finally {
      setBusy(false);
    }
  };

  const remedialHref = result
    ? `/knowledge?remedial=${encodeURIComponent(result.suspect_tags.join(","))}`
    : "";

  return (
    <div className="rounded-md border border-border-default bg-surface-1 p-4">
      <h3 className="text-sm font-medium text-text-primary">K3 診斷模擬</h3>
      <p className="mt-1 text-xs text-text-muted">
        對指定概念注入連續答錯 3 次的作答紀錄並立即診斷；之後在 Quiz 答錯該概念也會觸發相同的診斷 UI。
      </p>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <DevConceptSelect value={tag} onChange={setTag} />
        <button
          type="button"
          onClick={handleInject}
          disabled={busy || !tag}
          className="inline-flex h-8 items-center rounded-md border border-btn-default-border bg-btn-default-bg px-3 text-sm text-text-primary hover:bg-surface-2 disabled:opacity-50"
        >
          注入 3 連錯
        </button>
      </div>
      {result && (
        <div className="mt-2 space-y-1 text-xs text-text-secondary">
          <p>
            連錯 {result.streak} 次 · 診斷{result.triggered ? "已觸發" : "未觸發"} · 嫌疑：
            {result.suspect_tags.length > 0 ? result.suspect_tags.join(", ") : "無（無前置概念）"}
          </p>
          {result.triggered && result.suspect_tags.length > 0 && (
            <Link href={remedialHref} className="text-text-link hover:underline">
              在知識圖譜檢視補救高亮
            </Link>
          )}
        </div>
      )}
      {error && <p className="mt-2 text-xs text-accent-red">{error}</p>}
    </div>
  );
}
