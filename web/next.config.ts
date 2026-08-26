import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**.onrender.com",
      },
    ],
  },
};

export default nextConfig;
