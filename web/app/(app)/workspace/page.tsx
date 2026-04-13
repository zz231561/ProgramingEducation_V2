"use client";

import { useState, useCallback, useRef } from "react";
import {
  Panel,
  Group as PanelGroup,
  Separator as PanelResizeHandle,
} from "react-resizable-panels";
import { CodeEditor } from "@/components/editor/code-editor";
import { Toolbar } from "@/components/workspace/toolbar";
import { OutputPanel, type OutputData } from "@/components/workspace/output-panel";
import { StdinPanel } from "@/components/workspace/stdin-panel";
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

const EMPTY_OUTPUT: OutputData = { stdout: "", stderr: "", compile: "" };

export default function WorkspacePage() {
  const [outputCollapsed, setOutputCollapsed] = useState(false);
  const [output, setOutput] = useState<OutputData>(EMPTY_OUTPUT);
  const [isRunning, setIsRunning] = useState(false);
  const [statusText, setStatusText] = useState<string | undefined>();
  const [stdinOpen, setStdinOpen] = useState(false);
  const [stdin, setStdin] = useState("");
  const codeRef = useRef("");

  const toggleOutput = useCallback(
    () => setOutputCollapsed((v) => !v),
    [],
  );

  const toggleStdin = useCallback(
    () => setStdinOpen((v) => !v),
    [],
  );

  const handleCodeChange = useCallback((value: string) => {
    codeRef.current = value;
  }, []);

  const handleRun = useCallback(async () => {
    const code = codeRef.current;
    if (!code.trim()) return;

    setIsRunning(true);
    setOutputCollapsed(false);
    setStatusText("⏳ Running...");
    setOutput(EMPTY_OUTPUT);

    try {
      const result = await api<ExecuteResponse>("/code/execute", {
        method: "POST",
        body: JSON.stringify({ code, stdin }),
      });

      setOutput({
        stdout: result.stdout,
        stderr: result.stderr,
        compile: result.compile_output,
      });

      if (result.status_description === "Accepted") {
        setStatusText(`✓ Passed (${result.time ?? "?"}s)`);
      } else {
        setStatusText(`✗ ${result.status_description}`);
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "未知錯誤";
      setOutput({ stdout: "", stderr: msg, compile: "" });
      setStatusText("✗ Error");
    } finally {
      setIsRunning(false);
    }
  }, [stdin]);

  /** Editor 區塊（含 stdin panel） */
  const editorBlock = (
    <div className="flex h-full flex-col">
      {stdinOpen && (
        <StdinPanel
          value={stdin}
          onChange={setStdin}
          onClose={() => setStdinOpen(false)}
        />
      )}
      <div className="min-h-0 flex-1">
        <CodeEditor onChange={handleCodeChange} />
      </div>
    </div>
  );

  return (
    <div className="flex h-full flex-col">
      <Toolbar
        onRun={handleRun}
        isRunning={isRunning}
        onToggleStdin={toggleStdin}
        stdinOpen={stdinOpen}
      />

      {outputCollapsed ? (
        <>
          {editorBlock}
          <OutputPanel
            collapsed
            onToggleCollapse={toggleOutput}
            statusText={statusText}
          />
        </>
      ) : (
        <PanelGroup orientation="vertical" className="min-h-0 flex-1">
          <Panel defaultSize={70} minSize={30}>
            {editorBlock}
          </Panel>
          <PanelResizeHandle className="h-px bg-border-default hover:bg-accent-blue transition-colors data-[resize-handle-active]:bg-accent-blue" />
          <Panel defaultSize={30} minSize={15}>
            <OutputPanel
              output={output}
              collapsed={false}
              onToggleCollapse={toggleOutput}
              statusText={statusText}
            />
          </Panel>
        </PanelGroup>
      )}
    </div>
  );
}
