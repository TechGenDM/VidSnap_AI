import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

function getBackendBaseUrl(): string {
  // 1. Explicit internal backend URL (configured in Railway, Docker Compose, or .env)
  if (process.env.BACKEND_INTERNAL_URL) {
    return process.env.BACKEND_INTERNAL_URL.replace(/\/+$/, "");
  }

  // 2. Railway private networking variable
  if (process.env.RAILWAY_PRIVATE_DOMAIN) {
    const port = process.env.BACKEND_PORT || "8000";
    return `http://${process.env.RAILWAY_PRIVATE_DOMAIN}:${port}`;
  }

  // 3. If running inside Railway environment and no explicit backend URL was provided,
  // default to the Railway private internal DNS for the 'backend' service
  if (process.env.RAILWAY_ENVIRONMENT || process.env.RAILWAY_PROJECT_ID) {
    return "http://backend.railway.internal:8000";
  }

  // 4. Public client API URL fallback
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL.replace(/\/+$/, "");
  }

  // 5. Default fallback for local Docker Compose vs local developer machine
  return process.env.NODE_ENV === "production"
    ? "http://backend:8000"
    : "http://127.0.0.1:8000";
}

async function proxyRequest(
  request: NextRequest,
  { params }: { params: Promise<{ path?: string[] }> }
) {
  const resolvedParams = await params;
  const path = resolvedParams?.path ? resolvedParams.path.join("/") : "";
  const backendBase = getBackendBaseUrl();
  const search = request.nextUrl.search || "";
  const targetUrl = `${backendBase}/api${path ? `/${path}` : ""}${search}`;

  try {
    const isBodyMethod = !["GET", "HEAD"].includes(request.method);
    const body = isBodyMethod ? await request.arrayBuffer() : undefined;

    const forwardHeaders = new Headers();
    for (const [key, value] of request.headers.entries()) {
      const lower = key.toLowerCase();
      if (lower !== "host" && lower !== "connection" && lower !== "content-length") {
        forwardHeaders.set(key, value);
      }
    }

    forwardHeaders.set("x-forwarded-host", request.headers.get("host") || "");
    forwardHeaders.set("x-forwarded-proto", request.headers.get("x-forwarded-proto") || "http");

    const response = await fetch(targetUrl, {
      method: request.method,
      headers: forwardHeaders,
      body,
      redirect: "manual",
      cache: "no-store",
      // @ts-expect-error duplex required for streaming in Node fetch
      duplex: "half",
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
    console.error(`[API Proxy Error] ${request.method} ${targetUrl} failed:`, error?.message || error);
    return NextResponse.json(
      {
        detail: `Backend connection error: ${error?.message || "Failed to reach backend API"}. Target: ${targetUrl}`,
        error: true,
        target: targetUrl,
      },
      { status: 502 }
    );
  }
}

export const GET = proxyRequest;
export const POST = proxyRequest;
export const PUT = proxyRequest;
export const DELETE = proxyRequest;
export const PATCH = proxyRequest;
export const HEAD = proxyRequest;
export const OPTIONS = proxyRequest;
