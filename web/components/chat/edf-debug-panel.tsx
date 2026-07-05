"use client";

/**
 * EDF Debug 面板（DEV-7）— dev 帳號在 AI 訊息下方展開中間層觀測。
 *
 * 顯示 Evidence（錯誤分類 / Bloom / concept tags）、Decision（hint level /
 * 策略指令）、RAG 命中（cosine 分數 + 片段）、K-Graph 鷹架 block。
 * 灰階 + JetBrains Mono，摺疊預設關閉不干擾一般對話。
 */

type RagChunk = { score: number; doc_id: string | null; preview: string };

export function EdfDebugPanel({ debug }: { debug: Record<string, unknown> }) {
  const evidence = (debug.evidence ?? {}) as Record<string, unknown>;
  const strategy = (debug.strategy ?? {}) as Record<string, unknown>;
  const ragChunks = (debug.rag_chunks ?? []) as RagChunk[];
  const kgraphBlock = (debug.kgraph_block ?? "") as string;

  return (
    <details className="mt-2 rounded-md border border-border-muted bg-surface-0 font-mono text-[11px] text-text-secondary">
      <summary className="cursor-pointer select-none px-2 py-1 text-text-muted hover:text-text-primary">
        EDF Debug
      </summary>
      <div className="space-y-2 border-t border-border-muted px-2 py-2">
        <Row label="evidence">
          error={String(evidence.error_type)} · bloom={String(evidence.bloom_level)} ·
          tags={(evidence.concept_tags as string[] | undefined)?.join(", ") || "—"}
        </Row>
        <Row label="strategy">
          hint={String(strategy.hint_level)} · code_snippet=
          {String(strategy.allow_code_snippet)}
          <div className="mt-0.5 whitespace-pre-wrap text-text-muted">
            {String(strategy.instruction ?? "")}
          </div>
        </Row>
        <Row label={`rag (${ragChunks.length})`}>
          {ragChunks.length === 0 ? (
            <span className="text-text-muted">無命中（低於 RAG_MIN_SCORE 或未檢索）</span>
          ) : (
            ragChunks.map((c, i) => (
              <div key={i} className="mt-0.5">
                <span className="text-text-primary">{c.score.toFixed(3)}</span>{" "}
                <span className="text-text-muted">{c.preview}</span>
              </div>
            ))
          )}
        </Row>
        {kgraphBlock && (
          <Row label="kgraph">
            <pre className="mt-0.5 whitespace-pre-wrap text-text-muted">
              {kgraphBlock}
            </pre>
          </Row>
        )}
      </div>
    </details>
  );
}

function Row({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <span className="uppercase tracking-wide text-text-muted">{label}</span>
      <div className="mt-0.5">{children}</div>
    </div>
  );
}
