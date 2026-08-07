"use client";

/**
 * 概念說明 tab — grounded 內容渲染、YouTube player 與時間跳轉。
 *
 * 三種狀態優先順序：
 * 1. 無 video_youtube_id（教授尚未補資料）→ placeholder
 * 2. 有影片但無 grounded content（content.concept_explanation 未生成 / promote）
 *    → 仍嵌入 player + 簡短說明
 * 3. 完整 grounded → player + Markdown（句尾註腳式播放標記可跳轉影片）
 *
 * 不顯示「影片出處」清單；句中 `[00:15]` 戳記會改寫為段尾標記。
 */

import { useMemo, useRef } from "react";
import { MonitorPlay, Play } from "lucide-react";

import { MarkdownContent } from "@/components/ui/markdown";
import { Unit } from "@/lib/learning";
import {
  rewriteTimestamps,
  seekSecondsFromHref,
} from "@/lib/transcript-timestamps";

import {
  YouTubePlayer,
  type YouTubePlayerHandle,
} from "./youtube-player";

interface Props {
  unit: Unit;
}

export function ConceptTab({ unit }: Props) {
  const playerRef = useRef<YouTubePlayerHandle>(null);
  const youtubeId = unit.video_youtube_id;

  if (!youtubeId) {
    return (
      <div className="space-y-4">
        <VideoPlaceholder />
        <FallbackIntro unit={unit} />
      </div>
    );
  }

  const explanation = unit.content.concept_explanation;
  const hasGrounded =
    !!explanation && !explanation.needs_more_source && !!explanation.markdown;

  return (
    <div className="space-y-4">
      <YouTubePlayer ref={playerRef} videoId={youtubeId} />
      {hasGrounded ? (
        <GroundedExplanation
          markdown={explanation.markdown}
          onSeek={(seconds) => playerRef.current?.seekTo(seconds)}
        />
      ) : (
        <PendingContentNotice
          reason={explanation?.reason ?? null}
          unit={unit}
        />
      )}
    </div>
  );
}

/**
 * grounded 內文 —— 7-U3：移除「影片出處」清單（與 Coddy 教材出處一致），
 * 句中的 `[00:15]` 戳記改寫為**句尾註腳式播放標記**，點擊跳轉影片。
 */
function GroundedExplanation({
  markdown,
  onSeek,
}: {
  markdown: string;
  onSeek: (seconds: number) => void;
}) {
  const rewritten = useMemo(() => rewriteTimestamps(markdown), [markdown]);
  const components = useMemo(
    () => ({
      a: ({ href, children }: { href?: string; children?: React.ReactNode }) => {
        const seconds = seekSecondsFromHref(href);
        if (seconds === null) {
          return (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-text-link underline underline-offset-2 hover:no-underline"
            >
              {children}
            </a>
          );
        }
        return <SeekMarker seconds={seconds} onSeek={onSeek}>{children}</SeekMarker>;
      },
    }),
    [onSeek],
  );

  return (
    <div className="rounded-md border border-border-default bg-surface-1 p-4 text-sm leading-relaxed text-text-secondary">
      <MarkdownContent components={components}>{rewritten}</MarkdownContent>
    </div>
  );
}

/** 註腳式播放標記：平常淡灰，hover 變藍 */
function SeekMarker({
  seconds,
  onSeek,
  children,
}: {
  seconds: number;
  onSeek: (seconds: number) => void;
  children?: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={() => onSeek(seconds)}
      title="跳到影片這個時間點"
      className="ml-1 inline-flex translate-y-[1px] items-center gap-0.5 align-baseline font-mono text-xs text-text-muted transition-colors hover:text-text-link"
    >
      <Play className="size-2.5 fill-current" />
      {children}
    </button>
  );
}

function PendingContentNotice({
  reason,
  unit,
}: {
  reason: string | null;
  unit: Unit;
}) {
  return (
    <div className="rounded-md border border-border-default bg-surface-1 p-4">
      <h3 className="text-sm font-medium text-text-primary">概念簡介</h3>
      <p className="mt-2 text-sm leading-relaxed text-text-secondary">
        這個單元對應 C++ 課程的「{unit.concept_name_zh}」。
        詳細教學內容由教授提供的 YouTube 影片提供（上方播放器）。
      </p>
      {reason && (
        <p className="mt-2 text-xs text-text-muted">
          說明：{reason}
        </p>
      )}
    </div>
  );
}

function FallbackIntro({ unit }: { unit: Unit }) {
  return (
    <div className="rounded-md border border-border-default bg-surface-1 p-4">
      <h3 className="text-sm font-medium text-text-primary">概念簡介</h3>
      <p className="mt-2 text-sm leading-relaxed text-text-secondary">
        這個單元對應 C++ 課程的「{unit.concept_name_zh}」。
        詳細教學內容由教授提供的 YouTube 影片提供（待 video_id 匯入後此處顯示播放器）。
      </p>
    </div>
  );
}

function VideoPlaceholder() {
  return (
    <div className="flex aspect-video w-full items-center justify-center rounded-md border border-border-default bg-bg-inset text-text-muted">
      <div className="text-center">
        <MonitorPlay className="mx-auto size-10" />
        <p className="mt-2 text-sm">教學影片（YT player 待整合）</p>
        <p className="mt-1 text-xs text-text-muted/70">
          教授提供影片 ID 後即可播放
        </p>
      </div>
    </div>
  );
}
