import type { NextConfig } from "next";

// Despliegue en un único origen (Hugging Face Space): si ESCUDO_API_PROXY está definido en el build,
// /api/* se reenvía a la API interna y la web se compila con NEXT_PUBLIC_API_URL=/api.
const apiProxy = process.env.ESCUDO_API_PROXY?.replace(/\/$/, "");

const nextConfig: NextConfig = {
  /* config options here */
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
  ...(apiProxy
    ? { rewrites: async () => [{ source: "/api/:path*", destination: `${apiProxy}/:path*` }] }
    : {}),
};

export default nextConfig;
