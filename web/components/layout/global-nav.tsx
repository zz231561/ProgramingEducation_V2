"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { useSession, signOut } from "next-auth/react";
import {
  ChevronDown,
  Bell,
  Settings,
  Home,
  LogOut,
} from "lucide-react";

interface NavTab {
  label: string;
  href: string;
}

/* design-plan §2.5：5 個頂部頁籤 */
const NAV_TABS: NavTab[] = [
  { label: "Workspace", href: "/workspace" },
  { label: "Learn", href: "/learn" },
  { label: "Quiz", href: "/quiz" },
  { label: "Knowledge", href: "/knowledge" },
  { label: "Dashboard", href: "/dashboard" },
];

/**
 * 頂部全域導覽（design-plan §2.5）：
 * 高度 48px、bg-canvas、底部 border-muted、Logo + 5 頁籤 + Avatar 下拉
 * Tab active：border-bottom: 2px solid #F78166（frontend.md 規範）
 * Chat toggle 移除（靠 Ctrl+B 切換）
 */
export function GlobalNav() {
  const pathname = usePathname();

  return (
    <nav className="flex h-12 shrink-0 items-center gap-1 border-b border-border-muted bg-bg-canvas px-3 body-ui">
      {/* Logo — 純文字（design-plan §0.3 R8.2 禁 emoji 字） */}
      <Link
        href="/workspace"
        className="flex h-full items-center pr-3 text-sm font-semibold text-text-primary hover:text-text-secondary transition-colors"
      >
        C++ Tutor
      </Link>

      {/* 5 個頁籤 */}
      <div className="flex h-full items-center">
        {NAV_TABS.map((tab) => {
          const active = pathname.startsWith(tab.href);
          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={`relative flex h-full items-center px-3 text-sm transition-colors ${
                active
                  ? "text-text-primary"
                  : "text-text-muted hover:text-text-secondary"
              }`}
            >
              {tab.label}
              {active && (
                <span className="absolute inset-x-3 bottom-0 h-0.5 bg-[#F78166]" />
              )}
            </Link>
          );
        })}
      </div>

      <div className="flex-1" />

      {/* Avatar Menu — Chat toggle 已移除，靠 Ctrl+B 開關 */}
      <AvatarMenu />
    </nav>
  );
}

function AvatarMenu() {
  const { data: session } = useSession();
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  /* click outside 關閉 */
  useEffect(() => {
    if (!open) return;
    function handleClick(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    function handleEsc(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    document.addEventListener("keydown", handleEsc);
    return () => {
      document.removeEventListener("mousedown", handleClick);
      document.removeEventListener("keydown", handleEsc);
    };
  }, [open]);

  const name = session?.user?.name ?? "使用者";
  const email = session?.user?.email ?? "";

  return (
    <div ref={containerRef} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex h-8 items-center gap-1 rounded-md px-1.5 text-text-secondary hover:text-text-primary hover:bg-surface-2 transition-colors"
        aria-label="使用者選單"
        aria-expanded={open}
      >
        {session?.user?.image ? (
          <img
            src={session.user.image}
            alt=""
            className="size-6 rounded-full"
            referrerPolicy="no-referrer"
          />
        ) : (
          <div className="flex size-6 items-center justify-center rounded-full border border-border-default bg-surface-1 text-[10px]">
            {name[0] ?? "U"}
          </div>
        )}
        <ChevronDown className={`size-3 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      {open && (
        <div
          className="absolute right-0 top-full mt-1 w-56 rounded-md border border-border-default bg-surface-1 py-1 shadow-modal z-50"
          role="menu"
        >
          {/* User info header */}
          <div className="px-3 py-2 border-b border-border-muted">
            <div className="text-sm font-medium text-text-primary truncate">{name}</div>
            {email && <div className="text-xs text-text-muted truncate">{email}</div>}
          </div>

          {/* Menu items */}
          <MenuLink href="/overview" icon={Home} label="學習總覽" onClick={() => setOpen(false)} />
          <MenuLink href="/notifications" icon={Bell} label="通知" onClick={() => setOpen(false)} />
          <MenuLink href="/settings" icon={Settings} label="設定" onClick={() => setOpen(false)} />

          <div className="my-1 border-t border-border-muted" />
          <button
            onClick={() => signOut({ callbackUrl: "/login" })}
            className="flex w-full items-center gap-2 px-3 py-1.5 text-sm text-text-secondary hover:bg-surface-2 hover:text-text-primary transition-colors"
            role="menuitem"
          >
            <LogOut className="size-3.5" />
            <span>登出</span>
          </button>
        </div>
      )}
    </div>
  );
}

function MenuLink({
  href,
  icon: Icon,
  label,
  onClick,
}: {
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  onClick: () => void;
}) {
  return (
    <Link
      href={href}
      onClick={onClick}
      className="flex items-center gap-2 px-3 py-1.5 text-sm text-text-secondary hover:bg-surface-2 hover:text-text-primary transition-colors"
      role="menuitem"
    >
      <Icon className="size-3.5" />
      <span>{label}</span>
    </Link>
  );
}
