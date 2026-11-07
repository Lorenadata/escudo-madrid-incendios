"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { Map as MlMap, GeoJSONSource, MapLayerMouseEvent } from "maplibre-gl";
import type { FeatureCollection, Layer } from "@/lib/api-types";
import { apiFetch } from "@/lib/api";
import { fmtNumber, fmtShare } from "@/lib/format";

export type ChoroplethKey = "density" | "age_65_plus_share" | "altitude_m";

export const CHOROPLETH_OPTIONS: Record<ChoroplethKey, { label: string; source: string; isShare: boolean; unit: string }> = {
  density: { label: "Densidad de población", source: "CAM-02", isShare: false, unit: "hab/km²" },
  age_65_plus_share: { label: "Población de 65 años o más", source: "CAM-01", isShare: true, unit: "%" },
  altitude_m: { label: "Altitud del municipio", source: "CAM-03", isShare: false, unit: "m" },
};

const RAMP = ["#E3ECE6", "#B9D0C2", "#86AE98", "#4F826A", "#1E3B2F"];
// Rampa ordinal para clases oficiales (de menor a mayor). Clases no ordinales → gris.
const ORDINAL_RAMP = ["#F4E9B8", "#EBC46E", "#D98A3A", "#B5502A", "#7A2416", "#4A120B"];
const NON_ORDINAL = "#8A8F8C";

/** Posición ordinal de una etiqueta literal («Riesgo muy bajo» … «muy alto»); null si no es ordinal. */
export function ordinalRank(label: string): number | null {
  const l = label.toLowerCase().normalize("NFD").replace(/\p{M}/gu, "");
  if (/no calculad|sin dato|sin clasificar|no aplica/.test(l)) return null;
  if (/muy baj/.test(l)) return 0;
  if (/\bbaj/.test(l)) return 1;
  if (/moderad|\bmedi/.test(l)) return 2;
  if (/muy alt/.test(l)) return 4;
  if (/\balt/.test(l)) return 3;
  if (/extrem/.test(l)) return 5;
  return null;
}

export function classLegend(labels: string[]): { label: string; color: string }[] {
  const uniq = Array.from(new Set(labels.filter(Boolean)));
  const ranked = uniq.map((label) => ({ label, rank: ordinalRank(label) }));
  ranked.sort((a, b) => (a.rank ?? 99) - (b.rank ?? 99) || a.label.localeCompare(b.label, "es"));
  const ordinalCount = ranked.filter((r) => r.rank !== null).length;
  const maxRank = Math.max(0, ...ranked.map((r) => r.rank ?? 0));
  return ranked.map((r) => ({
    label: r.label,
    color:
      r.rank === null
        ? NON_ORDINAL
        : ORDINAL_RAMP[Math.round((r.rank / Math.max(1, maxRank)) * (Math.min(ORDINAL_RAMP.length, Math.max(ordinalCount, 2)) - 1))],
  }));
}

export const BASEMAP_IGN =
  "https://www.ign.es/wmts/ign-base?service=WMTS&request=GetTile&version=1.0.0&layer=IGNBaseTodo&style=default&tilematrixset=GoogleMapsCompatible&tilematrix={z}&tilerow={y}&tilecol={x}&format=image/jpeg";

/** Lee el valor de una propiedad aceptando nombres alternativos y objetos Indicator anidados. */
export function featureValue(props: Record<string, unknown>, key: ChoroplethKey): number | null {
  const candidates = [key, `${key}_value`, key === "density" ? "density_hab_km2" : "", key === "age_65_plus_share" ? "share_65_plus" : ""].filter(Boolean);
  for (const c of candidates) {
    const v = props[c];
    if (typeof v === "number") return v;
    if (v && typeof v === "object" && "value" in (v as object)) {
      const iv = (v as { value: unknown }).value;
      if (typeof iv === "number") return iv;
    }
    if (typeof v === "string" && v !== "" && !Number.isNaN(Number(v))) return Number(v);
  }
  return null;
}

function quantileBreaks(values: number[], n = 5): number[] {
  const s = [...values].sort((a, b) => a - b);
  if (!s.length) return [];
  const br: number[] = [];
  for (let i = 1; i < n; i++) br.push(s[Math.min(s.length - 1, Math.floor((i * s.length) / n))]);
  return Array.from(new Set(br));
}

export interface LegendSpec {
  title: string;
  items: { label: string; color: string; pattern?: boolean }[];
  note: string;
}

interface Props {
  choropleth: ChoroplethKey;
  selected: string | null;
  highlight: Set<string> | null;
  officialLayers: Layer[];
  activeOfficial: string | null;
  onSelect: (ine: string) => void;
  onLegend: (l: LegendSpec[]) => void;
  onError: (msg: string | null) => void;
}

