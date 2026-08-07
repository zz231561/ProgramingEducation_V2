import { CompletionContext } from "@codemirror/autocomplete";
import { EditorState } from "@codemirror/state";
import { describe, expect, it } from "vitest";

import {
  cppCompletionSource,
  scanIdentifiers,
} from "@/components/editor/cpp-completion-source";

/** 以游標停在 `doc` 結尾建立補全 context */
function contextAtEnd(doc: string, explicit = false): CompletionContext {
  const state = EditorState.create({ doc });
  return new CompletionContext(state, doc.length, explicit);
}

const labels = (code: string) => scanIdentifiers(code).map((c) => c.label);

describe("scanIdentifiers", () => {
  it("掃出基本型別與模板型別的變數宣告", () => {
    const found = labels(
      "int count = 0;\nvector<int> nums;\nconst string& title = s;",
    );
    expect(found).toContain("count");
    expect(found).toContain("nums");
    expect(found).toContain("title");
  });

  it("函式名稱標為 function 並覆蓋同名變數標記", () => {
    const found = scanIdentifiers("int total = 0;\nint total(int b) {}");
    expect(found).toHaveLength(1);
    expect(found[0]).toMatchObject({
      label: "total",
      type: "function",
      detail: "本檔函式",
    });
  });

  it("變數帶「本檔變數」說明且排在標準庫之前", () => {
    const [first] = scanIdentifiers("double average = 0;");
    expect(first).toMatchObject({
      label: "average",
      type: "variable",
      detail: "本檔變數",
      boost: 1,
    });
  });

  it("過濾保留字與單字元名稱", () => {
    const found = labels("int main() {\n  int i = 0;\n  int sum = 0;\n}");
    expect(found).not.toContain("main");
    expect(found).not.toContain("i");
    expect(found).toContain("sum");
  });

  it("重複宣告只留一筆", () => {
    expect(labels("int score = 0;\nint score = 1;")).toEqual(["score"]);
  });

  it("空程式碼回空陣列", () => {
    expect(scanIdentifiers("")).toEqual([]);
  });
});

describe("cppCompletionSource", () => {
  it("輸入中的識別字回傳候選，含本檔變數與標準庫", () => {
    const res = cppCompletionSource(contextAtEnd("int counter = 0;\ncou"));
    expect(res).not.toBeNull();
    expect(res!.from).toBe("int counter = 0;\n".length);

    const options = res!.options.map((o) => o.label);
    expect(options).toContain("counter");
    expect(options).toContain("cout");
  });

  it("行內註解中不補全", () => {
    expect(cppCompletionSource(contextAtEnd("// 這裡說明 cou"))).toBeNull();
  });

  it("程式碼後接註解時，註解內仍不補全", () => {
    expect(cppCompletionSource(contextAtEnd("int x = 0; // 說明 in"))).toBeNull();
  });

  it("沒打字且非手動觸發時不跳出來", () => {
    expect(cppCompletionSource(contextAtEnd("int x = 0;\n"))).toBeNull();
  });

  it("手動觸發（Ctrl+Space）即使沒打字也給候選", () => {
    const res = cppCompletionSource(contextAtEnd("int x = 0;\n", true));
    expect(res).not.toBeNull();
    expect(res!.options.length).toBeGreaterThan(0);
  });
});
