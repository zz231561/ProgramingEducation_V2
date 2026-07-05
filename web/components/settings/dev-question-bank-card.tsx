"use client";

/**
 * 題庫檢視卡（DEV-9）— 列出指定 concept 的題庫題目 + 直接作答。
 *
 * 「作答」導向 /quiz?question=<id>（QuizRunner 深連結直接進入該題），
 * 供 6-4a 出題品質抽查使用。
 */

import Link from "next/link";
import { useState } from "react";

import { type DevBankQuestion, devListQuestions } from "@/lib/dev-mode";

import { DevConceptSelect } from "./dev-concept-select";

export function DevQuestionBankCard() {
  const [tag, setTag] = useState("");
  const [busy, setBusy] = useState(false);
  const [questions, setQuestions] = useState<DevBankQuestion[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleLoad = async () => {
    setBusy(true);
    setError(null);
    try {
      setQuestions((await devListQuestions(tag)).questions);
    } catch {
      setError("載入失敗");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="rounded-md border border-border-default bg-surface-1 p-4">
      <h3 className="text-sm font-medium text-text-primary">題庫檢視</h3>
      <p className="mt-1 text-xs text-text-muted">
        列出指定概念的題庫題目（含 validate 狀態），可直接跳轉作答抽查品質。
      </p>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <DevConceptSelect value={tag} onChange={setTag} />
        <button
          type="button"
          onClick={handleLoad}
          disabled={busy || !tag}
          className="inline-flex h-8 items-center rounded-md border border-btn-default-border bg-btn-default-bg px-3 text-sm text-text-primary hover:bg-surface-2 disabled:opacity-50"
        >
          載入題目
        </button>
      </div>
      {questions !== null && (
        <ul className="mt-3 space-y-1.5">
          {questions.length === 0 && (
            <li className="text-xs text-text-muted">此概念題庫無題目。</li>
          )}
          {questions.map((q) => (
            <li
              key={q.id}
              className="flex items-center gap-2 rounded-md border border-border-muted bg-surface-0 px-2 py-1.5 text-xs"
            >
              <span className="shrink-0 rounded-pill border border-border-default px-1.5 text-[10px] text-text-muted">
                {q.type} · B{q.bloom_level} · D{q.difficulty}
              </span>
              <span
                className={`shrink-0 text-[10px] ${q.validated ? "text-accent-green" : "text-text-muted"}`}
              >
                {q.validated ? "validated" : "unvalidated"}
              </span>
              <span className="min-w-0 flex-1 truncate text-text-secondary">
                {q.stem || "（無題幹）"}
              </span>
              <Link
                href={`/quiz?question=${q.id}`}
                className="shrink-0 text-text-link hover:underline"
              >
                作答
              </Link>
            </li>
          ))}
        </ul>
      )}
      {error && <p className="mt-2 text-xs text-accent-red">{error}</p>}
    </div>
  );
}
