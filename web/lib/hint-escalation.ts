/**
 * Hint Ladder 前端追蹤（2026-08-06 修復：hint_level 原本寫死 0，
 * 導致對話永遠停在策略矩陣第 0 欄、連問四次也不升級說明）。
 *
 * 設計對齊 `decide_strategy()` 的契約「hint_level 由前端追蹤
 * （學生同一問題連續求助次數）」：
 * - 同一脈絡內每次追問 +1（連續求助＝需要更多幫助）
 * - 學生明說「不懂／無法回答」＝已卡住，跳 2 級（最低升到 2：指出具體位置與概念）
 * - 學生表示理解（致謝／收到）＝問題解決，歸零
 * - 新脈絡（新 session／重新執行程式）＝歸零重爬
 *
 * 純函式無狀態，狀態由 use-chat 的 ref 持有。
 */

export const HINT_LEVEL_MAX = 5;

// 卡住訊號：學生明確表示無法理解或無法回答（保守列舉，避免誤傷一般提問）。
// 注意「不會」單獨列會誤中「會不會」，只收「我不會／還不會／不會寫／不會做」。
const STUCK_RE =
  /不懂|不明白|不知道|不理解|看不懂|聽不懂|沒辦法|無法回答|搞不清楚|還是不|我不會|還不會|不會寫|不會做|學不會|卡住|直接告訴我|給我答案/;

// 理解訊號：問題已解決，階梯歸零（卡住訊號優先於此，
// 「謝謝，但我還是不懂」仍視為卡住）。
const ACK_RE = /懂了|了解|瞭解|明白了|知道了|原來如此|謝謝|感謝|清楚了/;

function clamp(level: number): number {
  return Math.max(0, Math.min(level, HINT_LEVEL_MAX));
}

/**
 * 計算本次訊息應送出的 hint_level。
 *
 * @param prev - 上一次送出的 hint_level
 * @param question - 學生本次訊息
 * @param freshContext - 是否為新脈絡（新 session／上次提問後有重新執行程式）
 * @returns 0-5 的 hint_level
 */
export function computeHintLevel(
  prev: number,
  question: string,
  freshContext: boolean,
): number {
  const base = freshContext ? 0 : prev;
  if (STUCK_RE.test(question)) return clamp(Math.max(base + 2, 2));
  if (ACK_RE.test(question)) return 0;
  return clamp(freshContext ? 0 : prev + 1);
}
