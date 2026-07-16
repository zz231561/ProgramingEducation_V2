"use client";

/**
 * 程式碼執行 hook — 提交 /code/execute（Judge0）並把結果寫進 workspace context。
 * 自 workspace/page.tsx 拆出（250 行硬性線）。
 */

import { useCallback, useState } from "react";

import { useWorkspace } from "@/components/workspace/workspace-context";
import { api } from "@/lib/api";

/** 後端 /code/execute 回傳格式 */
interface ExecuteResponse {
  stdout: string;
  stderr: string;
  compile_output: string;
  exit_code: number | null;
  time: string | null;
  memory: number | null;
  status_description: string;
}

export function useRunCode({
  getCode,
  onRunStart,
}: {
  /** 取得編輯器目前內容 */
  getCode: () => string;
  /** 開始執行時呼叫（展開 output 面板） */
  onRunStart: () => void;
}) {
  const workspace = useWorkspace();
  const [isRunning, setIsRunning] = useState(false);
  // 程式碼自上次成功執行後是否已修改（Toolbar dot）
  const [isDirty, setIsDirty] = useState(false);

  const markChanged = useCallback(() => setIsDirty(true), []);

  const run = useCallback(async () => {
    const code = getCode();
    if (!code.trim()) return;

    setIsRunning(true);
    onRunStart();

    try {
      const result = await api<ExecuteResponse>("/code/execute", {
        method: "POST",
        body: JSON.stringify({ code }),
      });

      workspace.setExecutionResult({
        stdout: result.stdout,
        stderr: result.stderr,
        compile_output: result.compile_output,
        exit_code: result.exit_code ?? -1,
        status_description: result.status_description,
        time: result.time ?? undefined,
        memory: result.memory ?? undefined,
      });
      setIsDirty(false);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "未知錯誤";
      workspace.setExecutionResult({
        stdout: "",
        stderr: msg,
        compile_output: "",
        exit_code: -1,
        status_description: "Internal Error",
      });
    } finally {
      setIsRunning(false);
    }
  }, [workspace, getCode, onRunStart]);

  return { isRunning, isDirty, markChanged, run };
}
