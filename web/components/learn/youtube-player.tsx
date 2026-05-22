"use client";

/**
 * YouTube IFrame Player wrapper（Phase 6-2c）— 概念說明 tab 用。
 *
 * 設計：
 * - 用官方 IFrame Player API（不是純 iframe src）→ 才能 imperative seekTo
 * - 透過 ref 暴露 `seekTo(seconds)`，讓父層 citation 列表點擊跳轉
 * - 全域 YT script 只 inject 一次（多 player 共用）
 * - videoId 切換（單元換頁）時自動 cueVideoById 重置
 *
 * 不處理：autoplay、播放完成事件、進度回報（6-2c 不需要）。
 */

import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
} from "react";

// 最小化的 YT IFrame API 型別宣告 — 只覆蓋本元件用到的 method/event
interface YTPlayer {
  seekTo(seconds: number, allowSeekAhead: boolean): void;
  cueVideoById(videoId: string): void;
  destroy(): void;
}

interface YTPlayerOptions {
  videoId: string;
  width?: string | number;
  height?: string | number;
  playerVars?: Record<string, string | number>;
  events?: {
    onReady?: (event: { target: YTPlayer }) => void;
  };
}

interface YTApi {
  Player: new (element: HTMLElement, options: YTPlayerOptions) => YTPlayer;
}

declare global {
  interface Window {
    YT?: YTApi;
    onYouTubeIframeAPIReady?: () => void;
  }
}

export interface YouTubePlayerHandle {
  /** 跳轉至指定秒數並開始播放。Player 尚未就緒時自動延後執行。 */
  seekTo: (seconds: number) => void;
}

interface Props {
  videoId: string;
  className?: string;
}

let apiScriptLoading: Promise<void> | null = null;

function loadYouTubeApi(): Promise<void> {
  if (typeof window === "undefined") return Promise.resolve();
  if (window.YT && window.YT.Player) return Promise.resolve();
  if (apiScriptLoading) return apiScriptLoading;
  apiScriptLoading = new Promise<void>((resolve) => {
    const prevReady = window.onYouTubeIframeAPIReady;
    window.onYouTubeIframeAPIReady = () => {
      prevReady?.();
      resolve();
    };
    const tag = document.createElement("script");
    tag.src = "https://www.youtube.com/iframe_api";
    document.head.appendChild(tag);
  });
  return apiScriptLoading;
}

export const YouTubePlayer = forwardRef<YouTubePlayerHandle, Props>(
  function YouTubePlayer({ videoId, className }, ref) {
    const containerRef = useRef<HTMLDivElement>(null);
    const playerRef = useRef<YTPlayer | null>(null);
    const pendingSeekRef = useRef<number | null>(null);

    // 初始化 + videoId 變更時 cue 新影片
    useEffect(() => {
      let cancelled = false;
      loadYouTubeApi().then(() => {
        if (cancelled || !containerRef.current || !window.YT) return;
        if (playerRef.current) {
          playerRef.current.cueVideoById(videoId);
          return;
        }
        playerRef.current = new window.YT.Player(containerRef.current, {
          videoId,
          width: "100%",
          height: "100%",
          playerVars: { rel: 0, modestbranding: 1, playsinline: 1 },
          events: {
            onReady: () => {
              if (pendingSeekRef.current != null && playerRef.current) {
                playerRef.current.seekTo(pendingSeekRef.current, true);
                pendingSeekRef.current = null;
              }
            },
          },
        });
      });
      return () => {
        cancelled = true;
      };
    }, [videoId]);

    // 元件卸載時清掉 player
    useEffect(() => {
      return () => {
        playerRef.current?.destroy();
        playerRef.current = null;
      };
    }, []);

    useImperativeHandle(ref, () => ({
      seekTo: (seconds: number) => {
        if (playerRef.current) {
          playerRef.current.seekTo(seconds, true);
        } else {
          // Player 尚未 ready → 暫存，onReady 時補跳
          pendingSeekRef.current = seconds;
        }
      },
    }));

    return (
      <div
        className={`aspect-video w-full overflow-hidden rounded-md border border-border-default bg-bg-inset ${className ?? ""}`}
      >
        <div ref={containerRef} className="size-full" />
      </div>
    );
  },
);
