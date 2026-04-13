"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import {
  Code,
  BookOpen,
  FileQuestion,
  Network,
  MoreHorizontal,
} from "lucide-react";

const navItems = [
  { icon: Code, label: "Workspace", href: "/workspace" },
  { icon: BookOpen, label: "Learn", href: "/learn" },
  { icon: FileQuestion, label: "Quiz", href: "/quiz" },
  { icon: Network, label: "Knowledge", href: "/knowledge" },
  { icon: MoreHorizontal, label: "更多", href: "/overview" },
];

export function MobileNav() {
  const pathname = usePathname();

  return (
    <nav className="flex h-14 shrink-0 items-center justify-around border-t border-border-default bg-bg-default">
      {navItems.map((item) => {
        const isActive = pathname.startsWith(item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            className="flex flex-col items-center gap-0.5 px-2"
          >
            <item.icon
              className={`size-5 ${
                isActive ? "text-accent-blue" : "text-text-muted"
              } transition-colors`}
            />
            <span
              className={`text-[10px] ${
                isActive ? "text-accent-blue" : "text-text-muted"
              }`}
            >
              {item.label}
            </span>
          </Link>
        );
      })}
    </nav>
  );
}
