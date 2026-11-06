"use client";

import type { MunicipalSeries } from "@/lib/api-types";
import { fmtNumber, fmtShare } from "@/lib/format";
import { useApi } from "@/lib/useApi";
import { StatusBadge } from "./StatusBadge";

const SERIES_META: Record<string, { label: string; source: string; share?: boolean; unit?: string }> = {
  municipality_population_total: { label: "Población censada", source: "CAM-01", unit: "personas" },
  municipality_age_65_plus_share: { label: "Población de 65 años o más", source: "CAM-01", share: true },
  municipality_density: { label: "Densidad de población", source: "CAM-02", unit: "hab/km²" },
};

function Spark({ points, share }: { points: { year: number; value: number }[]; share?: boolean }) {
  const W = 300, H = 56, P = 4;
  const xs = points.map((p) => p.year), ys = points.map((p) => p.value);
  const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
  const x = (v: number) => P + ((v - x0) / Math.max(1, x1 - x0)) * (W - 2 * P);
  const y = (v: number) => H - P - ((v - y0) / Math.max(1e-9, y1 - y0)) * (H - 2 * P);
  const d = points.map((p, i) => `${i ? "L" : "M"}${x(p.year).toFixed(1)},${y(p.value).toFixed(1)}`).join(" ");
  const fmt = (v: number) => (share ? fmtShare(v) : fmtNumber(v));
  const first = points[0], last = points[points.length - 1];
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="h-14 w-full" role="img" aria-label={`De ${fmt(first.value)} en ${first.year} a ${fmt(last.value)} en ${last.year}`}>
      <path d={d} fill="none" stroke="#1E3B2F" strokeWidth="1.6" />
      <circle cx={x(last.year)} cy={y(last.value)} r="2.5" fill="#1E3B2F" />
    </svg>
  );
}

/** Evolución anual de indicadores municipales del Portal CAM. Cambia al reingerir CAM-01/CAM-02. */
export function SeriesPanel({ ine }: { ine: string }) {
  const s = useApi<MunicipalSeries>(`/v1/municipalities/${ine}/series`);
  if (s.loading) return <p className="text-xs text-ink-500">Cargando series…</p>;
  if (s.error || !s.data) return <p className="text-xs text-ink-500">Series anuales no disponibles.</p>;
  const keys = Object.keys(s.data.series).filter((k) => SERIES_META[k] && s.data!.series[k].some((p) => p.value !== null));
  if (!keys.length) return null;
  return (
    <section aria-labelledby={`series-${ine}`} className="border-t border-line pt-4">
      <div className="flex items-center justify-between">
        <h3 id={`series-${ine}`} className="font-cond text-base font-semibold text-ink">Evolución anual</h3>
        <StatusBadge status="official" />
      </div>
      <div className="mt-1 space-y-3">
        {keys.map((k) => {
          const meta = SERIES_META[k];
          const pts = s.data!.series[k].filter((p): p is { year: number; value: number; source_id: string } => p.value !== null).sort((a, b) => a.year - b.year);
          const first = pts[0], last = pts[pts.length - 1];
          const fmt = (v: number) => (meta.share ? fmtShare(v) : `${fmtNumber(v)}${meta.unit ? ` ${meta.unit}` : ""}`);
          return (
            <figure key={k}>
              <figcaption className="flex items-baseline justify-between gap-2 text-xs text-ink-600">
                <span>{meta.label} · {meta.source}</span>
                <span className="tabular-nums">{first.year}: {fmt(first.value)} → {last.year}: {fmt(last.value)}</span>
              </figcaption>
              {pts.length > 1 ? <Spark points={pts} share={meta.share} /> : null}
            </figure>
          );
        })}
      </div>
      <p className="mt-1 text-xs text-ink-500">Serie municipal del Portal de Datos Abiertos; no describe ámbitos inferiores al municipio.</p>
    </section>
  );
}
