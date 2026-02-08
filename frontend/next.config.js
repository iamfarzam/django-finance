/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',

  // Base path for static serving from Django
  basePath: '/static/react',

  // Asset prefix for static files
  assetPrefix: '/static/react',

  // Disable image optimization for static export
  images: {
    unoptimized: true,
  },

  // Trailing slash for static HTML files
  trailingSlash: true,

  // Disable server-side features for static export
  eslint: {
    ignoreDuringBuilds: true,
  },

  // Environment variables available at build time
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || '/api/v1',
  },
};

module.exports = nextConfig;
