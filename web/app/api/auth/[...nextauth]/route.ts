/**
 * NextAuth.js API route handler。
 *
 * 處理 /api/auth/* 路徑（sign-in、callback、session 等）。
 * 比 catch-all /api/[...path] 更具體，Next.js 會優先匹配此 route。
 */

import { handlers } from "@/auth";

export const { GET, POST } = handlers;
