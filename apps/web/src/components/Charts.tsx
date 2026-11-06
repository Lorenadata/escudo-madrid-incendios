import type { SensitivityPoint, StrategyResult } from "@/lib/api-types";
import { fmtEur, fmtNumber, fmtShare } from "@/lib/format";

export const STRATEGY_LABEL: Record<string, string> = {
  manual: "Priorización manual",
  cheapest_first: "Menor coste primero",
  optimized: "Optimizado (CP-SAT)",
};

const STRATEGY_COLOR: Record<string, string> = {
  manual: "#8A8F8C",
  cheapest_first: "#3C5A73",
  optimized: "#1E3B2F",
};

/** Barras horizontales del valor objetivo por estrategia. Valores calculados por el solver. */
export function StrategyBars({ strategies }: { strategies: StrategyResult[] }) {
  const max = Math.max(1, ...strategies.map((s) => s.objective_value));
  return (
    <figure>
      <figcaption className="mb-2 text-sm text-ink-600">
        Valor de la función objetivo acordada (prioridad técnica × cobertura). No mide reducción de riesgo.
      </figcaption>
      <div className="space-y-2">
        {strategies.map((s) => (
          <div key={s.strategy} className="grid grid-cols-[10rem_1fr_4rem] items-center gap-2 text-sm">
            <span className="text-ink-700">{STRATEGY_LABEL[s.strategy] ?? s.strategy}</span>
            <div className="h-5 rounded-sm bg-granite" aria-hidden>
              <div
                className="h-5 rounded-sm"
                style={{ width: `${(s.objective_value / max) * 100}%`, background: STRATEGY_COLOR[s.strategy] ?? "#3C5A73" }}
              />
            </div>
            <span className="text-right tabular-nums font-semibold">{fmtNumber(s.objective_value)}</span>
          </div>
        ))}
      </div>
    </figure>
  );
}

export function StrategyTable({ strategies, budget }: { strategies: StrategyResult[]; budget: number }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[34rem] text-sm">
        <caption className="sr-only">Comparación de estrategias de selección de actuaciones</caption>
        <thead>
          <tr className="border-b border-ink/20 text-left text-xs text-ink-500">
            <th className="py-1.5 font-medium">Estrategia</th>
            <th className="py-1.5 text-right font-medium">Actuaciones</th>
            <th className="py-1.5 text-right font-medium">Coste total</th>
            <th className="py-1.5 text-right font-medium">Presupuesto usado</th>
            <th className="py-1.5 text-right font-medium">Valor objetivo</th>
            <th className="py-1.5 text-right font-medium">Cobertura de prioridad</th>
          </tr>
        </thead>
        <tbody>
          {strategies.map((s) => (
            <tr key={s.strategy} className={`border-b border-line ${s.strategy === "optimized" ? "bg-pine-50 font-semibold" : ""}`}>
              <td className="py-1.5">{STRATEGY_LABEL[s.strategy] ?? s.strategy}</td>
              <td className="py-1.5 text-right tabular-nums">{s.selected.length}</td>
              <td className="py-1.5 text-right tabular-nums">{fmtEur(s.total_cost_eur)}</td>
              <td className="py-1.5 text-right tabular-nums">{budget > 0 ? fmtShare(s.total_cost_eur / budget) : "—"}</td>
              <td className="py-1.5 text-right tabular-nums">{fmtNumber(s.objective_value)}</td>
              <td className="py-1.5 text-right tabular-nums">{fmtShare(s.priority_coverage_share)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** Curva de sensibilidad: valor objetivo óptimo frente a presupuesto. SVG accesible. */
export function SensitivityChart({ points, currentBudget }: { points: SensitivityPoint[]; currentBudget?: number }) {
  if (!points.length) return <p className="text-sm text-ink-500">Sin análisis de sensibilidad.</p>;
  // La curva solo usa puntos con costes nominales; los de estrés de costes se listan aparte.
  const pts = points.filter((p) => (p.cost_multiplier ?? 1) === 1).sort((a, b) => a.budget_eur - b.budget_eur);
  const stress = points.filter((p) => (p.cost_multiplier ?? 1) !== 1);
  const W = 520, H = 220, L = 56, R = 12, T = 12, B = 36;
  const xMax = Math.max(...pts.map((p) => p.budget_eur), currentBudget ?? 0) || 1;
  const yMax = Math.max(...pts.map((p) => p.objective_value)) || 1;
  const x = (v: number) => L + (v / xMax) * (W - L - R);
  const y = (v: number) => H - B - (v / yMax) * (H - T - B);
  const path = pts.map((p, i) => `${i ? "L" : "M"}${x(p.budget_eur).toFixed(1)},${y(p.objective_value).toFixed(1)}`).join(" ");
  const yTicks = [0, 0.5, 1].map((f) => f * yMax);
  const xTicks = [0, 0.5, 1].map((f) => f * xMax);
  return (
    <figure>
      <figcaption className="mb-1 text-sm text-ink-600">
        Sensibilidad: valor objetivo óptimo al variar el presupuesto.
      </figcaption>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full max-w-xl" role="img" aria-label="Curva de valor objetivo frente a presupuesto">
        {yTicks.map((t) => (
          <g key={`y${t}`}>
            <line x1={L} x2={W - R} y1={y(t)} y2={y(t)} stroke="#D5DBD8" />
            <text x={L - 6} y={y(t) + 4} textAnchor="end" fontSize="11" fill="#56615B">{fmtNumber(t)}</text>
          </g>
        ))}
        {xTicks.map((t) => (
          <text key={`x${t}`} x={x(t)} y={H - B + 16} textAnchor="middle" fontSize="11" fill="#56615B">{fmtEur(t)}</text>
        ))}
        {currentBudget !== undefined && (
          <g>
            <line x1={x(currentBudget)} x2={x(currentBudget)} y1={T} y2={H - B} stroke="#B7791F" strokeDasharray="4 3" />
            <text x={x(currentBudget) + 4} y={T + 10} fontSize="11" fill="#7A5114">presupuesto del escenario</text>
          </g>
        )}
        <path d={path} fill="none" stroke="#1E3B2F" strokeWidth="2" />
        {pts.map((p) => (
          <circle key={p.budget_eur} cx={x(p.budget_eur)} cy={y(p.objective_value)} r="3" fill="#1E3B2F">
            <title>{`${fmtEur(p.budget_eur)}: objetivo ${fmtNumber(p.objective_value)}, coste ${fmtEur(p.total_cost_eur)}`}</title>
          </circle>
        ))}
        <text x={L} y={H - 4} fontSize="11" fill="#56615B">Presupuesto</text>
      </svg>
      {stress.length > 0 && (
        <ul className="mt-2 space-y-0.5 text-xs text-ink-700">
          {stress.map((p) => (
            <li key={`${p.label}-${p.cost_multiplier}`}>
              Prueba de estrés {p.label ?? `costes ×${p.cost_multiplier}`}: objetivo {fmtNumber(p.objective_value)}, coste{" "}
              {fmtEur(p.total_cost_eur)}{p.status ? ` (${p.status})` : ""}.
            </li>
          ))}
        </ul>
      )}
    </figure>
  );
}
