"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import type { GeoJSONSource, Map as MlMap, MapLayerMouseEvent } from "maplibre-gl";
import type { FeatureCollection } from "@/lib/api-types";
import { apiFetch } from "@/lib/api";
import { fmtShare } from "@/lib/format";
import { loadMaplibre } from "@/lib/maplibre";
import { BASEMAP_IGN, RISK_RAMP, SELECT_COLOR, trackRendered, type LegendSpec } from "./MapExplorer";
import { MapLegend } from "./MapLegend";

const OUT = "#D9DCDA"; // no cumple el filtro
const BREAKS = [0.2, 0.4, 0.6, 0.8]; // tramos fijos de 20 puntos: comparables entre filtros y capas

export interface AnalysisMapRow {
  ine_code: string;
  name: string;
  high_share: number | null;
}

interface Props {
  rows: AnalysisMapRow[];
  /** Nombre de la medida, p. ej. «Riesgo alto + muy alto». */
  measure: string;
  sourceId: string;
  hovered: string | null;
}

/** M04 · Mapa del análisis municipal: colorea solo los municipios que cumplen los filtros. */
export function AnalysisMap({ rows, measure, sourceId, hovered }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MlMap | null>(null);
  const [ready, setReady] = useState(false);
  const [muni, setMuni] = useState<FeatureCollection | null>(null);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const routerRef = useRef(router);
  useEffect(() => {
    routerRef.current = router;
  }, [router]);

  useEffect(() => {
    let disposed = false;
    (async () => {
      const maplibregl = await loadMaplibre();
      if (disposed || !ref.current) return;
      const map = new maplibregl.Map({
        container: ref.current,
        style: {
          version: 8,
          sources: {
            ign: { type: "raster", tiles: [BASEMAP_IGN], tileSize: 256, attribution: "Mapa base © Instituto Geográfico Nacional de España (CC BY 4.0)" },
          },
          layers: [{ id: "ign", type: "raster", source: "ign", paint: { "raster-saturation": -0.8, "raster-opacity": 0.7 } }],
        },
        bounds: [[-4.58, 39.88], [-3.05, 41.17]],
        fitBoundsOptions: { padding: 16 },
        minZoom: 6,
        maxZoom: 13,
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
      trackRendered(map, "a-fill", ref.current);
      const popup = new maplibregl.Popup({ closeButton: false, closeOnClick: false, offset: 8 });
      map.on("mousemove", "a-fill", (e: MapLayerMouseEvent) => {
        const p = e.features?.[0]?.properties;
        if (!p) return;
        map.getCanvas().style.cursor = p.__in ? "pointer" : "";
        const v = typeof p.__v === "number" ? fmtShare(p.__v) : "sin dato";
        popup.setLngLat(e.lngLat).setText(p.__in ? `${p.name}: ${v}` : `${p.name} (no cumple el filtro)`).addTo(map);
      });
      map.on("mouseleave", "a-fill", () => {
        map.getCanvas().style.cursor = "";
        popup.remove();
      });
      map.on("click", "a-fill", (e: MapLayerMouseEvent) => {
        const p = e.features?.[0]?.properties;
        if (p?.__in) routerRef.current.push(`/#${p.ine_code}`);
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

  const byCode = useMemo(() => new Map(rows.map((r) => [r.ine_code, r.high_share])), [rows]);

  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map || !muni) return;
    const data = {
      ...muni,
      features: muni.features.map((f) => {
        const code = String(f.properties.ine_code);
        return { ...f, properties: { ine_code: code, name: f.properties.name, __in: byCode.has(code), __v: byCode.get(code) ?? null } };
      }),
    } as unknown as GeoJSON.FeatureCollection;
    const src = map.getSource("a") as GeoJSONSource | undefined;
    if (src) {
      src.setData(data);
      return;
    }
    map.addSource("a", { type: "geojson", data, promoteId: "ine_code" });
    const step: unknown[] = ["step", ["coalesce", ["get", "__v"], 0], RISK_RAMP[0]];
    BREAKS.forEach((b, i) => step.push(b, RISK_RAMP[i + 1]));
    map.addLayer({
      id: "a-fill",
      type: "fill",
      source: "a",
      paint: {
        "fill-color": ["case", ["!", ["get", "__in"]], OUT, ["==", ["get", "__v"], null], "#FFFFFF", step] as never,
        "fill-opacity": ["case", ["get", "__in"], 0.88, 0.45] as never,
      },
    });
    map.addLayer({ id: "a-line", type: "line", source: "a", paint: { "line-color": "#15201A", "line-width": 0.35, "line-opacity": 0.5 } });
    map.addLayer({
      id: "a-hover",
      type: "line",
      source: "a",
      paint: { "line-color": SELECT_COLOR, "line-width": ["case", ["boolean", ["feature-state", "hover"], false], 3, 0] as never },
    });
  }, [ready, muni, byCode]);

  // Resalta en el mapa la fila de la tabla sobre la que está el puntero o el foco.
  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map || !map.getSource("a")) return;
    map.removeFeatureState({ source: "a" });
    if (hovered) map.setFeatureState({ source: "a", id: hovered }, { hover: true });
  }, [ready, hovered, muni]);

  const legend: LegendSpec[] = [
    {
      title: `${measure} (% de la superficie municipal), ${sourceId}`,
      items: [
        ...RISK_RAMP.map((color, i) => ({
          color,
          label: i === 0 ? "< 20 %" : i === RISK_RAMP.length - 1 ? "≥ 80 %" : `${i * 20}–${(i + 1) * 20} %`,
        })),
        { color: OUT, label: "No cumple el filtro" },
      ],
      note: "Solo se colorean los municipios de la tabla. Tramos fijos de 20 puntos sobre el reparto de la capa oficial.",
    },
  ];

  return (
    <div className="relative h-[440px] overflow-hidden rounded border border-line bg-granite sm:h-[520px]">
      <div
        ref={ref}
        style={{ position: "absolute", inset: 0 }}
        role="region"
        aria-label="Mapa de los municipios que cumplen los filtros"
      />
      {error && (
        <div role="alert" className="absolute left-3 right-3 top-3 z-10 rounded border-l-4 border-rust bg-white p-2 text-sm shadow">
          {error}
        </div>
      )}
      <MapLegend specs={legend} className="absolute bottom-3 left-3 max-w-[15rem]" />
    </div>
  );
}
