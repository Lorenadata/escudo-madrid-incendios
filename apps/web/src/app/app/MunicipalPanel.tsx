"use client";

import { useState } from "react";
import { IndicatorValue } from "@/components/IndicatorValue";
import { OfficialFirePanel } from "@/components/ProfilePanels";
import { Empty, ErrorState, Loading } from "@/components/States";
import { StatusBadge, SyntheticBadge } from "@/components/StatusBadge";
import { apiDownload } from "@/lib/api";
import type { Indicator, MunicipalityProfile } from "@/lib/api-types";
import { fmtDate, fmtEur, fmtShare } from "@/lib/format";
import { useApi } from "@/lib/useApi";

// Flujo B (PRD §3.2): responsable municipal. Solo ámbitos cuya organización ha autorizado compartirlos.

interface AreaStatus {
  area_id: string;
  name: string;
  organization: string;
  record_status: string;
  inspections_total: number;
  inspections_pending_review: number;
  last_inspection_on: string | null;
  scenario: null | {
    id: string;
    name: string;
    budget_eur: number;
    is_demo_budget: boolean;
    optimized_priority_coverage: number | null;
    optimized_cost_eur: number | null;
  };
  actions_total: number;
  actions_done: number;
  actions_overdue: number;
  actions_documented: number;
  planned_cost_eur: number;
  actual_cost_eur: number;
  budget_coverage_share: number | null;
}

interface Overview {
  notice: string;
  municipality: { ine_code: string; name: string; population: Indicator; density: Indicator; age_65_plus_share: Indicator };
  official_fire: MunicipalityProfile["official_fire"];
  sources: { ok: number; total: number };
  areas: AreaStatus[];
  totals: {
    areas_shared: number;
    inspections_pending_review: number;
    actions_total: number;
    actions_done: number;
    actions_overdue: number;
    actions_documented: number;
    planned_cost_eur: number;
    actual_cost_eur: number;
  };
  kpi_caveat: string;
}

interface PlanActionRow {
  id: string;
  measure_code: string;
  status: string;
  responsible: string | null;
  due_date: string | null;
  planned_cost_eur: number;
  actual_cost_eur: number | null;
  evidence_count: number;
}

interface AreaFile {
  notice: string;
  status: AreaStatus;
  inspections: { id: string; inspected_on: string; inspector_name: string; review_status: string; items: unknown[]; evidence: unknown[] }[];
  plan: null | { id: string; actions: PlanActionRow[] };
}

const STATUS_LABEL: Record<string, string> = { pending: "Pendiente", in_progress: "En curso", done: "Hecha", blocked: "Bloqueada" };

function Kpi({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="rounded border border-line bg-white p-3">
      <p className="text-xs text-ink-600">{label}</p>
      <p className="font-cond text-2xl font-semibold tabular-nums text-ink">{value}</p>
      {hint && <p className="text-xs text-ink-500">{hint}</p>}
    </div>
  );
}

