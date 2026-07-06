import { AppShell } from "@/components/layout/app-shell";
import { ProfileGate } from "@/components/onboarding/profile-gate";

/**
 * 已登入使用者的共用 layout — 首次登入 profile gate 包住 AppShell
 * （學生未填身分資料先擋在填寫頁），gate 通過後才進 Activity Bar + Chat + Status Bar。
 */
export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ProfileGate>
      <AppShell>{children}</AppShell>
    </ProfileGate>
  );
}
