"use client";

import { useMemo, useState, type ReactNode } from "react";
import { fmtNumber } from "@/lib/format";
import { fmtDay, fmtDayHour, fmtHour, rampColor, WIND_MAX_KMH, WIND_RAMP, type RegionalRow } from "@/lib/ranking";
import { Tip, useWidth } from "./ScoreCharts";

export interface HourPoint {
  t: string;
  temp_c: number | null;
  rh_pct: number | null;
  wind_kmh: number | null;
  wind_dir: string | null;
  gust_kmh: number | null;
  precip_mm: number | null;
  precip_trace: boolean;
  snow_mm: number | null;
  sky: string | null;
}

export interface DayPoint {
  date: string;
  temp_max_c: number | null;
  temp_min_c: number | null;
  rh_min_pct: number | null;
  precip_prob_pct: number | null;
  wind_max_kmh: number | null;
  wind_dir: string | null;
  gust_max_kmh: number | null;
  sky: string | null;
}

const L = 38;
const R = 10;
const T = 8;
const B = 18;
const GUST = "#7AD7D3";
const WIND = "#F4EFE3";
const RAIN = "#5AA5EE";
const RH = "#B58CF0";
const TEMP = "#E8C547";

function pathOf(vals: (number | null)[], x: (i: number) => number, y: (v: number) => number) {
  let d = "";
  let pen = false;
  vals.forEach((v, i) => {
    if (v === null) {
      pen = false;
      return;
    }
    d += `${pen ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`;
    pen = true;
  });
  return d;
}

interface TrackApi {
  x: (i: number) => number;
  y: (v: number) => number;
  base: number;
  step: number;
}

function Track({
  title, note, points, width, height = 118, domain, ticks, unit, hover, children,
}: {
  title: string; note?: ReactNode; points: HourPoint[]; width: number; height?: number; domain: [number, number]; ticks: number[];
  unit: string; hover: number | null; children: (a: TrackApi) => ReactNode;
}) {
  const step = (width - L - R) / Math.max(1, points.length - 1);
  const x = (i: number) => L + i * step;
  const base = height - B;
  const y = (v: number) => base - ((v - domain[0]) / (domain[1] - domain[0] || 1)) * (base - T);
  const midnights = points.flatMap((p, i) => (fmtHour(p.t).startsWith("00") ? [i] : []));
  return (
    <figure>
      <figcaption className="mb-0.5 flex flex-wrap items-baseline justify-between gap-x-3 text-sm">
        <span className="font-medium text-noct-ink">{title} <span className="font-normal text-noct-ink3">({unit})</span></span>
        {note && <span className="text-xs text-noct-ink3">{note}</span>}
      </figcaption>
      <svg width={width} height={height} role="img" aria-label={`${title}, próximas ${points.length} horas. Valores en la tabla de datos.`}>
        {ticks.map((t) => (
          <g key={t}>
            <line x1={L} x2={width - R} y1={y(t)} y2={y(t)} stroke="#22332B" />
            <text x={L - 6} y={y(t) + 3.5} textAnchor="end" fontSize="11" fill="#A3A698">{fmtNumber(t)}</text>
          </g>
        ))}
        {midnights.map((i) => (
          <g key={i}>
            <line x1={x(i)} x2={x(i)} y1={T} y2={base} stroke="#3A4C42" strokeDasharray="2 3" />
            <text x={x(i) + 4} y={height - 5} fontSize="11" fill="#CFCBBD">{fmtDay(points[i].t)}</text>
          </g>
        ))}
        {children({ x, y, base, step })}
        {hover !== null && <line x1={x(hover)} x2={x(hover)} y1={T} y2={base} stroke="#D8B76A" />}
      </svg>
    </figure>
  );
}

