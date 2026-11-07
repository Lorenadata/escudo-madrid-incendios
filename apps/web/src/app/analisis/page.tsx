"use client";

import Link from "next/link";
import { useState } from "react";
import { Empty, ErrorState, Loading } from "@/components/States";
import { StatusBadge } from "@/components/StatusBadge";
import { fmtNumber, fmtShare } from "@/lib/format";
import { useApi } from "@/lib/useApi";

type Layer = "risk" | "hazard" | "vulnerability";

interface MatrixRow {
  ine_code: string;
  name: string;
  high_share: number | null;
  density_hab_km2: number | null;
  density_year: number | null;
  age_65_plus_share: number | null;
  population_total: number | null;
  population_year: number | null;
}

interface MatrixResponse {
  layer: Layer;
  layer_source_id: string;
  status: string;
  sources: string[];
  definition: string;
  caveat: string;
  count: number;
  rows: MatrixRow[];
}

const LAYERS: { value: Layer; label: string; high: string }[] = [
  { value: "risk", label: "Riesgo (GEO-01)", high: "Riesgo alto + muy alto" },
  { value: "hazard", label: "Peligrosidad (GEO-02)", high: "Peligrosidad alta + muy alta" },
  { value: "vulnerability", label: "Vulnerabilidad (GEO-03)", high: "Vulnerabilidad alta + muy alta" },
];

const SORTS = [
  { value: "high_share", label: "Superficie en clases altas" },
  { value: "density", label: "Densidad" },
  { value: "age65", label: "% de 65 años o más" },
  { value: "population", label: "Población" },
];

function numOrEmpty(v: string): string {
  return v.trim() === "" ? "" : v;
}

