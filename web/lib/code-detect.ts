/**
 * 程式碼靜態偵測 — 純字串比對，零成本，用於決定要不要顯示某個 UI 或主動說明。
 * （原散落在 `stdin-panel.tsx`，該檔隨互動終端上線移除後集中至此。）
 */

/** 程式是否使用 main 的參數（章節 58）— 決定是否顯示執行參數列 */
export function codeUsesArgs(code: string): boolean {
  return /\bmain\s*\([^)]*\bargv\b/.test(code);
}

/** 程式是否會印出「當地時間」（章節 45）— 伺服器時鐘為 UTC，Coddy 需主動提醒 */
export function usesLocalTime(code: string): boolean {
  return /\b(localtime|strftime|asctime|ctime)\s*\(/.test(code);
}
