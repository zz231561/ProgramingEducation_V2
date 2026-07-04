"use client";

/**
 * 共用 Markdown 渲染元件 — Chat（Coddy 回覆）與 Learn（grounded 內容）共用。
 *
 * 缺 @tailwindcss/typography，手動覆寫元素樣式維持可讀性；
 * code block 對齊 frontend.md Code Block 規格（bg-inset / border / JetBrains Mono）。
 * react-markdown 預設不渲染 raw HTML，天然防 XSS。
 */

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export const MARKDOWN_COMPONENTS = {
  h1: ({ children }: { children?: React.ReactNode }) => (
    <h1 className="mt-3 mb-2 text-base font-medium text-text-primary">{children}</h1>
  ),
  h2: ({ children }: { children?: React.ReactNode }) => (
    <h2 className="mt-3 mb-2 text-sm font-medium text-text-primary">{children}</h2>
  ),
  h3: ({ children }: { children?: React.ReactNode }) => (
    <h3 className="mt-3 mb-1.5 text-sm font-medium text-text-primary">{children}</h3>
  ),
  p: ({ children }: { children?: React.ReactNode }) => (
    <p className="mb-2 last:mb-0">{children}</p>
  ),
  ul: ({ children }: { children?: React.ReactNode }) => (
    <ul className="mb-2 list-disc pl-5">{children}</ul>
  ),
  ol: ({ children }: { children?: React.ReactNode }) => (
    <ol className="mb-2 list-decimal pl-5">{children}</ol>
  ),
  li: ({ children }: { children?: React.ReactNode }) => (
    <li className="mb-0.5">{children}</li>
  ),
  code: ({ children }: { children?: React.ReactNode }) => (
    <code className="rounded-sm bg-bg-inset px-1 font-mono text-[0.8125rem] text-text-primary">
      {children}
    </code>
  ),
  pre: ({ children }: { children?: React.ReactNode }) => (
    <pre className="my-2 overflow-x-auto rounded-md border border-border-default bg-bg-inset p-3 font-mono text-[0.8125rem] text-text-primary">
      {children}
    </pre>
  ),
  strong: ({ children }: { children?: React.ReactNode }) => (
    <strong className="text-text-primary">{children}</strong>
  ),
};

/** 渲染 Markdown 字串（GFM 支援：列表、表格、刪除線等）。 */
export function MarkdownContent({ children }: { children: string }) {
  return (
    <ReactMarkdown remarkPlugins={[remarkGfm]} components={MARKDOWN_COMPONENTS}>
      {children}
    </ReactMarkdown>
  );
}
