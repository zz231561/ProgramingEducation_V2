"use client";

/**
 * Chat 執行期狀態（2026-08-05 修 A1）。
 *
 * `ChatPanel` 是**條件掛載**的（收合聊天就 unmount），原本訊息、session id、
 * 執行結果訂閱全都住在裡面 → 收合再展開，對話看起來整個消失（資料其實還在 DB）。
 * 與 Output 執行歷史同一類問題，解法一致：把狀態移到永遠掛載的層級。
 *
 * 一併修好的副作用：
 * - 聊天收合時執行程式，結果卡片不再被丟掉
 * - 編譯錯誤的去重簽章不再隨面板開合重置（不會重複花配額）
 */

import { createContext, useContext, useEffect, useRef } from "react";

import { useWorkspace } from "@/components/workspace/workspace-context";
import { usesLocalTime } from "@/lib/code-detect";
import { useChat } from "@/hooks/use-chat";
import { useSessions } from "@/hooks/use-sessions";

type ChatRuntime = ReturnType<typeof useChat> & {
  sessions: ReturnType<typeof useSessions>["sessions"];
  activeId: string | null;
  setActiveId: (id: string | null) => void;
  deleteSession: (id: string) => Promise<void>;
};

const Ctx = createContext<ChatRuntime | null>(null);

/**
 * 編譯錯誤的去重簽章：取前兩行並抹掉行號欄位。
 * 學生改了程式碼但錯誤本質相同（行號漂移）時視為同一個錯誤，避免重複花配額。
 */
function errorSignature(compileOutput: string): string {
  return compileOutput
    .split("\n")
    .slice(0, 2)
    .join(" ")
    .replace(/:\d+:\d+:/g, ":")
    .replace(/^\s*\d+\s*\|/gm, "")
    .trim();
}

export function ChatRuntimeProvider({ children }: { children: React.ReactNode }) {
  const {
    getCode, getExecutionResult, onExecutionComplete,
    onChatInjectionRequest, onReflectionKickoff,
  } = useWorkspace();
  const { sessions, activeId, setActiveId, deleteSession, addSession } =
    useSessions();
  const chat = useChat({ getCode, getExecutionResult, onSessionCreated: addSession });
  const { injectExecutionResult, requestRunHelp, loadKickoff } = chat;

  // 已主動說明過的執行問題（編譯錯誤簽章 / 逾時狀態）
  const explainedRef = useRef<Set<string>>(new Set());

  /* Run 完成：注入結果卡片；編譯失敗或逾時時 Coddy 主動說明 */
  useEffect(() => {
    return onExecutionComplete((result) => {
      injectExecutionResult(result);
      const output = result.compile_output;
      const status = result.status_description ?? "";
      const timedOut = status.toLowerCase().includes("time limit");
      if (!output && !timedOut) {
        // 跑成功但會印當地時間 → 提醒伺服器時鐘是 UTC（每個 session 一次）
        if (usesLocalTime(getCode()) && !explainedRef.current.has("timezone")) {
          explainedRef.current.add("timezone");
          void requestRunHelp("", status, "timezone");
        }
        return;
      }
      // 逾時沒有編譯訊息，以狀態當簽章
      const signature = output ? errorSignature(output) : status;
      if (explainedRef.current.has(signature)) return;
      explainedRef.current.add(signature);
      void requestRunHelp(output, status);
    });
  }, [onExecutionComplete, injectExecutionResult, requestRunHelp, getCode]);

  /* 從 Output block「詢問 Coddy」按鈕手動注入（含掛載前 queue drain） */
  useEffect(() => {
    return onChatInjectionRequest((result) => injectExecutionResult(result));
  }, [onChatInjectionRequest, injectExecutionResult]);

  /* 實作題 handoff → Coddy 反思開場（含掛載前 queue drain） */
  useEffect(() => {
    return onReflectionKickoff((reflectionId) => void loadKickoff(reflectionId));
  }, [onReflectionKickoff, loadKickoff]);

  return (
    <Ctx value={{ ...chat, sessions, activeId, setActiveId, deleteSession }}>
      {children}
    </Ctx>
  );
}

export function useChatRuntime(): ChatRuntime {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useChatRuntime must be inside ChatRuntimeProvider");
  return ctx;
}
