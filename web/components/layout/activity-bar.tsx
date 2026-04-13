"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import {
  Code,
  BookOpen,
  FileQuestion,
  Network,
  Home,
  Bell,
  LayoutDashboard,
  Settings,
} from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

/** 導覽項目定義 */
interface NavItem {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  href: string;
}

const topNavItems: NavItem[] = [
  { icon: Code, label: "Workspace", href: "/workspace" },
  { icon: BookOpen, label: "Learn", href: "/learn" },
  { icon: FileQuestion, label: "Quiz", href: "/quiz" },
  { icon: Network, label: "Knowledge", href: "/knowledge" },
  { icon: Home, label: "Overview", href: "/overview" },
];

const bottomNavItems: NavItem[] = [
  { icon: Bell, label: "通知", href: "/notifications" },
  { icon: LayoutDashboard, label: "Dashboard", href: "/dashboard" },
  { icon: Settings, label: "設定", href: "/settings" },
];

function NavButton({ item, isActive }: { item: NavItem; isActive: boolean }) {
  return (
    <Tooltip>
      <TooltipTrigger
        render={<Link href={item.href} />}
        className="relative flex h-12 w-12 items-center justify-center transition-colors"
      >
        {isActive && (
          <span className="absolute left-0 top-1/2 h-6 w-0.5 -translate-y-1/2 bg-accent-blue rounded-r" />
        )}
        <item.icon
          className={`size-6 ${
            isActive
              ? "text-text-primary"
              : "text-text-muted hover:text-text-secondary"
          } transition-colors`}
        />
      </TooltipTrigger>
      <TooltipContent side="right" sideOffset={8}>
        {item.label}
      </TooltipContent>
    </Tooltip>
  );
}

export function ActivityBar() {
  const pathname = usePathname();

  return (
    <nav className="flex h-full w-12 shrink-0 flex-col border-r border-border-default bg-bg-default">
      {/* Logo */}
      <Tooltip>
        <TooltipTrigger
          render={<Link href="/workspace" />}
          className="flex h-12 w-12 items-center justify-center text-accent-blue hover:text-accent-blue/80 transition-colors"
        >
          <span className="text-lg font-bold">◇</span>
        </TooltipTrigger>
        <TooltipContent side="right" sideOffset={8}>
          ProgramingEducation
        </TooltipContent>
      </Tooltip>

      {/* 上方導覽 */}
      <div className="flex flex-col">
        {topNavItems.map((item) => (
          <NavButton
            key={item.href}
            item={item}
            isActive={pathname.startsWith(item.href)}
          />
        ))}
      </div>

      {/* 彈性空間 */}
      <div className="flex-1" />

      {/* 下方導覽 */}
      <div className="flex flex-col">
        {bottomNavItems.map((item) => (
          <NavButton
            key={item.href}
            item={item}
            isActive={pathname.startsWith(item.href)}
          />
        ))}

        {/* Avatar */}
        <Tooltip>
          <TooltipTrigger className="flex h-12 w-12 items-center justify-center">
            <div className="size-7 rounded-full bg-bg-subtle border border-border-default flex items-center justify-center text-xs text-text-secondary">
              U
            </div>
          </TooltipTrigger>
          <TooltipContent side="right" sideOffset={8}>
            使用者
          </TooltipContent>
        </Tooltip>
      </div>
    </nav>
  );
}
