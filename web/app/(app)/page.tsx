"use client";

/**
 * 根路由 — 依角色導向：教師 → 班級管理，其餘 → Workspace（U1a + 5-5 導航改造）。
 *
 * 背景：OAuth callback 落在 `/`（login callbackUrl）。原為固定 redirect /workspace，
 * 導航改造後教師預設落地改為班級管理，故改成 client 端依角色分流。
 */

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Loader2 } from "lucide-react";

import { useRole } from "@/lib/use-role";

export default function Home() {
  const router = useRouter();
  const role = useRole();

  useEffect(() => {
    if (role === null) return;
    router.replace(role === "teacher" ? "/teacher" : "/workspace");
  }, [role, router]);

  return (
    <div className="flex h-full items-center justify-center">
      <Loader2 className="size-5 animate-spin text-text-muted" />
    </div>
  );
}
