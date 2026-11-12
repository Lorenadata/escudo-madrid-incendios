// MapLibre 6 carga su worker como fichero aparte (maplibre-gl-worker.mjs) junto al módulo.
// Al empaquetar con Next.js ese fichero no se publica, así que lo copiamos a public/ y
// src/lib/maplibre.ts fija su URL con setWorkerUrl. Se ejecuta antes de dev y build.
import { copyFileSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("..", import.meta.url));
const src = `${root}node_modules/maplibre-gl/dist/maplibre-gl-worker.mjs`;
const dst = `${root}public/maplibre-gl-worker.mjs`;
copyFileSync(src, dst);
const { version } = JSON.parse(readFileSync(`${root}node_modules/maplibre-gl/package.json`, "utf8"));
console.log(`maplibre-gl-worker.mjs ${version} copiado a public/`);
