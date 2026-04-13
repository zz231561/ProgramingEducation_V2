import { Bell } from "lucide-react";

export default function NotificationsPage() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="text-center">
        <Bell className="mx-auto size-12 text-text-muted/50" />
        <h1 className="mt-4 text-xl font-medium text-text-primary">
          通知
        </h1>
        <p className="mt-2 text-sm text-text-secondary">
          通知中心將在後續任務中實作
        </p>
      </div>
    </div>
  );
}
