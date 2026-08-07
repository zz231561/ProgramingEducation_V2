import { describe, expect, it } from "vitest";

import {
  SEEK_SCHEME,
  formatClock,
  parseClock,
  rewriteTimestamps,
  seekSecondsFromHref,
} from "@/lib/transcript-timestamps";

describe("parseClock", () => {
  it("解析 mm:ss 與 hh:mm:ss", () => {
    expect(parseClock("1:02")).toBe(62);
    expect(parseClock("00:15")).toBe(15);
    expect(parseClock("01:02:03")).toBe(3723);
  });

  it("格式錯誤回 null", () => {
    expect(parseClock("abc")).toBeNull();
    expect(parseClock("15")).toBeNull();
    expect(parseClock("1:2:3:4")).toBeNull();
    expect(parseClock("-1:00")).toBeNull();
  });
});

describe("formatClock", () => {
  it("一小時以內顯示 m:ss", () => {
    expect(formatClock(5)).toBe("0:05");
    expect(formatClock(62)).toBe("1:02");
    expect(formatClock(3599)).toBe("59:59");
  });

  it("超過一小時才顯示 h:mm:ss", () => {
    expect(formatClock(3723)).toBe("1:02:03");
  });
});

describe("rewriteTimestamps", () => {
  it("把段落中的戳記移到段尾並轉成可點連結", () => {
    const out = rewriteTimestamps("這是一段 [00:15] 說明。");
    expect(out).toBe(`這是一段 說明。 [0:15](${SEEK_SCHEME}15)`);
  });

  it("同段落內重複的時間只留一個標記", () => {
    const out = rewriteTimestamps("前面 [0:15] 中間 [00:15] 後面 [01:00]");
    expect(out).toBe(
      `前面 中間 後面 [0:15](${SEEK_SCHEME}15) [1:00](${SEEK_SCHEME}60)`,
    );
  });

  it("區間戳記取起點", () => {
    expect(rewriteTimestamps("說明 [01:02-01:20]")).toBe(
      `說明 [1:02](${SEEK_SCHEME}62)`,
    );
  });

  it("各段落各自結尾，空行不併段", () => {
    const out = rewriteTimestamps("第一段 [0:10]\n\n第二段 [0:20]");
    expect(out).toBe(
      `第一段 [0:10](${SEEK_SCHEME}10)\n\n第二段 [0:20](${SEEK_SCHEME}20)`,
    );
  });

  it("程式碼圍籬內原樣不動", () => {
    const src = "說明 [0:05]\n```cpp\nint x; // [0:30]\n```\n結尾 [0:40]";
    const out = rewriteTimestamps(src);
    expect(out).toContain("int x; // [0:30]");
    expect(out).toContain(`說明 [0:05](${SEEK_SCHEME}5)`);
    expect(out).toContain(`結尾 [0:40](${SEEK_SCHEME}40)`);
  });

  it("沒有戳記就完全不動（含標點與空白）", () => {
    const src = "一般段落，不含任何戳記。\n\n```\nraw\n```";
    expect(rewriteTimestamps(src)).toBe(src);
  });

  it("戳記緊鄰標點時不留下多餘空白", () => {
    expect(rewriteTimestamps("先宣告再使用 [0:15]。")).toBe(
      `先宣告再使用。 [0:15](${SEEK_SCHEME}15)`,
    );
  });
});

describe("seekSecondsFromHref", () => {
  it("辨識自訂 scheme 並取出秒數", () => {
    expect(seekSecondsFromHref(`${SEEK_SCHEME}90`)).toBe(90);
    expect(seekSecondsFromHref(`${SEEK_SCHEME}0`)).toBe(0);
  });

  it("外部連結與壞值回 null", () => {
    expect(seekSecondsFromHref("https://youtu.be/abc")).toBeNull();
    expect(seekSecondsFromHref(undefined)).toBeNull();
    expect(seekSecondsFromHref(`${SEEK_SCHEME}abc`)).toBeNull();
    expect(seekSecondsFromHref(`${SEEK_SCHEME}-5`)).toBeNull();
  });
});
