import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",

  async headers() {
    return [
      {
        // Zeabur 邊緣層預設宣告 `alt-svc: h3=":443"`，Chromium 系瀏覽器收到後會改走
        // HTTP/3（QUIC over UDP）。實測同一批檔案：TCP 633 KB/s、瀏覽器走 UDP 只剩
        // 約 7 KB/s——校園 / 企業 / 部分 ISP 網路對 UDP 443 常有丟包或限速。
        // `clear` 是 RFC 7838 定義的值，讓瀏覽器清除既有 alt-svc 記錄並留在 HTTP/2。
        source: "/:path*",
        headers: [{ key: "Alt-Svc", value: "clear" }],
      },
    ];
  },
};

export default nextConfig;