/** Cuatro gráficos con el mismo eje horario y un cursor común. Cada uno tiene su propia escala (sin doble eje). */
export function HourlyPanel({ points }: { points: HourPoint[] }) {
  const [ref, w] = useWidth<HTMLDivElement>();
  const [hover, setHover] = useState<number | null>(null);
  const v = useMemo(() => {
    const nums = (k: keyof HourPoint) => points.map((p) => p[k] as number | null);
    const finite = (a: (number | null)[]) => a.filter((n): n is number => n !== null);
    const gust = nums("gust_kmh");
    const wind = nums("wind_kmh");
    const rain = nums("precip_mm");
    const temp = nums("temp_c");
    const windTop = Math.max(40, Math.ceil(Math.max(0, ...finite(gust), ...finite(wind)) / 20) * 20);
    const rainTop = Math.max(1, Math.ceil(Math.max(0, ...finite(rain))));
    const t = finite(temp);
    const tLo = t.length ? Math.floor(Math.min(...t) / 5) * 5 : 0;
    const tHi = t.length ? Math.max(tLo + 5, Math.ceil(Math.max(...t) / 5) * 5) : 30;
    return { gust, wind, rain, temp, rh: nums("rh_pct"), windTop, rainTop, tLo, tHi };
  }, [points]);
  const p = hover === null ? null : points[hover];
  const onMove = (e: React.PointerEvent<HTMLDivElement>) => {
    const box = e.currentTarget.getBoundingClientRect();
    const i = Math.round(((e.clientX - box.left - L) / (w - L - R)) * (points.length - 1));
    setHover(Math.max(0, Math.min(points.length - 1, i)));
  };
  return (
    <div>
      <p className="mb-3 min-h-10 border-l-2 border-brass pl-3 text-sm leading-5 text-noct-ink2" aria-live="off">
        {p ? (
          <>
            <span className="font-medium text-noct-ink">{fmtDayHour(p.t)}.</span> Racha {fmtNumber(p.gust_kmh)} km/h, viento {fmtNumber(p.wind_kmh)} km/h
            {p.wind_dir ? ` del ${p.wind_dir}` : ""}, lluvia {p.precip_trace ? "inapreciable" : `${fmtNumber(p.precip_mm)} mm`}, humedad {fmtNumber(p.rh_pct)} %, {fmtNumber(p.temp_c)} °C
            {p.sky ? `, ${p.sky.toLowerCase()}` : ""}.
          </>
        ) : (
          "Pasa el cursor o toca los gráficos para leer cada hora."
        )}
      </p>
      <div ref={ref} className="space-y-4" onPointerMove={onMove} onPointerLeave={() => setHover(null)}>
        {w > 0 && (
          <>
            <Track
              title="Rachas y viento medio" unit="km/h" points={points} width={w} height={150} hover={hover} domain={[0, v.windTop]} ticks={[0, v.windTop / 2, v.windTop]}
              note={
                <span className="flex gap-3">
                  <span className="flex items-center gap-1"><span className="h-0.5 w-3" style={{ background: GUST }} />Racha máxima</span>
                  <span className="flex items-center gap-1"><span className="h-px w-3 border-t border-dashed" style={{ borderColor: WIND }} />Viento medio</span>
                </span>
              }
            >
              {({ x, y, base }) => {
                const line = pathOf(v.gust, x, y);
                const idx = v.gust.flatMap((g, i) => (g === null ? [] : [i]));
                return (
                  <>
                    <defs>
                      <linearGradient id="gust-fill" x1="0" x2="0" y1="0" y2="1">
                        <stop offset="0" stopColor={GUST} stopOpacity="0.38" />
                        <stop offset="1" stopColor={GUST} stopOpacity="0.02" />
                      </linearGradient>
                    </defs>
                    {idx.length > 1 && <path d={`${line}L${x(idx[idx.length - 1])},${base}L${x(idx[0])},${base}Z`} fill="url(#gust-fill)" />}
                    <path d={line} fill="none" stroke={GUST} strokeWidth="2" strokeLinejoin="round" />
                    <path d={pathOf(v.wind, x, y)} fill="none" stroke={WIND} strokeWidth="1.3" strokeDasharray="3 3" />
                  </>
                );
              }}
            </Track>
            <Track title="Precipitación por hora" unit="mm" points={points} width={w} hover={hover} domain={[0, v.rainTop]} ticks={[0, v.rainTop]} note="Un punto indica lluvia inapreciable">
              {({ x, y, base, step }) =>
                points.map((pt, i) =>
                  pt.precip_trace ? (
                    <circle key={pt.t} cx={x(i)} cy={base - 3} r="1.8" fill={RAIN} />
                  ) : pt.precip_mm ? (
                    <rect key={pt.t} x={x(i) - Math.max(1, step * 0.36)} y={y(pt.precip_mm)} width={Math.max(2, step * 0.72)} height={Math.max(1, base - y(pt.precip_mm))} rx="1" fill={RAIN} />
                  ) : null,
                )
              }
            </Track>
            <Track title="Humedad relativa" unit="%" points={points} width={w} hover={hover} domain={[0, 100]} ticks={[0, 50, 100]}>
              {({ x, y }) => <path d={pathOf(v.rh, x, y)} fill="none" stroke={RH} strokeWidth="2" strokeLinejoin="round" />}
            </Track>
            <Track title="Temperatura" unit="°C" points={points} width={w} hover={hover} domain={[v.tLo, v.tHi]} ticks={[v.tLo, v.tHi]}>
              {({ x, y }) => <path d={pathOf(v.temp, x, y)} fill="none" stroke={TEMP} strokeWidth="2" strokeLinejoin="round" />}
            </Track>
          </>
        )}
      </div>
      <details className="mt-3 text-sm text-noct-ink2">
        <summary className="cursor-pointer">Ver la tabla de datos horarios</summary>
        <div className="mt-2 max-h-72 overflow-auto" tabIndex={0} role="region" aria-label="Tabla de datos horarios">
          <table className="w-full min-w-[34rem] text-xs tabular-nums">
            <thead className="sticky top-0 bg-noct-surface text-left text-noct-ink3">
              <tr><th className="py-1 font-medium">Hora</th><th className="font-medium">Racha km/h</th><th className="font-medium">Viento km/h</th><th className="font-medium">Dirección</th><th className="font-medium">Lluvia mm</th><th className="font-medium">Humedad %</th><th className="font-medium">°C</th></tr>
            </thead>
            <tbody>
              {points.map((q) => (
                <tr key={q.t} className="border-t border-noct-line">
                  <td className="py-0.5">{fmtDayHour(q.t)}</td><td>{fmtNumber(q.gust_kmh)}</td><td>{fmtNumber(q.wind_kmh)}</td><td>{q.wind_dir ?? "—"}</td>
                  <td>{q.precip_trace ? "Ip" : fmtNumber(q.precip_mm)}</td><td>{fmtNumber(q.rh_pct)}</td><td>{fmtNumber(q.temp_c)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}

const DIRS = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"];

/** Rosa de vientos de las horas previstas: longitud = horas, color = racha media de esas horas. */
export function WindRose({ points }: { points: HourPoint[] }) {
  const size = 230;
  const c = size / 2;
  const inner = 16;
  const outer = c - 22;
  const data = DIRS.map((d) => {
    const hrs = points.filter((p) => p.wind_dir === d);
    const g = hrs.map((p) => p.gust_kmh).filter((n): n is number => n !== null);
    return { d, hours: hrs.length, gust: g.length ? g.reduce((a, b) => a + b, 0) / g.length : null };
  });
  const calm = points.filter((p) => p.wind_dir === "C").length;
  const max = Math.max(1, ...data.map((x) => x.hours));
  const pt = (r: number, deg: number) => {
    const a = ((deg - 90) * Math.PI) / 180;
    return `${(c + r * Math.cos(a)).toFixed(1)},${(c + r * Math.sin(a)).toFixed(1)}`;
  };
  const summary = data.filter((x) => x.hours).sort((a, b) => b.hours - a.hours)[0];
  return (
    <figure>
      <figcaption className="mb-1 text-sm font-medium text-noct-ink">De dónde vendrá el viento</figcaption>
      <svg viewBox={`0 0 ${size} ${size}`} className="mx-auto w-full max-w-[250px]" role="img" aria-label={summary ? `Dirección más frecuente: ${summary.d}, ${summary.hours} horas.` : "Sin datos de dirección."}>
        {[1 / 3, 2 / 3, 1].map((f) => <circle key={f} cx={c} cy={c} r={inner + (outer - inner) * f} fill="none" stroke="#22332B" />)}
        {data.map((x, i) => {
          const deg = i * 45;
          const r = inner + (x.hours / max) * (outer - inner);
          const lab = pt(outer + 12, deg).split(",");
          return (
            <g key={x.d}>
              {x.hours > 0 && (
                <path d={`M${pt(inner, deg - 17)}L${pt(r, deg - 17)}A${r},${r} 0 0 1 ${pt(r, deg + 17)}L${pt(inner, deg + 17)}A${inner},${inner} 0 0 0 ${pt(inner, deg - 17)}Z`} fill={rampColor(WIND_RAMP, 0.25 + (x.gust ?? 0) / WIND_MAX_KMH)}>
                  <title>{`${x.d}: ${x.hours} h, racha media ${fmtNumber(x.gust)} km/h`}</title>
                </path>
              )}
              <text x={lab[0]} y={+lab[1] + 4} textAnchor="middle" fontSize="11.5" fill="#CFCBBD">{x.d}</text>
            </g>
          );
        })}
      </svg>
      <p className="text-center text-xs text-noct-ink3">Longitud: horas previstas. Color: racha media.{calm ? ` ${calm} h en calma.` : ""}</p>
    </figure>
  );
}

/** Próximos días: temperaturas, probabilidad de lluvia y racha máxima publicadas por AEMET. */
export function DayStrip({ days }: { days: DayPoint[] }) {
  if (!days.length) return <p className="text-sm text-noct-ink3">Predicción diaria no disponible.</p>;
  const label = new Intl.DateTimeFormat("es-ES", { weekday: "short", day: "numeric", timeZone: "UTC" });
  return (
    <div className="overflow-x-auto" tabIndex={0} role="region" aria-label="Predicción de los próximos días">
      <ul className="grid min-w-[36rem] gap-px bg-noct-line" style={{ gridTemplateColumns: `repeat(${days.length}, minmax(0, 1fr))` }}>
        {days.map((d) => (
          <li key={d.date} className="space-y-2 bg-noct-surface p-3 text-sm">
            <p className="text-noct-ink2">{label.format(new Date(`${d.date}T12:00:00Z`))}</p>
            <p className="font-display text-2xl leading-none tabular-nums">{fmtNumber(d.temp_max_c)}°<span className="ml-1 text-base text-noct-ink3">{fmtNumber(d.temp_min_c)}°</span></p>
            <div>
              <div className="flex justify-between text-xs text-noct-ink3"><span>Lluvia</span><span className="tabular-nums">{d.precip_prob_pct === null ? "—" : `${fmtNumber(d.precip_prob_pct)} %`}</span></div>
              <div className="mt-0.5 h-1 bg-noct-raise"><div className="h-1" style={{ width: `${d.precip_prob_pct ?? 0}%`, background: RAIN }} /></div>
            </div>
            <p className="text-xs text-noct-ink3">Racha <span className="tabular-nums text-noct-ink">{d.gust_max_kmh === null ? "—" : `${fmtNumber(d.gust_max_kmh)} km/h`}</span></p>
          </li>
        ))}
      </ul>
    </div>
  );
}

/** Mapa de calor: municipios por horas, con la misma escala fija de racha todos los días. */
export function GustHeatmap({ rows, hours, selected, onSelect }: { rows: RegionalRow[]; hours: string[]; selected: string | null; onSelect: (c: string) => void }) {
  const [ref, w] = useWidth<HTMLDivElement>();
  const [hover, setHover] = useState<{ x: number; y: number; r: RegionalRow; i: number } | null>(null);
  const nameW = 158;
  const width = Math.max(w, 620);
  const cell = (width - nameW - 44) / hours.length;
  const rowH = 23;
  const top = 22;
  return (
    <div ref={ref} className="relative overflow-x-auto" tabIndex={0} role="region" aria-label="Rachas previstas por municipio y hora" onPointerLeave={() => setHover(null)}>
      {w > 0 && (
        <svg width={width} height={top + rows.length * rowH + 2} role="img" aria-label={`Rachas previstas por hora en ${rows.length} municipios, ordenados de mayor a menor racha máxima en 24 horas.`}>
          {hours.map((h, i) => (fmtHour(h).startsWith("00") || i === 0) && (
            <text key={h} x={nameW + i * cell} y={13} fontSize="11.5" fill="#CFCBBD">{i === 0 ? "Ahora" : fmtDay(h)}</text>
          ))}
          <text x={width - 2} y={13} textAnchor="end" fontSize="11" fill="#A3A698">máx. 24 h</text>
          {rows.map((r, ri) => {
            const y = top + ri * rowH;
            const on = r.ine_code === selected;
            return (
              <g key={r.ine_code} className="cursor-pointer" onClick={() => onSelect(r.ine_code)}>
                <text x={nameW - 8} y={y + 15} textAnchor="end" fontSize="12.5" fill={on ? "#F4EFE3" : "#CFCBBD"} fontWeight={on ? 600 : 400}>
                  {r.name.length > 22 ? `${r.name.slice(0, 21)}…` : r.name}
                </text>
                {r.gust_hourly_kmh.map((g, i) => (
                  <rect
                    key={hours[i]} x={nameW + i * cell} y={y + 1} width={Math.max(1, cell - 1)} height={rowH - 3}
                    fill={g === null ? "#16231D" : rampColor(WIND_RAMP, g / WIND_MAX_KMH)}
                    onPointerEnter={() => setHover({ x: nameW + i * cell, y: y - 54, r, i })}
                  />
                ))}
                <text x={width - 2} y={y + 15} textAnchor="end" fontSize="12.5" fill="#F4EFE3" className="tabular-nums">{fmtNumber(r.gust_max_24h_kmh)}</text>
                {on && <rect x={nameW - 1} y={y} width={hours.length * cell + 1} height={rowH - 1} fill="none" stroke="#D8B76A" />}
              </g>
            );
          })}
        </svg>
      )}
      {hover && (
        <Tip x={hover.x} y={hover.y} width={width}>
          <span className="block font-semibold text-noct-ink">{hover.r.name}</span>
          {fmtDayHour(hours[hover.i])}: racha {hover.r.gust_hourly_kmh[hover.i] === null ? "sin dato" : `${fmtNumber(hover.r.gust_hourly_kmh[hover.i])} km/h`}
        </Tip>
      )}
    </div>
  );
}
