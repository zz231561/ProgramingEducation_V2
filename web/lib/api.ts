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

  // FormData（檔案上傳）交由瀏覽器自帶 multipart boundary，不可覆寫 Content-Type
  const isForm =
    typeof FormData !== "undefined" && options?.body instanceof FormData;

  const res = await fetch(url, {
    ...options,
    headers: {
      ...(isForm ? {} : { "Content-Type": "application/json" }),
      ...options?.headers,
    },
  });

  if (!res.ok) {
    const body: ApiError = await res.json().catch(() => ({
      error: "UNKNOWN",
      message: "未知錯誤",
    }));

    // 401 → 重導登入（token 過期 / 未登入統一入口；已在 /login 則不重導避免迴圈）
    if (
      res.status === 401 &&
      typeof window !== "undefined" &&
      !window.location.pathname.startsWith("/login")
    ) {
      window.location.href = "/login";
    }

    throw new ApiRequestError(res.status, body);
  }

  // 204 No Content（如 DELETE）無 body，res.json() 會拋解析錯誤誤判為失敗
  if (res.status === 204) return undefined as T;

  return res.json() as Promise<T>;
}
