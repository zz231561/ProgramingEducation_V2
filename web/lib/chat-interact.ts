/**
 * `/chat/interact` SSE 呼叫（7-U6）。
 *
 * 後端把 EDF 三層管線的進度即時推回來，前端據此顯示「分析你的程式碼…／
 * 查找相關教材…／整理回答…」，取代原本一動不動的「Coddy思考中…」。
 *
 * 錯誤有兩種來源，都要接住：
 * - 串流**開始前**（401 / 429 / 422）→ 正常 HTTP status，走 ApiRequestError
 * - 串流**途中**（LLM 失敗）→ header 已送出改不了 status，後端發 `error` 事件
 */

import { ApiRequestError, type ApiError } from "@/lib/api";
import { readSse } from "@/lib/sse";
import type { InteractResponse } from "@/lib/chat-types";

/** EDF 管線階段；值需與 backend `services/chat.py` 的常數一致 */
export type InteractStage = "analyzing" | "retrieving" | "composing";

export const STAGE_LABEL: Record<InteractStage, string> = {
  analyzing: "分析你的程式碼",
  retrieving: "查找相關教材",
  composing: "整理回答",
};

export interface InteractPayload {
  code: string;
  question: string;
  session_id: string | null;
  execution_result: object | null;
  reflection_id: string | null;
}

export async function interactStream(
  payload: InteractPayload,
  onStage: (stage: InteractStage) => void,
): Promise<InteractResponse> {
  const res = await fetch("/api/chat/interact", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok || !res.body) {
    let body: ApiError = { error: "UNKNOWN", message: "AI 回覆失敗，請再試一次" };
    try {
      body = (await res.json()) as ApiError;
    } catch {
      // 非 JSON 回應（如代理層錯誤頁）：沿用預設訊息
    }
    throw new ApiRequestError(res.status, body);
  }

  let result: InteractResponse | null = null;
  for await (const evt of readSse(res.body)) {
    if (evt.event === "stage") {
      const { stage } = JSON.parse(evt.data) as { stage: InteractStage };
      if (stage in STAGE_LABEL) onStage(stage);
    } else if (evt.event === "done") {
      result = JSON.parse(evt.data) as InteractResponse;
    } else if (evt.event === "error") {
      throw new ApiRequestError(500, JSON.parse(evt.data) as ApiError);
    }
  }

  // 串流被中途切斷（網路掉線 / 代理逾時）：done 沒收到就是失敗
  if (!result) {
    throw new ApiRequestError(502, {
      error: "STREAM_INCOMPLETE",
      message: "AI 回覆中斷，請再試一次",
    });
  }
  return result;
}