export default function AnalysisPage() {
  const [layer, setLayer] = useState<Layer>("risk");
  const [minHigh, setMinHigh] = useState("50");
  const [maxDensity, setMaxDensity] = useState("");
  const [minAge, setMinAge] = useState("");
  const [sort, setSort] = useState("high_share");

  const qs = new URLSearchParams({ layer, sort });
  if (numOrEmpty(minHigh)) qs.set("min_high_share", String(Math.min(100, Math.max(0, Number(minHigh))) / 100));
  if (numOrEmpty(maxDensity)) qs.set("max_density", String(Math.max(0, Number(maxDensity))));
  if (numOrEmpty(minAge)) qs.set("min_age65_share", String(Math.min(100, Math.max(0, Number(minAge))) / 100));
  const path = `/v1/analysis/municipal-matrix?${qs.toString()}`;
  const m = useApi<MatrixResponse>(path);
  const meta = LAYERS.find((l) => l.value === layer)!;

  return (
    <div className="mx-auto w-full max-w-6xl space-y-5 px-4 py-6">
      <header>
        <h1 className="font-cond text-2xl font-semibold text-ink">Análisis municipal</h1>
        <p className="max-w-prose text-sm text-ink-600">
          Cruza datos del Portal de Datos Abiertos de la Comunidad de Madrid (densidad CAM-02, población de 65 años o más
          CAM-01) con el reparto de la cartografía oficial de incendios. Es un filtro comparativo a escala municipal:
          no crea un índice propio ni decide prioridades.
        </p>
      </header>

      <form className="grid gap-4 rounded border border-line bg-white p-4 sm:grid-cols-2 lg:grid-cols-5" onSubmit={(e) => e.preventDefault()}>
        <div>
          <label htmlFor="layer" className="label">Capa oficial</label>
          <select id="layer" className="field" value={layer} onChange={(e) => setLayer(e.target.value as Layer)}>
            {LAYERS.map((l) => <option key={l.value} value={l.value}>{l.label}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="minHigh" className="label">Mín. % en clases altas</label>
          <input id="minHigh" className="field" type="number" min={0} max={100} inputMode="numeric" value={minHigh} onChange={(e) => setMinHigh(e.target.value)} />
        </div>
        <div>
          <label htmlFor="maxDensity" className="label">Máx. densidad (hab/km²)</label>
          <input id="maxDensity" className="field" type="number" min={0} inputMode="numeric" value={maxDensity} onChange={(e) => setMaxDensity(e.target.value)} />
        </div>
        <div>
          <label htmlFor="minAge" className="label">Mín. % de 65 años o más</label>
          <input id="minAge" className="field" type="number" min={0} max={100} inputMode="numeric" value={minAge} onChange={(e) => setMinAge(e.target.value)} />
        </div>
        <div>
          <label htmlFor="sort" className="label">Ordenar por</label>
          <select id="sort" className="field" value={sort} onChange={(e) => setSort(e.target.value)}>
            {SORTS.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
          </select>
        </div>
      </form>

      {m.loading && !m.data && <Loading label="Calculando matriz" />}
      {!!m.error && <ErrorState error={m.error} onRetry={m.reload} />}
      {m.data && m.data.status === "unavailable" && (
        <Empty title="Capa oficial no disponible">La capa {meta.label} no está cargada; no se muestran valores sustitutos.</Empty>
      )}
      {m.data && m.data.status !== "unavailable" && (
        <section aria-label="Resultados" className="space-y-3">
          <div className="flex flex-wrap items-center gap-2 text-sm text-ink-600">
            <span className="font-semibold text-ink" aria-live="polite">{m.data.count} municipios</span>
            <span>· fuentes {m.data.sources.join(", ")}</span>
          </div>
          {m.data.count === 0 ? (
            <Empty title="Ningún municipio cumple los filtros">Relaja algún umbral.</Empty>
          ) : (
            <div className="overflow-x-auto rounded border border-line bg-white">
              <table className="w-full text-sm">
                <caption className="sr-only">Matriz municipal: datos CAM y reparto de la capa oficial</caption>
                <thead className="bg-granite text-left text-xs uppercase tracking-wide text-ink-600">
                  <tr>
                    <th scope="col" className="px-3 py-2">Municipio</th>
                    <th scope="col" className="px-3 py-2 text-right">{meta.high} <StatusBadge status="derived" /></th>
                    <th scope="col" className="px-3 py-2 text-right">Densidad <StatusBadge status="official" /></th>
                    <th scope="col" className="px-3 py-2 text-right">65 años o más <StatusBadge status="derived" /></th>
                    <th scope="col" className="px-3 py-2 text-right">Población <StatusBadge status="official" /></th>
                  </tr>
                </thead>
                <tbody>
                  {m.data.rows.map((r) => (
                    <tr key={r.ine_code} className="border-t border-line">
                      <th scope="row" className="px-3 py-2 text-left font-medium">
                        <Link className="underline-offset-2 hover:underline" href={`/#${r.ine_code}`}>{r.name}</Link>
                        <span className="ml-1 text-xs text-ink-500">INE {r.ine_code}</span>
                      </th>
                      <td className="px-3 py-2 text-right tabular-nums">{fmtShare(r.high_share)}</td>
                      <td className="px-3 py-2 text-right tabular-nums">{fmtNumber(r.density_hab_km2)} <span className="text-xs text-ink-500">({r.density_year ?? "s/f"})</span></td>
                      <td className="px-3 py-2 text-right tabular-nums">{fmtShare(r.age_65_plus_share)}</td>
                      <td className="px-3 py-2 text-right tabular-nums">{fmtNumber(r.population_total)} <span className="text-xs text-ink-500">({r.population_year ?? "s/f"})</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <details className="rounded border border-line bg-white p-3 text-sm">
            <summary className="cursor-pointer font-medium">Ver método y fuentes</summary>
            <p className="mt-2 text-ink-600">{m.data.definition}</p>
            <p className="mt-1 text-ink-600">{m.data.caveat}</p>
          </details>
        </section>
      )}
    </div>
  );
}
