"use client";

import { IndicatorValue } from "@/components/IndicatorValue";
import { ErrorState, Loading, Empty } from "@/components/States";
import type { AuditEvent, ImpactResponse } from "@/lib/api-types";
import { fmtDate } from "@/lib/format";
import { useApi } from "@/lib/useApi";

export function ImpactPanel() {
  const impact = useApi<ImpactResponse>("/v1/impact");
  return (
    <section aria-labelledby="impact-h" className="panel">
      <h2 id="impact-h" className="font-cond text-lg font-semibold">Indicadores de gestión</h2>
      {impact.loading && <Loading label="Calculando" />}
      {!!impact.error && <ErrorState error={impact.error} onRetry={impact.reload} />}
      {impact.data && (
        <>
          <div className="divide-y divide-line/70">
            {impact.data.kpis.map((k) => <IndicatorValue key={k.indicator_id} indicator={k} compact />)}
          </div>
          {impact.data.notice && <p className="mt-2 text-xs text-ink-500">{impact.data.notice}</p>}
          <button type="button" onClick={impact.reload} className="mt-2 text-xs text-slate underline">Actualizar</button>
        </>
      )}
    </section>
  );
}

export function AuditPanel() {
  const audit = useApi<AuditEvent[]>("/v1/audit");
  return (
    <details className="panel">
      <summary className="cursor-pointer font-cond text-lg font-semibold">Registro de auditoría</summary>
      {audit.loading && <Loading label="Cargando auditoría" />}
      {!!audit.error && <ErrorState error={audit.error} onRetry={audit.reload} />}
      {audit.data && audit.data.length === 0 && <Empty title="Sin eventos registrados" />}
      {audit.data && audit.data.length > 0 && (
        <div className="mt-2 max-h-72 overflow-auto">
          <table className="w-full text-xs">
            <caption className="sr-only">Eventos de auditoría de la organización</caption>
            <thead>
              <tr className="text-left text-ink-500">
                <th className="py-1 font-medium">Fecha</th>
                <th className="py-1 font-medium">Acción</th>
                <th className="py-1 font-medium">Entidad</th>
                <th className="py-1 font-medium">Detalle</th>
              </tr>
            </thead>
            <tbody>
              {audit.data.map((e, i) => (
                <tr key={`${e.at}-${i}`} className="border-t border-line align-top">
                  <td className="py-1 pr-2 whitespace-nowrap">{fmtDate(e.at, true)}</td>
                  <td className="py-1 pr-2">{e.action}</td>
                  <td className="py-1 pr-2">{e.entity}</td>
                  <td className="py-1 font-mono text-[11px] text-ink-600">{e.detail ? JSON.stringify(e.detail) : ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </details>
  );
}
