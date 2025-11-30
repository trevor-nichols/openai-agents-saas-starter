import path from "path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  cacheComponents: true,
  outputFileTracingRoot: __dirname,
  turbopack: {
    // Explicitly set the project root so Next doesn't mis-infer it as app/
    root: __dirname,
  },
};

export default nextConfig;
