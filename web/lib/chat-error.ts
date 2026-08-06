/**
 * 聊天錯誤 → 學生看得懂的訊息（7-C2b）。
 *
 * 修的問題：原本 catch 一律顯示「無法取得 AI 回應，請稍後再試」，
 * 於是「今日配額用盡」「太快了」「系統故障」三件事長得一模一樣——
 * 學生只會一直重按，而重按對前兩種完全沒用。
 *
 * 後端 429 有兩種（`core/rate_limit.py`）：
 * - `DAILY_QUOTA_EXCEEDED`：每日成本天花板，message 已寫明何時恢復 → 原文照用
 * - `RATE_LIMITED`：每分鐘限流，`detail.retry_after_seconds` 有剩餘冷卻秒數
 */

import { ApiRequestError } from "@/lib/api";

const GENERIC = "無法取得 AI 回應，請稍後再試。";

export function describeChatError(err: unknown): string {
  if (!(err instanceof ApiRequestError)) return GENERIC;

  if (err.status === 429) {
    if (err.body.error === "DAILY_QUOTA_EXCEEDED") {
      return err.body.message || "今日 AI 互動已達上限，明天會重新計算。";
    }
    const retry = err.body.detail?.retry_after_seconds;
    return typeof retry === "number" && retry > 0
      ? `訊息送太快了，請 ${retry} 秒後再試。`
      : "訊息送太快了，請稍後再試。";
  }

  // 401 已由 api client 重導登入；其餘 4xx 多半是輸入被擋（如 prompt injection 偵測）
  if (err.status >= 400 && err.status < 500 && err.body.message) {
    return err.body.message;
  }

  return GENERIC;
}
