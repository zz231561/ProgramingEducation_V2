"use client";

/**
 * Concept Detail Panel — 點節點後右側顯示的詳情面板（roadmap 2-2d）。
 *
 * 串接 GET /concepts/{tag}，渲染：基本資訊 + 先修概念 + 進階概念。
 * 點鄰居可切換到該 concept（保持 panel 開啟，graph 不重新整理）。
 */

import { X } from "lucide-react";
import { useEffect, useState } from "react";

import { ApiRequestError, api } from "@/lib/api";

import {
  CATEGORY_COLOR,
  DEFAULT_CATEGORY_COLOR,
} from "./knowledge-graph-style";
import type {
  ConceptDetailData,
  MasteryEntry,
  NeighborRecord,
} from "./knowledge-graph-types";
import { getMasteryBand } from "./knowledge-graph-types";

const MASTERY_BAND_LABEL: Record<string, { label: string; color: string }> = {
  mastered: { label: "已掌握", color: "#3FB950" },
  learning: { label: "學習中", color: "#D29922" },
  struggling: { label: "需加強", color: "#F85149" },
  unseen: { label: "尚未互動", color: "#6E7681" },
};

const EDGE_TYPE_LABEL: Record<string, string> = {
  prerequisite: "先修",
  contains: "包含",
  specialization: "特化",
  related: "相關",
};

export type ConceptDetailPanelProps = {
  tag: string;
  /** 此 tag 對應的學生精熟度；undefined 表示尚未互動 */
  mastery?: MasteryEntry;
  onClose: () => void;
  onSelectTag: (tag: string) => void;
};

export function ConceptDetailPanel({
  tag,
  mastery,
  onClose,
  onSelectTag,
}: ConceptDetailPanelProps) {
  const [data, setData] = useState<ConceptDetailData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setData(null);
    setError(null);
    (async () => {
      try {
        const result = await api<ConceptDetailData>(
          `/concepts/${encodeURIComponent(tag)}`,
        );
        if (!cancelled) setData(result);
      } catch (e) {
        if (cancelled) return;
        const msg =
          e instanceof ApiRequestError ? e.body.message : "載入詳情失敗";
        setError(msg);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [tag]);

  return (
    <aside className="flex h-full w-[320px] flex-col border-l border-border-default bg-surface-1">
      <PanelHeader onClose={onClose} />
      {error ? (
        <p className="px-4 py-6 text-sm text-text-secondary">{error}</p>
      ) : !data ? (
        <p className="px-4 py-6 text-sm text-text-secondary">載入中…</p>
      ) : (
        <PanelBody data={data} mastery={mastery} onSelectTag={onSelectTag} />
      )}
    </aside>
  );
}

function PanelHeader({ onClose }: { onClose: () => void }) {
  return (
    <div className="flex items-center justify-between border-b border-border-default px-4 py-3">
      <span className="text-xs font-medium uppercase tracking-wide text-text-muted">
        Concept
      </span>
      <button
        type="button"
        onClick={onClose}
        className="rounded p-1 text-text-secondary transition-colors hover:bg-surface-2 hover:text-text-primary"
        aria-label="關閉詳情面板"
      >
        <X className="size-4" />
      </button>
    </div>
  );
}

function PanelBody({
  data,
  mastery,
  onSelectTag,
}: {
  data: ConceptDetailData;
  mastery?: MasteryEntry;
  onSelectTag: (tag: string) => void;
}) {
  const { concept, neighbors } = data;
  const incoming = neighbors.filter((n) => n.direction === "incoming");
  const outgoing = neighbors.filter((n) => n.direction === "outgoing");
  const color = CATEGORY_COLOR[concept.category] ?? DEFAULT_CATEGORY_COLOR;

  return (
    <div className="flex-1 overflow-auto px-4 py-4">
      <h2 className="text-base font-medium text-text-primary">{concept.name_zh}</h2>
      <p className="mt-0.5 font-mono text-xs text-text-muted">{concept.tag}</p>

      <div className="mt-3 flex items-center gap-2">
        <span
          className="rounded-pill px-2 py-0.5 text-xs font-medium text-bg-canvas"
          style={{ backgroundColor: color }}
        >
          {concept.category}
        </span>
        <DifficultyDots level={concept.difficulty_level} />
      </div>

      <p className="mt-1 text-xs text-text-secondary">{concept.name_en}</p>

      <MasterySection mastery={mastery} />

      <section className="mt-5">
        <h3 className="text-xs font-medium uppercase tracking-wide text-text-muted">
          說明
        </h3>
        <p className="mt-2 text-sm leading-relaxed text-text-primary">
          {concept.description || "（尚無說明）"}
        </p>
      </section>

      <NeighborSection
        title="先修概念"
        emptyHint="無 prerequisite / contains 邊指向此概念"
        items={incoming}
        onSelectTag={onSelectTag}
      />
      <NeighborSection
        title="進階概念"
        emptyHint="無從此概念出發的邊"
        items={outgoing}
        onSelectTag={onSelectTag}
      />
    </div>
  );
}

function MasterySection({ mastery }: { mastery?: MasteryEntry }) {
  const band = getMasteryBand(mastery?.confidence);
  const { label, color } = MASTERY_BAND_LABEL[band];
  return (
    <section className="mt-5">
      <h3 className="text-xs font-medium uppercase tracking-wide text-text-muted">
        我的精熟度
      </h3>
      <div className="mt-2 flex items-center gap-2">
        <span
          className="inline-flex size-2 rounded-full"
          style={{ backgroundColor: color }}
          aria-hidden
        />
        <span className="text-sm text-text-primary">{label}</span>
        {mastery ? (
          <span className="text-xs text-text-muted">
            {Math.round(mastery.confidence * 100)}% · {mastery.exposure_count} 次互動
          </span>
        ) : null}
      </div>
    </section>
  );
}


function DifficultyDots({ level }: { level: number }) {
  return (
    <span className="flex items-center gap-0.5" aria-label={`難度 ${level}/5`}>
      {[1, 2, 3, 4, 5].map((i) => (
        <span
          key={i}
          className={`size-1.5 rounded-full ${
            i <= level ? "bg-text-primary" : "bg-border-default"
          }`}
        />
      ))}
    </span>
  );
}

function NeighborSection({
  title,
  emptyHint,
  items,
  onSelectTag,
}: {
  title: string;
  emptyHint: string;
  items: NeighborRecord[];
  onSelectTag: (tag: string) => void;
}) {
  return (
    <section className="mt-5">
      <h3 className="text-xs font-medium uppercase tracking-wide text-text-muted">
        {title}
      </h3>
      {items.length === 0 ? (
        <p className="mt-2 text-xs text-text-muted">{emptyHint}</p>
      ) : (
        <ul className="mt-2 space-y-1">
          {items.map((n) => (
            <li key={n.edge.id}>
              <button
                type="button"
                onClick={() => onSelectTag(n.concept.tag)}
                className="flex w-full items-center justify-between rounded border border-border-default bg-surface-2 px-2 py-1.5 text-left text-sm text-text-primary transition-colors hover:border-border-emphasis"
              >
                <span>{n.concept.name_zh}</span>
                <span className="font-mono text-[10px] uppercase text-text-muted">
                  {EDGE_TYPE_LABEL[n.edge.edge_type] ?? n.edge.edge_type}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
