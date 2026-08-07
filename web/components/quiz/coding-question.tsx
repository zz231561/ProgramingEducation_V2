"use client";

/** 程式撰寫題作答 UI；提交後保存答案，目前不執行自動判分。 */

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
    // eslint-disable-next-line react-hooks/set-state-in-effect -- 題目切換時重設編輯器狀態
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
          ⓘ 程式題會保存答案，目前不自動判分，可由教師檢視
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
