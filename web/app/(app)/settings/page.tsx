import { Settings } from "lucide-react";

import { DevToolsSection } from "@/components/settings/dev-tools-section";

export default function SettingsPage() {
  return (
    <div className="mx-auto h-full max-w-3xl overflow-y-auto px-6 py-8">
      <div className="flex items-center gap-2">
        <Settings className="size-5 text-text-secondary" />
        <h1 className="text-xl font-medium text-text-primary">設定</h1>
      </div>
      <p className="mt-2 text-sm text-text-secondary">
        個人設定將在後續任務中實作。
      </p>
      <DevToolsSection />
    </div>
  );
}
