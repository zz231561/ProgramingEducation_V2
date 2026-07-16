"use client";

/**
 * Workspace 頁 — layout 組裝與狀態接線。
 * 拆檔（250 行硬性線）：
 * - use-run-code.ts — Judge0 執行 + isDirty
 * - use-draft-restore.ts — 進頁還原草稿內容 + 檔名關聯
 * - use-named-file.ts — Ctrl/Cmd+S、另存、開新檔
 */

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
import { useDraftRestore } from "@/components/workspace/use-draft-restore";
import { useNamedFile } from "@/components/workspace/use-named-file";
import { useRunCode } from "@/components/workspace/use-run-code";
import { useWorkspace } from "@/components/workspace/workspace-context";
import {
  ACTIVE_REFLECTION_EVENT,
  getActiveReflectionId,
  getHandedOffReflectionId,
  getHandoffFileName,
  isKickoffDone,
  markKickoffDone,
} from "@/lib/active-reflection";
import { useDraftAutosave } from "@/lib/use-draft-autosave";

export default function WorkspacePage() {
  const [outputCollapsed, setOutputCollapsed] = useState(false);
  // 左側欄互斥：反思計畫 / 我的程式碼 同時只開一個。
  // 初始值含反思 gating（U1c）：只有經「前往 Workspace」正確 handoff 的反思
  // 才自動展開；直接 navigate 的殘留反思會被 getHandedOffReflectionId 清除。
  const [sidePanel, setSidePanel] = useState<"reflection" | "files" | null>(
    () =>
      typeof window !== "undefined" && getHandedOffReflectionId()
        ? "reflection"
        : null,
  );
  const [hasActiveReflection, setHasActiveReflection] = useState(false);
  // 反思綁定的檔名 — 只有開啟該檔時才顯示反思計畫按鈕
  const [reflectionFile, setReflectionFile] = useState<string | null>(null);
  // 受控編輯器內容（載入檔案 / 開新檔時注入）
  const [editorValue, setEditorValue] = useState<string | undefined>(undefined);
  const codeRef = useRef("");
  const workspace = useWorkspace();
  // 解構出穩定 callback，避免以物件為 effect/useCallback 依賴造成重跑
  const { status: saveStatus, schedule: scheduleSave, markSaved } =
    useDraftAutosave();
  // 命名檔案（Ctrl/Cmd+S、另存、開新檔）
  const {
    currentName,
    saveAsOpen,
    setSaveAsOpen,
    savedFlash,
    refreshToken,
    markTyped,
    markLoaded,
    restoreName,
    saveNamed,
    newFile,
  } = useNamedFile({
    getCode: () => codeRef.current,
    injectCode: setEditorValue,
    defaultCode: DEFAULT_CODE,
  });
  // 進頁還原：實作題 handoff 自動開檔，否則還原草稿（null=載入中）
  const draftCode = useDraftRestore({
    defaultCode: DEFAULT_CODE,
    markSaved,
    restoreName,
  });
  const expandOutput = useCallback(() => setOutputCollapsed(false), []);
  const { isRunning, isDirty, markChanged, run } = useRunCode({
    getCode: () => codeRef.current,
    onRunStart: expandOutput,
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
      setReflectionFile(id ? getHandoffFileName() : null);
    };
    update();
    window.addEventListener(ACTIVE_REFLECTION_EVENT, update);
    window.addEventListener("storage", update);
    return () => {
      window.removeEventListener(ACTIVE_REFLECTION_EVENT, update);
      window.removeEventListener("storage", update);
    };
  }, []);

  // 實作題 handoff：自動展開 chat + 請求 Coddy 反思開場（每反思一次）
  const kickoffFiredRef = useRef(false);
  useEffect(() => {
    if (kickoffFiredRef.current || draftCode === null) return;
    const id = getHandedOffReflectionId();
    if (!id || !getHandoffFileName()) return;
    kickoffFiredRef.current = true;
    if (!isKickoffDone(id)) {
      markKickoffDone(id);
      workspace.requestReflectionKickoff(id);
    }
    if (!workspace.chatOpen) workspace.toggleChat();
  }, [draftCode, workspace]);

  const handleCodeChange = useCallback(
    (value: string) => {
      codeRef.current = value;
      workspace.setCode(value);
      markChanged();
      setEditorValue(value);
      scheduleSave(value);
      markTyped(value);
    },
    [workspace, scheduleSave, markChanged, markTyped],
  );

  /** 載入命名檔案至編輯器（後續變更照常自動存入草稿）。 */
  const handleLoadFile = useCallback(
    (code: string, name: string) => {
      markLoaded(code, name);
      setEditorValue(code);
    },
    [markLoaded],
  );

  // 反思按鈕只在「目前開啟檔案 === 反思綁定檔案」時出現（實作題入口）
  const reflectionAvailable =
    reflectionFile !== null && currentName === reflectionFile;
  const effectivePanel =
    sidePanel === "reflection" && !reflectionAvailable ? null : sidePanel;

  const editorAndOutput = (
    <div className="flex h-full flex-col">
      <Toolbar
        fileName={currentName ?? "main.cpp"}
        onRun={run}
        isRunning={isRunning}
        isDirty={isDirty}
        reflectionSidebarOpen={effectivePanel === "reflection"}
        onToggleReflectionSidebar={
          reflectionAvailable ? toggleReflection : undefined
        }
        hasActiveReflection={hasActiveReflection}
        saveStatus={saveStatus}
        codeFilesSidebarOpen={effectivePanel === "files"}
        onToggleCodeFilesSidebar={toggleFiles}
        onNewFile={newFile}
        savedFlash={savedFlash}
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
  const saveDialog = saveAsOpen ? (
    <SaveAsDialog
      suggestedName={currentName ?? "main.cpp"}
      onSave={saveNamed}
      onClose={() => setSaveAsOpen(false)}
    />
  ) : null;

  // 草稿載入完成前不掛編輯器，避免先閃預設範本再被草稿覆蓋
  if (draftCode === null) {
    return null;
  }

  if (effectivePanel === null) {
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
          {effectivePanel === "reflection" ? (
            <ReflectionSidebar onCollapse={toggleReflection} />
          ) : (
            <CodeFilesSidebar
              onSaveAs={saveNamed}
              onLoad={handleLoadFile}
              onCollapse={toggleFiles}
              refreshToken={refreshToken}
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
