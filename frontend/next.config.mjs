/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    proxyTimeout: 120000, // Extends the timeout to 2 minutes (120,000 ms)
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*', // Proxy to Backend
      },
    ];
  },
};

export default nextConfig;