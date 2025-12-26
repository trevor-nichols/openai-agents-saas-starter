import { resolve } from "node:path";

import type { NextConfig } from "next";

const workspaceRoot = resolve(__dirname, "../..");

const nextConfig: NextConfig = {
  cacheComponents: true,
  output: "standalone",
  outputFileTracingRoot: workspaceRoot,
  turbopack: {
    // Ensure Turbopack can resolve hoisted workspace dependencies in Docker/CI.
    root: workspaceRoot,
  },
};

export default nextConfig;
