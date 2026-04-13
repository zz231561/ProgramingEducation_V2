import { Home } from "lucide-react";

export default function OverviewPage() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="text-center">
        <Home className="mx-auto size-12 text-text-muted/50" />
        <h1 className="mt-4 text-xl font-medium text-text-primary">
          Overview
        </h1>
        <p className="mt-2 text-sm text-text-secondary">
          學習總覽將在後續任務中實作
        </p>
      </div>
    </div>
  );
}
