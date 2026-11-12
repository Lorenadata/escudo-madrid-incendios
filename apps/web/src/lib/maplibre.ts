// Carga única de MapLibre con la URL de su worker (ver scripts/copy-maplibre-worker.mjs).
// Sin esto, MapLibre 6 busca el worker junto al chunk empaquetado, no lo encuentra y
// ninguna capa GeoJSON se dibuja («Worker failed to load»).
type MaplibreModule = typeof import("maplibre-gl");

let loading: Promise<MaplibreModule> | null = null;

export function loadMaplibre(): Promise<MaplibreModule> {
  loading ??= import("maplibre-gl").then((m) => {
    m.setWorkerUrl(new URL(`/maplibre-gl-worker.mjs?v=${m.getVersion()}`, window.location.origin).href);
    return m;
  });
  return loading;
}
