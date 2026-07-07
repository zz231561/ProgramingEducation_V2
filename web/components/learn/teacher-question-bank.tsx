"use client";

/**
 * 教師題庫檢視（5-6c）— 列出該單元 concept 的題目；解答預設隱藏 + 一鍵切換，
 * 避免示範時對學生露出正解。
 */

import { useEffect, useState } from "react";
import { Check, Eye, EyeOff, Loader2 } from "lucide-react";

import { ApiRequestError } from "@/lib/api";
import { TeacherQuestion, listTeacherQuestions } from "@/lib/teacher-questions";

const TYPE_LABEL: Record<string, string> = {
  multiple_choice: "選擇題",
  coding: "程式題",
  fill_blank: "填空題",
};

export function TeacherQuestionBank({ conceptTag }: { conceptTag: string }) {
  const [items, setItems] = useState<TeacherQuestion[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showAnswers, setShowAnswers] = useState(false);

  useEffect(() => {
    let cancelled = false;
    listTeacherQuestions(conceptTag).then(
      (qs) => !cancelled && setItems(qs),
      (e) =>
        !cancelled &&
        setError(e instanceof ApiRequestError ? e.body.message : "載入題庫失敗"),
    );
    return () => {
      cancelled = true;
    };
  }, [conceptTag]);

  if (error) return <p className="text-sm text-accent-red">{error}</p>;
  if (items === null)
    return (
      <div className="flex items-center gap-2 text-sm text-text-muted">
        <Loader2 className="size-4 animate-spin" />
        載入題庫…
      </div>
    );
  if (items.length === 0)
    return <p className="text-sm text-text-muted">此單元題庫尚無題目。</p>;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-xs text-text-muted">共 {items.length} 題（僅教師可見）</p>
        <button
          onClick={() => setShowAnswers((v) => !v)}
          className="flex items-center gap-1.5 rounded-md border border-border-default px-2.5 py-1 text-xs text-text-secondary transition-colors hover:bg-surface-2 hover:text-text-primary"
        >
          {showAnswers ? <EyeOff className="size-3.5" /> : <Eye className="size-3.5" />}
          {showAnswers ? "隱藏解答" : "顯示解答"}
        </button>
      </div>
      <ol className="space-y-3">
        {items.map((q, i) => (
          <QuestionItem
            key={q.id}
            index={i + 1}
            q={q}
            showAnswers={showAnswers}
            typeLabel={TYPE_LABEL[q.type] ?? q.type}
          />
        ))}
      </ol>
    </div>
  );
}

function QuestionItem({
  index,
  q,
  showAnswers,
  typeLabel,
}: {
  index: number;
  q: TeacherQuestion;
  showAnswers: boolean;
  typeLabel: string;
}) {
  const options = q.content.options ?? [];
  const answerIndex = q.content.answer_index;

  return (
    <li className="rounded-md border border-border-default bg-surface-1 p-4">
      <div className="mb-2 flex items-center gap-2 text-xs text-text-muted">
        <span className="rounded-pill border border-border-default px-1.5">
          {typeLabel}
        </span>
        <span>難度 {q.difficulty}</span>
        <span>Bloom {q.bloom_level}</span>
      </div>
      <p className="whitespace-pre-wrap text-sm text-text-primary">
        {index}. {q.content.stem ?? "（無題幹）"}
      </p>
      {options.length > 0 && (
        <ul className="mt-2 space-y-1">
          {options.map((opt, oi) => {
            const correct = showAnswers && oi === answerIndex;
            return (
              <li
                key={oi}
                className={`flex items-start gap-2 rounded px-2 py-1 text-sm ${
                  correct
                    ? "border border-accent-green text-text-primary"
                    : "text-text-secondary"
                }`}
              >
                <span className="font-mono text-xs text-text-muted">
                  {String.fromCharCode(65 + oi)}.
                </span>
                <span className="whitespace-pre-wrap">{opt}</span>
                {correct && (
                  <Check className="ml-auto size-3.5 shrink-0 text-accent-green" />
                )}
              </li>
            );
          })}
        </ul>
      )}
      {q.content.starter_code != null && (
        <pre className="mt-2 overflow-x-auto rounded bg-surface-inset p-2 font-mono text-xs text-text-secondary">
          {String(q.content.starter_code)}
        </pre>
      )}
      {showAnswers && q.explanation && (
        <p className="mt-2 rounded bg-surface-inset px-2 py-1.5 text-xs text-text-secondary">
          <span className="text-text-muted">解析：</span>
          {q.explanation}
        </p>
      )}
    </li>
  );
}
