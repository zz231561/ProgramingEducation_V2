/**
 * NextAuth.js v5 設定 — Google OAuth provider。
 *
 * 環境變數（.env.local）：
 *   AUTH_SECRET          — NextAuth session 簽名密鑰
 *   AUTH_GOOGLE_ID       — Google OAuth Client ID
 *   AUTH_GOOGLE_SECRET   — Google OAuth Client Secret
 */

import NextAuth from "next-auth";
import Google from "next-auth/providers/google";

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [Google],

  pages: {
    signIn: "/login",
  },

  callbacks: {
    /** middleware 用 — 未登入重導至 /login */
    authorized({ auth: session, request }) {
      const isLoggedIn = !!session?.user;
      const isOnLogin = request.nextUrl.pathname.startsWith("/login");

      if (isOnLogin) {
        if (isLoggedIn) return Response.redirect(new URL("/workspace", request.nextUrl));
        return true;
      }

      return isLoggedIn;
    },

    /** 將 Google profile 資訊寫入 JWT token */
    jwt({ token, account, profile }) {
      if (account && profile) {
        token.googleId = profile.sub;
        token.picture = profile.picture;
      }
      return token;
    },

    /** 將 JWT 資訊暴露至 client-side session */
    session({ session, token }) {
      if (session.user) {
        session.user.id = token.sub!;
        session.user.image = token.picture as string;
      }
      return session;
    },
  },
});
