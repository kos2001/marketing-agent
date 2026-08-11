import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Docker 런타임 이미지가 필요한 서버 파일만 담도록 한다 (node_modules 전체
  // 대신 standalone 서버 하나) — weekly-report-harness와 같은 배포 방식.
  output: "standalone",
};

export default nextConfig;
