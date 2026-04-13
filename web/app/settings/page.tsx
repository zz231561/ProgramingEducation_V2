import { Settings } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="text-center">
        <Settings className="mx-auto size-12 text-text-muted/50" />
        <h1 className="mt-4 text-xl font-medium text-text-primary">
          設定
        </h1>
        <p className="mt-2 text-sm text-text-secondary">
          個人設定將在後續任務中實作
        </p>
      </div>
    </div>
  );
}
