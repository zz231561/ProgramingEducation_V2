"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { useSession, signOut } from "next-auth/react";
import {
  Code,
  BookOpen,
  FileQuestion,
  Network,
  Home,
  Bell,
  LayoutDashboard,
  Settings,
  LogOut,
} from "lucide-react";

interface NavItem {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  description: string;
  href: string;
}

const topNavItems: NavItem[] = [
  { icon: Code, label: "Workspace", description: "程式碼編輯", href: "/workspace" },
  { icon: BookOpen, label: "Learn", description: "學習路徑", href: "/learn" },
  { icon: FileQuestion, label: "Quiz", description: "智慧測驗", href: "/quiz" },
  { icon: Network, label: "Knowledge", description: "知識圖譜", href: "/knowledge" },
  { icon: Home, label: "Overview", description: "學習總覽", href: "/overview" },
];

const bottomNavItems: NavItem[] = [
  { icon: Bell, label: "通知", description: "通知中心", href: "/notifications" },
  { icon: LayoutDashboard, label: "Dashboard", description: "教師儀表板", href: "/dashboard" },
  { icon: Settings, label: "設定", description: "個人設定", href: "/settings" },
];

function NavButton({ item, isActive }: { item: NavItem; isActive: boolean }) {
  return (
    <Link
      href={item.href}
      className={`relative flex items-center gap-3 px-3 py-2.5 text-sm transition-colors ${
        isActive
          ? "bg-bg-subtle text-text-primary"
          : "text-text-muted hover:bg-bg-subtle/50 hover:text-text-secondary"
      }`}
    >
      {isActive && (
        <span className="absolute left-0 top-1/2 h-6 w-0.5 -translate-y-1/2 rounded-r bg-accent-blue" />
      )}
      <item.icon className="size-5 shrink-0" />
      <div className="min-w-0">
        <div className="truncate font-medium leading-tight">{item.label}</div>
        <div className="truncate text-xs text-text-muted leading-tight">
          {item.description}
        </div>
      </div>
    </Link>
  );
}

export function ActivityBar() {
  const pathname = usePathname();
  const { data: session } = useSession();

  return (
    <nav className="flex h-full w-[180px] shrink-0 flex-col border-r border-border-default bg-bg-default">
      {/* Logo */}
      <Link
        href="/workspace"
        className="flex h-12 items-center gap-2 px-3 text-accent-blue hover:text-accent-blue/80 transition-colors"
      >
        <span className="text-lg font-semibold">◇</span>
        <span className="text-sm font-semibold text-text-primary">
          C++ Tutor
        </span>
      </Link>

      {/* 分隔線 */}
      <div className="mx-3 border-t border-border-muted" />

      {/* 上方導覽 */}
      <div className="mt-1 flex flex-col gap-0.5 px-1">
        {topNavItems.map((item) => (
          <NavButton
            key={item.href}
            item={item}
            isActive={pathname.startsWith(item.href)}
          />
        ))}
      </div>

      <div className="flex-1" />

      {/* 下方導覽 */}
      <div className="flex flex-col gap-0.5 px-1 pb-1">
        <div className="mx-2 mb-1 border-t border-border-muted" />
        {bottomNavItems.map((item) => (
          <NavButton
            key={item.href}
            item={item}
            isActive={pathname.startsWith(item.href)}
          />
        ))}

        {/* 使用者資訊 + 登出 */}
        <div className="mx-2 mt-1 border-t border-border-muted" />
        <div className="flex items-center gap-2 px-3 py-2">
          {session?.user?.image ? (
            <img
              src={session.user.image}
              alt=""
              className="size-6 shrink-0 rounded-full"
              referrerPolicy="no-referrer"
            />
          ) : (
            <div className="size-6 shrink-0 rounded-full bg-bg-subtle border border-border-default flex items-center justify-center text-[10px]">
              {session?.user?.name?.[0] ?? "U"}
            </div>
          )}
          <span className="min-w-0 flex-1 truncate text-sm text-text-secondary">
            {session?.user?.name ?? "使用者"}
          </span>
          <button
            onClick={() => signOut({ callbackUrl: "/login" })}
            className="shrink-0 rounded p-1 text-text-muted hover:text-text-secondary hover:bg-bg-subtle transition-colors"
            title="登出"
          >
            <LogOut className="size-3.5" />
          </button>
        </div>
      </div>
    </nav>
  );
}
