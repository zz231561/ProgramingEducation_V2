"use client";

/**
 * 學生身分填寫表單（5-1c-2）— 首次登入強制引導。
 * Google 顯示名不一定是真名，故要求補填校名/系所/學號/姓名；email 唯讀。
 */

import { useState } from "react";
import { GraduationCap, Loader2 } from "lucide-react";

import { ApiRequestError } from "@/lib/api";
import { ProfileInput, submitProfile } from "@/lib/profile";

const FIELDS: { key: keyof ProfileInput; label: string; placeholder: string }[] = [
  { key: "real_name", label: "姓名", placeholder: "你的真實姓名" },
  { key: "student_id", label: "學號", placeholder: "例如：B10901001" },
  { key: "school", label: "學校", placeholder: "例如：國立台灣大學" },
  { key: "department", label: "系所", placeholder: "例如：資訊工程學系" },
];

export function ProfileSetupForm({
  email,
  onComplete,
}: {
  email: string;
  onComplete: () => void;
}) {
  const [form, setForm] = useState<ProfileInput>({
    real_name: "",
    student_id: "",
    school: "",
    department: "",
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit =
    !busy && FIELDS.every((f) => form[f.key].trim().length > 0);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;
    setBusy(true);
    setError(null);
    try {
      await submitProfile({
        real_name: form.real_name.trim(),
        student_id: form.student_id.trim(),
        school: form.school.trim(),
        department: form.department.trim(),
      });
      onComplete();
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.body.message : "送出失敗，請重試");
      setBusy(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-bg-canvas px-4 py-8">
      <div className="w-full max-w-md rounded-lg border border-border-default bg-bg-default p-8">
        <div className="mx-auto flex size-12 items-center justify-center rounded-lg border border-border-default bg-bg-canvas text-text-secondary">
          <GraduationCap className="size-6" />
        </div>
        <h1 className="mt-4 text-center text-xl font-semibold text-text-primary">
          完善你的學生資料
        </h1>
        <p className="mt-2 text-center text-sm text-text-secondary">
          第一次使用，請填寫以下資料以確認身分；教師將以此辨識你。
        </p>

        <form onSubmit={submit} className="mt-6 space-y-4">
          {FIELDS.map((f) => (
            <label key={f.key} className="block">
              <span className="text-xs text-text-secondary">{f.label}</span>
              <input
                value={form[f.key]}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, [f.key]: e.target.value }))
                }
                placeholder={f.placeholder}
                maxLength={f.key === "student_id" ? 50 : 100}
                className="mt-1 h-9 w-full rounded-md border border-border-default bg-bg-canvas px-3 text-sm text-text-primary placeholder:text-text-muted focus:border-accent-blue focus:outline-none"
              />
            </label>
          ))}

          <label className="block">
            <span className="text-xs text-text-secondary">Email（登入帳號）</span>
            <input
              value={email}
              readOnly
              className="mt-1 h-9 w-full cursor-not-allowed rounded-md border border-border-muted bg-bg-inset px-3 text-sm text-text-muted"
            />
          </label>

          {error && <p className="text-xs text-accent-red">{error}</p>}

          <button
            type="submit"
            disabled={!canSubmit}
            className="flex h-9 w-full items-center justify-center gap-1.5 rounded-md bg-btn-primary-bg text-sm font-medium text-white transition-colors hover:bg-btn-primary-hover disabled:opacity-50"
          >
            {busy && <Loader2 className="size-4 animate-spin" />}
            開始學習
          </button>
        </form>
      </div>
    </div>
  );
}
