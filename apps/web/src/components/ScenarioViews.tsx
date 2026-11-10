"use client";

import type { ActionPlan, Measure, PlanAction, Scenario, ScenarioResult } from "@/lib/api-types";
import { fmtDate, fmtEur } from "@/lib/format";
import { SensitivityChart, StrategyBars, StrategyTable } from "./Charts";
import { StatusBadge } from "./StatusBadge";

export function measureName(measures: Measure[] | undefined, code: string) {
  return measures?.find((m) => m.code === code)?.name ?? code;
}

export function ScenarioOptionsTable({ scenario, measures }: { scenario: Scenario; measures?: Measure[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[40rem] text-sm">
        <caption className="sr-only">Actuaciones candidatas del escenario</caption>
        <thead>
          <tr className="border-b border-ink/20 text-left text-xs text-ink-500">
            <th className="py-1.5 font-medium">Actuación</th>
            <th className="py-1.5 text-right font-medium">Cantidad</th>
            <th className="py-1.5 text-right font-medium">Coste unitario</th>
            <th className="py-1.5 text-right font-medium">Coste total</th>
            <th className="py-1.5 text-right font-medium">Prioridad técnica</th>
            <th className="py-1.5 font-medium">Origen del coste</th>
          </tr>
        </thead>
        <tbody>
          {scenario.options.map((o, i) => (
            <tr key={o.option_id ?? `${o.measure_code}-${i}`} className="border-b border-line">
              <td className="py-1.5">
                {measureName(measures, o.measure_code)}
                {o.mandatory && <span className="ml-2 text-xs text-ochre-800">obligatoria</span>}
              </td>
              <td className="py-1.5 text-right tabular-nums">{o.quantity}</td>
              <td className="py-1.5 text-right tabular-nums">{fmtEur(o.unit_cost_eur)}</td>
              <td className="py-1.5 text-right tabular-nums">{fmtEur(o.total_cost_eur ?? o.quantity * o.unit_cost_eur)}</td>
              <td className="py-1.5 text-right tabular-nums">{o.technical_priority} / 5</td>
              <td className="py-1.5">
                <StatusBadge status={o.cost_status === "user_quote" ? "user_reported" : o.cost_status === "reference" ? "derived" : "scenario"} />
                <span className="ml-1 text-xs text-ink-500">
                  {o.cost_status === "reference" ? "precio de referencia" : o.cost_status === "user_quote" ? "presupuesto aportado" : "supuesto"}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function ScenarioResultView({ result, measures }: { result: ScenarioResult; measures?: Measure[] }) {
  const opt = result.strategies.find((s) => s.strategy === "optimized");
  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <span>Resultado del solver: <strong>{result.status}</strong></span>
        <span className="text-ink-500">· {result.solver} {result.solver_version}</span>
        {result.deterministic && <span className="text-ink-500">· determinista</span>}
        {result.is_demo_budget && <StatusBadge status="scenario" />}
        {result.is_demo_budget && <span className="text-xs text-ochre-800">Presupuesto de demostración, no es una adjudicación real</span>}
      </div>
      {result.message && <p className="rounded bg-ochre-50 p-2 text-sm">{result.message}</p>}
      <StrategyTable strategies={result.strategies} budget={result.budget_eur} />
      <div className="grid gap-6 lg:grid-cols-2">
        <StrategyBars strategies={result.strategies} />
        <SensitivityChart points={result.sensitivity} currentBudget={result.budget_eur} />
      </div>
      {opt && (
        <div>
          <h4 className="font-cond text-base font-semibold">Actuaciones seleccionadas por el modelo optimizado</h4>
          <ul className="mt-1 list-inside list-disc text-sm text-ink-700">
            {opt.selected.map((c, i) => <li key={`${c}-${i}`}>{measureName(measures, c)}</li>)}
          </ul>
        </div>
      )}
      <details className="rounded border border-line bg-white p-3 text-sm">
        <summary className="cursor-pointer font-medium text-slate">Ver método y fuentes</summary>
        <p className="mt-2"><span className="font-semibold">Función objetivo. </span>{result.objective_definition}</p>
        <p className="mt-1"><span className="font-semibold">Límite. </span>{result.disclaimer}</p>
        {result.input_hash && (
          <p className="mt-1 text-xs text-ink-500">Huella de entrada (reproducibilidad): <code className="font-mono">{result.input_hash.slice(0, 16)}…</code></p>
        )}
      </details>
    </div>
  );
}

const ACTION_STATUS: Record<string, string> = {
  pending: "Pendiente",
  in_progress: "En curso",
  done: "Hecha",
  blocked: "Bloqueada",
};

export function ActionPlanTable({
  plan,
  measures,
  onPatch,
  onUpload,
  busy,
  renderThread,
}: {
  plan: ActionPlan;
  measures?: Measure[];
  onPatch?: (a: PlanAction, patch: Partial<PlanAction> & { note?: string }) => void;
  onUpload?: (a: PlanAction, file: File) => void;
  busy?: boolean;
  renderThread?: (a: PlanAction) => React.ReactNode;
}) {
  if (!plan.actions.length) return <p className="text-sm text-ink-500">El plan no tiene actuaciones.</p>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[52rem] text-sm">
        <caption className="sr-only">Plan de ejecución</caption>
        <thead>
          <tr className="border-b border-ink/20 text-left text-xs text-ink-500">
            <th className="py-1.5 font-medium">Actuación</th>
            <th className="py-1.5 font-medium">Estado</th>
            <th className="py-1.5 font-medium">Responsable</th>
            <th className="py-1.5 font-medium">Vencimiento</th>
            <th className="py-1.5 text-right font-medium">Planificado</th>
            <th className="py-1.5 text-right font-medium">Coste real</th>
            <th className="py-1.5 font-medium">Evidencias</th>
          </tr>
        </thead>
        <tbody>
          {plan.actions.map((a) => (
            <tr key={a.id} className="border-b border-line align-top">
              <td className="py-1.5 pr-2">
                {measureName(measures, a.measure_code)}
                {renderThread?.(a)}
                {a.history?.length > 0 && (
                  <details className="text-xs text-ink-500">
                    <summary className="cursor-pointer">Historial ({a.history.length})</summary>
                    <ul className="mt-1 space-y-0.5">
                      {a.history.map((h, i) => (
                        <li key={i}>{fmtDate(String(h.at ?? ""), true)} · {String(h.change ?? h.field ?? "cambio")}{h.to !== undefined ? ` → ${String(h.to)}` : ""}</li>
                      ))}
                    </ul>
                  </details>
                )}
              </td>
              <td className="py-1.5 pr-2">
                {onPatch ? (
                  <select
                    aria-label={`Estado de ${measureName(measures, a.measure_code)}`}
                    className="field py-1"
                    value={a.status}
                    disabled={busy}
                    onChange={(e) => onPatch(a, { status: e.target.value })}
                  >
                    {Object.entries(ACTION_STATUS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                  </select>
                ) : (
                  ACTION_STATUS[a.status] ?? a.status
                )}
              </td>
              <td className="py-1.5 pr-2">
                {onPatch ? (
                  <input
                    aria-label="Responsable"
                    className="field py-1"
                    defaultValue={a.responsible ?? ""}
                    disabled={busy}
                    onBlur={(e) => e.target.value !== (a.responsible ?? "") && onPatch(a, { responsible: e.target.value })}
                  />
                ) : (
                  a.responsible ?? "—"
                )}
              </td>
              <td className="py-1.5 pr-2">
                {onPatch ? (
                  <input
                    aria-label="Fecha de vencimiento"
                    type="date"
                    className="field py-1"
                    defaultValue={a.due_date ?? ""}
                    disabled={busy}
                    onChange={(e) => e.target.value && onPatch(a, { due_date: e.target.value })}
                  />
                ) : (
                  fmtDate(a.due_date)
                )}
              </td>
              <td className="py-1.5 text-right tabular-nums">{fmtEur(a.planned_cost_eur)}</td>
              <td className="py-1.5 text-right">
                {onPatch ? (
                  <input
                    aria-label="Coste real en euros"
                    type="number"
                    min={0}
                    className="field w-28 py-1 text-right"
                    defaultValue={a.actual_cost_eur ?? ""}
                    disabled={busy}
                    onBlur={(e) => e.target.value !== "" && Number(e.target.value) !== a.actual_cost_eur && onPatch(a, { actual_cost_eur: Number(e.target.value) })}
                  />
                ) : (
                  <span className="tabular-nums">{fmtEur(a.actual_cost_eur)}</span>
                )}
              </td>
              <td className="py-1.5">
                <span className="tabular-nums">{a.evidence_count}</span>
                {onUpload && (
                  <label className="ml-2 cursor-pointer text-xs text-slate underline">
                    Adjuntar
                    <input
                      type="file"
                      accept="image/jpeg,image/png,application/pdf"
                      className="sr-only"
                      disabled={busy}
                      onChange={(e) => {
                        const f = e.target.files?.[0];
                        if (f) onUpload(a, f);
                        e.target.value = "";
                      }}
                    />
                  </label>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
