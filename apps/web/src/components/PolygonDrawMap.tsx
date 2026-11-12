"use client";

import type { Map as MlMap, MapMouseEvent } from "maplibre-gl";
import { useEffect, useRef, useState } from "react";
import { API_URL } from "@/lib/api";
import { loadMaplibre } from "@/lib/maplibre";
import { BASEMAP_IGN } from "./MapExplorer";

// Dibujo de la geometría AUTORIZADA de un ámbito (M05): clic = vértice, «Cerrar polígono» = terminar.
// Alternativa accesible sin ratón: pegar un GeoJSON Polygon. Nunca se dibujan viviendas individuales.

export type Polygon = { type: "Polygon"; coordinates: number[][][] };

type Feature = { type: "Feature"; properties: { ine_code: string }; geometry: { type: string; coordinates: unknown } };
let muniCache: Promise<{ features: Feature[] }> | null = null;
function municipalities() {
  muniCache ??= fetch(`${API_URL}/v1/layers/municipalities/geojson`).then((r) => {
    if (!r.ok) throw new Error(`Error ${r.status}`);
    return r.json();
  });
  return muniCache;
}

function bboxOf(coords: unknown, acc: [number, number, number, number] = [180, 90, -180, -90]) {
  if (Array.isArray(coords) && typeof coords[0] === "number") {
    const [x, y] = coords as number[];
    acc[0] = Math.min(acc[0], x); acc[1] = Math.min(acc[1], y); acc[2] = Math.max(acc[2], x); acc[3] = Math.max(acc[3], y);
  } else if (Array.isArray(coords)) coords.forEach((c) => bboxOf(c, acc));
  return acc;
}

export function parsePolygon(text: string): Polygon | null {
  try {
    let g = JSON.parse(text);
    if (g?.type === "FeatureCollection") g = g.features?.[0];
    if (g?.type === "Feature") g = g.geometry;
    if (g?.type !== "Polygon" || !Array.isArray(g.coordinates?.[0]) || g.coordinates[0].length < 4) return null;
    return { type: "Polygon", coordinates: g.coordinates };
  } catch {
    return null;
  }
}

