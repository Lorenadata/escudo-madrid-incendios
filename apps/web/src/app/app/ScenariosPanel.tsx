"use client";

import { useState } from "react";
import { ActionPlanTable, ScenarioOptionsTable, ScenarioResultView } from "@/components/ScenarioViews";
import { Empty, ErrorState, Loading } from "@/components/States";
import { StatusBadge } from "@/components/StatusBadge";
import { apiDownload, apiFetch } from "@/lib/api";
import type { ActionPlan, Measure, PlanAction, Scenario, ScenarioResult } from "@/lib/api-types";
import { fmtEur } from "@/lib/format";
import { useApi } from "@/lib/useApi";

interface Row {
  measure_code: string;
  quantity: string;
  unit_cost_eur: string;
  technical_priority: string;
  cost_status: "reference" | "user_quote" | "scenario";
  mandatory: boolean;
}

function NewScenario({ areaId, measures, onCreated }: { areaId: string; measures: Measure[]; onCreated: (s: Scenario) => void }) {
  const [name, setName] = useState("");
  const [budget, setBudget] = useState("");
  const [isDemo, setIsDemo] = useState(true);
  const [rows, setRows] = useState<Row[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const addRow = (code: string) => {
    const m = measures.find((x) => x.code === code);
    if (!m) return;
    setRows((r) => [
      ...r,
      {
        measure_code: code,
        quantity: "1",
        unit_cost_eur: m.reference_unit_cost_eur !== null ? String(m.reference_unit_cost_eur) : "",
        technical_priority: "3",
        cost_status: m.reference_unit_cost_eur !== null && m.cost_status === "reference" ? "reference" : "scenario",
        mandatory: false,
      },
    ]);
  };
  const update = (i: number, patch: Partial<Row>) => setRows((r) => r.map((x, j) => (j === i ? { ...x, ...patch } : x)));
  const total = rows.reduce((s, r) => s + (Number(r.quantity) || 0) * (Number(r.unit_cost_eur) || 0), 0);
  const valid = name.length >= 2 && budget !== "" && rows.length > 0 && rows.every((r) => Number(r.quantity) > 0 && r.unit_cost_eur !== "");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const s = await apiFetch<Scenario>("/v1/scenarios", {
        method: "POST",
        body: JSON.stringify({
          area_id: areaId,
          name,
          budget_eur: Number(budget),
          is_demo_budget: isDemo,
          options: rows.map((r, i) => ({
            measure_code: r.measure_code,
            quantity: Number(r.quantity),
            unit_cost_eur: Number(r.unit_cost_eur),
            technical_priority: Number(r.technical_priority),
            coverage_weight: 1,
            cost_status: r.cost_status,
            mandatory: r.mandatory,
            manual_rank: i + 1,
          })),
        }),
      });
      setRows([]);
      setName("");
      onCreated(s);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="panel space-y-3">
      <h3 className="font-cond text-lg font-semibold">Nuevo escenario de presupuesto</h3>
      <div className="grid gap-3 sm:grid-cols-[1fr_12rem]">
        <div>
          <label htmlFor="sn" className="label">Nombre</label>
          <input id="sn" className="field" value={name} onChange={(e) => setName(e.target.value)} required minLength={2} />
        </div>
        <div>
          <label htmlFor="sb" className="label">Presupuesto disponible (€)</label>
          <input id="sb" type="number" min={0} className="field" value={budget} onChange={(e) => setBudget(e.target.value)} required />
        </div>
      </div>
      <label className="flex items-center gap-2 text-sm">
        <input type="checkbox" className="accent-pine" checked={isDemo} onChange={(e) => setIsDemo(e.target.checked)} />
        Presupuesto de demostración o simulado (no es una adjudicación real)
      </label>
      <div>
        <label htmlFor="addm" className="label">Añadir actuación del catálogo</label>
        <select id="addm" className="field" value="" onChange={(e) => addRow(e.target.value)}>
          <option value="">Elige una actuación</option>
          {measures.map((m) => (
            <option key={m.code} value={m.code}>{m.name} ({m.unit})</option>
          ))}
        </select>
      </div>
      {rows.length === 0 ? (
        <p className="text-sm text-ink-500">Añade al menos una actuación propuesta por personal técnico.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[44rem] text-sm">
            <caption className="sr-only">Actuaciones candidatas</caption>
            <thead>
              <tr className="text-left text-xs text-ink-500">
                <th className="py-1 font-medium">Actuación</th>
                <th className="py-1 font-medium">Cantidad</th>
                <th className="py-1 font-medium">Coste unitario (€)</th>
                <th className="py-1 font-medium">Prioridad técnica (1–5)</th>
                <th className="py-1 font-medium">Origen del coste</th>
                <th className="py-1 font-medium">Obligatoria</th>
                <th className="py-1"><span className="sr-only">Quitar</span></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => {
                const m = measures.find((x) => x.code === r.measure_code);
                return (
                  <tr key={i} className="border-t border-line">
                    <td className="py-1 pr-2">{m?.name ?? r.measure_code}<span className="block text-xs text-ink-500">{m?.unit}</span></td>
                    <td className="py-1 pr-2"><input aria-label="Cantidad" type="number" min={0} step="any" className="field w-24 py-1" value={r.quantity} onChange={(e) => update(i, { quantity: e.target.value })} /></td>
                    <td className="py-1 pr-2"><input aria-label="Coste unitario" type="number" min={0} step="any" className="field w-28 py-1" value={r.unit_cost_eur} onChange={(e) => update(i, { unit_cost_eur: e.target.value, cost_status: r.cost_status === "reference" ? "user_quote" : r.cost_status })} /></td>
                    <td className="py-1 pr-2">
                      <select aria-label="Prioridad técnica" className="field w-20 py-1" value={r.technical_priority} onChange={(e) => update(i, { technical_priority: e.target.value })}>
                        {[1, 2, 3, 4, 5].map((p) => <option key={p} value={p}>{p}</option>)}
                      </select>
                    </td>
                    <td className="py-1 pr-2">
                      <select aria-label="Origen del coste" className="field py-1" value={r.cost_status} onChange={(e) => update(i, { cost_status: e.target.value as Row["cost_status"] })}>
                        <option value="reference">Precio de referencia</option>
                        <option value="user_quote">Presupuesto aportado</option>
                        <option value="scenario">Supuesto</option>
                      </select>
                    </td>
                    <td className="py-1 pr-2 text-center"><input aria-label="Obligatoria" type="checkbox" className="accent-pine" checked={r.mandatory} onChange={(e) => update(i, { mandatory: e.target.checked })} /></td>
                    <td className="py-1"><button type="button" className="text-xs text-rust underline" onClick={() => setRows((rs) => rs.filter((_, j) => j !== i))}>Quitar</button></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <p className="mt-1 text-sm text-ink-600">Coste de todas las candidatas: <strong>{fmtEur(total)}</strong>{budget && ` · presupuesto ${fmtEur(Number(budget))}`}</p>
        </div>
      )}
      <p className="text-xs text-ink-500">El orden de la lista se usa como priorización manual de referencia.</p>
      {error && <p role="alert" className="text-sm text-rust">{error}</p>}
      <button type="submit" className="btn-primary" disabled={busy || !valid}>{busy ? "Guardando…" : "Guardar escenario"}</button>
    </form>
  );
}

function ScenarioDetail({ scenario, measures, onChanged }: { scenario: Scenario; measures: Measure[]; onChanged: () => void }) {
  const [solved, setResult] = useState<ScenarioResult | null>(null);
  const result = solved ?? scenario.latest_result ?? null;
  const plans = useApi<ActionPlan[]>("/v1/action-plans");
  const [updatedPlan, setPlan] = useState<ActionPlan | null>(null);
  const plan = updatedPlan ?? plans.data?.filter((x) => String(x.scenario_id) === String(scenario.id)).pop() ?? null;
  const [strategy, setStrategy] = useState("optimized");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  async function run<T>(fn: () => Promise<T>, ok?: string) {
    setBusy(true);
    setMsg(null);
    try {
      const r = await fn();
      if (ok) setMsg(ok);
      return r;
    } catch (err) {
      setMsg(err instanceof Error ? err.message : String(err));
      return null;
    } finally {
      setBusy(false);
    }
  }

  const solve = () =>
    run(async () => {
      const r = await apiFetch<ScenarioResult>(`/v1/scenarios/${scenario.id}/solve`, { method: "POST" });
      setResult(r);
      onChanged();
    }, "Escenario resuelto.");

  const createPlan = () =>
    run(async () => {
      const p = await apiFetch<ActionPlan>("/v1/action-plans", {
        method: "POST",
        body: JSON.stringify({ scenario_id: scenario.id, strategy }),
      });
      setPlan(p);
      plans.reload();
    }, "Plan creado.");

  const patch = (a: PlanAction, body: Record<string, unknown>) =>
    plan &&
    run(async () => {
      await apiFetch(`/v1/action-plans/${plan.id}/actions/${a.id}`, { method: "PATCH", body: JSON.stringify(body) });
      setPlan(await apiFetch<ActionPlan>(`/v1/action-plans/${plan.id}`));
    }, "Actuación actualizada.");

  const upload = (a: PlanAction, file: File) =>
    plan &&
    run(async () => {
      const fd = new FormData();
      fd.append("file", file);
      await apiFetch(`/v1/action-plans/${plan.id}/actions/${a.id}/evidence`, { method: "POST", body: fd });
      setPlan(await apiFetch<ActionPlan>(`/v1/action-plans/${plan.id}`));
    }, `Evidencia «${file.name}» adjuntada.`);

  const pdf = () =>
    run(() => apiDownload(`/v1/reports/scenario/${scenario.id}.pdf`, `escudo-escenario-${scenario.id}.pdf`), "Informe descargado.");

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="font-cond text-lg font-semibold">{scenario.name}</h3>
        <span className="text-sm text-ink-600">Presupuesto {fmtEur(scenario.budget_eur)}</span>
        {scenario.is_demo_budget && <StatusBadge status="scenario" />}
      </div>
      <ScenarioOptionsTable scenario={scenario} measures={measures} />
      <div className="flex flex-wrap gap-2">
        <button type="button" className="btn-primary" disabled={busy} onClick={solve}>{result ? "Volver a resolver" : "Resolver escenario"}</button>
        <button type="button" className="btn-secondary" disabled={busy || !result} onClick={pdf}>Descargar informe PDF</button>
      </div>
      {msg && <p role="status" className="text-sm text-ink-700">{msg}</p>}
      {result ? <ScenarioResultView result={result} measures={measures} /> : <Empty title="Sin resolver">Resuelve el escenario para comparar las tres estrategias.</Empty>}

      {result && (
        <section aria-labelledby="plan-h" className="space-y-3 border-t border-line pt-4">
          <h3 id="plan-h" className="font-cond text-lg font-semibold">Plan de ejecución</h3>
          {plans.loading && <Loading label="Cargando planes" />}
          {!!plans.error && <ErrorState error={plans.error} onRetry={plans.reload} />}
          {!plan && (
            <div className="flex flex-wrap items-end gap-2">
              <div>
                <label htmlFor="strat" className="label">Estrategia a ejecutar</label>
                <select id="strat" className="field" value={strategy} onChange={(e) => setStrategy(e.target.value)}>
                  <option value="optimized">Optimizado (CP-SAT)</option>
                  <option value="manual">Priorización manual</option>
                  <option value="cheapest_first">Menor coste primero</option>
                </select>
              </div>
              <button type="button" className="btn-primary" disabled={busy} onClick={createPlan}>Confirmar plan</button>
            </div>
          )}
          {plan && <ActionPlanTable plan={plan} measures={measures} onPatch={patch} onUpload={upload} busy={busy} />}
        </section>
      )}
    </div>
  );
}

export function ScenariosPanel({ areaId, measures }: { areaId: string; measures: Measure[] }) {
  const list = useApi<Scenario[]>(`/v1/scenarios?area_id=${encodeURIComponent(areaId)}`);
  const [picked, setSelected] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const current = list.data?.find((s) => String(s.id) === picked) ?? list.data?.[0] ?? null;
  const selected = current ? String(current.id) : null;

  return (
    <div className="space-y-4">
      {list.loading && !list.data && <Loading label="Cargando escenarios" />}
      {!!list.error && <ErrorState error={list.error} onRetry={list.reload} />}
      <div className="flex flex-wrap items-center gap-2">
        {list.data?.map((s) => (
          <button
            key={s.id}
            type="button"
            aria-pressed={String(s.id) === selected}
            onClick={() => { setSelected(String(s.id)); setCreating(false); }}
            className={`rounded border px-3 py-1.5 text-sm ${String(s.id) === selected && !creating ? "border-pine bg-pine-50 font-semibold" : "border-line bg-white hover:bg-granite"}`}
          >
            {s.name}
          </button>
        ))}
        <button type="button" className="btn-secondary" onClick={() => setCreating((v) => !v)}>
          {creating ? "Cancelar" : "Nuevo escenario"}
        </button>
      </div>
      {list.data && list.data.length === 0 && !creating && (
        <Empty title="Sin escenarios">Crea un escenario con las actuaciones propuestas y el presupuesto disponible.</Empty>
      )}
      {creating && (
        <NewScenario
          areaId={areaId}
          measures={measures}
          onCreated={(s) => {
            setCreating(false);
            setSelected(String(s.id));
            list.reload();
          }}
        />
      )}
      {!creating && current && <ScenarioDetail key={current.id} scenario={current} measures={measures} onChanged={list.reload} />}
    </div>
  );
}
