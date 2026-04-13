/**
 * Catch-all API proxy — 將 /api/* 轉發至 FastAPI backend。
 *
 * Browser → Next.js /api/health → FastAPI http://localhost:8000/health
 */

import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

async function proxyRequest(
  req: NextRequest,
  { params }: { params: Promise<{ path: string[] }> },
): Promise<NextResponse> {
  const { path } = await params;
  const backendPath = path.join("/");
  const url = new URL(backendPath, BACKEND_URL);

  // 保留 query string
  req.nextUrl.searchParams.forEach((value, key) => {
    url.searchParams.append(key, value);
  });

  const headers = new Headers(req.headers);
  // 移除 Next.js 特有的 header，避免干擾後端
  headers.delete("host");

  const init: RequestInit = {
    method: req.method,
    headers,
  };

  // 有 body 的 method 才附帶 body
  if (!["GET", "HEAD"].includes(req.method)) {
    init.body = await req.arrayBuffer();
  }

  try {
    const upstream = await fetch(url.toString(), init);

    return new NextResponse(upstream.body, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers: upstream.headers,
    });
  } catch {
    return NextResponse.json(
      {
        error: "BACKEND_UNAVAILABLE",
        message: "後端服務暫時不可用，請稍後再試",
      },
      { status: 502 },
    );
  }
}

export const GET = proxyRequest;
export const POST = proxyRequest;
export const PUT = proxyRequest;
export const PATCH = proxyRequest;
export const DELETE = proxyRequest;
