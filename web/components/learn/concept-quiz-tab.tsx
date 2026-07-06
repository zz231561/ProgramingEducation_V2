"use client";

/**
 * 觀念題 tab（6-3c）— 逐題作答該單元「預生成題組」（source='batch'）。
 *
 * 不呼叫 LLM：題目全為批次預生成。學生依序答完所有未答題；全部答過 →
 * 顯示「已完成」+ 可重新作答。QUIZ 弱項現生題不列入此題組。
 */

import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, Loader2, XCircle } from "lucide-react";

import { MCQuestion } from "@/components/quiz/mc-question";
import { ApiRequestError } from "@/lib/api";
import {
  SubmitResponse,
  UnitQuestionItem,
  getUnitQuestionSet,
  submitAnswer,
} from "@/lib/quiz";

type Status = "loading" | "answering" | "completed" | "empty" | "error";

export function ConceptQuizTab({ conceptTag }: { conceptTag: string }) {
  const [status, setStatus] = useState<Status>("loading");
  const [items, setItems] = useState<UnitQuestionItem[]>([]);
  const [queue, setQueue] = useState<number[]>([]); // 待答題在 items 中的 index
  const [pos, setPos] = useState(0);
  const [result, setResult] = useState<SubmitResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const set = await getUnitQuestionSet(conceptTag, "multiple_choice");
      setItems(set.items);
      if (set.total === 0) {
        setStatus("empty");
        return;
      }
      const unanswered = set.items
        .map((it, i) => (it.is_answered ? -1 : i))
        .filter((i) => i >= 0);
      if (unanswered.length === 0) {
        setStatus("completed");
        return;
      }
      setQueue(unanswered);
      setPos(0);
      setResult(null);
      setStatus("answering");
    } catch (e) {
      setStatus("error");
      setError(
        e instanceof ApiRequestError
          ? e.body.message || "載入題組失敗。"
          : "載入題組失敗。",
      );
    }
  }, [conceptTag]);

  useEffect(() => {
    load();
  }, [load]);

  const restart = useCallback(() => {
    setQueue(items.map((_, i) => i));
    setPos(0);
    setResult(null);
    setStatus("answering");
  }, [items]);

  const handleSubmit = useCallback(
    async (selectedIndex: number) => {
      const question = items[queue[pos]].question;
      setBusy(true);
      setError(null);
      try {
        setResult(
          await submitAnswer({
            question_id: question.id,
            answer: { selected_index: selectedIndex },
          }),
        );
      } catch {
        setError("提交失敗，請再試一次。");
      } finally {
        setBusy(false);
      }
    },
    [items, queue, pos],
  );

  const next = useCallback(() => {
    if (pos + 1 >= queue.length) {
      setStatus("completed");
      return;
    }
    setPos((p) => p + 1);
    setResult(null);
  }, [pos, queue.length]);

  if (status === "loading") {
    return (
      <div className="flex flex-col items-center gap-3 py-12 text-text-secondary">
        <Loader2 className="size-6 animate-spin" />
        <p className="text-sm">載入題組...</p>
      </div>
    );
  }

  if (status === "empty") {
    return (
      <p className="rounded-md border border-border-default bg-surface-1 px-4 py-8 text-center text-sm text-text-secondary">
        本單元尚無觀念題。
      </p>
    );
  }

  if (status === "error") {
    return (
      <div className="rounded-md border-l-2 border-accent-red bg-surface-2 px-3 py-2 text-xs text-accent-red">
        {error}
      </div>
    );
  }

  if (status === "completed") {
    return (
      <div className="space-y-3 rounded-md border border-border-default bg-surface-1 px-6 py-8 text-center">
        <CheckCircle2 className="mx-auto size-8 text-accent-green" />
        <p className="text-sm text-text-primary">
          本單元 {items.length} 題觀念題已全部完成！
        </p>
        <button
          type="button"
          onClick={restart}
          className="inline-flex h-9 items-center rounded-md border border-btn-default-border bg-btn-default-bg px-4 text-sm text-text-primary hover:bg-surface-2"
        >
          重新作答
        </button>
      </div>
    );
  }

  // answering
  const question = items[queue[pos]].question;
  return (
    <div className="space-y-3">
      <p className="text-xs text-text-muted">
        第 {pos + 1} / {queue.length} 題
      </p>
      <div className="rounded-md border border-border-default bg-surface-1 p-4">
        {result === null ? (
          <MCQuestion question={question} busy={busy} onSubmit={handleSubmit} />
        ) : (
          <QuizResult result={result} onNext={next} isLast={pos + 1 >= queue.length} />
        )}
      </div>
      {error && (
        <div className="rounded-md border-l-2 border-accent-red bg-surface-2 px-3 py-2 text-xs text-accent-red">
          {error}
        </div>
      )}
    </div>
  );
}

function QuizResult({
  result,
  onNext,
  isLast,
}: {
  result: SubmitResponse;
  onNext: () => void;
  isLast: boolean;
}) {
  return (
    <div className="space-y-3">
      <div
        className={`flex items-center gap-2 text-sm ${
          result.is_correct ? "text-accent-green" : "text-accent-red"
        }`}
      >
        {result.is_correct ? (
          <CheckCircle2 className="size-4" />
        ) : (
          <XCircle className="size-4" />
        )}
        <span>{result.is_correct ? "答對了！" : "答錯了"}</span>
      </div>
      {result.explanation && (
        <p className="rounded-md border-l-2 border-accent-blue bg-surface-2 px-3 py-2 text-xs leading-relaxed text-text-secondary">
          {result.explanation}
        </p>
      )}
      <button
        type="button"
        onClick={onNext}
        className="inline-flex h-8 items-center rounded-md bg-btn-primary-bg px-3 text-xs font-medium text-white hover:bg-btn-primary-hover"
      >
        {isLast ? "完成" : "下一題"}
      </button>
    </div>
  );
}