function AreaFileView({ areaId, onClose }: { areaId: string; onClose: () => void }) {
  const f = useApi<AreaFile>(`/v1/municipal/areas/${areaId}`);
  const [msg, setMsg] = useState<string | null>(null);
  return (
    <section aria-labelledby="exp-h" className="panel space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 id="exp-h" className="font-cond text-lg font-semibold">Expediente (solo lectura)</h3>
        <div className="flex gap-2">
          <button
            type="button"
            className="btn-primary"
            onClick={async () => {
              setMsg(null);
              try {
                await apiDownload(`/v1/municipal/areas/${areaId}/report.pdf`, `escudo-expediente-${areaId.slice(0, 8)}.pdf`);
                setMsg("Informe descargado.");
              } catch (e) {
                setMsg(e instanceof Error ? e.message : "No se pudo descargar el informe.");
              }
            }}
          >
            Descargar informe PDF
          </button>
          <button type="button" className="btn-secondary" onClick={onClose}>Cerrar</button>
        </div>
      </div>
      {msg && <p role="status" className="text-sm text-ink-600">{msg}</p>}
      {f.loading && <Loading label="Cargando expediente" />}
      {!!f.error && <ErrorState error={f.error} onRetry={f.reload} />}
      {f.data && (
        <>
          <p className="text-xs text-ink-600">{f.data.notice}</p>
          <div>
            <h4 className="font-cond font-semibold">Inspecciones</h4>
            {f.data.inspections.length === 0 ? (
              <p className="text-sm text-ink-600">Sin inspecciones registradas.</p>
            ) : (
              <ul className="text-sm">
                {f.data.inspections.map((i) => (
                  <li key={i.id} className="border-t border-line py-1">
                    {fmtDate(i.inspected_on)} · {i.inspector_name} · {i.items.length} elementos · {i.evidence.length} evidencias ·{" "}
                    <b>{i.review_status === "pending_technical_review" ? "revisión técnica pendiente" : "revisada"}</b>
                  </li>
                ))}
              </ul>
            )}
          </div>
          <div>
            <h4 className="font-cond font-semibold">Plan de ejecución</h4>
            {!f.data.plan || f.data.plan.actions.length === 0 ? (
              <p className="text-sm text-ink-600">Sin plan de acciones.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <caption className="sr-only">Acciones del plan</caption>
                  <thead className="text-left text-xs text-ink-600">
                    <tr>
                      <th scope="col">Medida</th>
                      <th scope="col">Estado</th>
                      <th scope="col">Responsable</th>
                      <th scope="col">Vence</th>
                      <th scope="col" className="text-right">Planificado</th>
                      <th scope="col" className="text-right">Real</th>
                      <th scope="col" className="text-right">Evidencias</th>
                    </tr>
                  </thead>
                  <tbody>
                    {f.data.plan.actions.map((a) => (
                      <tr key={a.id} className="border-t border-line">
                        <td>{a.measure_code}</td>
                        <td>{STATUS_LABEL[a.status] ?? a.status}</td>
                        <td>{a.responsible ?? "—"}</td>
                        <td>{a.due_date ? fmtDate(a.due_date) : "—"}</td>
                        <td className="text-right tabular-nums">{fmtEur(a.planned_cost_eur)}</td>
                        <td className="text-right tabular-nums">{fmtEur(a.actual_cost_eur)}</td>
                        <td className="text-right tabular-nums">{a.evidence_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </section>
  );
}

export function MunicipalPanel() {
  const ov = useApi<Overview>("/v1/municipal/overview");
  const [openArea, setOpenArea] = useState<string | null>(null);

  if (ov.loading && !ov.data) return <Loading label="Cargando panel municipal" />;
  if (ov.error) return <ErrorState error={ov.error} onRetry={ov.reload} />;
  if (!ov.data) return null;
  const d = ov.data;
  const t = d.totals;
  const profile = { ...d.municipality, official_fire: d.official_fire } as unknown as MunicipalityProfile;

  return (
    <div className="mt-5 space-y-6">
      <section aria-labelledby="muni-h" className="space-y-2">
        <p className="text-xs uppercase tracking-wide text-ink-500">Panel municipal · INE {d.municipality.ine_code}</p>
        <h2 id="muni-h" className="font-cond text-2xl font-semibold">{d.municipality.name}</h2>
        <p className="max-w-prose rounded border-l-4 border-slate bg-white px-3 py-2 text-sm text-ink-600">{d.notice}</p>
        <p className="text-sm text-ink-600">
          Estado de las fuentes de datos: <b>{d.sources.ok} de {d.sources.total}</b> ingeridas correctamente.
        </p>
      </section>

      <section aria-label="Indicadores municipales" className="grid gap-4 md:grid-cols-3">
        <div className="panel"><IndicatorValue indicator={d.municipality.population} /></div>
        <div className="panel"><IndicatorValue indicator={d.municipality.density} /></div>
        <div className="panel"><IndicatorValue indicator={d.municipality.age_65_plus_share} /></div>
      </section>

      <section aria-labelledby="gest-h" className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <h3 id="gest-h" className="font-cond text-lg font-semibold">Actuaciones preventivas registradas</h3>
          <StatusBadge status="derived" />
        </div>
        <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
          <Kpi label="Ámbitos compartidos" value={String(t.areas_shared)} />
          <Kpi label="Inspecciones pendientes de revisión" value={String(t.inspections_pending_review)} />
          <Kpi label="Acciones hechas" value={`${t.actions_done} / ${t.actions_total}`} />
          <Kpi label="Acciones vencidas" value={String(t.actions_overdue)} />
          <Kpi label="Acciones con evidencia" value={`${t.actions_documented} / ${t.actions_total}`} />
          <Kpi label="Coste planificado" value={fmtEur(t.planned_cost_eur)} hint={`Real: ${fmtEur(t.actual_cost_eur)}`} />
        </div>
        <p className="text-xs text-ink-500">{d.kpi_caveat}</p>

        {d.areas.length === 0 ? (
          <Empty title="Ninguna organización ha compartido ámbitos todavía">
            Las urbanizaciones deciden si autorizan al ayuntamiento a consultar su planificación.
          </Empty>
        ) : (
          <div className="overflow-x-auto rounded border border-line bg-white">
            <table className="w-full text-sm">
              <caption className="sr-only">Ámbitos compartidos con el ayuntamiento</caption>
              <thead className="bg-granite text-left text-xs uppercase tracking-wide text-ink-600">
                <tr>
                  <th scope="col" className="px-3 py-2">Ámbito</th>
                  <th scope="col" className="px-3 py-2">Última inspección</th>
                  <th scope="col" className="px-3 py-2 text-right">Acciones hechas</th>
                  <th scope="col" className="px-3 py-2 text-right">Vencidas</th>
                  <th scope="col" className="px-3 py-2 text-right">Presupuesto planificado</th>
                  <th scope="col" className="px-3 py-2 text-right">Cobertura de prioridad</th>
                  <th scope="col" className="px-3 py-2"><span className="sr-only">Acciones</span></th>
                </tr>
              </thead>
              <tbody>
                {d.areas.map((a) => (
                  <tr key={a.area_id} className="border-t border-line align-top">
                    <th scope="row" className="px-3 py-2 text-left font-medium">
                      {a.name}
                      <span className="mt-0.5 flex items-center gap-1.5 text-xs font-normal text-ink-500">
                        {a.organization} {a.record_status === "synthetic" && <SyntheticBadge />}
                      </span>
                    </th>
                    <td className="px-3 py-2">
                      {a.last_inspection_on ? fmtDate(a.last_inspection_on) : "—"}
                      {a.inspections_pending_review > 0 && <span className="block text-xs text-ochre-800">{a.inspections_pending_review} pendiente(s) de revisión técnica</span>}
                    </td>
                    <td className="px-3 py-2 text-right tabular-nums">{a.actions_done} / {a.actions_total}</td>
                    <td className="px-3 py-2 text-right tabular-nums">{a.actions_overdue}</td>
                    <td className="px-3 py-2 text-right tabular-nums">
                      {fmtEur(a.planned_cost_eur)}
                      {a.scenario && (
                        <span className="block text-xs text-ink-500">
                          de {fmtEur(a.scenario.budget_eur)}{a.scenario.is_demo_budget ? " (demostración)" : ""}
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-right tabular-nums">
                      {fmtShare(a.scenario?.optimized_priority_coverage ?? null)}
                    </td>
                    <td className="px-3 py-2 text-right">
                      <button type="button" className="text-sm text-slate underline" onClick={() => setOpenArea(a.area_id)}>
                        Abrir expediente
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {openArea && <AreaFileView areaId={openArea} onClose={() => setOpenArea(null)} />}

      <section className="panel max-w-3xl">
        <OfficialFirePanel profile={profile} />
      </section>
    </div>
  );
}
