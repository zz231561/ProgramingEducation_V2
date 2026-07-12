import { Settings } from "lucide-react";

import { DevToolsSection } from "@/components/settings/dev-tools-section";
import { IdentityCard } from "@/components/settings/identity-card";
import { MyClassesCard } from "@/components/settings/my-classes-card";

export default function SettingsPage() {
  return (
    <div className="mx-auto h-full max-w-3xl overflow-y-auto px-6 py-8">
      <div className="flex items-center gap-2">
        <Settings className="size-5 text-text-secondary" />
        <h1 className="text-xl font-medium text-text-primary">設定</h1>
      </div>
      <div className="mt-6 space-y-4">
        <MyClassesCard />
        <IdentityCard />
      </div>
      <DevToolsSection />
    </div>
  );
}
