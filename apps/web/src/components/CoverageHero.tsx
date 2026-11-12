import type { StrategyResult } from "@/lib/api-types";
import { fmtEur, fmtShare } from "@/lib/format";
import { STRATEGY_LABEL } from "./Charts";

const ORDER = ["manual", "cheapest_first", "optimized"];

/**
 * Resumen del caso guiado: cobertura de la prioridad técnica de cada estrategia con el mismo presupuesto.
 * Escala fija 0–100 % para no exagerar diferencias. Valores del solver; nunca reducción de riesgo.
 */
export function CoverageHero({ strategies, budget, isDemoBudget }: { strategies: StrategyResult[]; budget: number; isDemoBudget: boolean }) {
  const rows = [...strategies].sort((a, b) => ORDER.indexOf(a.strategy) - ORDER.indexOf(b.strategy));
  const best = rows.find((s) => s.strategy === "optimized");
  if (!best) return null;
  return (
    <figure className="mt-6 grid gap-6 rounded border border-line bg-white p-5 md:grid-cols-[minmax(0,2fr)_minmax(0,3fr)] md:p-6">
      <div className="space-y-2">
        <p className="font-cond text-[56px] font-bold leading-none tabular-nums text-pine">{fmtShare(best.priority_coverage_share)}</p>
        <p className="max-w-sm text-sm leading-relaxed text-ink-700">
          de la prioridad técnica cubierta con {fmtEur(budget)}
          {isDemoBudget ? " (presupuesto ficticio)" : ""}, eligiendo las actuaciones con el optimizador.
        </p>
      </div>
      <div className="space-y-3">
        {rows.map((s) => {
          const opt = s.strategy === "optimized";
          return (
            <div key={s.strategy}>
              <div className="flex items-baseline justify-between gap-2 text-sm">
                <span className={opt ? "font-semibold text-ink" : "text-ink-700"}>{STRATEGY_LABEL[s.strategy] ?? s.strategy}</span>
                <span className={`tabular-nums ${opt ? "font-semibold text-ink" : "text-ink-700"}`}>
                  {fmtShare(s.priority_coverage_share)} <span className="text-xs font-normal text-ink-500">con {fmtEur(s.total_cost_eur)}</span>
                </span>
              </div>
              <div className="mt-1 h-3 bg-granite" aria-hidden>
                <div className={`h-3 ${opt ? "bg-pine" : "bg-ash"}`} style={{ width: `${Math.max(0, Math.min(1, s.priority_coverage_share)) * 100}%` }} />
              </div>
            </div>
          );
        })}
        <figcaption className="text-xs leading-relaxed text-ink-500">
          Cobertura de la prioridad técnica ponderada que asigna el personal técnico, en escala de 0 a 100 %. Mide qué parte de las
          prioridades cabe en el presupuesto; no es una estimación de reducción del riesgo.
        </figcaption>
      </div>
    </figure>
  );
}
