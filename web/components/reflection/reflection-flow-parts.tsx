"use client";

/**
 * ReflectionFlow modal 的 sub-component 拆分（Phase 2-5c）— 控制主檔行數。
 * 純展示元件，狀態與動作由 caller (`reflection-flow.tsx`) 注入。
 */

import { Dialog } from "@base-ui/react/dialog";
import { Loader2, X } from "lucide-react";

import { ApiRequestError } from "@/lib/api";
import { ReflectionForm, ReflectionFormValue } from "./reflection-form";
import { ReflectionFollowup } from "./reflection-followup";

export type Stage = "form" | "submitting" | "followup" | "approved";

export function FlowHeader({ stage, onClose }: { stage: Stage; onClose: () => void }) {
  const title =
    stage === "followup"
      ? "再多想一下"
      : stage === "submitting"
        ? "AI 教練評估中..."
        : "動手前先想想";
  return (
    <div className="flex shrink-0 items-center justify-between border-b border-border-default px-5 py-3">
      <Dialog.Title className="text-base font-medium text-text-primary">
        {title}
      </Dialog.Title>
      <Dialog.Close
        onClick={onClose}
        className="flex size-7 items-center justify-center rounded-md text-text-muted hover:bg-bg-subtle hover:text-text-primary"
        aria-label="關閉"
      >
        <X className="size-4" />
      </Dialog.Close>
    </div>
  );
}

export interface FlowBodyProps {
  stage: Stage;
  formValue: ReflectionFormValue;
  onFormChange: (v: ReflectionFormValue) => void;
  followupQuestion: string;
  followupAnswer: string;
  onFollowupAnswerChange: (v: string) => void;
  error: string | null;
}

export function FlowBody(props: FlowBodyProps) {
  const { stage, error } = props;
  if (stage === "approved") return null;

  if (stage === "form" || stage === "submitting") {
    return (
      <>
        <p className="mb-4 text-xs leading-5 text-text-secondary">
          先把你的解題思路寫下來。研究顯示，動手前先反思能顯著提升解題正確率與學習效果。
        </p>
        <ReflectionForm
          value={props.formValue}
          onChange={props.onFormChange}
          disabled={stage === "submitting"}
        />
        {error && <ErrorBanner message={error} />}
      </>
    );
  }
  return (
    <>
      <ReflectionFollowup
        question={props.followupQuestion}
        value={props.followupAnswer}
        onChange={props.onFollowupAnswerChange}
      />
      {error && <ErrorBanner message={error} />}
    </>
  );
}

export interface FlowFooterProps {
  stage: Stage;
  formValid: boolean;
  followupAnswerFilled: boolean;
  onSubmitInitial: () => void;
  onSubmitFollowup: () => void;
  onGiveUp: () => void;
}

export function FlowFooter({
  stage,
  formValid,
  followupAnswerFilled,
  onSubmitInitial,
  onSubmitFollowup,
  onGiveUp,
}: FlowFooterProps) {
  if (stage === "approved") return null;
  const submitting = stage === "submitting";
  const disabled =
    submitting ||
    (stage === "form" && !formValid) ||
    (stage === "followup" && !followupAnswerFilled);

  return (
    <div className="flex shrink-0 items-center justify-end gap-2 border-t border-border-default bg-surface-2 px-5 py-3">
      {/* 追問是引導不是門檻：隨時可直接開始作答 */}
      {stage === "followup" && (
        <button
          type="button"
          onClick={onGiveUp}
          disabled={submitting}
          className="text-xs text-text-muted hover:text-text-secondary disabled:opacity-50"
        >
          直接開始作答
        </button>
      )}
      <button
        type="button"
        onClick={stage === "form" ? onSubmitInitial : onSubmitFollowup}
        disabled={disabled}
        className="flex h-8 items-center gap-1.5 rounded-md bg-btn-primary-bg px-3 text-sm font-medium text-white transition-colors hover:bg-btn-primary-hover disabled:opacity-50"
      >
        {submitting && <Loader2 className="size-3.5 animate-spin" />}
        {stage === "form" ? "送出反思" : "再次提交"}
      </button>
    </div>
  );
}

function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="mt-3 rounded-md border-l-2 border-accent-red bg-surface-2 px-3 py-2 text-xs text-accent-red">
      {message}
    </div>
  );
}

export function humanizeReflectionError(e: unknown): string {
  if (e instanceof ApiRequestError) {
    if (e.status === 404 && e.body.error === "REFLECTION_SOURCE_NOT_FOUND") {
      return "找不到對應題目，請重新開題。";
    }
    if (e.status === 409) return "此題已有反思紀錄。";
    return e.body.message || "送出失敗，請稍後再試。";
  }
  return e instanceof Error ? e.message : "未知錯誤";
}
