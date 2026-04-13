"use client";

import { useState, useCallback } from "react";
import {
  Panel,
  Group as PanelGroup,
  Separator as PanelResizeHandle,
} from "react-resizable-panels";
import { CodeEditor } from "@/components/editor/code-editor";
import { Toolbar } from "@/components/workspace/toolbar";
import { OutputPanel, type OutputData } from "@/components/workspace/output-panel";

const EMPTY_OUTPUT: OutputData = { stdout: "", stderr: "", compile: "" };

export default function WorkspacePage() {
  const [outputCollapsed, setOutputCollapsed] = useState(false);
  const [output] = useState<OutputData>(EMPTY_OUTPUT);

  const toggleOutput = useCallback(
    () => setOutputCollapsed((v) => !v),
    [],
  );

  return (
    <div className="flex h-full flex-col">
      {/* Toolbar */}
      <Toolbar />

      {/* Editor + Output 垂直分割 */}
      {outputCollapsed ? (
        <>
          <div className="min-h-0 flex-1">
            <CodeEditor />
          </div>
          <OutputPanel collapsed onToggleCollapse={toggleOutput} />
        </>
      ) : (
        <PanelGroup orientation="vertical" className="min-h-0 flex-1">
          <Panel defaultSize={70} minSize={30}>
            <CodeEditor />
          </Panel>
          <PanelResizeHandle className="h-px bg-border-default hover:bg-accent-blue transition-colors data-[resize-handle-active]:bg-accent-blue" />
          <Panel defaultSize={30} minSize={15}>
            <OutputPanel
              output={output}
              collapsed={false}
              onToggleCollapse={toggleOutput}
            />
          </Panel>
        </PanelGroup>
      )}
    </div>
  );
}
