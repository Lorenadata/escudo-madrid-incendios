"use client";

import type { FireHistory } from "@/lib/api-types";
import { fmtNumber } from "@/lib/format";
import { useApi } from "@/lib/useApi";
import { ErrorState, Loading } from "./States";
import { StatusBadge } from "./StatusBadge";

/** Serie histórica REGIONAL de incendios (CAM-05). Sin desagregación municipal. */
export function FireHistoryPanel() {
  const h = useApi<FireHistory>("/v1/fire-history");
  if (h.loading) return <Loading label="Cargando serie histórica" />;
  if (h.error) return <ErrorState error={h.error} onRetry={h.reload} />;
  if (!h.data) return null;
  const rows = h.data.series
    .map((r) => ({ year: r.year, n: (r.total_siniestros as number | null) ?? null, ha: (r.superficie_total_ha as number | null) ?? null }))
    .filter((r) => r.n !== null || r.ha !== null)
    .sort((a, b) => a.year - b.year);
  if (!rows.length) return <p className="text-sm text-ink-500">Serie sin valores.</p>;
  const maxHa = Math.max(1, ...rows.map((r) => r.ha ?? 0));
  const W = 640, H = 160, L = 44, B = 22, T = 8;
  const bw = (W - L - 4) / rows.length;
  return (
    <section aria-labelledby="fh-h" className="panel max-w-4xl">
      <div className="flex flex-wrap items-center gap-2">
        <h2 id="fh-h" className="font-cond text-lg font-semibold">Superficie afectada por incendios forestales, {rows[0].year}–{rows[rows.length - 1].year}</h2>
        <StatusBadge status="official" />
      </div>
      <p className="text-sm text-ink-600">{h.data.scope} · {h.data.source_id}. {h.data.caveat}</p>
      <svg viewBox={`0 0 ${W} ${H}`} className="mt-2 w-full" role="img" aria-label="Superficie total afectada por año, en hectáreas">
        {[0, 0.5, 1].map((f) => (
          <g key={f}>
            <line x1={L} x2={W} y1={T + (1 - f) * (H - T - B)} y2={T + (1 - f) * (H - T - B)} stroke="#D5DBD8" />
            <text x={L - 4} y={T + (1 - f) * (H - T - B) + 4} textAnchor="end" fontSize="10" fill="#56615B">{fmtNumber(f * maxHa)}</text>
          </g>
        ))}
        {rows.map((r, i) => {
          const hgt = ((r.ha ?? 0) / maxHa) * (H - T - B);
          return (
            <g key={r.year}>
              <rect x={L + 2 + i * bw} y={H - B - hgt} width={Math.max(1, bw - 1.5)} height={hgt} fill="#9A3B1F">
                <title>{`${r.year}: ${fmtNumber(r.ha)} ha, ${fmtNumber(r.n)} siniestros`}</title>
              </rect>
              {(i === 0 || i === rows.length - 1 || r.year % 10 === 0) && (
                <text x={i === rows.length - 1 ? L + 2 + (i + 1) * bw : i === 0 ? L + 2 : L + 2 + i * bw + bw / 2} y={H - 6} textAnchor={i === rows.length - 1 ? "end" : i === 0 ? "start" : "middle"} fontSize="10" fill="#56615B">{r.year}</text>
              )}
            </g>
          );
        })}
      </svg>
      <details className="mt-2 text-sm">
        <summary className="cursor-pointer text-slate">Ver tabla de datos</summary>
        <div className="mt-2 max-h-64 overflow-auto">
          <table className="w-full text-xs">
            <thead><tr className="text-left text-ink-500"><th className="py-1 font-medium">Año</th><th className="py-1 text-right font-medium">Siniestros</th><th className="py-1 text-right font-medium">Superficie total (ha)</th></tr></thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.year} className="border-t border-line"><td className="py-0.5">{r.year}</td><td className="py-0.5 text-right tabular-nums">{fmtNumber(r.n)}</td><td className="py-0.5 text-right tabular-nums">{fmtNumber(r.ha)}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </section>
  );
}
