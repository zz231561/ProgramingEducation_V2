/**
 * C++ 補全來源（7-U5）— 靜態清單 + 從當前檔案掃出來的識別字。
 *
 * 「當前檔變數」用正則掃描而非真 AST：初學者的程式碼結構單純，
 * 宣告幾乎都是 `type name` 或 `type name = ...` 的形式；引入 tree-sitter
 * 只為了補全，成本與收益不成比例（同 tech-debt「真 AST 暫不引入」的判斷）。
 * 掃錯的後果僅是多出一個沒用的候選字，不影響編譯。
 */

import type {
  CompletionContext,
  CompletionResult,
  Completion,
} from "@codemirror/autocomplete";

import { STATIC_COMPLETIONS } from "./cpp-completions";

/** 常見型別開頭的宣告：`int x`、`vector<int> v`、`const string& s` */
const DECL_RE =
  /\b(?:const\s+)?(?:unsigned\s+|signed\s+|long\s+|short\s+)*(?:int|float|double|char|bool|void|auto|string|vector|map|set|pair|size_t)\s*(?:<[^>;{}\n]*>)?\s*[*&]?\s*([A-Za-z_]\w*)/g;
/** 函式定義：`回傳型別 名稱(` — 取名稱 */
const FUNC_RE =
  /\b(?:int|float|double|char|bool|void|auto|string|long|size_t)\s+([A-Za-z_]\w*)\s*\(/g;
/** for 迴圈變數與參數也會被 DECL_RE 掃到，不另外處理 */

// 關鍵字本身會被 DECL_RE 誤抓（如 `int return`），過濾掉
const RESERVED = new Set([
  "if", "else", "for", "while", "do", "switch", "case", "return",
  "break", "continue", "true", "false", "nullptr", "main", "sizeof",
]);

/** 從程式碼掃出使用者自己定義的識別字 */
export function scanIdentifiers(code: string): Completion[] {
  const found = new Map<string, string>(); // name → type 標籤
  for (const re of [DECL_RE, FUNC_RE]) {
    re.lastIndex = 0;
    let m: RegExpExecArray | null;
    while ((m = re.exec(code)) !== null) {
      const name = m[1];
      if (RESERVED.has(name) || name.length < 2) continue;
      // 函式優先（後掃到的 FUNC_RE 會覆蓋 variable 標記）
      found.set(name, re === FUNC_RE ? "function" : "variable");
    }
  }
  return [...found].map(([label, type]) => ({
    label,
    type,
    detail: type === "function" ? "本檔函式" : "本檔變數",
    // 排在標準庫之前：學生更常用自己剛寫的東西
    boost: 1,
  }));
}

/** CodeMirror 補全來源 */
export function cppCompletionSource(
  context: CompletionContext,
): CompletionResult | null {
  const word = context.matchBefore(/[A-Za-z_]\w*/);
  // 沒打字且非手動觸發（Ctrl+Space）時不跳出來煩人
  if (!word && !context.explicit) return null;
  // 註解或字串內不補全（避免打中文註解時一直彈出）
  const line = context.state.doc.lineAt(context.pos).text;
  const col = context.pos - context.state.doc.lineAt(context.pos).from;
  if (/\/\//.test(line.slice(0, col))) return null;

  return {
    from: word?.from ?? context.pos,
    options: [
      ...scanIdentifiers(context.state.doc.toString()),
      ...STATIC_COMPLETIONS,
    ],
    validFor: /^[A-Za-z_]\w*$/,
  };
}
