"use client";

/**
 * 檔案拖曳/點選選取區（5-5a-3）— 上傳前即時驗證型別與大小。
 */

import { useRef, useState } from "react";
import { Paperclip, X } from "lucide-react";

import { validateFile } from "@/lib/assignments";

export function FileDropzone({
  files,
  onChange,
}: {
  files: File[];
  onChange: (files: File[]) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [drag, setDrag] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const add = (list: FileList | null) => {
    if (!list) return;
    const accepted: File[] = [];
    let err: string | null = null;
    for (const f of Array.from(list)) {
      const v = validateFile(f);
      if (v) err = `${f.name}：${v}`;
      else accepted.push(f);
    }
    setError(err);
    if (accepted.length) onChange([...files, ...accepted]);
  };

  return (
    <div>
      <div
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDrag(false);
          add(e.dataTransfer.files);
        }}
        className={`flex cursor-pointer flex-col items-center gap-1 rounded-md border border-dashed px-4 py-6 text-center text-xs transition-colors ${
          drag
            ? "border-accent-blue bg-surface-2 text-text-secondary"
            : "border-border-emphasis text-text-muted hover:bg-surface-2"
        }`}
      >
        <Paperclip className="size-4" />
        拖曳檔案到此或點擊選擇（word / pdf / pptx / 程式碼，單檔 ≤ 10MB）
      </div>
      <input
        ref={inputRef}
        type="file"
        multiple
        hidden
        onChange={(e) => add(e.target.files)}
      />
      {error && <p className="mt-1 text-xs text-accent-red">{error}</p>}
      {files.length > 0 && (
        <ul className="mt-2 space-y-1">
          {files.map((f, i) => (
            <li
              key={`${f.name}-${i}`}
              className="flex items-center justify-between rounded bg-surface-inset px-2 py-1 text-xs text-text-secondary"
            >
              <span className="truncate">{f.name}</span>
              <button
                type="button"
                onClick={() => onChange(files.filter((_, j) => j !== i))}
                className="text-text-muted hover:text-accent-red"
                aria-label={`移除 ${f.name}`}
              >
                <X className="size-3.5" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
