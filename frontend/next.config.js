/** @type {import('next').NextConfig} */
const nextConfig = {
  turbopack: {
    root: __dirname,
  },
  output: 'standalone', // For SSR with Docker
};
module.exports = nextConfig;
