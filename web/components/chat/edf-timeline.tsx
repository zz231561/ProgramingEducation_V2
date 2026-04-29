"use client";

/**
 * EDF Pipeline mini timeline（design-plan §2.1）：
 * 在每則 AI 訊息上方顯示教學決策過程，把 Evidence → Decision → Feedback → RAG 變成可教學的 UI。
 *
 * Phase 1：3 個必經步驟永遠 active；RAG 顯示為 inactive（Phase 2-1 啟用後才會點亮）。
 * Phase 2-1 完成後可改為依 evidence + strategy 動態切換 RAG active 狀態。
 */

interface EdfTimelineProps {
  ragActive?: boolean;
}

interface Step {
  key: string;
  label: string;
  /** 對應 GitHub Dark accent token（design-plan §2.1） */
  colorClass: string;
  borderColorClass: string;
  active: boolean;
  hint?: string;
}

export function EdfTimeline({ ragActive = false }: EdfTimelineProps) {
  const steps: Step[] = [
    {
      key: "evidence",
      label: "Evidence",
      colorClass: "bg-accent-orange",
      borderColorClass: "border-accent-orange",
      active: true,
      hint: "分析程式碼錯誤、概念與 Bloom 等級",
    },
    {
      key: "decision",
      label: "Decision",
      colorClass: "bg-accent-purple",
      borderColorClass: "border-accent-purple",
      active: true,
      hint: "依 Bloom × Hint Ladder 矩陣選擇教學策略",
    },
    {
      key: "feedback",
      label: "Feedback",
      colorClass: "bg-accent-green",
      borderColorClass: "border-accent-green",
      active: true,
      hint: "依策略生成本回合回應",
    },
    {
      key: "rag",
      label: "RAG",
      colorClass: "bg-accent-blue",
      borderColorClass: "border-accent-blue",
      active: ragActive,
      hint: ragActive ? "已檢索教材片段" : "Phase 2-1 啟用",
    },
  ];

  return (
    <div className="mb-1 flex items-center gap-1.5 text-[10px] text-text-muted body-ui select-none">
      {steps.map((step, i) => (
        <span key={step.key} className="flex items-center gap-1.5">
          <span
            className={`size-2 rounded-pill border ${
              step.active
                ? `${step.colorClass} ${step.borderColorClass}`
                : `bg-transparent border-border-default`
            }`}
            title={`${step.label}：${step.hint}`}
            aria-label={`${step.label} ${step.active ? "已完成" : "未觸發"}`}
          />
          <span className={step.active ? "text-text-secondary" : "text-text-muted/60"}>
            {step.label}
          </span>
          {i < steps.length - 1 && (
            <span className="h-px w-3 bg-border-default" aria-hidden />
          )}
        </span>
      ))}
    </div>
  );
}
