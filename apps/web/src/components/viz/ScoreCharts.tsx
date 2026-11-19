"use client";

import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { fmtShare } from "@/lib/format";
import { BAND_COLOR, BANDS, BLOCKS, type LiveRow, type Weights } from "@/lib/ranking";
import { RISK_RAMP } from "../MapExplorer";

/** Anchura disponible de un contenedor, para dibujar el SVG a su tamaño real. */
export function useWidth<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  const [width, setWidth] = useState(0);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver(([e]) => setWidth(Math.round(e.contentRect.width)));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  return [ref, width] as const;
}

export function Tip({ x, y, width, children }: { x: number; y: number; width: number; children: ReactNode }) {
  const left = Math.max(4, Math.min(x - 100, width - 208));
  return (
    <div
      role="presentation"
      className="pointer-events-none absolute z-20 w-[204px] rounded-sm border border-noct-line bg-noct-bg px-2.5 py-1.5 text-xs leading-snug text-noct-ink2 shadow-[0_6px_20px_rgba(0,0,0,0.45)]"
      style={{ left, top: Math.max(0, y) }}
    >
      {children}
    </div>
  );
}

const BIN = 2; // puntos por columna

/** Cada punto es un municipio, apilado según su puntuación. Es la imagen de toda la región de un vistazo. */
export function ScoreConstellation({ rows, selected, onSelect }: { rows: LiveRow[]; selected: string | null; onSelect: (c: string) => void }) {
  const [ref, w] = useWidth<HTMLDivElement>();
  const [hover, setHover] = useState<{ r: LiveRow; x: number; y: number } | null>(null);
  const layout = useMemo(() => {
    if (!w) return null;
    const pad = 6;
    const binW = (w - pad * 2) / (100 / BIN);
    const dot = Math.max(2.4, Math.min(binW / 2 - 0.7, 8));
    const pitch = dot * 2 + 1.6;
    const bins = new Map<number, LiveRow[]>();
    for (const r of rows) {
      if (r.liveScore === null) continue;
      const b = Math.min(49, Math.floor(r.liveScore / BIN));
      bins.set(b, [...(bins.get(b) ?? []), r]);
    }
    const tallest = Math.max(1, ...[...bins.values()].map((v) => v.length));
    const plot = Math.max(120, tallest * pitch + 8);
    const dots = [...bins.entries()].flatMap(([b, list]) =>
      [...list]
        .sort((a, c) => (a.liveScore ?? 0) - (c.liveScore ?? 0))
        .map((r, i) => ({ r, x: pad + (b + 0.5) * binW, y: plot - dot - i * pitch, delay: b * 16 + i * 14 })),
    );
    return { pad, binW, dot, plot, dots, h: plot + 30 };
  }, [rows, w]);
  const x = (s: number) => (layout ? layout.pad + (s / BIN) * layout.binW : 0);
  return (
    <div ref={ref} className="relative w-full" onPointerLeave={() => setHover(null)}>
      {layout && (
        <svg width={w} height={layout.h} role="img" aria-label="Distribución de los 179 municipios por puntuación de atención. El detalle está en la lista del ranking.">
          {BANDS.map((b, i) => {
            const hi = i === 0 ? 100 : BANDS[i - 1].min;
            return (
              <g key={b.id}>
                <rect x={x(b.min) + 1} y={layout.plot + 5} width={Math.max(0, x(hi) - x(b.min) - 2)} height={3} fill={BAND_COLOR[b.id]} />
                <text x={(x(b.min) + x(hi)) / 2} y={layout.plot + 23} textAnchor="middle" fontSize="12" fill="#CFCBBD">{b.label}</text>
              </g>
            );
          })}
          {layout.dots.map(({ r, x: cx, y: cy, delay }) => (
            <circle
              key={r.ine_code}
              className="dot-in cursor-pointer"
              style={{ animationDelay: `${delay}ms` }}
              cx={cx}
              cy={cy}
              r={layout.dot}
              fill={BAND_COLOR[r.liveBand.id]}
              stroke={r.ine_code === selected ? "#F4EFE3" : "#0B1512"}
              strokeWidth={r.ine_code === selected ? 2 : 0.8}
              onPointerEnter={() => setHover({ r, x: cx, y: cy - 62 })}
              onClick={() => onSelect(r.ine_code)}
            />
          ))}
        </svg>
      )}
      {hover && (
        <Tip x={hover.x} y={hover.y} width={w}>
          <span className="block font-semibold text-noct-ink">{hover.r.name}</span>
          Puesto {hover.r.liveRank}, {hover.r.liveScore?.toFixed(1).replace(".", ",")} puntos
          <span className="block">{fmtShare(hover.r.high_share)} en riesgo alto o muy alto</span>
        </Tip>
      )}
    </div>
  );
}

