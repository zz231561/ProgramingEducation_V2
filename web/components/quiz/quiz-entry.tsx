"use client";

/**
 * QUIZ 入口分派（6-3d）：
 * - 一般進入 → 弱項綜合測驗組（WeaknessQuizRunner，選 10/25 一次生成）
 * - DEV 深連結 `?question=<id>` → 舊 QuizRunner（單題檢視 / 診斷微測驗）
 */

import { useSearchParams } from "next/navigation";

import { QuizRunner } from "./quiz-runner";
import { WeaknessQuizRunner } from "./weakness-quiz-runner";

export function QuizEntry() {
  const deepLinkQuestionId = useSearchParams().get("question");
  return deepLinkQuestionId ? <QuizRunner /> : <WeaknessQuizRunner />;
}
