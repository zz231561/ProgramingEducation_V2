import type { ExecutionResult } from "@/components/workspace/workspace-context";

/** 一般對話訊息 */
export interface MessageItem {
  type: "message";
  id: string;
  role: "user" | "assistant";
  content: string;
  codeSnapshot?: string;
  /** EDF Evidence 結果（assistant 訊息才有） — 提供 bloom_level / concept_tags 等資訊給 UI 顯示 */
  evidence?: Record<string, unknown>;
  createdAt: string;
}

/** 執行結果卡片 */
export interface ExecutionItem {
  type: "execution";
  id: string;
  result: ExecutionResult;
  createdAt: string;
}

/** Chat 列表中的項目（訊息或執行結果） */
export type ChatItem = MessageItem | ExecutionItem;

/** /chat/interact 回應格式 */
export interface InteractResponse {
  session_id: string;
  user_message: ApiMessage;
  assistant_message: ApiMessage;
}

/** /chat/sessions/{id} 回應格式 */
export interface SessionDetailResponse {
  session: { id: string; title: string; updated_at: string };
  messages: ApiMessage[];
}

export interface ApiMessage {
  id: string;
  role: string;
  content: string;
  code_snapshot: string | null;
  evidence: Record<string, unknown> | null;
  created_at: string;
}
