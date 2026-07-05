"use client";

/**
 * 熟練度編輯卡（DEV-5）— 選章節（可再選單一概念）+ confidence 滑桿覆寫。
 *
 * 概念清單來自 GET /concepts/graph（與 Knowledge 頁同源）；
 * 覆寫立即影響知識圖譜填色與出題弱項選擇，適合搭配 K5 視覺驗收。
 */

import { useEffect, useMemo, useState } from "react";

import { api } from "@/lib/api";
import { devSetMastery } from "@/lib/dev-mode";
import type { GraphData } from "@/components/knowledge/knowledge-graph-types";

const SELECT_CLASS =
  "h-8 rounded-md border border-border-default bg-surface-0 px-2 text-sm text-text-primary";
const WHOLE_CHAPTER = "__all__";

export function DevMasteryCard() {
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [category, setCategory] = useState("");
  const [tag, setTag] = useState(WHOLE_CHAPTER);
  const [percent, setPercent] = useState(80);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api<GraphData>("/concepts/graph").then(
      (data) => {
        if (cancelled) return;
        setGraph(data);
        setCategory((prev) => prev || (data.nodes[0]?.category ?? ""));
      },
      () => {
        if (!cancelled) setError("無法載入概念清單");
      },
    );
    return () => {
      cancelled = true;
    };
  }, []);

  const categories = useMemo(
    () => [...new Set(graph?.nodes.map((n) => n.category) ?? [])],
    [graph],
  );
  const concepts = useMemo(
    () => graph?.nodes.filter((n) => n.category === category) ?? [],
    [graph, category],
  );

  const handleApply = async () => {
    setBusy(true);
    setMessage(null);
    setError(null);
    try {
      const target =
        tag === WHOLE_CHAPTER ? { category } : { tags: [tag] };
      const { updated } = await devSetMastery(target, percent / 100);
      setMessage(`已更新 ${updated} 個概念的熟練度為 ${percent}%`);
    } catch {
      setError("更新失敗");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="rounded-md border border-border-default bg-surface-1 p-4">
      <h3 className="text-sm font-medium text-text-primary">熟練度編輯</h3>
      <p className="mt-1 text-xs text-text-muted">
        覆寫指定章節或單一概念的 confidence，立即反映在知識圖譜與出題弱項選擇。
      </p>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <select
          aria-label="章節"
          value={category}
          onChange={(e) => {
            setCategory(e.target.value);
            setTag(WHOLE_CHAPTER);
          }}
          className={SELECT_CLASS}
        >
          {categories.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
        <select
          aria-label="概念"
          value={tag}
          onChange={(e) => setTag(e.target.value)}
          className={`${SELECT_CLASS} max-w-64`}
        >
          <option value={WHOLE_CHAPTER}>整章（{concepts.length} 個概念）</option>
          {concepts.map((n) => (
            <option key={n.tag} value={n.tag}>{n.name_zh}</option>
          ))}
        </select>
        <label className="flex items-center gap-2 text-sm text-text-secondary">
          <input
            type="range"
            min={0}
            max={100}
            step={5}
            value={percent}
            onChange={(e) => setPercent(Number(e.target.value))}
            className="w-36 accent-btn-primary-bg"
          />
          <span className="w-10 font-mono text-text-primary">{percent}%</span>
        </label>
        <button
          type="button"
          onClick={handleApply}
          disabled={busy || !category || graph === null}
          className="inline-flex h-8 items-center rounded-md bg-btn-primary-bg px-4 text-sm font-medium text-white hover:bg-btn-primary-hover disabled:opacity-50"
        >
          套用
        </button>
      </div>
      {message && <p className="mt-2 text-xs text-text-secondary">{message}</p>}
      {error && <p className="mt-2 text-xs text-accent-red">{error}</p>}
    </div>
  );
}
