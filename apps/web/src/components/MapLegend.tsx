import type { LegendSpec } from "./MapExplorer";

/** Leyenda de mapa como cajetín de hoja cartográfica: muestras contiguas, título y nota de método. */
export function MapLegend({ specs, className = "" }: { specs: LegendSpec[]; className?: string }) {
  if (!specs.length) return null;
  return (
    <div className={`space-y-2 overflow-y-auto ${className}`}>
      {specs.map((l) => (
        <div key={l.title} className="map-legend">
          <p className="mb-1.5 font-cond text-[13px] font-semibold leading-snug text-ink">{l.title}</p>
          <ul className="pt-px">
            {l.items.map((it) => (
              <li key={it.label} className="-mt-px flex h-[19px] items-stretch gap-2">
                <span className="w-6 shrink-0 border border-ink/25" style={{ background: it.color }} aria-hidden />
                <span className="self-center tabular-nums leading-none">{it.label}</span>
              </li>
            ))}
          </ul>
          <p className="mt-1.5 leading-snug text-ink-500">{l.note}</p>
        </div>
      ))}
    </div>
  );
}
