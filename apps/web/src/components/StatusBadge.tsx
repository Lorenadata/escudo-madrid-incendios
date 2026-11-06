import type { IndicatorStatus } from "@/lib/api-types";

// Cada estado se distingue por FORMA (relleno, contorno, discontinuo, rayado) además de color,
// para que la diferencia sea legible sin color y en impresión.
export const STATUS_META: Record<IndicatorStatus, { label: string; help: string; cls: string }> = {
  official: {
    label: "Oficial",
    help: "Dato publicado por un organismo oficial, mostrado sin recalcular.",
    cls: "bg-pine text-white border-pine",
  },
  derived: {
    label: "Derivado",
    help: "Calculado por ESCUDO a partir de datos oficiales con un método documentado.",
    cls: "bg-white text-slate border-slate",
  },
  scenario: {
    label: "Escenario",
    help: "Simulación o supuesto de planificación. No es un dato observado ni una adjudicación real.",
    cls: "bg-ochre-50 text-ochre-800 border-ochre border-dashed",
  },
  user_reported: {
    label: "Aportado",
    help: "Información registrada por una persona usuaria; pendiente de revisión técnica.",
    cls: "bg-white text-plum border-plum border-double border-[3px]",
  },
  unavailable: {
    label: "No disponible",
    help: "La fuente no ha devuelto un dato válido. No se sustituye por estimaciones.",
    cls: "status-hatch text-ash-800 border-ash",
  },
  stale: {
    label: "Caducado",
    help: "El último dato válido ha superado su periodo de vigencia.",
    cls: "bg-rust-50 text-rust border-rust border-dotted border-2",
  },
};

export function StatusBadge({ status, className = "" }: { status: IndicatorStatus | string; className?: string }) {
  const meta = STATUS_META[status as IndicatorStatus] ?? STATUS_META.unavailable;
  return (
    <span
      title={meta.help}
      className={`inline-flex items-center whitespace-nowrap rounded-[3px] border px-1.5 py-px font-cond text-[11px] font-semibold leading-4 tracking-wide ${meta.cls} ${className}`}
    >
      {meta.label}
    </span>
  );
}

// Registros de demostración inventados (record_status = "synthetic"). No es un estado de indicador:
// un dato ficticio no es un escenario de planificación ni un dato observado.
export function SyntheticBadge({ className = "" }: { className?: string }) {
  return (
    <span
      title="Dato ficticio de demostración: inventado para ilustrar el flujo, no describe ninguna urbanización real."
      className={`inline-flex items-center whitespace-nowrap rounded-[3px] border border-dashed border-ochre bg-white px-1.5 py-px font-cond text-[11px] font-semibold uppercase leading-4 tracking-wide text-ochre-800 ${className}`}
    >
      Ficticio
    </span>
  );
}

export function StatusLegend() {
  return (
    <dl className="grid grid-cols-1 gap-2 text-sm sm:grid-cols-2">
      {(Object.keys(STATUS_META) as IndicatorStatus[]).map((s) => (
        <div key={s} className="flex items-start gap-2">
          <dt className="shrink-0"><StatusBadge status={s} /></dt>
          <dd className="text-ink-600">{STATUS_META[s].help}</dd>
        </div>
      ))}
    </dl>
  );
}
