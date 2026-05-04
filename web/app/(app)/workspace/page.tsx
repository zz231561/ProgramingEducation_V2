"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import {
  Panel,
  Group as PanelGroup,
  Separator as PanelResizeHandle,
} from "react-resizable-panels";
import { CodeEditor } from "@/components/editor/code-editor";
import { ReflectionSidebar } from "@/components/reflection/reflection-sidebar";
import { Toolbar } from "@/components/workspace/toolbar";
import { OutputPanel } from "@/components/workspace/output-panel";
import { useWorkspace } from "@/components/workspace/workspace-context";
import { api } from "@/lib/api";
import {
  ACTIVE_REFLECTION_EVENT,
  getActiveReflectionId,
} from "@/lib/active-reflection";

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
  const [isDirty, setIsDirty] = useState(false);
  const [reflectionOpen, setReflectionOpen] = useState(false);
  const [hasActiveReflection, setHasActiveReflection] = useState(false);
  const codeRef = useRef("");
  const workspace = useWorkspace();

  const toggleOutput = useCallback(() => setOutputCollapsed((v) => !v), []);
  const toggleReflection = useCallback(() => setReflectionOpen((v) => !v), []);

  // 訂閱 sessionStorage 變化，控制 toolbar dot 與「初次自動展開」
  useEffect(() => {
    const update = () => {
      const id = getActiveReflectionId();
      setHasActiveReflection(!!id);
    };
    update();
    window.addEventListener(ACTIVE_REFLECTION_EVENT, update);
    window.addEventListener("storage", update);
    return () => {
      window.removeEventListener(ACTIVE_REFLECTION_EVENT, update);
      window.removeEventListener("storage", update);
    };
  }, []);

  // 進入 Workspace 時若有 active reflection（例如剛從 Quiz 跳來），自動展開
  useEffect(() => {
    if (getActiveReflectionId()) setReflectionOpen(true);
  }, []);

  const handleCodeChange = useCallback(
    (value: string) => {
      codeRef.current = value;
      workspace.setCode(value);
      setIsDirty(true);
    },
    [workspace],
  );

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
  }, [workspace]);

  const editorAndOutput = (
    <div className="flex h-full flex-col">
      <Toolbar
        onRun={handleRun}
        isRunning={isRunning}
        isDirty={isDirty}
        reflectionSidebarOpen={reflectionOpen}
        onToggleReflectionSidebar={toggleReflection}
        hasActiveReflection={hasActiveReflection}
      />
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

  if (!reflectionOpen) {
    return editorAndOutput;
  }

  return (
    <PanelGroup orientation="horizontal" className="h-full">
      <Panel defaultSize={28} minSize={20} maxSize={40}>
        <ReflectionSidebar onCollapse={toggleReflection} />
      </Panel>
      <PanelResizeHandle className="relative flex w-1 items-center justify-center transition-colors before:absolute before:inset-y-0 before:w-px before:bg-border-default hover:before:bg-accent-blue data-[resize-handle-active]:before:bg-accent-blue" />
      <Panel minSize={40}>{editorAndOutput}</Panel>
    </PanelGroup>
  );
}
