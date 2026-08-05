"use client";

/**
 * Workspace 頁 — 狀態接線（版面組裝在 workspace-layout.tsx）。
 * 拆檔（250 行硬性線）：
 * - workspace-layout.tsx — Panel 版面（側欄 / 編輯器 / Output）
 * - use-run-code.ts — Judge0 執行 + isDirty
 * - use-draft-restore.ts — 進頁還原草稿內容 + 檔名關聯
 * - use-named-file.ts — Ctrl/Cmd+S、另存、開新檔
 */

import { useState, useCallback, useEffect, useRef } from "react";
import { CodeEditor, DEFAULT_CODE } from "@/components/editor/code-editor";
import { ReflectionSidebar } from "@/components/reflection/reflection-sidebar";
import { Toolbar } from "@/components/workspace/toolbar";
import { OutputPanel } from "@/components/workspace/output-panel";
import { CodeFilesSidebar } from "@/components/workspace/code-files-sidebar";
import { SaveAsDialog } from "@/components/workspace/save-as-dialog";
import { useDraftRestore } from "@/components/workspace/use-draft-restore";
import { useNamedFile } from "@/components/workspace/use-named-file";
import { useRunCode } from "@/components/workspace/use-run-code";
import { setActiveRunFile } from "@/components/workspace/use-run-history";
import { useReflectionHandoff } from "@/components/workspace/use-reflection-handoff";
import { useWorkspace } from "@/components/workspace/workspace-context";
import { WorkspaceLayout } from "@/components/workspace/workspace-layout";
import { getHandedOffReflectionId } from "@/lib/active-reflection";
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
    renameCurrent,
    newFile,
    resetToDefault,
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
  const { hasActiveReflection, reflectionFile } = useReflectionHandoff({
    ready: draftCode !== null,
    workspace,
  });
  const expandOutput = useCallback(() => setOutputCollapsed(false), []);
  const { isRunning, isDirty, markChanged, run, terminal, resetTerminal } =
    useRunCode({
      getCode: () => codeRef.current,
      onRunStart: expandOutput,
    });

  // 7-U4：切換程式時終端機清空、歷史切換到該檔自己的紀錄
  useEffect(() => {
    setActiveRunFile(currentName);
    resetTerminal();
  }, [currentName, resetTerminal]);

  const toggleOutput = useCallback(() => setOutputCollapsed((v) => !v), []);
  const toggleReflection = useCallback(
    () => setSidePanel((p) => (p === "reflection" ? null : "reflection")),
    [],
  );
  const toggleFiles = useCallback(
    () => setSidePanel((p) => (p === "files" ? null : "files")),
    [],
  );
  const openSaveAs = useCallback(() => setSaveAsOpen(true), [setSaveAsOpen]);

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

  const toolbar = (
    <Toolbar
      fileName={currentName ?? "main.cpp"}
      isNamed={currentName !== null}
      onRename={renameCurrent}
      onSaveAs={openSaveAs}
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
  );

  // 草稿載入完成前不掛編輯器，避免先閃預設範本再被草稿覆蓋
  if (draftCode === null) {
    return null;
  }

  return (
    <>
      <WorkspaceLayout
        toolbar={toolbar}
        editor={
          <CodeEditor
            initialValue={draftCode}
            value={editorValue}
            onChange={handleCodeChange}
          />
        }
        output={
          <OutputPanel
            collapsed={outputCollapsed}
            onToggleCollapse={toggleOutput}
            terminal={terminal}
          />
        }
        outputCollapsed={outputCollapsed}
        sidePanel={
          effectivePanel === "reflection" ? (
            <ReflectionSidebar onCollapse={toggleReflection} />
          ) : effectivePanel === "files" ? (
            <CodeFilesSidebar
              onSaveAs={saveNamed}
              onLoad={handleLoadFile}
              onCollapse={toggleFiles}
              currentName={currentName}
              onDeletedCurrent={resetToDefault}
              refreshToken={refreshToken}
            />
          ) : null
        }
      />
      {/* Ctrl/Cmd+S 於未命名檔案 → 另存對話框（檔名預填反白） */}
      {saveAsOpen && (
        <SaveAsDialog
          suggestedName={currentName ?? "main.cpp"}
          onSave={saveNamed}
          onClose={() => setSaveAsOpen(false)}
        />
      )}
    </>
  );
}
