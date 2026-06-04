/** @type {import('next').NextConfig} */
const nextConfig = {
  // Allow the web app to read JSON files from data/schools at build time
  // by extending the webpack config (not needed for server components reading fs)
  experimental: {
    // Enable server actions for form handling
    serverActions: {
      allowedOrigins: ["localhost:3000"],
    },
  },
};

module.exports = nextConfig;
