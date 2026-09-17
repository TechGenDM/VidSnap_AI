import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

function getBackendBaseUrl(): string {
  if (process.env.BACKEND_INTERNAL_URL) {
    return process.env.BACKEND_INTERNAL_URL.replace(/\/+$/, "");
  }
  if (process.env.RAILWAY_PRIVATE_DOMAIN) {
    const port = process.env.BACKEND_PORT || "8000";
    return `http://${process.env.RAILWAY_PRIVATE_DOMAIN}:${port}`;
  }
  if (process.env.RAILWAY_ENVIRONMENT || process.env.RAILWAY_PROJECT_ID) {
    return "http://backend.railway.internal:8000";
  }
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL.replace(/\/+$/, "");
  }
  return process.env.NODE_ENV === "production"
    ? "http://backend:8000"
    : "http://127.0.0.1:8000";
}

async function proxyMedia(
  request: NextRequest,
  { params }: { params: Promise<{ path?: string[] }> }
) {
  const resolvedParams = await params;
  const path = resolvedParams?.path ? resolvedParams.path.join("/") : "";
  const backendBase = getBackendBaseUrl();
  const search = request.nextUrl.search || "";
  const targetUrl = `${backendBase}/media${path ? `/${path}` : ""}${search}`;

  try {
    const forwardHeaders = new Headers();
    const range = request.headers.get("range");
    if (range) {
      forwardHeaders.set("range", range);
    }
    forwardHeaders.set("x-forwarded-host", request.headers.get("host") || "");
    forwardHeaders.set("x-forwarded-proto", request.headers.get("x-forwarded-proto") || "http");

    const response = await fetch(targetUrl, {
      method: request.method,
      headers: forwardHeaders,
      redirect: "manual",
      cache: "no-store",
    });

    const responseHeaders = new Headers();
    for (const [key, value] of response.headers.entries()) {
      const lower = key.toLowerCase();
      if (!["connection", "keep-alive", "transfer-encoding"].includes(lower)) {
        responseHeaders.set(key, value);
      }
    }

    return new NextResponse(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
  } catch (error: any) {
    console.error(`[Media Proxy Error] ${request.method} ${targetUrl} failed:`, error?.message || error);
    return new NextResponse(`Media asset unavailable: ${error?.message || "Internal error"}`, {
      status: 502,
    });
  }
}

export const GET = proxyMedia;
export const HEAD = proxyMedia;
