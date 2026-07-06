import { AppShell } from "@/components/layout/app-shell";
import { OnboardingGate } from "@/components/onboarding/onboarding-gate";

/**
 * 已登入使用者的共用 layout — onboarding gate（身分選擇 → 學生 profile 填寫）
 * 包住 AppShell，gate 通過後才進 Activity Bar + Chat + Status Bar。
 */
export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <OnboardingGate>
      <AppShell>{children}</AppShell>
    </OnboardingGate>
  );
}
