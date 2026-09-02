/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    // next/image validates the src hostname even when a component passes
    // `unoptimized`, so scan images will not render unless their origin is
    // listed here. The http entries are for the API serving images out of
    // GridFS in development (see backend/app/api/images.py) — add the deployed
    // API's own https host alongside them when this ships.
    remotePatterns: [
      { protocol: "https", hostname: "**" },
      { protocol: "http", hostname: "localhost" },
      { protocol: "http", hostname: "127.0.0.1" },
    ],
  },
};
export default nextConfig;
