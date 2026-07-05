"use client";

/**
 * 根源弱點診斷區塊（roadmap K3e）— 答錯時掛在 ResultView 下方。
 *
 * 自動呼叫 GET /concepts/{tag}/diagnosis：未觸發（triggered=false）或請求失敗
 * 一律不渲染（後端設計即供前端隱藏入口）。觸發時呈現嫌疑鏈 + 每節點微測驗入口
 * + 補救路徑開放（K4c）+ 知識圖譜高亮跳轉（K5c ?remedial=）。
 */

import Link from "next/link";
import { useEffect, useState } from "react";
import { GitBranch, Loader2, Play } from "lucide-react";

import {
  DiagnosisResponse,
  RemediateResponse,
  Suspect,
  getDiagnosis,
  remediate,
} from "@/lib/diagnosis";
import { Question, getQuestionById } from "@/lib/quiz";

interface Props {
  conceptTag: string;
  /** 微測驗入口：取到診斷題後交給 QuizRunner 直接進入作答。 */
  onStartQuestion?: (question: Question) => void;
}

export function DiagnosisSection({ conceptTag, onStartQuestion }: Props) {
  const [diagnosis, setDiagnosis] = useState<DiagnosisResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    getDiagnosis(conceptTag)
      .then((d) => {
        if (!cancelled && d.triggered) setDiagnosis(d);
      })
      .catch((e) => console.warn("診斷查詢失敗，隱藏入口", e));
    return () => {
      cancelled = true;
    };
  }, [conceptTag]);

  if (!diagnosis) return null;

  const remedialHref = `/knowledge?remedial=${encodeURIComponent(
    diagnosis.suspects.map((s) => s.tag).join(","),
  )}`;

  return (
    <section className="rounded-md border border-border-default bg-surface-1 p-4">
      <div className="flex items-start gap-3">
        <GitBranch className="mt-0.5 size-5 shrink-0 text-accent-orange" />
        <div>
          <h3 className="text-sm font-medium text-text-primary">找出根本原因</h3>
          <p className="mt-1 text-sm text-text-secondary">
            這個概念你最近已連續答錯 {diagnosis.recent_failure_streak} 次，
            問題可能出在以下前置概念：
          </p>
        </div>
      </div>

      <ul className="mt-3 divide-y divide-border-muted border-t border-border-muted">
        {diagnosis.suspects.map((s) => (
          <SuspectRow
            key={s.tag}
            suspect={s}
            onStartQuestion={onStartQuestion}
          />
        ))}
      </ul>

      <RemediateFooter targetTag={conceptTag} remedialHref={remedialHref} />
    </section>
  );
}

function SuspectRow({
  suspect,
  onStartQuestion,
}: {
  suspect: Suspect;
  onStartQuestion?: (q: Question) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startMicroQuiz = async () => {
    if (!suspect.question_id || !onStartQuestion || busy) return;
    setBusy(true);
    setError(null);
    try {
      onStartQuestion(await getQuestionById(suspect.question_id));
    } catch {
      setError("題目載入失敗（可能已被移除）");
      setBusy(false);
    }
  };

  return (
    <li className="flex items-center gap-3 py-2.5">
      <span className="shrink-0 rounded-pill border border-border-default px-1.5 text-xs text-text-muted">
        往前 {suspect.depth} 層
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm text-text-primary">
          {suspect.name_zh}
          <span className="ml-2 font-mono text-xs text-text-muted">
            {suspect.tag}
          </span>
        </p>
        <p className="text-xs text-text-secondary">
          {suspect.confidence === null ? (
            <span className="text-accent-red">未學過（盲區）</span>
          ) : (
            <>熟練度 {Math.round(suspect.confidence * 100)}%</>
          )}
          {error && <span className="ml-2 text-accent-red">{error}</span>}
        </p>
      </div>
      {suspect.question_id && onStartQuestion && (
        <button
          type="button"
          onClick={startMicroQuiz}
          disabled={busy}
          className="inline-flex h-8 shrink-0 items-center gap-1.5 rounded-md border border-btn-default-border bg-btn-default-bg px-3 text-xs text-text-primary hover:bg-surface-2 disabled:opacity-50"
        >
          {busy ? (
            <Loader2 className="size-3.5 animate-spin" />
          ) : (
            <Play className="size-3.5" />
          )}
          微測驗
        </button>
      )}
    </li>
  );
}

function RemediateFooter({
  targetTag,
  remedialHref,
}: {
  targetTag: string;
  remedialHref: string;
}) {
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<RemediateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRemediate = async () => {
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      setResult(await remediate(targetTag));
    } catch {
      setError("補救路徑開放失敗，請稍後再試");
    } finally {
      setBusy(false);
    }
  };

  if (result) {
    return (
      <div className="mt-3 border-t border-border-muted pt-3 text-sm text-text-secondary">
        已重新開放 {result.remedial_units.length} 個補救單元，
        依建議順序：
        {result.remedial_units.map((u) => u.name_zh).join(" → ")}
        <span className="ml-2">
          <Link href="/learn" className="text-text-link hover:underline">
            前往 Learn
          </Link>
        </span>
      </div>
    );
  }

  return (
    <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-border-muted pt-3">
      <button
        type="button"
        onClick={handleRemediate}
        disabled={busy}
        className="inline-flex h-8 items-center gap-1.5 rounded-md border border-btn-default-border bg-btn-default-bg px-3 text-xs text-text-primary hover:bg-surface-2 disabled:opacity-50"
      >
        {busy && <Loader2 className="size-3.5 animate-spin" />}
        開放補救路徑
      </button>
      <Link
        href={remedialHref}
        className="text-xs text-text-link hover:underline"
      >
        在知識圖譜查看嫌疑鏈
      </Link>
      {error && <span className="text-xs text-accent-red">{error}</span>}
    </div>
  );
}
