"use client";

import { useState } from "react";
import { IndicatorValue } from "@/components/IndicatorValue";
import { OfficialFirePanel } from "@/components/ProfilePanels";
import { Empty, ErrorState, Loading } from "@/components/States";
import type { CompareResponse, Indicator, MunicipalityProfile, MunicipalitySummary } from "@/lib/api-types";
import { useApi } from "@/lib/useApi";

const ROWS: { key: keyof MunicipalityProfile; label: string }[] = [
  { key: "population", label: "Población" },
  { key: "density", label: "Densidad" },
  { key: "age_65_plus_share", label: "65 años o más" },
  { key: "altitude_m", label: "Altitud" },
  { key: "area_km2", label: "Superficie" },
  { key: "forest_share", label: "Superficie forestal" },
];

function Picker({ id, label, value, onChange, options }: { id: string; label: string; value: string; onChange: (v: string) => void; options: MunicipalitySummary[] }) {
  return (
    <div>
      <label htmlFor={id} className="label">{label}</label>
      <select id={id} className="field" value={value} onChange={(e) => onChange(e.target.value)}>
        <option value="">Elige un municipio</option>
        {options.map((m) => (
          <option key={m.ine_code} value={m.ine_code}>{m.name}</option>
        ))}
      </select>
    </div>
  );
}

export default function ComparePage() {
  const [a, setA] = useState("");
  const [b, setB] = useState("");
  const list = useApi<MunicipalitySummary[]>("/v1/municipalities?sort=name");
  const cmp = useApi<CompareResponse>(a && b && a !== b ? `/v1/compare?a=${a}&b=${b}` : null);

  return (
    <div className="mx-auto w-full max-w-6xl space-y-5 px-4 py-6">
      <header>
        <h1 className="font-cond text-2xl font-semibold text-ink">Comparar municipios</h1>
        <p className="max-w-prose text-sm text-ink-600">
          Dos municipios lado a lado con los mismos indicadores, la misma escala municipal y la misma fuente.
        </p>
      </header>
      {list.loading && <Loading label="Cargando municipios" />}
      {!!list.error && <ErrorState error={list.error} onRetry={list.reload} />}
      {list.data && (
        <div className="grid gap-4 sm:grid-cols-2">
          <Picker id="ma" label="Municipio A" value={a} onChange={setA} options={list.data} />
          <Picker id="mb" label="Municipio B" value={b} onChange={setB} options={list.data} />
        </div>
      )}
      {a && b && a === b && <Empty title="Elige dos municipios distintos" />}
      {(!a || !b) && <Empty title="Elige dos municipios para compararlos">La comparación usa el último año disponible en cada fuente.</Empty>}
      {cmp.loading && <Loading label="Comparando" />}
      {!!cmp.error && <ErrorState error={cmp.error} onRetry={cmp.reload} />}
      {cmp.data && (
        <>
          {!cmp.data.same_reference_year && (
            <p role="note" className="rounded border-l-4 border-ochre bg-ochre-50 p-2 text-sm text-ink-800">
              Los indicadores no comparten el mismo año de referencia. Revisa la fecha de cada valor antes de comparar.
            </p>
          )}
          <div className="overflow-x-auto rounded border border-line bg-white">
            <table className="w-full min-w-[40rem]">
              <caption className="sr-only">Comparación de indicadores municipales</caption>
              <thead>
                <tr className="border-b border-line text-left">
                  <th className="w-40 p-3 text-xs font-medium text-ink-500">Indicador</th>
                  <th className="p-3 font-cond text-lg font-semibold">{cmp.data.a.name}</th>
                  <th className="p-3 font-cond text-lg font-semibold">{cmp.data.b.name}</th>
                </tr>
              </thead>
              <tbody>
                {ROWS.map((r) => (
                  <tr key={String(r.key)} className="border-b border-line align-top">
                    <th scope="row" className="p-3 text-left text-sm font-normal text-ink-600">{r.label}</th>
                    <td className="px-3"><IndicatorValue indicator={cmp.data!.a[r.key] as Indicator} /></td>
                    <td className="px-3"><IndicatorValue indicator={cmp.data!.b[r.key] as Indicator} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="panel"><h2 className="font-cond text-lg font-semibold">{cmp.data.a.name}</h2><OfficialFirePanel profile={cmp.data.a} /></div>
            <div className="panel"><h2 className="font-cond text-lg font-semibold">{cmp.data.b.name}</h2><OfficialFirePanel profile={cmp.data.b} /></div>
          </div>
          <p className="text-xs text-ink-500">{cmp.data.a.scale_notice}</p>
        </>
      )}
    </div>
  );
}
