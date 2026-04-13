/**
 * NextAuth.js v5 設定 — Google OAuth provider。
 *
 * 環境變數：
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
