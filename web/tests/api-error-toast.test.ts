import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const { toastError } = vi.hoisted(() => ({ toastError: vi.fn() }));

vi.mock("sonner", () => ({
  toast: { error: toastError },
}));

import { showApiErrorToast } from "@/lib/api-error-toast";
import { api } from "@/lib/api";

describe("showApiErrorToast", () => {
  beforeEach(() => toastError.mockClear());
  afterEach(() => vi.unstubAllGlobals());

  it("API 收到 429 時顯示剩餘冷卻秒數", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({
      error: "RATE_LIMITED",
      message: "請稍後再試",
      detail: { retry_after_seconds: 12.2 },
    }), { status: 429 })));

    await expect(api("/quiz/questions")).rejects.toMatchObject({ status: 429 });

    expect(toastError).toHaveBeenCalledWith("操作太頻繁", {
      description: "請在 13 秒後再試。",
      duration: 3000,
    });
  });

  it("API 收到 5xx 時顯示後端錯誤訊息", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({
      error: "SERVICE_UNAVAILABLE",
      message: "服務忙碌中",
    }), { status: 503 })));

    await expect(api("/learning/units")).rejects.toMatchObject({ status: 503 });

    expect(toastError).toHaveBeenCalledWith("服務暫時無法使用", {
      description: "服務忙碌中",
      duration: 3000,
    });
  });

  it("其他狀態不顯示 toast", () => {
    showApiErrorToast(422, {
      error: "VALIDATION_ERROR",
      message: "資料格式錯誤",
    });

    expect(toastError).not.toHaveBeenCalled();
  });
});
