"use client";

/**
 * Reflection Flow — 開題前反思 modal 容器（Phase 2-5c）。
 *
 * 狀態機：form → submitting → (approved | followup) → submitting → approved
 *
 * - LLM 失敗（quality_score=null）→ 視為通過，不擋學生流程
 * - 達門檻（followup_question=null）→ approved
 * - 追問是引導不是門檻（2026-07-16 修訂）：追問階段隨時可「直接開始作答」跳過；
 *   回答過一次追問後無論分數一律放行（self-explanation 的效益來自提示本身）
 *
 * 純受控 — open/close 由 caller 用 prop 管；onApprove 通知放行 + 回傳 reflection。
 */

import { useCallback, useState } from "react";
import { Dialog } from "@base-ui/react/dialog";

import {
  CreateReflectionPayload,
  Reflection,
  ReflectionSourceType,
  createReflection,
  patchReflection,
} from "@/lib/reflection";
import {
  EMPTY_REFLECTION_FORM,
  ReflectionFormValue,
  isReflectionFormValid,
  toBackendPayload,
} from "./reflection-form";
import {
  FlowBody,
  FlowFooter,
  FlowHeader,
  Stage,
  humanizeReflectionError,
} from "./reflection-flow-parts";

export interface ReflectionFlowProps {
  open: boolean;
  sourceType: ReflectionSourceType;
  sourceId: string | null;
  /** 題目題幹 — 提供時固定顯示於視窗頂部，學生反思時不需關窗回看題目 */
  questionStem?: string | null;
  onApprove: (reflection: Reflection) => void;
  onClose: () => void;
}

/**
 * 對外元件 — 純 Dialog 殼；內部內容只在 open=true 時 mount，
 * 確保每次重新開啟時 state 自然從零開始（避免在 effect 裡 setState）。
 */
export function ReflectionFlow(props: ReflectionFlowProps) {
  const { open, onClose } = props;
  return (
    <Dialog.Root open={open} onOpenChange={(v) => !v && onClose()}>
      <Dialog.Portal>
        <Dialog.Backdrop className="fixed inset-0 bg-black/60 backdrop-blur-sm" />
        <Dialog.Popup className="fixed top-1/2 left-1/2 z-50 flex max-h-[85vh] w-[min(560px,calc(100vw-2rem))] -translate-x-1/2 -translate-y-1/2 flex-col overflow-hidden rounded-lg border border-border-default bg-surface-1 shadow-modal">
          {open && <ReflectionFlowContent {...props} />}
        </Dialog.Popup>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

function ReflectionFlowContent({
  sourceType,
  sourceId,
  questionStem,
  onApprove,
  onClose,
}: Omit<ReflectionFlowProps, "open">) {
  const [stage, setStage] = useState<Stage>("form");
  const [formValue, setFormValue] = useState<ReflectionFormValue>(EMPTY_REFLECTION_FORM);
  const [reflection, setReflection] = useState<Reflection | null>(null);
  const [followupAnswer, setFollowupAnswer] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleResult = useCallback(
    (result: Reflection) => {
      setReflection(result);
      const approved =
        result.quality_score === null || result.followup_question === null;
      if (approved) {
        setStage("approved");
        onApprove(result);
      } else {
        setStage("followup");
        setFollowupAnswer("");
      }
    },
    [onApprove],
  );

  const submitInitial = useCallback(async () => {
    if (!sourceId) return;
    setStage("submitting");
    setError(null);
    const payload: CreateReflectionPayload = {
      source_type: sourceType,
      source_id: sourceId,
      ...toBackendPayload(formValue),
    };
    try {
      handleResult(await createReflection(payload));
    } catch (e) {
      setStage("form");
      setError(humanizeReflectionError(e));
    }
  }, [sourceId, sourceType, formValue, handleResult]);

  const submitFollowup = useCallback(async () => {
    if (!reflection) return;
    setStage("submitting");
    setError(null);
    try {
      const result = await patchReflection(reflection.id, {
        followup_answer: followupAnswer.trim(),
      });
      // 回答過追問即放行（不再二輪）：追問目的是引發再思考，不是考試
      setReflection(result);
      setStage("approved");
      onApprove(result);
    } catch (e) {
      setStage("followup");
      setError(humanizeReflectionError(e));
    }
  }, [reflection, followupAnswer, onApprove]);

  const giveUp = useCallback(() => {
    if (reflection) {
      setStage("approved");
      onApprove(reflection);
    }
  }, [reflection, onApprove]);

  return (
    <>
      <FlowHeader stage={stage} onClose={onClose} />
      {questionStem && (
        <div className="max-h-[22vh] shrink-0 overflow-y-auto border-b border-border-default bg-surface-2 px-5 py-3">
          <p className="mb-1 text-xs font-medium text-text-muted">題目</p>
          <p className="whitespace-pre-wrap text-xs leading-relaxed text-text-secondary">
            {questionStem}
          </p>
        </div>
      )}
      <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">
        <FlowBody
          stage={stage}
          formValue={formValue}
          onFormChange={setFormValue}
          followupQuestion={reflection?.followup_question ?? ""}
          followupAnswer={followupAnswer}
          onFollowupAnswerChange={setFollowupAnswer}
          error={error}
        />
      </div>
      <FlowFooter
        stage={stage}
        formValid={isReflectionFormValid(formValue)}
        followupAnswerFilled={followupAnswer.trim().length > 0}
        onSubmitInitial={submitInitial}
        onSubmitFollowup={submitFollowup}
        onGiveUp={giveUp}
      />
    </>
  );
}
