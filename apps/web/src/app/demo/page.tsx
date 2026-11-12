"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { CoverageHero } from "@/components/CoverageHero";
import { MunicipalityProfileView } from "@/components/ProfilePanels";
import { ActionPlanTable, ScenarioOptionsTable, ScenarioResultView } from "@/components/ScenarioViews";
import { ErrorState, Loading } from "@/components/States";
import { SyntheticBadge } from "@/components/StatusBadge";
import { API_URL } from "@/lib/api";
import type { GuidedDemo } from "@/lib/api-types";
import { fmtDate, fmtEur } from "@/lib/format";
import { useApi } from "@/lib/useApi";

const STEPS = [
  { id: "municipio", label: "Municipio real" },
  { id: "ambito", label: "Ámbito ficticio" },
  { id: "inspeccion", label: "Inspección" },
  { id: "escenario", label: "Medidas y presupuesto" },
  { id: "resultado", label: "Comparación" },
  { id: "plan", label: "Plan y evidencias" },
  { id: "informe", label: "Informe" },
];

const ANSWER: Record<string, string> = { si: "Sí", "sí": "Sí", no: "No", parcial: "Parcial", na: "No aplica" };

function Step({ n, id, title, synthetic, children }: { n: number; id: string; title: string; synthetic?: boolean; children: React.ReactNode }) {
  return (
    <section id={id} aria-labelledby={`${id}-h`} className="scroll-mt-16 grid gap-4 border-t border-line py-8 md:grid-cols-[3.5rem_1fr]">
      <span className="font-cond text-4xl font-bold leading-none text-pine tabular-nums" aria-hidden>{n}</span>
      <div className="min-w-0 space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <h2 id={`${id}-h`} className="font-cond text-2xl font-bold text-ink">{title}</h2>
          {synthetic && <SyntheticBadge />}
          {synthetic && <span className="text-xs font-semibold text-ochre-800">Datos ficticios</span>}
        </div>
        {children}
      </div>
    </section>
  );
}

