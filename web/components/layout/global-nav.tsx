"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { useSession, signOut } from "next-auth/react";
import { MessageSquare, ChevronDown, Settings, LogOut } from "lucide-react";

import { getMyProfile, StudentProfile } from "@/lib/profile";
import { Role, useRole } from "@/lib/use-role";

interface GlobalNavProps {
  chatOpen: boolean;
  onToggleChat: () => void;
}

interface NavTab {
  label: string;
  href: string;
}

/* 學生頂部頁籤（design-plan §2.5） */
const STUDENT_TABS: NavTab[] = [
  { label: "Workspace", href: "/workspace" },
  { label: "Learn", href: "/learn" },
  { label: "Quiz", href: "/quiz" },
  { label: "Knowledge", href: "/knowledge" },
  { label: "Dashboard", href: "/dashboard" },
];

/* 教師頂部頁籤：班級 + 作業 + 示範用 Workspace + 教材 Learn（不含 Quiz/Knowledge） */
const TEACHER_TABS: NavTab[] = [
  { label: "班級", href: "/teacher" },
  { label: "作業", href: "/teacher/assignments" },
  { label: "Workspace", href: "/workspace" },
  { label: "Learn", href: "/learn" },
];

/** /teacher 是 /teacher/assignments 的前綴，故 /teacher 需精確比對避免兩籤同亮。 */
function isTabActive(href: string, pathname: string): boolean {
  if (href === "/teacher") return pathname === "/teacher";
  return pathname === href || pathname.startsWith(`${href}/`);
}

/**
 * 頂部全域導覽（design-plan §2.5）：
 * 高度 48px、bg-canvas、底部 border-muted、Logo + 5 頁籤 + Avatar 下拉
 * Tab active：border-bottom: 2px solid #F78166（frontend.md 規範）
 * Chat toggle 僅在 chat 收合時顯示（提供視覺 affordance 重新開啟）；
 * chat 開啟時靠 ChatPanel 內的收合按鈕或 Ctrl+B 關閉。
 */
export function GlobalNav({ chatOpen, onToggleChat }: GlobalNavProps) {
  const pathname = usePathname();
  const role = useRole();
  const tabs = role === "teacher" ? TEACHER_TABS : STUDENT_TABS;

  return (
    <nav className="flex h-12 shrink-0 items-center gap-1 border-b border-border-muted bg-bg-canvas px-3 body-ui">
      {/* Logo — 純文字（design-plan §0.3 R8.2 禁 emoji 字） */}
      <Link
        href={role === "teacher" ? "/teacher" : "/workspace"}
        className="flex h-full items-center pr-3 text-sm font-semibold text-text-primary hover:text-text-secondary transition-colors"
      >
        Codedge
      </Link>

      {/* 角色化頁籤（role 未定前不渲染，避免教師閃現學生頁籤） */}
      <div className="flex h-full items-center">
        {role !== null &&
          tabs.map((tab) => {
            const active = isTabActive(tab.href, pathname);
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

      {/* Chat Toggle — 僅 chat 收合時顯示，避免重複（chat 開啟時 ChatPanel 內已有收合按鈕） */}
      {!chatOpen && (
        <button
          onClick={onToggleChat}
          className="flex size-8 items-center justify-center rounded-md text-text-muted hover:text-text-primary hover:bg-surface-2 transition-colors"
          title="展開 Coddy (Ctrl+B)"
          aria-label="展開 Coddy"
        >
          <MessageSquare className="size-4" />
        </button>
      )}

      <AvatarMenu role={role} />
    </nav>
  );
}

function AvatarMenu({ role }: { role: Role | null }) {
  const { data: session } = useSession();
  const [open, setOpen] = useState(false);
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  /* 學生 profile（右上角顯示真實身分）；教師/未知角色不 fetch，顯示端另以 role gate。 */
  useEffect(() => {
    if (role !== "student") return;
    let cancelled = false;
    getMyProfile().then(
      (p) => !cancelled && setProfile(p),
      () => !cancelled && setProfile(null), // 未填（404）等一律視為無 profile
    );
    return () => {
      cancelled = true;
    };
  }, [role]);

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

  /* 學生優先顯示自填真名，否則退回 Google 顯示名；教師只用 Google 名 */
  const studentProfile = role === "student" ? profile : null;
  const displayName =
    studentProfile?.real_name ?? session?.user?.name ?? "使用者";
  const email = session?.user?.email ?? "";

  return (
    <div ref={containerRef} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex h-8 items-center gap-1.5 rounded-md px-1.5 text-text-secondary hover:text-text-primary hover:bg-surface-2 transition-colors"
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
            {displayName[0] ?? "U"}
          </div>
        )}
        <span className="hidden max-w-[7rem] truncate text-sm sm:inline">
          {displayName}
        </span>
        <ChevronDown className={`size-3 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      {open && (
        <div
          className="absolute right-0 top-full mt-1 w-56 rounded-md border border-border-default bg-surface-1 py-1 shadow-modal z-50"
          role="menu"
        >
          {/* User info header — 學生顯示自填身分（真名 + 校系 + 學號） */}
          <div className="px-3 py-2 border-b border-border-muted">
            <div className="text-sm font-medium text-text-primary truncate">
              {displayName}
            </div>
            {studentProfile && (
              <div className="text-xs text-text-secondary truncate">
                {studentProfile.school} · {studentProfile.department}
              </div>
            )}
            {studentProfile?.student_id && (
              <div className="text-xs text-text-muted truncate">
                學號 {studentProfile.student_id}
              </div>
            )}
            {email && <div className="text-xs text-text-muted truncate">{email}</div>}
          </div>

          {/* Menu items（教師的班級/作業已移至頂部導航） */}
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
