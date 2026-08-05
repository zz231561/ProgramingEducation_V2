/**
 * SSE 讀取器（7-U6）。
 *
 * 不用瀏覽器內建的 `EventSource`：它只支援 GET 且無法帶 body，
 * 而 `/chat/interact` 是帶 payload 的 POST。改用 fetch + ReadableStream 自行解析。
 */

export interface SseEvent {
  event: string;
  data: string;
}

/** 解析 SSE 位元流；逐一 yield 完整事件（以空行分隔） */
export async function* readSse(
  body: ReadableStream<Uint8Array>,
): AsyncGenerator<SseEvent> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let sep: number;
    // 事件之間以空行分隔；\r\n 由代理層加入時也要吃掉
    while ((sep = buffer.search(/\r?\n\r?\n/)) !== -1) {
      const raw = buffer.slice(0, sep);
      buffer = buffer.slice(sep).replace(/^\r?\n\r?\n/, "");
      const parsed = parseBlock(raw);
      if (parsed) yield parsed;
    }
  }
}

function parseBlock(raw: string): SseEvent | null {
  let event = "message";
  const dataLines: string[] = [];
  for (const line of raw.split(/\r?\n/)) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
  }
  if (dataLines.length === 0) return null;
  return { event, data: dataLines.join("\n") };
}
