"use client";

import { fmtNumber } from "@/lib/format";
import { useApi } from "@/lib/useApi";
import { ErrorState, Loading } from "./States";
import { StatusBadge } from "./StatusBadge";

interface RegionalSeries {
  source_id: string;
  scope: string;
  series: Array<{ concept: string; year: number; value: number | null; unit: string }>;
}

/** Serie REGIONAL de repoblaciones forestales (CAM-06, M14). Sin desagregación municipal. */
export function ReforestationPanel() {
  const s = useApi<RegionalSeries>("/v1/regional-series/CAM-06");
  if (s.loading) return <Loading label="Cargando repoblaciones" />;
  if (s.error) return <ErrorState error={s.error} onRetry={s.reload} />;
  if (!s.data) return null;

  const groups = [...new Set(s.data.series.map((r) => r.concept))].sort();
  const byYear = new Map<number, Record<string, number | null>>();
  for (const r of s.data.series) {
    const row = byYear.get(r.year) ?? {};
    row[r.concept] = r.value;
    byYear.set(r.year, row);
  }
  const rows = [...byYear.entries()]
    .sort(([a], [b]) => a - b)
    .map(([year, g]) => {
      const vals = groups.map((k) => g[k]).filter((v): v is number => typeof v === "number");
      return { year, g, total: vals.length ? vals.reduce((a, b) => a + b, 0) : null };
    });
  if (!rows.length) return <p className="text-sm text-ink-500">Serie sin valores.</p>;

  const maxHa = Math.max(1, ...rows.map((r) => r.total ?? 0));
  const W = 640, H = 160, L = 44, B = 22, T = 8;
  const bw = (W - L - 4) / rows.length;
  return (
    <section aria-labelledby="refo-h" className="panel max-w-4xl">
      <div className="flex flex-wrap items-center gap-2">
        <h2 id="refo-h" className="font-cond text-lg font-semibold">
          Superficie repoblada, {rows[0].year}–{rows[rows.length - 1].year}
        </h2>
        <StatusBadge status="official" />
      </div>
      <p className="text-sm text-ink-600">
        {s.data.scope} · {s.data.source_id}. Suma por año de los grupos publicados ({groups.join(", ")}). Serie regional:
        no describe ningún municipio ni urbanización.
      </p>
      <svg viewBox={`0 0 ${W} ${H}`} className="mt-2 w-full" role="img" aria-label="Superficie repoblada por año, en hectáreas">
        {[0, 0.5, 1].map((f) => (
          <g key={f}>
            <line x1={L} x2={W} y1={T + (1 - f) * (H - T - B)} y2={T + (1 - f) * (H - T - B)} stroke="#D5DBD8" />
            <text x={L - 4} y={T + (1 - f) * (H - T - B) + 4} textAnchor="end" fontSize="10" fill="#56615B">{fmtNumber(f * maxHa)}</text>
          </g>
        ))}
        {rows.map((r, i) => {
          const hgt = ((r.total ?? 0) / maxHa) * (H - T - B);
          return (
            <g key={r.year}>
              {/* objetivo de hover más alto que la barra */}
              <rect x={L + 2 + i * bw} y={T} width={Math.max(1, bw - 1.5)} height={H - T - B} fill="transparent">
                <title>{`${r.year}: ${fmtNumber(r.total)} ha · ${groups.map((k) => `${k} ${fmtNumber(r.g[k] ?? null)}`).join(" · ")}`}</title>
              </rect>
              <rect x={L + 2 + i * bw} y={H - B - hgt} width={Math.max(1, bw - 2)} height={hgt} fill="#2F5D46" pointerEvents="none" />
              {(i === 0 || i === rows.length - 1 || r.year % 5 === 0) && (
                <text x={L + 2 + i * bw + bw / 2} y={H - 6} textAnchor="middle" fontSize="10" fill="#56615B">{r.year}</text>
              )}
            </g>
          );
        })}
      </svg>
      <details className="mt-2 text-sm">
        <summary className="cursor-pointer text-slate">Ver tabla de datos</summary>
        <div className="mt-2 max-h-64 overflow-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left text-ink-500">
                <th className="py-1 font-medium">Año</th>
                {groups.map((k) => <th key={k} className="py-1 text-right font-medium">{k} (ha)</th>)}
                <th className="py-1 text-right font-medium">Total (ha)</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.year} className="border-t border-line">
                  <td className="py-0.5">{r.year}</td>
                  {groups.map((k) => <td key={k} className="py-0.5 text-right tabular-nums">{fmtNumber(r.g[k] ?? null)}</td>)}
                  <td className="py-0.5 text-right tabular-nums">{fmtNumber(r.total)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </section>
  );
}
