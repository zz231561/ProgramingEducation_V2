/**
 * NextAuth v5 proxy（Next.js 16 將 middleware 改名為 proxy）— 未登入使用者重導至 /login。
 * /login 和 /api 路徑不做驗證。
 */

export { auth as proxy } from "@/auth";

export const config = {
  matcher: [
    /*
     * 排除以下路徑：
     * - /login（登入頁本身）
     * - /api（API 路由，含 NextAuth callback）
     * - /_next（Next.js 內部資源）
     * - favicon.ico、圖片等靜態資源
     */
    "/((?!login|api|_next|favicon\\.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
