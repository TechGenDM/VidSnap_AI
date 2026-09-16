import type { NextConfig } from "next";

const isProd = process.env.NODE_ENV === "production";
const defaultBackend = isProd ? "http://backend:8000" : "http://127.0.0.1:8000";

const BACKEND_URL =
  process.env.BACKEND_INTERNAL_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  defaultBackend;

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${BACKEND_URL}/api/:path*`,
      },
      {
        source: "/media/:path*",
        destination: `${BACKEND_URL}/media/:path*`,
      },
    ];
  },
};

export default nextConfig;
