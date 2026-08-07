import { toast } from "sonner";

import type { ApiError } from "@/lib/api";

const TOAST_DURATION_MS = 3000;

/** 統一呈現需要跨頁一致處理的 HTTP 錯誤。 */
export function showApiErrorToast(status: number, body: ApiError): void {
  if (typeof window === "undefined") return;

  if (status === 429) {
    const retryAfter = body.detail?.retry_after_seconds;
    const description =
      typeof retryAfter === "number"
        ? `請在 ${Math.ceil(retryAfter)} 秒後再試。`
        : body.message;

    toast.error("操作太頻繁", {
      description,
      duration: TOAST_DURATION_MS,
    });
    return;
  }

  if (status >= 500) {
    toast.error("服務暫時無法使用", {
      description: body.message,
      duration: TOAST_DURATION_MS,
    });
  }
}
