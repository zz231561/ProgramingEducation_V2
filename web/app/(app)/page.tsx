import { redirect } from "next/navigation";

/**
 * 根路由 — 一律導向 Workspace（U1a）。
 *
 * 背景：首次登入時 OAuth callback 偶爾落在 `/`（NextAuth callbackUrl 遺失時的
 * 預設值），原本這裡是 Phase 1 的「待製作」placeholder，造成使用者誤以為
 * Workspace 沒做完。改為 server-side redirect 徹底消除此路徑。
 */
export default function Home() {
  redirect("/workspace");
}
