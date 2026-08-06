"use client";

/**
 * 變體挑戰 — 換一個情境重寫，驗證概念真的遷移得過去（2-6d）。
 *
 * **禁用 AI 是這一題的核心**：能問 Coddy 就等於沒驗到遷移能力。
 * 鎖由 `useAiLock` 在挑戰開始時上、離開時解（見 comprehension-modal）。
 */

import { Lock } from "lucide-react";

import { StepShell } from "./step-parts";
import type { VariationGenerated } from "@/lib/comprehension";

interface Props {
  challenge: VariationGenerated;
  code: string;
  onCodeChange: (value: string) => void;
  onSubmit: () => void;
  busy: boolean;
  passed: boolean | null;
}

export function VariationStep({
  challenge, code, onCodeChange, onSubmit, busy, passed,
}: Props) {
  if (passed !== null) {
    return (
      <p className="text-sm text-text-secondary">
        這題練的是「{challenge.concept_focus}」。
        {passed
          ? "你把它換個情境也寫出來了，代表概念真的遷移過去了。"
          : "先別急著看解法——回頭比對測資，想想哪一個情境沒被你的條件涵蓋到。"}
      </p>
    );
  }

  return (
    <StepShell
      prompt={challenge.stem}
      onSubmit={onSubmit}
      busy={busy}
      canSubmit={code.trim().length > 0}
      submitLabel="提交解答"
      aside={
        <div className="space-y-2">
          <div className="flex items-center gap-1.5 rounded-md border border-border-default px-2.5 py-1.5 text-xs text-text-secondary">
            <Lock className="size-3.5 shrink-0 text-text-muted" />
            這題請自己寫，Coddy 已暫時停用——換個情境還寫得出來，才代表你真的會了。
          </div>
          {challenge.test_cases.length > 0 && (
            <div className="space-y-1">
              <span className="text-xs text-text-muted">測試資料</span>
              <div className="overflow-x-auto rounded-md border border-border-default bg-bg-inset">
                <table className="w-full font-mono text-xs">
                  <tbody>
                    {challenge.test_cases.map((tc, i) => (
                      <tr key={i} className="border-b border-border-muted last:border-0">
                        <td className="px-3 py-1.5 text-text-secondary">{tc.input}</td>
                        <td className="px-3 py-1.5 text-text-primary">→ {tc.expected}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      }
    >
      <textarea
        value={code}
        onChange={(e) => onCodeChange(e.target.value)}
        disabled={busy}
        rows={12}
        spellCheck={false}
        className="w-full resize-none rounded-md border border-border-default bg-bg-inset px-3 py-2 font-mono text-xs leading-relaxed text-text-primary focus:border-accent-blue focus:outline-none disabled:opacity-50"
      />
    </StepShell>
  );
}
