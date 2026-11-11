import type { NextConfig } from "next";

// Despliegue en un único origen (Hugging Face Space): si ESCUDO_API_PROXY está definido en el build,
// /api/* se reenvía a la API interna y la web se compila con NEXT_PUBLIC_API_URL=/api.
const apiProxy = process.env.ESCUDO_API_PROXY?.replace(/\/$/, "");

// 5.1 · Política de contenidos: solo la API propia, teselas del IGN e imágenes oficiales de AEMET.
const apiOrigin = (() => {
  try {
    return new URL(process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").origin;
  } catch {
    return ""; // URL relativa (/api): mismo origen
  }
})();
const CSP = [
  "default-src 'self'",
  "script-src 'self' 'unsafe-inline'",
  "style-src 'self' 'unsafe-inline'",
  `img-src 'self' data: blob: https://www.ign.es https://opendata.aemet.es`,
  `connect-src 'self' ${apiOrigin} https://www.ign.es`.trim(),
  "worker-src 'self' blob:",
  "font-src 'self' data:",
  "frame-ancestors 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "object-src 'none'",
].join("; ");
const SECURITY_HEADERS = [
  { key: "Content-Security-Policy", value: CSP },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "geolocation=(), microphone=(), camera=(self)" },
];

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
  headers: async () => [{ source: "/:path*", headers: SECURITY_HEADERS }],
  ...(apiProxy
    ? { rewrites: async () => [{ source: "/api/:path*", destination: `${apiProxy}/:path*` }] }
    : {}),
};

export default nextConfig;
