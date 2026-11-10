"use client";

import Link from "next/link";
import { ErrorState, Loading, Empty } from "@/components/States";
import { StatusBadge, SyntheticBadge } from "@/components/StatusBadge";
import { fmtNumber, fmtShare } from "@/lib/format";
import { useApi } from "@/lib/useApi";

interface PublishedRow {
  ine_code: string;
  name: string | null;
  zar_declared: boolean;
  areas_band: string;
  synthetic: boolean;
  actions_total_approx: number;
  actions_done_share: number | null;
  actions_documented_share: number | null;
  actions_overdue_share: number | null;
  areas_inspected_last_12m_share: number | null;
}

interface Progress {
  notice: string;
  thresholds: { min_areas: number; min_organizations: number; max_org_share: number; share_bin: number; count_bin: number };
  published: PublishedRow[];
  withheld: { ine_code: string; name: string | null; reason: string }[];
  method: string;
}

/** M18 · Portal público: avance agregado de la gestión preventiva por municipio, sin datos privados. */
export default function AvancePage() {
  const d = useApi<Progress>("/v1/public/progress");
  return (
    <div className="mx-auto w-full max-w-6xl space-y-5 px-4 py-6">
      <header className="max-w-prose">
        <h1 className="font-cond text-2xl font-semibold text-ink">Avance público de la prevención</h1>
        <p className="text-sm text-ink-600">
          Cuánto avanza la gestión preventiva en cada municipio, sumando los ámbitos (urbanizaciones, zonas) cuyas
          organizaciones han autorizado compartir su información. Son indicadores de gestión, no de riesgo.
        </p>
      </header>
      {d.loading && <Loading label="Calculando agregados" />}
      {!!d.error && <ErrorState error={d.error} onRetry={d.reload} />}
      {d.data && (
        <>
          <p role="note" className="rounded border-l-4 border-ochre bg-ochre-50 p-2 text-xs text-ink-800">{d.data.notice}</p>
          {d.data.published.length === 0 ? (
            <Empty title="Todavía no hay municipios publicables">
              Ningún municipio alcanza el umbral de {d.data.thresholds.min_areas} ámbitos autorizados de {d.data.thresholds.min_organizations} organizaciones.
            </Empty>
          ) : (
            <div className="overflow-x-auto rounded border border-line bg-white">
              <table className="w-full min-w-[52rem] text-sm">
                <caption className="sr-only">Avance agregado por municipio</caption>
                <thead className="bg-granite text-left text-xs uppercase tracking-wide text-ink-600">
                  <tr>
                    <th scope="col" className="px-3 py-2">Municipio</th>
                    <th scope="col" className="px-3 py-2 text-center">ZAR 2026 <StatusBadge status="official" /></th>
                    <th scope="col" className="px-3 py-2 text-right">Ámbitos</th>
                    <th scope="col" className="px-3 py-2 text-right">Actuaciones planificadas (aprox.)</th>
                    <th scope="col" className="px-3 py-2 text-right">Hechas (declarado)</th>
                    <th scope="col" className="px-3 py-2 text-right">Con evidencia</th>
                    <th scope="col" className="px-3 py-2 text-right">Vencidas sin hacer</th>
                    <th scope="col" className="px-3 py-2 text-right">Ámbitos inspeccionados (12 meses)</th>
                  </tr>
                </thead>
                <tbody>
                  {d.data.published.map((r) => (
                    <tr key={r.ine_code} className="border-t border-line">
                      <th scope="row" className="px-3 py-2 text-left font-medium">
                        <Link className="underline-offset-2 hover:underline" href={`/#${r.ine_code}`}>{r.name ?? r.ine_code}</Link>
                        <span className="ml-1 text-xs text-ink-500">INE {r.ine_code}</span>
                        {r.synthetic && <span className="ml-2"><SyntheticBadge /></span>}
                      </th>
                      <td className="px-3 py-2 text-center">{r.zar_declared ? "Sí" : "No"}</td>
                      <td className="px-3 py-2 text-right tabular-nums">{r.areas_band}</td>
                      <td className="px-3 py-2 text-right tabular-nums">≈ {fmtNumber(r.actions_total_approx)}</td>
                      <td className="px-3 py-2 text-right tabular-nums">{fmtShare(r.actions_done_share)}</td>
                      <td className="px-3 py-2 text-right tabular-nums">{fmtShare(r.actions_documented_share)}</td>
                      <td className="px-3 py-2 text-right tabular-nums">{fmtShare(r.actions_overdue_share)}</td>
                      <td className="px-3 py-2 text-right tabular-nums">{fmtShare(r.areas_inspected_last_12m_share)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {d.data.withheld.length > 0 && (
            <section aria-labelledby="withheld-h" className="text-sm">
              <h2 id="withheld-h" className="font-cond text-base font-semibold">No se publican (umbral de privacidad)</h2>
              <p className="text-xs text-ink-600">
                Municipios con algún ámbito autorizado que no alcanzan {d.data.thresholds.min_areas} ámbitos de{" "}
                {d.data.thresholds.min_organizations} organizaciones, o en los que una organización aporta más de la mitad
                de las actuaciones: no se muestra ninguna cifra.
              </p>
              <p className="mt-1 text-ink-700">{d.data.withheld.map((w) => w.name ?? w.ine_code).join(" · ")}</p>
            </section>
          )}
          <details className="rounded border border-line bg-white p-3 text-sm">
            <summary className="cursor-pointer font-medium">Ver método y fuentes</summary>
            <p className="mt-2 text-ink-600">{d.data.method}</p>
            <p className="mt-1 text-ink-600">Declaración ZAR: Plan Anual 2026, Anexo II (DOC-01). Resto: datos aportados por las organizaciones (agregados).</p>
          </details>
        </>
      )}
    </div>
  );
}
