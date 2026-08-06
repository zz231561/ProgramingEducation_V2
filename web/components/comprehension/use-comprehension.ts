"use client";

/**
 * Comprehension 流程狀態機（7-C3）。
 *
 * 答對 → 問後端要不要驗（`trigger-suggestion`）→ 依建議的 type 出題 → 作答 → 評分。
 * 三種 type 的資料形狀不同，用 discriminated union 表示，避免用一堆可選欄位互相污染。
 *
 * 容錯原則：**任何一步失敗都不擋學生**——理解驗證是加分項，不是關卡。
 * 出題失敗直接收掉（skip），評分失敗顯示訊息但保留學生打的內容。
 */

import { useCallback, useEffect, useRef, useState } from "react";

import {
  ComprehensionType,
  EplGrade,
  PredictGrade,
  VariationGenerated,
  generateEpl,
  generatePredict,
  generateVariation,
  getTriggerSuggestion,
  gradeEpl,
  gradePredict,
  gradeVariation,
} from "@/lib/comprehension";

import { useAiLock } from "./ai-lock";

type Data =
  | { type: "epl"; prompt: string }
  | { type: "predict_output"; testInput: string }
  | { type: "variation"; challenge: VariationGenerated };

export type Phase =
  | { k: "checking" }
  | { k: "skip" }
  | { k: "loading"; type: ComprehensionType }
  | { k: "answering"; data: Data }
  | { k: "grading"; data: Data }
  | {
      k: "done";
      data: Data;
      passed: boolean | null;
      feedback: string | null;
      epl: EplGrade | null;
      predict: PredictGrade | null;
    };

const AI_LOCK_REASON = "變體挑戰進行中：這題請自己寫，寫完就會解鎖。";

export function useComprehension(answerId: string) {
  const [phase, setPhase] = useState<Phase>({ k: "checking" });
  const [answer, setAnswer] = useState("");
  const [error, setError] = useState<string | null>(null);
  const { lockAi, unlockAi } = useAiLock();
  // StrictMode 會跑兩次 effect；出題是計費的 LLM 呼叫，必須只發一次
  const startedRef = useRef(false);

  useEffect(() => {
    if (startedRef.current) return;
    startedRef.current = true;

    let alive = true;
    (async () => {
      try {
        const decision = await getTriggerSuggestion(answerId);
        if (!alive) return;
        if (!decision.should_trigger || !decision.suggested_type) {
          setPhase({ k: "skip" });
          return;
        }
        const type = decision.suggested_type;
        setPhase({ k: "loading", type });
        const data = await generateFor(type, answerId);
        if (!alive) return;
        setAnswer(data.type === "variation" ? data.challenge.starter_code : "");
        setPhase({ k: "answering", data });
      } catch {
        // 出題失敗（LLM 不可用 / 題型不支援）→ 靜默收掉，學生照常看結果頁
        if (alive) setPhase({ k: "skip" });
      }
    })();

    return () => {
      alive = false;
    };
  }, [answerId]);

  // 變體挑戰期間鎖住 Coddy；離開此畫面（含中途關閉）一律解鎖
  useEffect(() => {
    const locked =
      (phase.k === "answering" || phase.k === "grading") &&
      phase.data.type === "variation";
    if (locked) lockAi(AI_LOCK_REASON);
    else unlockAi();
  }, [phase, lockAi, unlockAi]);

  useEffect(() => () => unlockAi(), [unlockAi]);

  const submit = useCallback(async () => {
    if (phase.k !== "answering") return;
    const { data } = phase;
    setPhase({ k: "grading", data });
    setError(null);
    try {
      const done = await gradeFor(data, answerId, answer);
      setPhase({ k: "done", data, ...done });
    } catch {
      setError("評分失敗，可以再送一次，或直接關閉繼續下一題。");
      setPhase({ k: "answering", data });
    }
  }, [phase, answerId, answer]);

  return { phase, answer, setAnswer, submit, error };
}

async function generateFor(type: ComprehensionType, id: string): Promise<Data> {
  if (type === "epl") {
    const r = await generateEpl(id);
    return { type: "epl", prompt: r.comprehension_prompt };
  }
  if (type === "predict_output") {
    const r = await generatePredict(id);
    return { type: "predict_output", testInput: r.test_input };
  }
  return { type: "variation", challenge: await generateVariation(id) };
}

async function gradeFor(data: Data, id: string, answer: string) {
  if (data.type === "epl") {
    const r = await gradeEpl(id, answer);
    return {
      passed: r.comprehension_passed,
      feedback: r.feedback,
      epl: r,
      predict: null,
    };
  }
  if (data.type === "predict_output") {
    const r = await gradePredict(id, answer);
    return {
      passed: r.comprehension_passed,
      feedback: r.feedback,
      epl: null,
      predict: r,
    };
  }
  const r = await gradeVariation(id, answer);
  return { passed: r.comprehension_passed, feedback: r.feedback, epl: null, predict: null };
}
