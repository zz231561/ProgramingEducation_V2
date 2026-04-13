import { AppShell } from "@/components/layout/app-shell";

/**
 * 已登入使用者的共用 layout — 套用 AppShell（Activity Bar + Chat + Status Bar）。
 */
export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AppShell>{children}</AppShell>;
}
