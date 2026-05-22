/**
 * Pending Workspace Code 持久化（Phase 6-2d）。
 *
 * 用 sessionStorage 在「範例 tab → Workspace」的跨頁跳轉間攜帶程式碼，
 * 避免：
 * - 用 URL query 攜帶整段 C++ source（會超出長度限制 + 編碼難看）
 * - 自製 global state（重新整理就消失，且要全域 provider）
 *
 * 為什麼用 consume（讀完即清）而非 get？
 * - 程式碼只在「使用者點按鈕 → Workspace 開啟」的單一轉場有效；若不清掉，
 *   使用者後續手動 navigate /workspace 仍會被舊範例覆蓋當前編輯內容。
 * - 配合 Workspace 初始化的「一次性 initialValue」語意。
 *
 * 復用 active-reflection.ts 的 pattern（同 tab 內 CustomEvent 通知 + SSR safe try/catch）。
 */

const KEY = "pending_workspace_code";

/**
 * 把範例程式碼暫存到 sessionStorage，給 Workspace 載入。
 *
 * 後續呼叫會覆蓋；同 tab 內 dispatch event 讓 Workspace（若已開啟）能即時更新。
 */
export function setPendingWorkspaceCode(code: string): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.setItem(KEY, code);
    window.dispatchEvent(new CustomEvent(PENDING_WORKSPACE_CODE_EVENT));
  } catch {
    // sessionStorage 阻擋（private mode 等）→ 靜默；使用者體驗為 Workspace 用 default code
  }
}

/**
 * 讀取並清除 pending code。
 *
 * 設計為「一次性消費」：Workspace 載入後此值即失效，避免下次重整誤覆蓋。
 */
export function consumePendingWorkspaceCode(): string | null {
  if (typeof window === "undefined") return null;
  try {
    const value = window.sessionStorage.getItem(KEY);
    if (value !== null) {
      window.sessionStorage.removeItem(KEY);
      window.dispatchEvent(new CustomEvent(PENDING_WORKSPACE_CODE_EVENT));
    }
    return value;
  } catch {
    return null;
  }
}

export const PENDING_WORKSPACE_CODE_EVENT = "pending-workspace-code-change";
