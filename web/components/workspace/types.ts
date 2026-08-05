/**
 * Workspace 共用型別 — 抽出以避免 context ⇄ run-history hook 的循環相依。
 */

/** Judge0 執行結果 */
export interface ExecutionResult {
  stdout: string;
  stderr: string;
  compile_output: string;
  exit_code: number;
  status_description?: string;
  time?: string;
  memory?: number;
}

/** 一次執行的歷史記錄（Run #N） */
export interface RunRecord {
  id: number;
  timestamp: number;
  result: ExecutionResult;
}
