/**
 * Active Reflection 持久化（Phase 2-5d）。
 *
 * 用 sessionStorage 記住「目前 Workspace 對應的反思」，避免：
 * - 跨頁跳轉（Quiz → Workspace）需要走 URL query
 * - 重新整理後反思就消失
 *
 * 為什麼不用 localStorage？
 * - 反思是「當下這段解題」的脈絡，登出/換瀏覽器分頁後就失效是合理的
 * - sessionStorage 隨 tab 關閉自動清，避免混淆「上週的反思」與「今天的」
 */

const KEY = "active_reflection_id";

/** SSR safe 取值 — server side 直接回 null（避免存取 window）。 */
export function getActiveReflectionId(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.sessionStorage.getItem(KEY);
  } catch {
    // 私密瀏覽 / 第三方 cookie 阻擋等情況 sessionStorage 可能 throw
    return null;
  }
}

export function setActiveReflectionId(id: string): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.setItem(KEY, id);
    // 同 tab 內的其他元件（例如 Workspace sidebar）需要被通知；
    // sessionStorage 預設只在 *其他* tab 觸發 storage event
    window.dispatchEvent(new CustomEvent("active-reflection-change"));
  } catch {
    // 寫入失敗就靜默 — UI 仍可運作（只是失去持久化）
  }
}

export function clearActiveReflectionId(): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.removeItem(KEY);
    window.dispatchEvent(new CustomEvent("active-reflection-change"));
  } catch {
    /* noop */
  }
}

export const ACTIVE_REFLECTION_EVENT = "active-reflection-change";
