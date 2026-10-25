import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async redirects() {
    return [
      {
        source: '/goals',
        destination: '/wealth-intelligence/goals',
        permanent: false,
      },
      {
        source: '/governance/transactions',
        destination: '/governance/data?tab=transactions',
        permanent: true,
      },
      {
        source: '/governance/positions',
        destination: '/governance/data?tab=positions',
        permanent: true,
      },
      {
        source: '/governance/dividends',
        destination: '/governance/data?tab=dividends',
        permanent: true,
      },
    ];
  },
};

export default nextConfig;
