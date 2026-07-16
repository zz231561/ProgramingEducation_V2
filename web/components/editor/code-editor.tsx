"use client";

import { useRef, useEffect } from "react";
import { EditorState } from "@codemirror/state";
import { EditorView, keymap, lineNumbers, highlightActiveLine, highlightActiveLineGutter } from "@codemirror/view";
import { defaultKeymap, indentWithTab, history, historyKeymap } from "@codemirror/commands";
import { syntaxHighlighting, defaultHighlightStyle, bracketMatching, indentOnInput, foldGutter, indentUnit } from "@codemirror/language";
import { cpp } from "@codemirror/lang-cpp";
import { oneDark } from "@codemirror/theme-one-dark";

/** CodeMirror 自訂主題：覆蓋 One Dark 背景色以匹配 Design Tokens */
const editorTheme = EditorView.theme({
  "&": {
    height: "100%",
    fontSize: "14px",
    fontFamily: "'JetBrains Mono', monospace",
  },
  ".cm-content": {
    padding: "8px 0",
    caretColor: "#58A6FF",
  },
  ".cm-gutters": {
    backgroundColor: "#0D1117",
    borderRight: "1px solid #21262D",
    color: "#6E7681",
  },
  ".cm-activeLineGutter": {
    backgroundColor: "#1C2128",
    color: "#E6EDF3",
  },
  ".cm-activeLine": {
    backgroundColor: "#1C212844",
  },
  "&.cm-focused .cm-cursor": {
    borderLeftColor: "#58A6FF",
  },
  "&.cm-focused .cm-selectionBackground, ::selection": {
    backgroundColor: "#264F78",
  },
  ".cm-scroller": {
    overflow: "auto",
  },
});

export const DEFAULT_CODE = `#include <iostream>
using namespace std;

int main() {
    cout << "Hello, World!" << endl;
    return 0;
}
`;

interface CodeEditorProps {
  /** 初始程式碼 */
  initialValue?: string;
  /**
   * 外部受控內容（U2e）：變更且與編輯器現值不同時整段替換
   * （載入檔案 / 還原草稿用）。使用者輸入回傳相同值時為 no-op。
   */
  value?: string;
  /** 程式碼變更回呼 */
  onChange?: (value: string) => void;
}

/**
 * CodeMirror 6 編輯器元件
 * - C++ 語法高亮
 * - One Dark 主題（匹配 GitHub Dark Design Tokens）
 * - 行號、括號配對、自動縮排、歷史紀錄
 */
export function CodeEditor({ initialValue, value, onChange }: CodeEditorProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewRef = useRef<EditorView | null>(null);

  // onChange 走 ref：父層 callback identity 變動不得觸發編輯器重建
  // （重建會重設游標到開頭，打字中斷）
  const onChangeRef = useRef(onChange);
  useEffect(() => {
    onChangeRef.current = onChange;
  });

  useEffect(() => {
    if (!containerRef.current) return;

    const state = EditorState.create({
      doc: initialValue ?? DEFAULT_CODE,
      extensions: [
        lineNumbers(),
        highlightActiveLine(),
        highlightActiveLineGutter(),
        foldGutter(),
        history(),
        bracketMatching(),
        indentOnInput(),
        syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
        // Enter 自動縮排單位 = 4 空格（預設 2，會與 4 空格程式碼錯位，
        // 導致換行後還要再按一次 Tab 才對齊）
        indentUnit.of("    "),
        cpp(),
        oneDark,
        editorTheme,
        keymap.of([...defaultKeymap, ...historyKeymap, indentWithTab]),
        EditorView.updateListener.of((update) => {
          if (update.docChanged) {
            onChangeRef.current?.(update.state.doc.toString());
          }
        }),
        EditorState.tabSize.of(4),
      ],
    });

    const view = new EditorView({
      state,
      parent: containerRef.current,
    });

    viewRef.current = view;

    // 初始化時通知父層目前的程式碼內容
    onChangeRef.current?.(state.doc.toString());

    return () => {
      view.destroy();
      viewRef.current = null;
    };
  }, [initialValue]);

  // 外部 value 與編輯器現值不同時整段替換（updateListener 會再通知 onChange）
  useEffect(() => {
    const view = viewRef.current;
    if (!view || value == null) return;
    const current = view.state.doc.toString();
    if (value !== current) {
      view.dispatch({
        changes: { from: 0, to: current.length, insert: value },
      });
    }
  }, [value]);

  return (
    <div
      ref={containerRef}
      className="h-full w-full overflow-hidden rounded border border-border-default bg-bg-inset"
    />
  );
}
