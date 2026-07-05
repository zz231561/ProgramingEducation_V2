"use client";

/**
 * 作答結果頁（roadmap 3-2a）。
 *
 * 顯示對錯、feedback、解釋，以及對應題型的「正確答案揭露」。
 * 完整 EDF 回饋（hint_level / 概念補強建議）屬 3-2c 範圍，本頁先做基本版。
 */

import { CheckCircle2, XCircle } from "lucide-react";

import { Question, SubmitResponse } from "@/lib/quiz";

import { DiagnosisSection } from "./diagnosis-section";
import { FeedbackSection } from "./feedback-section";

interface Props {
  question: Question;
  result: SubmitResponse;
  onNext: () => void;
  onExit: () => void;
  /** K3e 微測驗入口：診斷嫌疑鏈點「微測驗」後直接切入該題作答。 */
  onStartQuestion?: (question: Question) => void;
}

export function ResultView({ question, result, onNext, onExit, onStartQuestion }: Props) {
  return (
    <div className="space-y-4">
      <ResultBanner isCorrect={result.is_correct} feedback={result.feedback} />

      {result.explanation && (
        <Section title="解析">
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-text-secondary">
            {result.explanation}
          </p>
        </Section>
      )}

      <CorrectAnswerSection
        questionType={question.type}
        correctContent={result.correct_content}
      />

      <FeedbackSection answerId={result.answer_id} />

      {/* K3e：答錯才查診斷；未觸發時元件自行隱藏 */}
      {!result.is_correct && question.concept_tags[0] && (
        <DiagnosisSection
          conceptTag={question.concept_tags[0]}
          onStartQuestion={onStartQuestion}
        />
      )}

      <div className="flex items-center justify-end gap-2 pt-2">
        <button
          type="button"
          onClick={onExit}
          className="h-9 rounded-md border border-btn-default-border bg-btn-default-bg px-4 text-sm text-text-primary hover:bg-surface-2"
        >
          結束
        </button>
        <button
          type="button"
          onClick={onNext}
          className="inline-flex h-9 items-center rounded-md bg-btn-primary-bg px-4 text-sm font-medium text-white hover:bg-btn-primary-hover"
        >
          下一題
        </button>
      </div>
    </div>
  );
}

function ResultBanner({ isCorrect, feedback }: { isCorrect: boolean; feedback: string }) {
  const Icon = isCorrect ? CheckCircle2 : XCircle;
  const colorClass = isCorrect ? "text-accent-green" : "text-accent-red";
  return (
    <div className="flex items-start gap-3 rounded-md border border-border-default bg-surface-1 p-4">
      <Icon className={`mt-0.5 size-5 shrink-0 ${colorClass}`} />
      <div>
        <p className={`text-sm font-medium ${colorClass}`}>
          {isCorrect ? "答對了！" : "答錯了"}
        </p>
        {feedback && (
          <p className="mt-1 text-sm text-text-secondary">{feedback}</p>
        )}
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-md border border-border-default bg-surface-1 p-4">
      <h3 className="mb-2 text-sm font-medium text-text-primary">{title}</h3>
      {children}
    </div>
  );
}

function CorrectAnswerSection({
  questionType,
  correctContent,
}: {
  questionType: string;
  correctContent: Record<string, unknown>;
}) {
  if (questionType === "multiple_choice") {
    const idx = correctContent.answer_index as number | undefined;
    const options = correctContent.options as string[] | undefined;
    if (idx === undefined || !options) return null;
    return (
      <Section title="正確答案">
        <p className="text-sm text-text-primary">
          <span className="font-mono text-text-muted">第 {idx + 1} 項：</span>
          {options[idx]}
        </p>
      </Section>
    );
  }

  if (questionType === "fill_blank") {
    const answers = correctContent.answers as string[] | undefined;
    if (!answers) return null;
    return (
      <Section title="正確答案">
        <ul className="list-disc pl-5 text-sm text-text-primary">
          {answers.map((a, i) => (
            <li key={i}>{a}</li>
          ))}
        </ul>
      </Section>
    );
  }

  // coding：3-2a 不顯示參考解答（避免影響後續 Judge0 判分情境）
  return null;
}
