"use client";

/**
 * Reflection Flow — 開題前反思 modal 容器（Phase 2-5c）。
 *
 * 狀態機：form → submitting → (approved | followup) → submitting → ...
 *
 * - LLM 失敗（quality_score=null）→ 視為通過，不擋學生流程
 * - 達門檻（followup_question=null）→ approved
 * - MAX_FOLLOWUP_ROUNDS 次仍未通過 → 提供「已盡力」放行（避免無限 loop）
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

const MAX_FOLLOWUP_ROUNDS = 2;

export interface ReflectionFlowProps {
  open: boolean;
  sourceType: ReflectionSourceType;
  sourceId: string | null;
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
        <Dialog.Popup className="fixed top-1/2 left-1/2 z-50 max-h-[85vh] w-[min(560px,calc(100vw-2rem))] -translate-x-1/2 -translate-y-1/2 overflow-hidden rounded-lg border border-border-default bg-surface-1 shadow-modal">
          {open && <ReflectionFlowContent {...props} />}
        </Dialog.Popup>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

function ReflectionFlowContent({
  sourceType,
  sourceId,
  onApprove,
  onClose,
}: Omit<ReflectionFlowProps, "open">) {
  const [stage, setStage] = useState<Stage>("form");
  const [formValue, setFormValue] = useState<ReflectionFormValue>(EMPTY_REFLECTION_FORM);
  const [reflection, setReflection] = useState<Reflection | null>(null);
  const [followupAnswer, setFollowupAnswer] = useState("");
  const [followupRound, setFollowupRound] = useState(0);
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
      setFollowupRound((n) => n + 1);
      handleResult(result);
    } catch (e) {
      setStage("followup");
      setError(humanizeReflectionError(e));
    }
  }, [reflection, followupAnswer, handleResult]);

  const giveUp = useCallback(() => {
    if (reflection) {
      setStage("approved");
      onApprove(reflection);
    }
  }, [reflection, onApprove]);

  return (
    <>
      <FlowHeader stage={stage} onClose={onClose} />
      <div className="max-h-[60vh] overflow-y-auto px-5 py-4">
        <FlowBody
          stage={stage}
          formValue={formValue}
          onFormChange={setFormValue}
          followupQuestion={reflection?.followup_question ?? ""}
          qualityScore={reflection?.quality_score ?? null}
          followupAnswer={followupAnswer}
          onFollowupAnswerChange={setFollowupAnswer}
          error={error}
        />
      </div>
      <FlowFooter
        stage={stage}
        formValid={isReflectionFormValid(formValue)}
        followupAnswerFilled={followupAnswer.trim().length > 0}
        canGiveUp={followupRound >= MAX_FOLLOWUP_ROUNDS - 1}
        onSubmitInitial={submitInitial}
        onSubmitFollowup={submitFollowup}
        onGiveUp={giveUp}
      />
    </>
  );
}