export function PolygonDrawMap({ municipalityCode, value, onChange }: { municipalityCode: string; value: Polygon | null; onChange: (p: Polygon | null) => void }) {
  const ref = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MlMap | null>(null);
  const [ready, setReady] = useState(false);
  const [points, setPoints] = useState<[number, number][]>([]);
  const [paste, setPaste] = useState("");
  const [pasteError, setPasteError] = useState<string | null>(null);
  const closed = value !== null;
  const closedRef = useRef(closed);
  useEffect(() => {
    closedRef.current = closed;
  }, [closed]);

  useEffect(() => {
    let disposed = false;
    (async () => {
      const maplibregl = await loadMaplibre();
      if (disposed || !ref.current) return;
      const map = new maplibregl.Map({
        container: ref.current,
        style: {
          version: 8,
          sources: { ign: { type: "raster", tiles: [BASEMAP_IGN], tileSize: 256, attribution: "Mapa base © Instituto Geográfico Nacional de España (CC BY 4.0)" } },
          layers: [{ id: "ign", type: "raster", source: "ign", paint: { "raster-saturation": -0.5 } }],
        },
        center: [-3.72, 40.5],
        zoom: 8,
        maxBounds: [[-5.6, 39.4], [-1.9, 41.7]],
        doubleClickZoom: false,
      });
      map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
      map.on("load", () => {
        map.addSource("muni", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
        map.addLayer({ id: "muni-line", type: "line", source: "muni", paint: { "line-color": "#1F3A2E", "line-width": 2, "line-dasharray": [2, 1] } });
        map.addSource("draw", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
        map.addLayer({ id: "draw-fill", type: "fill", source: "draw", filter: ["==", "$type", "Polygon"], paint: { "fill-color": "#C2741F", "fill-opacity": 0.25 } });
        map.addLayer({ id: "draw-line", type: "line", source: "draw", paint: { "line-color": "#93530F", "line-width": 2.5 } });
        map.addLayer({ id: "draw-pts", type: "circle", source: "draw", filter: ["==", "$type", "Point"], paint: { "circle-radius": 5, "circle-color": "#93530F", "circle-stroke-color": "#ffffff", "circle-stroke-width": 1.5 } });
        mapRef.current = map;
        setReady(true);
      });
      map.on("click", (e: MapMouseEvent) => {
        if (closedRef.current) return;
        setPoints((p) => [...p, [Number(e.lngLat.lng.toFixed(6)), Number(e.lngLat.lat.toFixed(6))]]);
      });
    })();
    return () => {
      disposed = true;
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, []);

  // Contorno del municipio elegido y encuadre
  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map || !municipalityCode) return;
    municipalities().then((fc) => {
      const f = fc.features.find((x) => x.properties.ine_code === municipalityCode);
      const src = map.getSource("muni") as { setData: (d: unknown) => void } | undefined;
      src?.setData({ type: "FeatureCollection", features: f ? [f] : [] });
      if (f) {
        const [a, b, c, d] = bboxOf(f.geometry.coordinates);
        map.fitBounds([[a, b], [c, d]], { padding: 24, duration: 0 });
      }
    }).catch(() => undefined);
  }, [ready, municipalityCode]);

  // Pinta el dibujo en curso o el polígono cerrado
  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map) return;
    const ring = value ? value.coordinates[0] : points;
    const feats: unknown[] = ring.map((c) => ({ type: "Feature", properties: {}, geometry: { type: "Point", coordinates: c } }));
    if (value) feats.push({ type: "Feature", properties: {}, geometry: value });
    else if (points.length >= 2) feats.push({ type: "Feature", properties: {}, geometry: { type: "LineString", coordinates: points } });
    (map.getSource("draw") as { setData: (d: unknown) => void } | undefined)?.setData({ type: "FeatureCollection", features: feats });
  }, [ready, points, value]);

  function close() {
    if (points.length < 3) return;
    onChange({ type: "Polygon", coordinates: [[...points, points[0]]] });
  }

  return (
    <div className="space-y-2">
      <div className="relative h-64 overflow-hidden rounded border border-line">
        <div ref={ref} style={{ position: "absolute", inset: 0 }} role="region" aria-label="Mapa para dibujar el ámbito" />
      </div>
      <p className="text-xs text-ink-600" aria-live="polite">
        {closed
          ? `Polígono cerrado (${(value?.coordinates[0].length ?? 1) - 1} vértices).`
          : `Haz clic en el mapa para añadir vértices (${points.length}). Mínimo 3.`}{" "}
        Dibuja el perímetro del ámbito autorizado, no viviendas concretas.
      </p>
      <div className="flex flex-wrap gap-2">
        <button type="button" className="btn-secondary" disabled={closed || points.length < 3} onClick={close}>Cerrar polígono</button>
        <button type="button" className="btn-secondary" disabled={closed || points.length === 0} onClick={() => setPoints((p) => p.slice(0, -1))}>Deshacer punto</button>
        <button type="button" className="btn-secondary" disabled={!closed && points.length === 0} onClick={() => { setPoints([]); onChange(null); }}>Borrar</button>
      </div>
      <details className="text-sm">
        <summary className="cursor-pointer text-slate">Pegar un GeoJSON (alternativa sin ratón)</summary>
        <textarea aria-label="GeoJSON del ámbito" className="field mt-1 font-mono text-xs" rows={3} value={paste} onChange={(e) => setPaste(e.target.value)} placeholder='{"type":"Polygon","coordinates":[[[lon,lat],...]]}' />
        <button
          type="button"
          className="btn-secondary mt-1"
          onClick={() => {
            const p = parsePolygon(paste);
            if (!p) {
              setPasteError("No es un Polygon GeoJSON válido (EPSG:4326, anillo cerrado de al menos 3 vértices).");
              return;
            }
            setPasteError(null);
            setPoints([]);
            onChange(p);
          }}
        >
          Usar este GeoJSON
        </button>
        {pasteError && <p role="alert" className="text-xs text-rust">{pasteError}</p>}
      </details>
    </div>
  );
}
