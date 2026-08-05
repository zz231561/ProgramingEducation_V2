"use client";

/**
 * xterm 畫布 — 嵌在 Output 面板內（非 modal：寫程式時必須看得到程式碼）。
 *
 * PTY 端已由 kernel 行規範處理回顯與行編輯，前端**不做 local echo**，
 * 按鍵原樣送出即可（這是 PTY 相對 pipe 的直接好處）。
 */

import { useEffect, useRef } from "react";
import type { Terminal } from "@xterm/xterm";

import {
  TERMINAL_FONT,
  TERMINAL_FONT_SIZE,
  TERMINAL_THEME,
} from "@/lib/terminal-theme";

export interface TerminalHandle {
  write: (data: string) => void;
  clear: () => void;
}

export function TerminalView({
  onData,
  onReady,
}: {
  onData: (data: string) => void;
  onReady: (handle: TerminalHandle) => void;
}) {
  const hostRef = useRef<HTMLDivElement>(null);
  // 以 ref 持有回呼，避免 prop 變動觸發終端機重建（會清空畫面）
  const onDataRef = useRef(onData);
  const onReadyRef = useRef(onReady);
  onDataRef.current = onData;
  onReadyRef.current = onReady;

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    let term: Terminal | null = null;
    let observer: ResizeObserver | null = null;
    let disposed = false;

    // xterm 觸碰 window/document，必須動態載入避開 SSR
    void (async () => {
      const [{ Terminal: Term }, { FitAddon }] = await Promise.all([
        import("@xterm/xterm"),
        import("@xterm/addon-fit"),
      ]);
      await import("@xterm/xterm/css/xterm.css");
      if (disposed) return;

      term = new Term({
        theme: { ...TERMINAL_THEME },
        fontFamily: TERMINAL_FONT,
        fontSize: TERMINAL_FONT_SIZE,
        lineHeight: 1.4,
        cursorBlink: true,
        scrollback: 3000,
        convertEol: false, // PTY 已送 \r\n
      });
      const fit = new FitAddon();
      term.loadAddon(fit);
      term.open(host);
      fit.fit();
      term.focus();
      term.onData((d) => onDataRef.current(d));

      observer = new ResizeObserver(() => {
        try {
          fit.fit();
        } catch {
          /* 面板收合時容器為 0 高，忽略 */
        }
      });
      observer.observe(host);

      onReadyRef.current({
        write: (data: string) => term?.write(data),
        clear: () => term?.clear(),
      });
    })();

    return () => {
      disposed = true;
      observer?.disconnect();
      term?.dispose();
    };
  }, []);

  return (
    <div
      ref={hostRef}
      className="h-full w-full overflow-hidden rounded-md border border-border-default bg-bg-inset p-1.5"
    />
  );
}
