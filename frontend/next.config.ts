import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // All /api/* and /media/* requests are dynamically proxied via Next.js
  // App Router Route Handlers (app/api/[[...path]] and app/media/[[...path]]),
  // allowing dynamic runtime resolution of internal backend URLs across environments.
};

export default nextConfig;
