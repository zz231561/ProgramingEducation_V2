"use client";

/**
 * 程式撰寫題作答 UI（roadmap 3-2a）。
 *
 * Editor 復用 components/editor/code-editor.tsx（CodeMirror 6 + cpp + oneDark theme）。
 * Note：3-2a 範圍提交後的判分結果由後端回傳（coding 題目前 is_correct=False，
 * Judge0 整合屬 Phase 4）— UI 仍會顯示 server feedback + explanation。
 */

import { useEffect, useRef, useState } from "react";

import { CodeEditor } from "@/components/editor/code-editor";
import { CodingContent, Question } from "@/lib/quiz";

interface Props {
  question: Question;
  busy: boolean;
  onSubmit: (code: string) => void;
}

export function CodingQuestion({ question, busy, onSubmit }: Props) {
  const content = question.content as CodingContent;
  const initial = content.starter_code ?? "";
  const codeRef = useRef<string>(initial);
  const [hasContent, setHasContent] = useState(initial.trim().length > 0);

  // 切換題目時 reset state 與 ref（典型「effect 同步外部 state」場景，rule 例外）
  useEffect(() => {
    codeRef.current = initial;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setHasContent(initial.trim().length > 0);
  }, [initial, question.id]);

  return (
    <div className="space-y-4">
      <p className="whitespace-pre-wrap text-sm leading-relaxed text-text-primary">
        {content.stem}
      </p>

      <div className="h-80 overflow-hidden rounded-md border border-border-default bg-bg-canvas">
        <CodeEditor
          initialValue={initial}
          onChange={(v) => {
            codeRef.current = v;
            setHasContent(v.trim().length > 0);
          }}
        />
      </div>

      <div className="flex items-center justify-between">
        <p className="text-xs text-text-muted">
          ⓘ 程式題目前由後端記錄答案；自動判分將於 Phase 4 整合 Judge0
        </p>
        <button
          type="button"
          onClick={() => onSubmit(codeRef.current)}
          disabled={busy || !hasContent}
          className="inline-flex h-9 items-center rounded-md bg-btn-primary-bg px-4 text-sm font-medium text-white hover:bg-btn-primary-hover disabled:cursor-not-allowed disabled:opacity-50"
        >
          {busy ? "提交中..." : "提交答案"}
        </button>
      </div>
    </div>
  );
}
