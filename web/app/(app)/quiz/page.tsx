"use client";

/**
 * Quiz 頁面 — 弱項綜合測驗場景（6-3d）。
 *
 * 一般進入 → 弱項綜合測驗組（選 10/25 一次生成、逐題作答）；
 * DEV 深連結 `?question=<id>` → 舊 QuizRunner 單題檢視（分派見 QuizEntry）。
 *
 * 設計分工：
 * - 本頁 = 純測驗（無反思）
 * - Learn 練習 tab = 學習場景含 Pre-Coding Reflection（見 3-1e）
 */

import { Suspense } from "react";

import { QuizEntry } from "@/components/quiz/quiz-entry";

export default function QuizPage() {
  return (
    <div className="h-full overflow-y-auto px-6 py-10">
      <div className="mx-auto w-full max-w-3xl">
        {/* Suspense：QuizEntry 內用 useSearchParams（DEV-9 深連結）需要 CSR 邊界 */}
        <Suspense fallback={null}>
          <QuizEntry />
        </Suspense>
      </div>
    </div>
  );
}
