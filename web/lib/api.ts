/**
 * 前端統一 API client — 所有請求經 /api/ proxy 到 FastAPI。
 *
 * 統一錯誤攔截：401 → 重導登入、429 → 冷卻提示、5xx → 錯誤訊息
 */

/** 後端標準錯誤格式 */
export interface ApiError {
  error: string;
  message: string;
  detail?: Record<string, unknown>;
}

export class ApiRequestError extends Error {
  constructor(
    public status: number,
    public body: ApiError,
  ) {
    super(body.message);
  }
}

/**
 * 發送 API 請求。
 *
 * @example
 * const data = await api<{ status: string }>("/health");
 */
export async function api<T = unknown>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const url = path.startsWith("/") ? `/api${path}` : `/api/${path}`;

  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!res.ok) {
    const body: ApiError = await res.json().catch(() => ({
      error: "UNKNOWN",
      message: "未知錯誤",
    }));

    // 401 → 重導登入（Phase 1-2 實作 NextAuth 後啟用）
    if (res.status === 401) {
      // TODO: window.location.href = "/login";
    }

    throw new ApiRequestError(res.status, body);
  }

  return res.json() as Promise<T>;
}
