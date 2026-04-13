import { Code } from "lucide-react";

export default function WorkspacePage() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="text-center">
        <Code className="mx-auto size-12 text-text-muted/50" />
        <h1 className="mt-4 text-xl font-medium text-text-primary">
          Workspace
        </h1>
        <p className="mt-2 text-sm text-text-secondary">
          程式碼編輯器將在後續任務中實作
        </p>
      </div>
    </div>
  );
}