/** Cuadrícula de municipios: cada celda es uno, y se puede abrir. */
export function Waffle({
  groups,
  onSelect,
}: {
  groups: { label: string; color?: string; hatch?: boolean; rows: { ine_code: string; name: string }[] }[];
  onSelect: (c: string) => void;
}) {
  return (
    <div>
      <div className="flex flex-wrap gap-[3px]">
        {groups.flatMap((g) =>
          g.rows.map((r) => (
            <button
              key={r.ine_code}
              type="button"
              title={`${r.name}: ${g.label}`}
              aria-label={`${r.name}: ${g.label}`}
              onClick={() => onSelect(r.ine_code)}
              className={`h-[15px] w-[15px] rounded-[2px] transition-transform hover:scale-125 ${g.hatch ? "hatch-dark border border-noct-ink3" : ""}`}
              style={g.hatch ? undefined : { background: g.color }}
            />
          )),
        )}
      </div>
      <ul className="mt-3 space-y-1 text-sm text-noct-ink2">
        {groups.map((g) => (
          <li key={g.label} className="flex items-center gap-2">
            <span className={`h-3 w-3 shrink-0 rounded-[2px] ${g.hatch ? "hatch-dark border border-noct-ink3" : ""}`} style={g.hatch ? undefined : { background: g.color }} aria-hidden />
            <span className="font-semibold tabular-nums text-noct-ink">{g.rows.length}</span> {g.label}
          </li>
        ))}
      </ul>
    </div>
  );
}

/** Reparto de la puntuación por bloques: la longitud total es la puntuación. */
export function ScoreStack({ row, weights, height = 8 }: { row: LiveRow; weights: Weights; height?: number }) {
  const total = BLOCKS.reduce((s, b) => s + (row.components[b.id] === null ? 0 : weights[b.id]), 0) || 1;
  return (
    <div className="flex w-full gap-[2px] bg-noct-raise" style={{ height }} aria-hidden>
      {BLOCKS.map((b) => {
        const pts = ((row.components[b.id] ?? 0) * weights[b.id] * 100) / total;
        return pts > 0 ? <span key={b.id} title={`${b.label}: ${pts.toFixed(1)} puntos`} style={{ width: `${pts}%`, background: b.color }} /> : null;
      })}
    </div>
  );
}

/** Indicador circular de la puntuación, con los cinco tramos marcados en el arco. */
export function ScoreGauge({ score, band }: { score: number | null; band: { id: string; label: string } }) {
  const R = 62;
  const C = 2 * Math.PI * R;
  const arc = 0.75;
  const f = (Math.max(0, Math.min(100, score ?? 0)) / 100) * arc;
  return (
    <div className="relative h-[150px] w-[150px] shrink-0">
      <svg viewBox="0 0 150 150" className="h-full w-full -rotate-[225deg]" aria-hidden>
        <circle cx="75" cy="75" r={R} fill="none" stroke="#182A22" strokeWidth="9" strokeDasharray={`${C * arc} ${C}`} />
        <circle cx="75" cy="75" r={R} fill="none" stroke={BAND_COLOR[band.id]} strokeWidth="9" strokeDasharray={`${C * f} ${C}`} style={{ transition: "stroke-dasharray .5s ease" }} />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center pt-1">
        <span className="font-display text-[46px] leading-none tabular-nums">{score === null ? "—" : Math.round(score)}</span>
        <span className="mt-1 text-xs text-noct-ink2">de 100</span>
      </div>
      <span className="absolute inset-x-0 bottom-1 text-center text-xs font-medium text-noct-ink">Atención {band.label.toLowerCase()}</span>
    </div>
  );
}

/** Reparto LITERAL del término entre las clases oficiales de riesgo (GEO-01), con su rampa oficial. */
export function RiskClassBar({ classes }: { classes: LiveRow["risk_classes"] }) {
  const color = (c: string | null) => (c && +c >= 1 && +c <= 5 ? RISK_RAMP[+c - 1] : "#5B665F");
  const shown = classes.filter((c) => c.share > 0);
  if (!shown.length) return <p className="text-sm text-noct-ink3">Clases oficiales no disponibles.</p>;
  return (
    <figure>
      <div className="flex h-3 w-full gap-[2px]" aria-hidden>
        {shown.map((c) => (
          <span key={c.label} title={`${c.label}: ${fmtShare(c.share)}`} style={{ width: `${c.share * 100}%`, background: color(c.code) }} />
        ))}
      </div>
      <figcaption className="mt-1.5 grid grid-cols-2 gap-x-3 text-xs leading-5 text-noct-ink2">
        {shown.map((c) => (
          <span key={c.label} className="flex items-center gap-1.5">
            <span className="h-2 w-2 shrink-0" style={{ background: color(c.code) }} aria-hidden />
            {c.label} <span className="ml-auto tabular-nums">{fmtShare(c.share)}</span>
          </span>
        ))}
      </figcaption>
    </figure>
  );
}
