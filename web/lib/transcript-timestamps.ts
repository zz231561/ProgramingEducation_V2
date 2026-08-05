/**
 * 教材內文的時間戳處理（7-U3）。
 *
 * grounded 生成的內容會在句中夾帶 `[00:15]`、`[01:02-01:20]` 等來源戳記，
 * 讀起來被切得很碎。這裡把每個段落的戳記**移到段尾**、去重後改寫成
 * markdown 連結（自訂 scheme），由渲染端接成可點的註腳式播放標記。
 *
 * 程式碼區塊（``` 圍籬）內的內容一律不動——那可能是學生要照抄的程式。
 */

/** 自訂 scheme：讓 markdown 的 `a` 元件辨識出這是「跳轉影片」而非外部連結 */
export const SEEK_SCHEME = "codedge-seek:";

// [mm:ss] / [hh:mm:ss] / [mm:ss-mm:ss]（區間取起點）
const TIMESTAMP_RE =
  /\[(\d{1,2}:\d{2}(?::\d{2})?)(?:\s*[-–~]\s*\d{1,2}:\d{2}(?::\d{2})?)?\]/g;

/** "1:02" / "01:02:03" → 秒數；格式錯誤回 null */
export function parseClock(clock: string): number | null {
  const parts = clock.split(":").map((p) => Number(p.trim()));
  if (parts.some((n) => !Number.isFinite(n) || n < 0)) return null;
  if (parts.length === 2) return parts[0] * 60 + parts[1];
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
  return null;
}

/** 秒數 → 顯示用 `m:ss`（超過一小時才顯示 `h:mm:ss`） */
export function formatClock(seconds: number): string {
  const s = seconds % 60;
  const m = Math.floor(seconds / 60) % 60;
  const h = Math.floor(seconds / 3600);
  const mm = String(m).padStart(h > 0 ? 2 : 1, "0");
  return h > 0
    ? `${h}:${mm}:${String(s).padStart(2, "0")}`
    : `${mm}:${String(s).padStart(2, "0")}`;
}

/** 單一段落：抽出戳記 → 去重 → 附到段尾 */
function rewriteBlock(block: string): string {
  const seconds: number[] = [];
  const stripped = block.replace(TIMESTAMP_RE, (_match, clock: string) => {
    const sec = parseClock(clock);
    if (sec !== null && !seconds.includes(sec)) seconds.push(sec);
    return "";
  });
  if (seconds.length === 0) return block;

  // 移除戳記後可能留下多餘空白（「銷毀。 　。」這種）
  const text = stripped.replace(/[ \t]{2,}/g, " ").replace(/[ \t]+([，。、；：)）])/g, "$1").trimEnd();
  const markers = seconds
    .map((sec) => `[${formatClock(sec)}](${SEEK_SCHEME}${sec})`)
    .join(" ");
  return `${text} ${markers}`;
}

/**
 * 把 markdown 內所有時間戳移到各自段落的結尾並轉為可點連結。
 * 程式碼圍籬內不處理。
 */
export function rewriteTimestamps(markdown: string): string {
  const lines = markdown.split("\n");
  const out: string[] = [];
  let buffer: string[] = [];
  let inFence = false;

  const flush = () => {
    if (buffer.length === 0) return;
    out.push(rewriteBlock(buffer.join("\n")));
    buffer = [];
  };

  for (const line of lines) {
    if (/^\s*```/.test(line)) {
      flush();
      inFence = !inFence;
      out.push(line);
      continue;
    }
    if (inFence) {
      out.push(line);
      continue;
    }
    if (line.trim() === "") {
      flush();
      out.push(line);
      continue;
    }
    buffer.push(line);
  }
  flush();
  return out.join("\n");
}

/** href 是否為跳轉標記；是則回傳秒數 */
export function seekSecondsFromHref(href: string | undefined): number | null {
  if (!href || !href.startsWith(SEEK_SCHEME)) return null;
  const sec = Number(href.slice(SEEK_SCHEME.length));
  return Number.isFinite(sec) && sec >= 0 ? sec : null;
}
