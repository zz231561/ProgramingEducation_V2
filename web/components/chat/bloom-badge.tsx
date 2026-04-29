"use client";

/**
 * Bloom 認知等級 pill badge — 顯示於 AI 訊息底部，告知學生本回合教學意圖。
 * 6 級配色取自 GitHub Dark accent token，符合 design-plan §2.4 統一視覺協議。
 */

type BloomMeta = { name: string; textClass: string };

const BLOOM_META: Record<number, BloomMeta> = {
  1: { name: "REMEMBER", textClass: "text-text-muted" },
  2: { name: "UNDERSTAND", textClass: "text-accent-blue" },
  3: { name: "APPLY", textClass: "text-accent-green" },
  4: { name: "ANALYZE", textClass: "text-accent-orange" },
  5: { name: "EVALUATE", textClass: "text-accent-purple" },
  6: { name: "CREATE", textClass: "text-accent-red" },
};

interface BloomBadgeProps {
  level: number;
}

export function BloomBadge({ level }: BloomBadgeProps) {
  const meta = BLOOM_META[level];
  if (!meta) return null;

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-pill border border-border-default px-2 py-0.5 text-xs font-medium body-ui ${meta.textClass}`}
      title={`本回合教學意圖：Bloom L${level} ${meta.name}`}
    >
      <span className="font-mono text-[10px] opacity-70">L{level}</span>
      <span>{meta.name}</span>
    </span>
  );
}

/** 從 evidence 物件提取 bloom_level（防禦性 parsing）。 */
export function extractBloomLevel(evidence?: Record<string, unknown>): number | null {
  if (!evidence) return null;
  const v = evidence.bloom_level;
  if (typeof v === "number" && v >= 1 && v <= 6) return v;
  if (typeof v === "string") {
    const n = parseInt(v, 10);
    if (n >= 1 && n <= 6) return n;
  }
  return null;
}
