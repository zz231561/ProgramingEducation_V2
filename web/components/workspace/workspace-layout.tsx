"use client";

/**
 * Workspace 版面組裝（2026-08-05 由 page.tsx 拆出，250 行硬性線）。
 *
 * 側邊欄開合時**永遠渲染同一棵 PanelGroup**，只讓側欄 slot 在有/無之間切換——
 * 原本是「有側欄 → PanelGroup / 無側欄 → Fragment」兩種根節點，切換時整棵子樹
 * 被 unmount，編輯器與 Output 一併重建（Output 因此清空）。
 */

import {
  Panel,
  Group as PanelGroup,
  Separator as PanelResizeHandle,
} from "react-resizable-panels";

const HANDLE_CLASS =
  "relative flex items-center justify-center transition-colors before:absolute before:bg-border-default hover:before:bg-accent-blue data-[resize-handle-active]:before:bg-accent-blue";

export function WorkspaceLayout({
  toolbar,
  editor,
  output,
  outputCollapsed,
  sidePanel,
}: {
  toolbar: React.ReactNode;
  editor: React.ReactNode;
  output: React.ReactNode;
  /** 收合時 Output 為單行 status bar，不佔可調整面板 */
  outputCollapsed: boolean;
  /** 反思計畫 / 我的程式碼（互斥，null = 不顯示） */
  sidePanel: React.ReactNode | null;
}) {
  const main = (
    <div className="flex h-full flex-col">
      {toolbar}
      {outputCollapsed ? (
        <>
          <div className="min-h-0 flex-1">{editor}</div>
          {output}
        </>
      ) : (
        <PanelGroup orientation="vertical" className="min-h-0 flex-1">
          {/* react-resizable-panels v4：裸數字是 px，百分比必須用字串（U1b） */}
          <Panel defaultSize="70%" minSize="30%">
            {editor}
          </Panel>
          <PanelResizeHandle className={`h-1 ${HANDLE_CLASS} before:inset-x-0 before:h-px`} />
          <Panel defaultSize="30%" minSize="15%">
            {output}
          </Panel>
        </PanelGroup>
      )}
    </div>
  );

  return (
    <PanelGroup orientation="horizontal" className="h-full">
      {sidePanel && (
        <>
          <Panel defaultSize="28%" minSize="20%" maxSize="40%">
            {sidePanel}
          </Panel>
          <PanelResizeHandle className={`w-1 ${HANDLE_CLASS} before:inset-y-0 before:w-px`} />
        </>
      )}
      <Panel minSize="40%">{main}</Panel>
    </PanelGroup>
  );
}
