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
// U1c：記錄「這個反思是否經由正確管道（前往 Workspace 按鈕）帶入」。
// 值 = 反思 id；與 KEY 不一致代表殘留（例如在 Quiz 建了反思但直接手動開 /workspace）。
const HANDOFF_KEY = "active_reflection_handoff";
// 實作題 handoff：反思綁定的程式碼檔名（「章節名稱 程式實作題」）與起手程式碼。
// Workspace 只在目前開啟檔案 === 此檔名時顯示反思計畫按鈕。
const FILE_KEY = "active_reflection_file";
const STARTER_KEY = "active_reflection_starter";

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

export function setActiveReflectionId(
  id: string,
  handoff?: { fileName: string; starterCode?: string },
): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.setItem(KEY, id);
    // 呼叫點只有「前往 Workspace」轉場按鈕，故 set 即代表正確管道 handoff。
    // 不做一次性消費：同 tab 內重新整理 Workspace 仍應保留當下解題脈絡。
    window.sessionStorage.setItem(HANDOFF_KEY, id);
    if (handoff) {
      window.sessionStorage.setItem(FILE_KEY, handoff.fileName);
      if (handoff.starterCode) {
        window.sessionStorage.setItem(STARTER_KEY, handoff.starterCode);
      } else {
        window.sessionStorage.removeItem(STARTER_KEY);
      }
    } else {
      window.sessionStorage.removeItem(FILE_KEY);
      window.sessionStorage.removeItem(STARTER_KEY);
    }
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
    window.sessionStorage.removeItem(HANDOFF_KEY);
    window.sessionStorage.removeItem(FILE_KEY);
    window.sessionStorage.removeItem(STARTER_KEY);
    window.dispatchEvent(new CustomEvent("active-reflection-change"));
  } catch {
    /* noop */
  }
}

/**
 * U1c gating：Workspace 進入時呼叫。
 *
 * 若存在 active reflection 但沒有對應的 handoff 標記（= 非經「前往 Workspace」
 * 按鈕帶入的殘留），清除並回傳 null；否則回傳反思 id。
 */
export function getHandedOffReflectionId(): string | null {
  if (typeof window === "undefined") return null;
  try {
    const id = window.sessionStorage.getItem(KEY);
    if (!id) return null;
    if (window.sessionStorage.getItem(HANDOFF_KEY) !== id) {
      clearActiveReflectionId();
      return null;
    }
    return id;
  } catch {
    return null;
  }
}

/** 反思綁定的程式碼檔名（無實作題 handoff 時為 null）。 */
export function getHandoffFileName(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.sessionStorage.getItem(FILE_KEY);
  } catch {
    return null;
  }
}

/** 實作題起手程式碼（可能無）。 */
export function getHandoffStarterCode(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.sessionStorage.getItem(STARTER_KEY);
  } catch {
    return null;
  }
}

export const ACTIVE_REFLECTION_EVENT = "active-reflection-change";
