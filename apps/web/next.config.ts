import type { NextConfig } from "next";

const isGitHubPages = process.env.GITHUB_PAGES === "true";

const nextConfig: NextConfig = {
  agentRules: false,
  ...(isGitHubPages
    ? {
        output: "export" as const,
        basePath: "/omnisight",
        assetPrefix: "/omnisight/",
      }
    : {}),
  experimental: {
    useTypeScriptCli: false,
  },
};

export default nextConfig;
