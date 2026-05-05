"use client";

/**
 * 計時器（roadmap 3-2b）— 顯示作答經過時間。
 *
 * 純 prop-driven：caller 傳 startedAt（Date.now() 時戳），元件自行 tick 每秒重算。
 * 不影響 submit 行為（submit 時 caller 仍自行從 startedAt 計算 time_spent_seconds）。
 */

import { useEffect, useState } from "react";
import { Clock } from "lucide-react";

interface Props {
  startedAt: number;
}

export function Timer({ startedAt }: Props) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const tick = () => setElapsed(Math.max(0, Math.floor((Date.now() - startedAt) / 1000)));
    tick();
    const id = window.setInterval(tick, 1000);
    return () => window.clearInterval(id);
  }, [startedAt]);

  return (
    <span className="inline-flex items-center gap-1 font-mono text-xs text-text-muted">
      <Clock className="size-3.5" />
      {formatElapsed(elapsed)}
    </span>
  );
}

function formatElapsed(secs: number): string {
  const m = Math.floor(secs / 60);
  const s = secs % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}
