"use client";

import { FireHistoryPanel } from "@/components/FireHistoryPanel";
import { ErrorState, Loading, Empty } from "@/components/States";
import { API_URL } from "@/lib/api";
import { StatusLegend } from "@/components/StatusBadge";
import type { Health, Source } from "@/lib/api-types";
import { fmtDate } from "@/lib/format";
import { useApi } from "@/lib/useApi";

const SOURCE_STATUS: Record<string, { label: string; cls: string }> = {
  ok: { label: "Ingerida", cls: "text-pine" },
  failed: { label: "Fallo del conector", cls: "text-rust" },
  not_ingested: { label: "Sin ingerir", cls: "text-ash-800" },
};

const PORTAL_LABEL: Record<string, string> = {
  CAM: "Portal de Datos Abiertos de la Comunidad de Madrid",
  IDEM: "IDEM / datos.gob.es",
  AEMET: "AEMET OpenData",
};

export default function SourcesPage() {
  const sources = useApi<Source[]>("/v1/sources");
  const health = useApi<Health>("/health");

  return (
    <div className="mx-auto w-full max-w-7xl space-y-6 px-4 py-6">
      <header className="max-w-prose">
        <h1 className="font-cond text-2xl font-semibold text-ink">Fuentes y procedencia</h1>
        <p className="text-sm text-ink-600">
          Cada dato que muestra ESCUDO MADRID procede de una de estas fuentes. Para cada descarga se guarda la URL, la fecha de
          extracción, la licencia y la huella SHA-256 del fichero, de modo que cualquiera pueda reproducirla.
        </p>
      </header>

      <div className="flex flex-wrap items-center gap-3">
        <a className="btn-primary" href={`${API_URL}/v1/exports/municipalities.csv`} download>
          Descargar indicadores municipales (CSV)
        </a>
        <a className="btn-secondary" href={`${API_URL}/docs`} target="_blank" rel="noopener noreferrer">
          Documentación de la API (OpenAPI)
        </a>
      </div>

      {health.data && (
        <p className="text-sm text-ink-700" aria-live="polite">
          Estado de la API: <strong>{health.data.status}</strong> · base de datos {health.data.db} · {health.data.sources_ok} de{" "}
          {health.data.sources_total} fuentes ingeridas · versión {health.data.version}
        </p>
      )}
      {!!health.error && <ErrorState error={health.error} onRetry={health.reload} />}

      {sources.loading && <Loading label="Cargando fuentes" />}
      {!!sources.error && <ErrorState error={sources.error} onRetry={sources.reload} />}
      {sources.data && sources.data.length === 0 && <Empty title="No hay fuentes registradas" />}
      {sources.data && sources.data.length > 0 && (
        <div className="overflow-x-auto rounded border border-line bg-white">
          <table className="w-full min-w-[64rem] text-sm">
            <caption className="sr-only">Registro de fuentes de datos</caption>
            <thead>
              <tr className="border-b border-ink/20 text-left text-xs text-ink-500">
                <th className="p-2.5 font-medium">Código</th>
                <th className="p-2.5 font-medium">Conjunto de datos</th>
                <th className="p-2.5 font-medium">Escala</th>
                <th className="p-2.5 font-medium">Licencia</th>
                <th className="p-2.5 font-medium">Actualizado en origen</th>
                <th className="p-2.5 font-medium">Extraído</th>
                <th className="p-2.5 font-medium">SHA-256</th>
                <th className="p-2.5 font-medium">Estado</th>
              </tr>
            </thead>
            <tbody>
              {sources.data.map((s) => {
                const st = SOURCE_STATUS[s.status] ?? { label: s.status, cls: "" };
                return (
                  <tr key={s.source_id} id={s.source_id} className="border-b border-line align-top target:bg-ochre-50">
                    <td className="p-2.5 font-cond font-semibold">{s.source_id}</td>
                    <td className="p-2.5">
                      <a href={s.catalog_url} target="_blank" rel="noopener noreferrer" className="font-medium text-slate underline">
                        {s.title}
                      </a>
                      <p className="text-xs text-ink-500">{s.producer} · {PORTAL_LABEL[s.portal] ?? s.portal}</p>
                      <p className="mt-1 text-xs text-ink-700"><span className="font-semibold">Uso: </span>{s.use_in_product}</p>
                      <p className="text-xs text-ink-600"><span className="font-semibold">Límite: </span>{s.caveats}</p>
                    </td>
                    <td className="p-2.5 text-xs">{s.spatial_scope}<br /><span className="text-ink-500">{s.temporal_scope}</span></td>
                    <td className="p-2.5 text-xs">{s.license}</td>
                    <td className="p-2.5 text-xs">{fmtDate(s.portal_modified_at)}</td>
                    <td className="p-2.5 text-xs">{fmtDate(s.last_extracted_at, true)}</td>
                    <td className="p-2.5">
                      {s.sha256 ? (
                        <code className="font-mono text-xs" title={s.sha256}>{s.sha256.slice(0, 12)}…</code>
                      ) : (
                        <span className="text-xs text-ink-500">—</span>
                      )}
                    </td>
                    <td className={`p-2.5 text-xs font-semibold ${st.cls}`}>
                      {st.label}
                      {s.quality_checks && s.quality_checks.length > 0 && (
                        <p className="mt-1 font-normal text-ink-600">
                          {s.quality_checks.filter((c) => c.passed ?? c.status === "passed").length}/{s.quality_checks.length} controles superados
                        </p>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <FireHistoryPanel />

      <section className="panel max-w-4xl">
        <h2 className="mb-3 font-cond text-lg font-semibold">Cómo leer el estado de cada dato</h2>
        <StatusLegend />
        <p className="mt-3 text-xs text-ink-500">
          Los distintivos se diferencian por forma (relleno, contorno, discontinuo, doble, rayado, punteado) además de por color.
        </p>
      </section>
    </div>
  );
}
