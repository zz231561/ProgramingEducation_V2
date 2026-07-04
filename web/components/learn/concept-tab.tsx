"use client";

/**
 * 概念說明 tab（Phase 6-2c）— grounded 內容渲染 + YT player + citation 跳轉。
 *
 * 三種狀態優先順序：
 * 1. 無 video_youtube_id（教授尚未補資料）→ placeholder
 * 2. 有影片但無 grounded content（content.concept_explanation 未生成 / promote）
 *    → 仍嵌入 player + 簡短說明
 * 3. 完整 grounded → player + Markdown + citations 列表（點擊跳轉影片時間）
 */

import { useRef } from "react";
import { MonitorPlay } from "lucide-react";

import { MarkdownContent } from "@/components/ui/markdown";
import { Citation, Unit } from "@/lib/learning";

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

  const handleCitationClick = (timestamp: string) => {
    const seconds = parseTimestampStart(timestamp);
    if (seconds != null) playerRef.current?.seekTo(seconds);
  };

  const explanation = unit.content.concept_explanation;
  const hasGrounded =
    !!explanation && !explanation.needs_more_source && !!explanation.markdown;

  return (
    <div className="space-y-4">
      <YouTubePlayer ref={playerRef} videoId={youtubeId} />
      {hasGrounded ? (
        <GroundedExplanation
          markdown={explanation.markdown}
          citations={explanation.citations}
          onCitationClick={handleCitationClick}
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
 * 解析 mm:ss / mm:ss-mm:ss / hh:mm:ss → 起點秒數。
 * 格式錯誤 → null（caller 不跳轉）。
 */
export function parseTimestampStart(timestamp: string): number | null {
  const [start] = timestamp.split("-");
  const parts = start.trim().split(":").map((p) => p.trim());
  if (parts.length < 2 || parts.length > 3) return null;
  const nums = parts.map((p) => Number(p));
  if (nums.some((n) => !Number.isFinite(n) || n < 0)) return null;
  if (parts.length === 2) {
    const [m, s] = nums;
    return m * 60 + s;
  }
  const [h, m, s] = nums;
  return h * 3600 + m * 60 + s;
}

function GroundedExplanation({
  markdown,
  citations,
  onCitationClick,
}: {
  markdown: string;
  citations: Citation[];
  onCitationClick: (timestamp: string) => void;
}) {
  return (
    <>
      <div className="rounded-md border border-border-default bg-surface-1 p-4 text-sm leading-relaxed text-text-secondary">
        <MarkdownContent>{markdown}</MarkdownContent>
      </div>
      {citations.length > 0 && (
        <CitationList citations={citations} onClick={onCitationClick} />
      )}
    </>
  );
}

function CitationList({
  citations,
  onClick,
}: {
  citations: Citation[];
  onClick: (timestamp: string) => void;
}) {
  return (
    <div className="rounded-md border border-border-default bg-surface-1 p-3">
      <h4 className="text-xs font-medium text-text-secondary">
        影片出處（點擊跳轉）
      </h4>
      <ul className="mt-2 space-y-1.5">
        {citations.map((c, idx) => (
          <li key={`${c.timestamp}-${idx}`}>
            <button
              type="button"
              onClick={() => onClick(c.timestamp)}
              className="flex w-full items-start gap-2 rounded-sm px-1.5 py-1 text-left text-xs hover:bg-surface-2"
            >
              <span className="font-mono text-text-link">{c.timestamp}</span>
              <span className="text-text-secondary">{c.text_excerpt}</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
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
