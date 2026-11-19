"use client";

import { useEffect, useRef, useState } from "react";
import type { GeoJSONSource, Map as MlMap, MapLayerMouseEvent } from "maplibre-gl";
import type { FeatureCollection } from "@/lib/api-types";
import { apiFetch } from "@/lib/api";
import { loadMaplibre } from "@/lib/maplibre";
import { BASEMAP_IGN, trackRendered } from "../MapExplorer";

export interface NoctMapValue {
  color: string;
  label: string;
}

interface Props {
  ariaLabel: string;
  values: Map<string, NoctMapValue>;
  selected?: string | null;
  onSelect?: (code: string) => void;
  legendTitle: string;
  legend: { color: string; label: string }[];
  className?: string;
}

const NO_DATA = "#26332D";

/** Mapa municipal sobre fondo nocturno. Los colores llegan ya calculados; aquí solo se dibujan. */
export function NoctMap({ ariaLabel, values, selected, onSelect, legendTitle, legend, className = "h-[420px]" }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MlMap | null>(null);
  const valuesRef = useRef(values);
  const onSelectRef = useRef(onSelect);
  const [ready, setReady] = useState(false);
  const [muni, setMuni] = useState<FeatureCollection | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    valuesRef.current = values;
    onSelectRef.current = onSelect;
  }, [values, onSelect]);

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
          layers: [
            { id: "bg", type: "background", paint: { "background-color": "#0B1512" } },
            { id: "ign", type: "raster", source: "ign", paint: { "raster-saturation": -1, "raster-brightness-max": 0.32, "raster-opacity": 0.55 } },
          ],
        },
        bounds: [[-4.58, 39.88], [-3.05, 41.17]],
        fitBoundsOptions: { padding: 14 },
        minZoom: 6,
        maxZoom: 12,
        attributionControl: { compact: true },
        cooperativeGestures: true,
      });
      map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
      map.on("load", () => {
        mapRef.current = map;
        setReady(true);
      });
      map.on("error", (e: { error?: { message?: string }; sourceId?: string }) => {
        if (e.sourceId !== "ign") setError(`El mapa no ha podido dibujar los datos: ${e.error?.message ?? "error desconocido"}`);
      });
      trackRendered(map, "n-fill", ref.current);
      const popup = new maplibregl.Popup({ closeButton: false, closeOnClick: false, offset: 8 });
      map.on("mousemove", "n-fill", (e: MapLayerMouseEvent) => {
        const p = e.features?.[0]?.properties;
        if (!p) return;
        map.getCanvas().style.cursor = "pointer";
        const v = valuesRef.current.get(String(p.ine_code));
        popup.setLngLat(e.lngLat).setText(`${p.name}: ${v?.label ?? "sin dato"}`).addTo(map);
      });
      map.on("mouseleave", "n-fill", () => {
        map.getCanvas().style.cursor = "";
        popup.remove();
      });
      map.on("click", "n-fill", (e: MapLayerMouseEvent) => {
        const code = e.features?.[0]?.properties?.ine_code;
        if (code) onSelectRef.current?.(String(code));
      });
    })();
    return () => {
      disposed = true;
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    apiFetch<FeatureCollection>("/v1/layers/municipalities/geojson")
      .then(setMuni)
      .catch((e) => setError(`Capa de municipios no disponible: ${e.message}`));
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map || !muni) return;
    const data = {
      ...muni,
      features: muni.features.map((f) => {
        const code = String(f.properties.ine_code);
        return { ...f, properties: { ine_code: code, name: f.properties.name, __c: values.get(code)?.color ?? NO_DATA } };
      }),
    } as unknown as GeoJSON.FeatureCollection;
    const src = map.getSource("n") as GeoJSONSource | undefined;
    if (src) {
      src.setData(data);
      return;
    }
    map.addSource("n", { type: "geojson", data, promoteId: "ine_code" });
    map.addLayer({ id: "n-fill", type: "fill", source: "n", paint: { "fill-color": ["get", "__c"] as never, "fill-opacity": 0.9 } });
    map.addLayer({ id: "n-line", type: "line", source: "n", paint: { "line-color": "#0B1512", "line-width": 0.7 } });
    map.addLayer({
      id: "n-sel",
      type: "line",
      source: "n",
      paint: { "line-color": "#F4EFE3", "line-width": ["case", ["boolean", ["feature-state", "sel"], false], 2.6, 0] as never },
    });
  }, [ready, muni, values]);

  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map || !muni || !map.getSource("n")) return;
    map.removeFeatureState({ source: "n" });
    if (selected) map.setFeatureState({ source: "n", id: selected }, { sel: true });
  }, [ready, muni, selected, values]);

  return (
    <div className={`relative overflow-hidden rounded-sm border border-noct-line bg-noct-bg ${className}`}>
      <div ref={ref} style={{ position: "absolute", inset: 0 }} role="region" aria-label={ariaLabel} />
      {error && (
        <p role="alert" className="absolute left-3 right-3 top-3 z-10 rounded-sm border border-[#EA3A54] bg-noct-surface p-2 text-sm text-noct-ink">
          {error}
        </p>
      )}
      <div className="absolute left-2 top-2 rounded-sm border border-noct-line bg-noct-bg/90 px-2.5 py-2 text-xs text-noct-ink2">
        <p className="mb-1 font-medium text-noct-ink">{legendTitle}</p>
        <ul>
          {legend.map((l) => (
            <li key={l.label} className="flex items-center gap-1.5 leading-[18px]">
              <span className="h-2.5 w-4 shrink-0" style={{ background: l.color }} aria-hidden />
              {l.label}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
