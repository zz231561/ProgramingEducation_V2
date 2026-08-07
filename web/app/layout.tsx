import type { Metadata } from "next";
import { Inter, Noto_Sans_TC, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { SessionProvider } from "@/components/providers/session-provider";
import { Toaster } from "sonner";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const notoSansTC = Noto_Sans_TC({
  variable: "--font-noto-sans-tc",
  subsets: ["latin"],
  weight: ["400", "500", "700"],
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Codedge — Code with Edge",
  description: "會思考的學習，從會提問的 AI 開始。Coddy 用蘇格拉底式提問陪你把 C++ 想清楚，不直接給答案，引導你想通每一行。",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="zh-TW"
      className={`${inter.variable} ${notoSansTC.variable} ${jetbrainsMono.variable} dark h-full antialiased`}
    >
      <body className="h-full overflow-hidden font-sans">
        <SessionProvider>
          {children}
        </SessionProvider>
        <Toaster
          position="top-right"
          theme="dark"
          duration={3000}
          toastOptions={{
            classNames: {
              toast: "!rounded-md !border !border-[#30363D] !border-l-[3px] !border-l-[#F85149] !bg-[#161B22] !text-[#E6EDF3]",
              description: "!text-[#8B949E]",
            },
          }}
        />
      </body>
    </html>
  );
}
