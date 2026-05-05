"use client";

/**
 * 生成新路徑 dialog — 表單填 title / description / category（roadmap 3-1c）。
 *
 * 輕量實作：用 fixed overlay + 中央 panel，不引入 shadcn Dialog（目前 ui/ 只有 button + tooltip）。
 * 後續若多處用到 modal 再抽 shadcn Dialog 統一。
 */

import { useState } from "react";
import { Loader2, X } from "lucide-react";

import { GeneratePathPayload } from "@/lib/learning";

interface Props {
  open: boolean;
  loading: boolean;
  error: string | null;
  onClose: () => void;
  onSubmit: (payload: GeneratePathPayload) => void;
}

export function GeneratePathDialog({
  open,
  loading,
  error,
  onClose,
  onSubmit,
}: Props) {
  const [title, setTitle] = useState("C++ 基礎學習路徑");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("");

  if (!open) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || loading) return;
    onSubmit({
      title: title.trim(),
      description: description.trim(),
      category: category.trim() || undefined,
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-bg-inset/80 px-4">
      <div className="w-full max-w-md rounded-md border border-border-default bg-surface-1 shadow-modal">
        <div className="flex items-center justify-between border-b border-border-default px-4 py-3">
          <h2 className="text-sm font-medium text-text-primary">
            生成新學習路徑
          </h2>
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="rounded p-1 text-text-muted hover:bg-surface-2 hover:text-text-primary disabled:opacity-50"
            aria-label="關閉"
          >
            <X className="size-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3 p-4">
          <Field
            label="標題"
            value={title}
            onChange={setTitle}
            disabled={loading}
            required
          />
          <Field
            label="描述（選填）"
            value={description}
            onChange={setDescription}
            disabled={loading}
            multiline
          />
          <Field
            label="分類（選填，限制特定 category 概念）"
            value={category}
            onChange={setCategory}
            disabled={loading}
            placeholder="例：基礎語法"
          />

          {error && (
            <div className="rounded-md border-l-2 border-accent-red bg-surface-2 px-3 py-2 text-xs text-accent-red">
              {error}
            </div>
          )}

          <div className="flex justify-end gap-2 pt-1">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="h-8 rounded-md border border-btn-default-border bg-btn-default-bg px-3 text-sm text-text-primary hover:bg-surface-2 disabled:opacity-50"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={!title.trim() || loading}
              className="inline-flex h-8 items-center gap-1.5 rounded-md bg-btn-primary-bg px-3 text-sm font-medium text-white hover:bg-btn-primary-hover disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading && <Loader2 className="size-3.5 animate-spin" />}
              {loading ? "生成中..." : "生成路徑"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

interface FieldProps {
  label: string;
  value: string;
  onChange: (v: string) => void;
  disabled?: boolean;
  required?: boolean;
  multiline?: boolean;
  placeholder?: string;
}

function Field({
  label,
  value,
  onChange,
  disabled,
  required,
  multiline,
  placeholder,
}: FieldProps) {
  const baseClass =
    "w-full rounded-md border border-border-default bg-bg-canvas px-2.5 py-1.5 text-sm text-text-primary outline-none placeholder:text-text-muted/60 focus:border-accent-blue disabled:opacity-60";
  return (
    <label className="block">
      <span className="block text-xs text-text-secondary">{label}</span>
      {multiline ? (
        <textarea
          rows={3}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          placeholder={placeholder}
          className={`${baseClass} mt-1 resize-none`}
        />
      ) : (
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          required={required}
          placeholder={placeholder}
          className={`${baseClass} mt-1`}
        />
      )}
    </label>
  );
}
