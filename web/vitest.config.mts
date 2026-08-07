import { fileURLToPath } from "node:url";

import { defineConfig } from "vitest/config";

export default defineConfig({
  resolve: {
    // 對齊 tsconfig 的 `@/*` → 專案根目錄
    alias: { "@": fileURLToPath(new URL("./", import.meta.url)) },
  },
  test: {
    // use-run-history 需要 sessionStorage；純函式測試在 jsdom 下也照跑
    environment: "jsdom",
    include: ["tests/**/*.test.ts"],
  },
});
