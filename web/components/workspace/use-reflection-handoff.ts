"use client";

/**
 * 實作題 handoff 接線：
 * - 追蹤 sessionStorage 的 active reflection → toolbar dot 與反思按鈕的顯示條件
 * - 經正確 handoff 進入時自動展開 chat 並請求 Coddy 反思開場（每份反思一次，U2i）
 */

import { useEffect, useRef, useState } from "react";

import {
  ACTIVE_REFLECTION_EVENT,
  getActiveReflectionId,
  getHandedOffReflectionId,
  getHandoffFileName,
  isKickoffDone,
  markKickoffDone,
} from "@/lib/active-reflection";

interface WorkspaceChat {
  chatOpen: boolean;
  toggleChat: () => void;
  requestReflectionKickoff: (reflectionId: string) => void;
}

export function useReflectionHandoff({
  ready,
  workspace,
}: {
  /** 草稿還原完成前不觸發 kickoff */
  ready: boolean;
  workspace: WorkspaceChat;
}): { hasActiveReflection: boolean; reflectionFile: string | null } {
  const [hasActiveReflection, setHasActiveReflection] = useState(false);
  // 反思綁定的檔名 — 只有開啟該檔時才顯示反思計畫按鈕
  const [reflectionFile, setReflectionFile] = useState<string | null>(null);

  // 訂閱 sessionStorage 變化（同分頁自訂事件 + 跨分頁 storage 事件）
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

  const kickoffFiredRef = useRef(false);
  useEffect(() => {
    if (kickoffFiredRef.current || !ready) return;
    const id = getHandedOffReflectionId();
    if (!id || !getHandoffFileName()) return;
    kickoffFiredRef.current = true;
    if (!isKickoffDone(id)) {
      markKickoffDone(id);
      workspace.requestReflectionKickoff(id);
    }
    if (!workspace.chatOpen) workspace.toggleChat();
  }, [ready, workspace]);

  return { hasActiveReflection, reflectionFile };
}
