import { LayoutDashboard } from "lucide-react";

export default function DashboardPage() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="text-center">
        <LayoutDashboard className="mx-auto size-12 text-text-muted/50" />
        <h1 className="mt-4 text-xl font-medium text-text-primary">
          Dashboard
        </h1>
        <p className="mt-2 text-sm text-text-secondary">
          教師儀表板將在後續任務中實作
        </p>
      </div>
    </div>
  );
}
