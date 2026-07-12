"use client";

/**
 * 評分表單（5-5b-4）— 分數 + 評語，儲存後回寫交件列表。
 */

import { useState } from "react";
import { Loader2 } from "lucide-react";

import { ApiRequestError } from "@/lib/api";
import { Submission, gradeSubmission } from "@/lib/assignments";

const inputCls =
  "rounded-md border border-border-default bg-bg-canvas px-2 text-sm text-text-primary focus:border-accent-blue focus:outline-none";

export function GradeForm({
  submission,
  onGraded,
}: {
  submission: Submission;
  onGraded: (s: Submission) => void;
}) {
  const [score, setScore] = useState(submission.score?.toString() ?? "");
  const [feedback, setFeedback] = useState(submission.feedback);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const save = async () => {
    const n = score.trim() === "" ? null : Number(score);
    if (n != null && (Number.isNaN(n) || n < 0)) {
      setError("分數需為 ≥ 0 的數字");
      return;
    }
    setBusy(true);
    setError(null);
    setSaved(false);
    try {
      onGraded(await gradeSubmission(submission.id, n, feedback));
      setSaved(true);
    } catch (e) {
      setError(e instanceof ApiRequestError ? e.body.message : "儲存失敗");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <label className="text-xs text-text-secondary" htmlFor={`score-${submission.id}`}>
          分數
        </label>
        <input
          id={`score-${submission.id}`}
          type="number"
          min={0}
          value={score}
          onChange={(e) => setScore(e.target.value)}
          placeholder="未評"
          className={`h-8 w-24 ${inputCls}`}
        />
      </div>
      <textarea
        value={feedback}
        onChange={(e) => setFeedback(e.target.value)}
        rows={3}
        maxLength={5000}
        placeholder="評語（選填）"
        className={`w-full py-1.5 ${inputCls}`}
      />
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={save}
          disabled={busy}
          className="flex h-8 items-center gap-1.5 rounded-md bg-btn-primary-bg px-3 text-sm font-medium text-white transition-colors hover:bg-btn-primary-hover disabled:opacity-50"
        >
          {busy && <Loader2 className="size-3.5 animate-spin" />}
          儲存評分
        </button>
        {saved && <span className="text-xs text-accent-green">已儲存</span>}
        {error && <span className="text-xs text-accent-red">{error}</span>}
      </div>
    </div>
  );
}