export function MapExplorer({ choropleth, selected, highlight, officialLayers, activeOfficial, onSelect, onLegend, onError }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MlMap | null>(null);
  const [ready, setReady] = useState(false);
  const [muni, setMuni] = useState<FeatureCollection | null>(null);
  const [officialLegends, setOfficialLegends] = useState<Record<string, { label: string; color: string }[]>>({});
  const onSelectRef = useRef(onSelect);
  useEffect(() => {
    onSelectRef.current = onSelect;
  }, [onSelect]);

  // Inicializa el mapa una sola vez.
  useEffect(() => {
    let disposed = false;
    (async () => {
      const maplibregl = (await import("maplibre-gl")).default;
      if (disposed || !ref.current) return;
      const map = new maplibregl.Map({
        container: ref.current,
        style: {
          version: 8,
          sources: {
            ign: {
              type: "raster",
              tiles: [BASEMAP_IGN],
              tileSize: 256,
              attribution: "Mapa base © Instituto Geográfico Nacional de España (CC BY 4.0)",
            },
          },
          layers: [{ id: "ign", type: "raster", source: "ign", paint: { "raster-saturation": -0.65, "raster-opacity": 0.85 } }],
        },
        center: [-3.72, 40.5],
        zoom: 7.6,
        minZoom: 6,
        maxZoom: 15,
        maxBounds: [[-5.6, 39.4], [-1.9, 41.7]],
        attributionControl: { compact: false },
      });
      map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
      map.addControl(new maplibregl.ScaleControl({ unit: "metric" }), "bottom-right");
      map.on("load", () => {
        mapRef.current = map;
        setReady(true);
      });
      const popup = new maplibregl.Popup({ closeButton: false, closeOnClick: false, offset: 8 });
      map.on("mousemove", "muni-fill", (e: MapLayerMouseEvent) => {
        const f = e.features?.[0];
        if (!f) return;
        map.getCanvas().style.cursor = "pointer";
        popup.setLngLat(e.lngLat).setText(String(f.properties?.name ?? f.properties?.ine_code ?? "")).addTo(map);
      });
      map.on("mouseleave", "muni-fill", () => {
        map.getCanvas().style.cursor = "";
        popup.remove();
      });
      map.on("click", "muni-fill", (e: MapLayerMouseEvent) => {
        const code = e.features?.[0]?.properties?.ine_code;
        if (code) onSelectRef.current(String(code));
      });
    })();
    return () => {
      disposed = true;
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, []);

  // Carga municipios.
  useEffect(() => {
    apiFetch<FeatureCollection>("/v1/layers/municipalities/geojson")
      .then((fc) => {
        setMuni(fc);
        onError(null);
      })
      .catch((e) => onError(`Capa de municipios no disponible: ${e.message}`));
  }, [onError]);

  const breaks = useMemo(() => {
    if (!muni) return [];
    const vals = muni.features.map((f) => featureValue(f.properties, choropleth)).filter((v): v is number => v !== null);
    return quantileBreaks(vals);
  }, [muni, choropleth]);

  // Pinta / repinta la coropleta de municipios.
  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map || !muni) return;
    const data = {
      ...muni,
      features: muni.features.map((f) => ({
        ...f,
        properties: {
          ...f.properties,
          __v: featureValue(f.properties, choropleth),
          __dim: highlight ? !highlight.has(String(f.properties.ine_code)) : false,
        },
      })),
    };
    const src = map.getSource("muni") as GeoJSONSource | undefined;
    if (src) src.setData(data as unknown as GeoJSON.FeatureCollection);
    else {
      map.addSource("muni", { type: "geojson", data: data as unknown as GeoJSON.FeatureCollection, promoteId: "ine_code" });
      map.addLayer({ id: "muni-fill", type: "fill", source: "muni", paint: { "fill-color": "#ccc", "fill-opacity": 0.72 } });
      map.addLayer({ id: "muni-line", type: "line", source: "muni", paint: { "line-color": "#15201A", "line-width": 0.4, "line-opacity": 0.55 } });
      map.addLayer({
        id: "muni-selected",
        type: "line",
        source: "muni",
        paint: { "line-color": "#B7791F", "line-width": 3 },
        filter: ["==", ["get", "ine_code"], "__none__"],
      });
    }
    const step: unknown[] = ["step", ["get", "__v"], RAMP[0]];
    breaks.forEach((b, i) => step.push(b, RAMP[Math.min(i + 1, RAMP.length - 1)]));
    const color = breaks.length ? step : RAMP[2];
    map.setPaintProperty("muni-fill", "fill-color", [
      "case",
      ["==", ["get", "__v"], null], "#D9DCDA",
      color,
    ] as never);
    map.setPaintProperty("muni-fill", "fill-opacity", ["case", ["get", "__dim"], 0.18, activeOfficial ? 0.25 : 0.75] as never);
  }, [ready, muni, choropleth, breaks, highlight, activeOfficial]);

  // Selección.
  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map || !map.getLayer("muni-selected")) return;
    map.setFilter("muni-selected", ["==", ["get", "ine_code"], selected ?? "__none__"]);
    if (selected && muni) {
      const f = muni.features.find((x) => String(x.properties.ine_code) === selected);
      if (f) {
        const coords: number[][] = [];
        const walk = (c: unknown) => {
          if (Array.isArray(c) && typeof c[0] === "number") coords.push(c as number[]);
          else if (Array.isArray(c)) c.forEach(walk);
        };
        walk((f.geometry as { coordinates?: unknown }).coordinates);
        if (coords.length) {
          const xs = coords.map((c) => c[0]), ys = coords.map((c) => c[1]);
          map.fitBounds([[Math.min(...xs), Math.min(...ys)], [Math.max(...xs), Math.max(...ys)]], { padding: 80, maxZoom: 11, duration: 600 });
        }
      }
    }
  }, [ready, selected, muni]);

  // Capa oficial activa (carga bajo demanda).
  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map) return;
    for (const l of officialLayers) {
      const id = `off-${l.name}`;
      if (map.getLayer(id)) map.setLayoutProperty(id, "visibility", l.name === activeOfficial ? "visible" : "none");
    }
    if (!activeOfficial) return;
    const layer = officialLayers.find((l) => l.name === activeOfficial);
    if (!layer) return;
    const id = `off-${layer.name}`;
    if (map.getLayer(id)) return;
    const draw = (fc: FeatureCollection) => {
      if (!mapRef.current || map.getLayer(id)) return;
      const prop = layer.class_property || "class_label";
      // Preferencia: colores sugeridos por la propia fuente (estilo oficial); si no hay, rampa ordinal.
      const official = (layer.classes ?? []).filter((c) => c.color_suggestion && !c.transparent_in_official_style && c.present_in_raster !== false);
      const legend = official.length
        ? official.map((c) => ({ label: c.class_label, color: c.color_suggestion as string }))
        : layer.legend?.length
          ? layer.legend
          : classLegend(fc.features.map((f) => String(f.properties[prop] ?? "")));
      const match: unknown[] = ["match", ["to-string", ["get", prop]]];
      legend.forEach((it) => match.push(it.label, it.color));
      match.push(NON_ORDINAL);
      map.addSource(id, { type: "geojson", data: fc as unknown as GeoJSON.FeatureCollection });
      map.addLayer(
        { id, type: "fill", source: id, paint: { "fill-color": legend.length ? (match as never) : "#A9401F", "fill-opacity": 0.65 } },
        "muni-line",
      );
      setOfficialLegends((d) => ({ ...d, [layer.name]: legend }));
    };
    apiFetch<FeatureCollection>(`/v1/layers/${encodeURIComponent(layer.name)}/geojson`)
      .then(draw)
      .catch((e) => onError(`Capa «${layer.title ?? layer.label ?? layer.name}» no disponible: ${e.message}`));
  }, [ready, activeOfficial, officialLayers, onError]);

  // Leyendas.
  useEffect(() => {
    const opt = CHOROPLETH_OPTIONS[choropleth];
    const fmt = (v: number) => (opt.isShare ? fmtShare(v) : fmtNumber(v));
    const items = RAMP.slice(0, breaks.length + 1).map((color, i) => {
      const lo = i === 0 ? null : breaks[i - 1];
      const hi = i < breaks.length ? breaks[i] : null;
      const label = lo === null ? `< ${fmt(hi as number)}` : hi === null ? `≥ ${fmt(lo)}` : `${fmt(lo)} – ${fmt(hi)}`;
      return { label, color };
    });
    items.push({ label: "Sin dato", color: "#D9DCDA" });
    const specs: LegendSpec[] = [
      {
        title: `${opt.label} (${opt.unit}) · ${opt.source}`,
        items,
        note: "Escala municipal. Cortes por quintiles calculados en el navegador (visualización derivada).",
      },
    ];
    const active = officialLayers.find((l) => l.name === activeOfficial);
    if (active) {
      specs.unshift({
        title: `${active.title ?? active.label ?? active.name}${active.source_id ? ` · ${active.source_id}` : ""}`,
        items: (officialLegends[active.name] ?? active.legend ?? []).map((x) => ({ label: x.label, color: x.color })),
        note: "Clases literales de la capa oficial, sin recalcular. Generalización web a 200 m: solo visualización, no consulta por parcela.",
      });
    }
    onLegend(specs);
  }, [choropleth, breaks, activeOfficial, officialLayers, onLegend, officialLegends]);

  // Estilo en línea: maplibre-gl.css fija `.maplibregl-map { position: relative }` y anularía la clase.
  return (
    <div
      ref={ref}
      style={{ position: "absolute", inset: 0 }}
      role="region"
      aria-label="Mapa de municipios de la Comunidad de Madrid"
    />
  );
}
