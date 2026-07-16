"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import {
  Panel,
  Group as PanelGroup,
  Separator as PanelResizeHandle,
} from "react-resizable-panels";
import { CodeEditor, DEFAULT_CODE } from "@/components/editor/code-editor";
import { ReflectionSidebar } from "@/components/reflection/reflection-sidebar";
import { Toolbar } from "@/components/workspace/toolbar";
import { OutputPanel } from "@/components/workspace/output-panel";
import { CodeFilesSidebar } from "@/components/workspace/code-files-sidebar";
import { SaveAsDialog } from "@/components/workspace/save-as-dialog";
import { useNamedFile } from "@/components/workspace/use-named-file";
import { useWorkspace } from "@/components/workspace/workspace-context";
import { api } from "@/lib/api";
import {
  ACTIVE_REFLECTION_EVENT,
  getActiveReflectionId,
  getHandedOffReflectionId,
} from "@/lib/active-reflection";
import { getDraft } from "@/lib/code-files";
import { useDraftAutosave } from "@/lib/use-draft-autosave";

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
  // 左側欄互斥：反思計畫 / 我的程式碼 同時只開一個
  const [sidePanel, setSidePanel] = useState<"reflection" | "files" | null>(null);
  const [hasActiveReflection, setHasActiveReflection] = useState(false);
  // U2e 程式碼存檔：草稿還原（null=載入中）+ 受控內容
  const [draftCode, setDraftCode] = useState<string | null | undefined>(null);
  const [editorValue, setEditorValue] = useState<string | undefined>(undefined);
  const codeRef = useRef("");
  const workspace = useWorkspace();
  // 解構出穩定 callback，避免以物件為 effect/useCallback 依賴造成重跑
  const { status: saveStatus, schedule: scheduleSave, markSaved } =
    useDraftAutosave();
  // 命名檔案（Ctrl/Cmd+S、另存、開新檔）
  const file = useNamedFile({
    getCode: () => codeRef.current,
    injectCode: setEditorValue,
    defaultCode: DEFAULT_CODE,
  });

  const toggleOutput = useCallback(() => setOutputCollapsed((v) => !v), []);
  const toggleReflection = useCallback(
    () => setSidePanel((p) => (p === "reflection" ? null : "reflection")),
    [],
  );
  const toggleFiles = useCallback(
    () => setSidePanel((p) => (p === "files" ? null : "files")),
    [],
  );

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

  // 進入 Workspace 先還原草稿（U2e）；404/失敗 fail-open 用預設範本
  useEffect(() => {
    let cancelled = false;
    getDraft().then(
      (d) => {
        if (cancelled) return;
        markSaved(d.code);
        setDraftCode(d.code);
      },
      () => !cancelled && setDraftCode(undefined),
    );
    return () => {
      cancelled = true;
    };
  }, [markSaved]);

  // 進入 Workspace 時的反思 gating（U1c）：
  // 只有經「前往 Workspace」按鈕正確 handoff 的反思才顯示並自動展開；
  // 直接 navigate 進來的殘留反思會被 getHandedOffReflectionId 清除。
  useEffect(() => {
    if (getHandedOffReflectionId()) setSidePanel("reflection");
  }, []);

  const handleCodeChange = useCallback(
    (value: string) => {
      codeRef.current = value;
      workspace.setCode(value);
      setIsDirty(true);
      setEditorValue(value);
      scheduleSave(value);
      file.markTyped(value);
    },
    [workspace, scheduleSave, file.markTyped], // eslint-disable-line react-hooks/exhaustive-deps
  );

  /** 載入命名檔案至編輯器（後續變更照常自動存入草稿）。 */
  const handleLoadFile = useCallback(
    (code: string, name: string) => {
      file.markLoaded(code, name);
      setEditorValue(code);
    },
    [file.markLoaded], // eslint-disable-line react-hooks/exhaustive-deps
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
        fileName={file.currentName ?? "main.cpp"}
        onRun={handleRun}
        isRunning={isRunning}
        isDirty={isDirty}
        reflectionSidebarOpen={sidePanel === "reflection"}
        onToggleReflectionSidebar={toggleReflection}
        hasActiveReflection={hasActiveReflection}
        saveStatus={saveStatus}
        codeFilesSidebarOpen={sidePanel === "files"}
        onToggleCodeFilesSidebar={toggleFiles}
        onNewFile={file.newFile}
        savedFlash={file.savedFlash}
      />
      {outputCollapsed ? (
        <>
          <div className="min-h-0 flex-1">
            <CodeEditor
              initialValue={draftCode ?? undefined}
              value={editorValue}
              onChange={handleCodeChange}
            />
          </div>
          <OutputPanel collapsed onToggleCollapse={toggleOutput} />
        </>
      ) : (
        <PanelGroup orientation="vertical" className="min-h-0 flex-1">
          {/* react-resizable-panels v4：裸數字是 px，百分比必須用字串（U1b） */}
          <Panel defaultSize="70%" minSize="30%">
            <CodeEditor
              initialValue={draftCode ?? undefined}
              value={editorValue}
              onChange={handleCodeChange}
            />
          </Panel>
          <PanelResizeHandle className="relative flex h-1 items-center justify-center transition-colors before:absolute before:inset-x-0 before:h-px before:bg-border-default hover:before:bg-accent-blue data-[resize-handle-active]:before:bg-accent-blue" />
          <Panel defaultSize="30%" minSize="15%">
            <OutputPanel collapsed={false} onToggleCollapse={toggleOutput} />
          </Panel>
        </PanelGroup>
      )}
    </div>
  );

  // Ctrl/Cmd+S 於未命名檔案 → 另存對話框（檔名預填反白）
  const saveDialog = file.saveAsOpen ? (
    <SaveAsDialog
      suggestedName={file.currentName ?? "main.cpp"}
      onSave={file.saveNamed}
      onClose={() => file.setSaveAsOpen(false)}
    />
  ) : null;

  // 草稿載入完成前不掛編輯器，避免先閃預設範本再被草稿覆蓋
  if (draftCode === null) {
    return null;
  }

  if (sidePanel === null) {
    return (
      <>
        {editorAndOutput}
        {saveDialog}
      </>
    );
  }

  return (
    <>
    <PanelGroup orientation="horizontal" className="h-full">
      <Panel defaultSize="28%" minSize="20%" maxSize="40%">
        {sidePanel === "reflection" ? (
          <ReflectionSidebar onCollapse={toggleReflection} />
        ) : (
          <CodeFilesSidebar
            onSaveAs={file.saveNamed}
            onLoad={handleLoadFile}
            onCollapse={toggleFiles}
            refreshToken={file.refreshToken}
          />
        )}
      </Panel>
      <PanelResizeHandle className="relative flex w-1 items-center justify-center transition-colors before:absolute before:inset-y-0 before:w-px before:bg-border-default hover:before:bg-accent-blue data-[resize-handle-active]:before:bg-accent-blue" />
      <Panel minSize="40%">{editorAndOutput}</Panel>
    </PanelGroup>
    {saveDialog}
    </>
  );
}