/** Paso visible en pantalla (para marcarlo en la barra de pasos). */
function useActiveStep(ready: boolean) {
  const [active, setActive] = useState<string>(STEPS[0].id);
  useEffect(() => {
    if (!ready || typeof IntersectionObserver === "undefined") return;
    const obs = new IntersectionObserver(
      (entries) => {
        const vis = entries.filter((e) => e.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
        if (vis[0]) setActive(vis[0].target.id);
      },
      { rootMargin: "-15% 0px -70% 0px" },
    );
    STEPS.forEach((s) => {
      const el = document.getElementById(s.id);
      if (el) obs.observe(el);
    });
    return () => obs.disconnect();
  }, [ready]);
  return active;
}

export default function DemoPage() {
  const demo = useApi<GuidedDemo>("/v1/demo/guided");
  const d = demo.data;
  const active = useActiveStep(!!d);
  const profile = d?.area?.municipality_profile ?? null;
  const result = d?.scenario?.latest_result ?? d?.scenario?.result ?? null;

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-6">
      <header className="max-w-3xl space-y-2">
        <h1 className="font-cond text-4xl font-bold leading-tight text-ink">Caso guiado: del dato oficial al plan documentado</h1>
        <p className="leading-relaxed text-ink-700">
          Un recorrido de solo lectura, sin credenciales. El municipio, sus indicadores y las capas oficiales son reales. La
          organización, la urbanización, la inspección, los costes y el presupuesto son ficticios y aparecen marcados.
        </p>
      </header>

      {d && result && (
        <CoverageHero strategies={result.strategies} budget={d.scenario.budget_eur} isDemoBudget={!!d.scenario.is_demo_budget} />
      )}

      <nav aria-label="Pasos del caso guiado" className="sticky top-0 z-10 -mx-4 mt-6 overflow-x-auto border-b border-line bg-granite/95 px-4 backdrop-blur">
        <ol className="flex text-sm">
          {STEPS.map((s, i) => {
            const on = active === s.id;
            return (
              <li key={s.id}>
                <a
                  href={`#${s.id}`}
                  aria-current={on ? "step" : undefined}
                  className={`flex items-center gap-1.5 whitespace-nowrap border-b-[3px] px-2.5 py-2.5 ${on ? "border-pine font-semibold text-ink" : "border-transparent text-ink-600 hover:text-ink"}`}
                >
                  <span className={`inline-flex h-5 w-5 items-center justify-center rounded-full text-[11px] tabular-nums ${on ? "bg-pine text-white" : "border border-ink/30 text-ink-600"}`}>{i + 1}</span>
                  {s.label}
                </a>
              </li>
            );
          })}
        </ol>
      </nav>

      {demo.loading && <Loading label="Cargando caso guiado" />}
      {!!demo.error && <ErrorState error={demo.error} onRetry={demo.reload} />}

      {d && (
        <>
          <p role="note" className="mt-4 rounded border-l-4 border-ochre bg-ochre-50 p-3 text-sm text-ink-800">{d.notice}</p>

          <Step n={1} id="municipio" title="Contexto territorial oficial">
            {profile ? (
              <div className="panel max-w-2xl"><MunicipalityProfileView profile={profile} /></div>
            ) : (
              <p className="text-sm text-ink-500">La API no ha devuelto la ficha municipal del ámbito.</p>
            )}
          </Step>

          <Step n={2} id="ambito" title={d.area.name} synthetic>
            <p className="text-sm text-ink-700">{d.area.description}</p>
            <p className="text-sm text-ink-600">
              Gestionado por «{d.organization.name}», en el municipio INE {d.area.municipality_code},{" "}
              {d.area.has_geometry ? "con geometría declarada." : "sin geometría."}
            </p>
            <p className="text-xs text-ink-500">
              {d.area.population_notice ?? "El ámbito no hereda población ni viviendas del municipio: esos datos solo existen a escala municipal."}
            </p>
          </Step>

          <Step n={3} id="inspeccion" title="Inspección preventiva" synthetic>
            {d.inspections.length === 0 && <p className="text-sm text-ink-500">Sin inspecciones registradas.</p>}
            {d.inspections.map((ins) => (
              <div key={ins.id} className="panel space-y-2">
                <p className="text-sm">
                  {fmtDate(ins.inspected_on)}, {ins.inspector_name}.{" "}
                  <span className="font-semibold">
                    {ins.review_status === "reviewed" ? "Revisada por técnico" : "Pendiente de revisión técnica"}
                  </span>
                </p>
                <ul className="divide-y divide-line text-sm">
                  {ins.items.map((it) => (
                    <li key={it.checklist_code} className="grid gap-1 py-1.5 sm:grid-cols-[1fr_6rem]">
                      <span>
                        {it.question || it.checklist_code}
                        {it.observation && <span className="block text-xs text-ink-500">{it.observation}</span>}
                      </span>
                      <span className="font-semibold sm:text-right">{ANSWER[it.answer?.toLowerCase()] ?? it.answer}</span>
                    </li>
                  ))}
                </ul>
                {ins.evidence.length > 0 && (
                  <p className="text-xs text-ink-600">
                    Evidencias adjuntas (ficticias): {ins.evidence.map((e) => e.original_name ?? e.filename).join(", ")}
                  </p>
                )}
              </div>
            ))}
          </Step>

          <Step n={4} id="escenario" title={`Escenario «${d.scenario.name}»`} synthetic>
            <p className="text-sm text-ink-700">
              Presupuesto disponible: <strong>{fmtEur(d.scenario.budget_eur)}</strong>
              {d.scenario.is_demo_budget && " (presupuesto de demostración)"}. Las medidas proceden del catálogo; cada una
              requiere validación de personal técnico competente.
            </p>
            <ScenarioOptionsTable scenario={d.scenario} measures={d.measures} />
          </Step>

          <Step n={5} id="resultado" title="Comparación de estrategias">
            {result ? (
              <ScenarioResultView result={result} measures={d.measures} />
            ) : (
              <p className="text-sm text-ink-500">El escenario aún no se ha resuelto.</p>
            )}
          </Step>

          <Step n={6} id="plan" title="Plan de ejecución y evidencias" synthetic>
            {d.plan ? (
              <ActionPlanTable plan={d.plan} measures={d.measures} />
            ) : (
              <p className="text-sm text-ink-500">Todavía no se ha creado un plan a partir del escenario.</p>
            )}
            <p className="text-xs font-semibold text-ochre-800">
              Responsables, fechas, costes reales y evidencias de este plan son FICTICIOS.
            </p>
          </Step>

          <Step n={7} id="informe" title="Informe reproducible">
            <p className="max-w-prose text-sm text-ink-700">
              El informe PDF recoge fuentes con fecha, método del optimizador, supuestos, qué es real y qué es simulado, y la
              revisión técnica pendiente.
            </p>
            <div className="flex flex-wrap gap-2">
              <a className="btn-primary" href={`${API_URL}${d.report_url}`} download>
                Descargar informe PDF
              </a>
              <Link className="btn-secondary" href="/fuentes">Revisar las fuentes</Link>
            </div>
          </Step>
        </>
      )}
    </div>
  );
}
