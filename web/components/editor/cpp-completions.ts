/**
 * C++ 靜態補全資料（7-U5）。
 *
 * 刻意**不接 clangd LSP**：B 機只有 2GB，clangd 每實例 300MB 起跳，
 * 30 人同時上課必爆（與不自架 Judge0 同一個資源理由，見 server-plan.md）。
 * 改以「關鍵字 + 教材用得到的 STL + 當前檔變數」涵蓋初學者 90% 的輸入。
 *
 * 收錄原則：**只放 62 章教材真的會用到的**。清單過長反而讓學生在
 * 一堆沒學過的 API 裡找東西，違背教學目的。
 */

import type { Completion } from "@codemirror/autocomplete";

/** 語言關鍵字（type=keyword） */
const KEYWORDS = [
  "int", "float", "double", "char", "bool", "void", "long", "short",
  "unsigned", "signed", "const", "static", "extern", "auto", "struct",
  "class", "public", "private", "protected", "virtual", "override",
  "namespace", "using", "template", "typename", "enum", "typedef",
  "if", "else", "switch", "case", "default", "for", "while", "do",
  "break", "continue", "return", "goto", "try", "catch", "throw",
  "new", "delete", "sizeof", "nullptr", "true", "false", "this",
  "inline", "friend", "operator", "explicit", "mutable", "constexpr",
];

/** 帶簽章與繁中說明的常用 API；info 會顯示在補全清單右側 */
interface ApiEntry {
  label: string;
  detail: string;
  info: string;
  /** 選取後插入的片段（`|` 標示游標落點） */
  insert?: string;
}

const APIS: ApiEntry[] = [
  // --- 輸入輸出（章節 1-10）---
  { label: "cout", detail: "std::ostream", info: "標準輸出；用 << 串接要印的內容" },
  { label: "cin", detail: "std::istream", info: "標準輸入；用 >> 讀取使用者輸入" },
  { label: "endl", detail: "std::endl", info: "換行並清空輸出緩衝區" },
  { label: "cerr", detail: "std::ostream", info: "標準錯誤輸出（不受緩衝影響）" },
  { label: "getline", detail: "getline(cin, str)", info: "讀取一整行（含空白），存進字串", insert: "getline(cin, |)" },
  { label: "setw", detail: "setw(n)", info: "設定下一個輸出的欄寬；需 #include <iomanip>", insert: "setw(|)" },
  { label: "fixed", detail: "std::fixed", info: "以固定小數點格式輸出浮點數" },
  { label: "setprecision", detail: "setprecision(n)", info: "設定小數位數；需 #include <iomanip>", insert: "setprecision(|)" },

  // --- 字串 ---
  { label: "string", detail: "std::string", info: "字串型別；需 #include <string>" },
  { label: "length", detail: "str.length()", info: "字串長度（等同 size()）", insert: "length()" },
  { label: "substr", detail: "str.substr(pos, len)", info: "取子字串：從 pos 開始取 len 個字元", insert: "substr(|)" },
  { label: "find", detail: "str.find(target)", info: "尋找子字串，找不到回傳 string::npos", insert: "find(|)" },
  { label: "to_string", detail: "to_string(n)", info: "數字轉字串", insert: "to_string(|)" },
  { label: "stoi", detail: "stoi(str)", info: "字串轉整數", insert: "stoi(|)" },

  // --- 容器（章節 30 之後）---
  { label: "vector", detail: "std::vector<T>", info: "動態陣列；需 #include <vector>", insert: "vector<|>" },
  { label: "push_back", detail: "v.push_back(x)", info: "在容器尾端加入元素", insert: "push_back(|)" },
  { label: "pop_back", detail: "v.pop_back()", info: "移除尾端元素", insert: "pop_back()" },
  { label: "size", detail: "v.size()", info: "元素個數", insert: "size()" },
  { label: "empty", detail: "v.empty()", info: "是否為空", insert: "empty()" },
  { label: "clear", detail: "v.clear()", info: "清空所有元素", insert: "clear()" },
  { label: "begin", detail: "v.begin()", info: "指向第一個元素的迭代器", insert: "begin()" },
  { label: "end", detail: "v.end()", info: "指向尾端之後的迭代器", insert: "end()" },
  { label: "at", detail: "v.at(i)", info: "取第 i 個元素（會檢查越界）", insert: "at(|)" },
  { label: "map", detail: "std::map<K,V>", info: "有序鍵值對；需 #include <map>", insert: "map<|>" },
  { label: "set", detail: "std::set<T>", info: "有序且不重複的集合；需 #include <set>", insert: "set<|>" },

  // --- 演算法 ---
  { label: "sort", detail: "sort(v.begin(), v.end())", info: "排序；需 #include <algorithm>", insert: "sort(|)" },
  { label: "max", detail: "max(a, b)", info: "取較大值", insert: "max(|)" },
  { label: "min", detail: "min(a, b)", info: "取較小值", insert: "min(|)" },
  { label: "swap", detail: "swap(a, b)", info: "交換兩個變數的值", insert: "swap(|)" },
  { label: "reverse", detail: "reverse(v.begin(), v.end())", info: "反轉；需 #include <algorithm>", insert: "reverse(|)" },

  // --- 數學 ---
  { label: "abs", detail: "abs(x)", info: "絕對值" , insert: "abs(|)" },
  { label: "pow", detail: "pow(base, exp)", info: "次方；需 #include <cmath>", insert: "pow(|)" },
  { label: "sqrt", detail: "sqrt(x)", info: "平方根；需 #include <cmath>", insert: "sqrt(|)" },
];

/** 常用程式骨架 */
const SNIPPETS: ApiEntry[] = [
  {
    label: "main",
    detail: "int main() { ... }",
    info: "程式進入點",
    insert: "int main() {\n    |\n    return 0;\n}",
  },
  {
    label: "for",
    detail: "for (int i = 0; i < n; i++)",
    info: "計數迴圈",
    insert: "for (int i = 0; i < |; i++) {\n    \n}",
  },
  {
    label: "while",
    detail: "while (condition)",
    info: "條件迴圈",
    insert: "while (|) {\n    \n}",
  },
  {
    label: "include",
    detail: "#include <...>",
    info: "引入標準函式庫",
    insert: "#include <|>",
  },
];

/** `|` 標示游標落點；轉為 CodeMirror 的 apply 形式 */
function toCompletion(entry: ApiEntry, type: string): Completion {
  const { label, detail, info, insert } = entry;
  if (!insert || !insert.includes("|")) {
    return { label, detail, info, type, apply: insert };
  }
  const cursor = insert.indexOf("|");
  const text = insert.replace("|", "");
  return {
    label,
    detail,
    info,
    type,
    apply: (view, _completion, from, to) => {
      view.dispatch({
        changes: { from, to, insert: text },
        selection: { anchor: from + cursor },
      });
    },
  };
}

export const STATIC_COMPLETIONS: Completion[] = [
  ...KEYWORDS.map((label) => ({ label, type: "keyword" })),
  ...APIS.map((e) => toCompletion(e, "function")),
  ...SNIPPETS.map((e) => toCompletion(e, "text")),
];
