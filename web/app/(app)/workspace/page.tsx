"use client";

import { useState, useCallback, useRef } from "react";
import {
  Panel,
  Group as PanelGroup,
  Separator as PanelResizeHandle,
} from "react-resizable-panels";
import { CodeEditor } from "@/components/editor/code-editor";
import { Toolbar } from "@/components/workspace/toolbar";
import { OutputPanel } from "@/components/workspace/output-panel";
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

export default function WorkspacePage() {
  const [outputCollapsed, setOutputCollapsed] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const codeRef = useRef("");
  const workspace = useWorkspace();

  const toggleOutput = useCallback(() => setOutputCollapsed((v) => !v), []);

  const handleCodeChange = useCallback((value: string) => {
    codeRef.current = value;
    workspace.setCode(value);
  }, [workspace]);

  const handleRun = useCallback(async () => {
    const code = codeRef.current;
    if (!code.trim()) return;

    setIsRunning(true);
    setOutputCollapsed(false);

    try {
      const result = await api<ExecuteResponse>("/code/execute", {
        method: "POST",
        body: JSON.stringify({ code }),
      });

      // 推送至 context — OutputPanel 與 ChatPanel 透過 listener 各自處理
      workspace.setExecutionResult({
        stdout: result.stdout,
        stderr: result.stderr,
        compile_output: result.compile_output,
        exit_code: result.exit_code ?? -1,
        status_description: result.status_description,
        time: result.time ?? undefined,
        memory: result.memory ?? undefined,
      });
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
  }, [workspace]);

  return (
    <div className="flex h-full flex-col">
      <Toolbar onRun={handleRun} isRunning={isRunning} />

      {outputCollapsed ? (
        <>
          <div className="min-h-0 flex-1">
            <CodeEditor onChange={handleCodeChange} />
          </div>
          <OutputPanel collapsed onToggleCollapse={toggleOutput} />
        </>
      ) : (
        <PanelGroup orientation="vertical" className="min-h-0 flex-1">
          <Panel defaultSize={70} minSize={30}>
            <CodeEditor onChange={handleCodeChange} />
          </Panel>
          <PanelResizeHandle className="relative flex h-1 items-center justify-center transition-colors before:absolute before:inset-x-0 before:h-px before:bg-border-default hover:before:bg-accent-blue data-[resize-handle-active]:before:bg-accent-blue" />
          <Panel defaultSize={30} minSize={15}>
            <OutputPanel collapsed={false} onToggleCollapse={toggleOutput} />
          </Panel>
        </PanelGroup>
      )}
    </div>
  );
}
