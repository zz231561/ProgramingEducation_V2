"use client";

/**
 * Quiz 頁面（roadmap 3-2a）— 純測驗場景。
 *
 * 流程委託給 QuizRunner 元件（idle / loading / question / result）。
 * 計時器 / 提示系統 / 完整 EDF 回饋屬 3-2b/c。
 *
 * 設計分工：
 * - 本頁 = 純測驗（無反思）
 * - Learn 練習 tab = 學習場景含 Pre-Coding Reflection（見 3-1e）
 */

import { Suspense } from "react";

import { QuizRunner } from "@/components/quiz/quiz-runner";

export default function QuizPage() {
  return (
    <div className="h-full overflow-y-auto px-6 py-10">
      <div className="mx-auto w-full max-w-3xl">
        {/* Suspense：QuizRunner 內用 useSearchParams（DEV-9 深連結）需要 CSR 邊界 */}
        <Suspense fallback={null}>
          <QuizRunner />
        </Suspense>
      </div>
    </div>
  );
}
