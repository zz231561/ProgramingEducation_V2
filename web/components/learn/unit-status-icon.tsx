"use client";

/**
 * 學習單元狀態圖示 — 4 種狀態各對應一個 lucide icon（roadmap 3-1c）。
 *
 * R8 反 AI 感：色彩僅用於語意（status），無裝飾性彩色塊。
 */

import { CheckCircle2, Circle, Lock, PlayCircle } from "lucide-react";

import { UnitStatus } from "@/lib/learning";

interface Props {
  status: UnitStatus;
  className?: string;
}

export function UnitStatusIcon({ status, className = "size-4" }: Props) {
  switch (status) {
    case "completed":
      return <CheckCircle2 className={`${className} text-accent-green`} aria-label="已完成" />;
    case "in_progress":
      return <PlayCircle className={`${className} text-accent-blue`} aria-label="進行中" />;
    case "available":
      return <Circle className={`${className} text-text-primary`} aria-label="可學習" />;
    case "locked":
    default:
      return <Lock className={`${className} text-text-muted`} aria-label="未解鎖" />;
  }
}

const STATUS_LABEL: Record<UnitStatus, string> = {
  completed: "已完成",
  in_progress: "進行中",
  available: "可學習",
  locked: "未解鎖",
};

export function statusLabel(status: UnitStatus): string {
  return STATUS_LABEL[status];
}
