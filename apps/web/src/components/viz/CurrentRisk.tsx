"use client";

import { useMemo, useState } from "react";
import { fmtNumber, fmtShare } from "@/lib/format";
import { BAND_COLOR, fmtDayHour, type CurrentRiskResponse, type CurrentRiskRow } from "@/lib/ranking";
import { NoctMap, type NoctMapValue } from "./NoctMap";
import { Tip, useWidth } from "./ScoreCharts";

const TERRITORY = "#D9663F";
const WEATHER = "#7AD7D3";
const fmt1 = (v: number | null) => (v === null ? "—" : v.toFixed(1).replace(".", ","));

function Factor({ label, value, text, color }: { label: string; value: number; text: string; color: string }) {
  return (
    <span className="block">
      <span className="flex justify-between gap-2 text-[11px] text-noct-ink3"><span>{label}</span><span className="tabular-nums text-noct-ink2">{text}</span></span>
      <span className="mt-0.5 block h-1 bg-noct-raise"><span className="block h-1" style={{ width: `${Math.min(100, value * 100)}%`, background: color }} /></span>
    </span>
  );
}

/** Evolución horaria del índice de Fosberg, siempre en su escala completa de 0 a 100. */
function FosbergTrack({ hours, values, name }: { hours: string[]; values: (number | null)[]; name: string }) {
  const [ref, w] = useWidth<HTMLDivElement>();
  const [hover, setHover] = useState<number | null>(null);
  const h = 118;
  const pad = { l: 26, r: 6, t: 8, b: 20 };
  const plotW = Math.max(1, w - pad.l - pad.r);
  const x = (i: number) => pad.l + (i / Math.max(1, hours.length - 1)) * plotW;
  const y = (v: number) => pad.t + (1 - v / 100) * (h - pad.t - pad.b);
  const pts = values.flatMap((v, i) => (v === null ? [] : [{ i, v }]));
  const line = pts.map((p, n) => `${n ? "L" : "M"}${x(p.i).toFixed(1)} ${y(p.v).toFixed(1)}`).join("");
  const area = pts.length ? `${line}L${x(pts[pts.length - 1].i).toFixed(1)} ${y(0)}L${x(pts[0].i).toFixed(1)} ${y(0)}Z` : "";
  const active = hover === null ? null : pts.reduce<{ i: number; v: number } | null>((b, p) => (!b || Math.abs(p.i - hover) < Math.abs(b.i - hover) ? p : b), null);
  return (
    <div
      ref={ref}
      className="relative"
      onPointerLeave={() => setHover(null)}
      onPointerMove={(e) => {
        const box = e.currentTarget.getBoundingClientRect();
        setHover(Math.round(((e.clientX - box.left - pad.l) / plotW) * (hours.length - 1)));
      }}
    >
      {w > 0 && (
        <svg width={w} height={h} role="img" aria-label={`Índice de Fosberg previsto hora a hora en ${name}, en escala de 0 a 100.`}>
          {[0, 50, 100].map((t) => (
            <g key={t}>
              <line x1={pad.l} x2={w - pad.r} y1={y(t)} y2={y(t)} stroke="#223A30" />
              <text x={pad.l - 5} y={y(t) + 4} textAnchor="end" fontSize="11" fill="#A9B0A4">{t}</text>
            </g>
          ))}
          {[0, 24].filter((i) => i < hours.length).map((i) => (
            <text key={i} x={x(i)} y={h - 5} textAnchor={i ? "middle" : "start"} fontSize="11" fill="#A9B0A4">{fmtDayHour(hours[i])}</text>
          ))}
          {area && <path d={area} fill={WEATHER} fillOpacity="0.14" />}
          {line && <path d={line} fill="none" stroke={WEATHER} strokeWidth="2" strokeLinejoin="round" />}
          {active && <circle cx={x(active.i)} cy={y(active.v)} r="4" fill={WEATHER} stroke="#0B1512" strokeWidth="2" />}
        </svg>
      )}
      {active && (
        <Tip x={x(active.i)} y={0} width={w}>
          <span className="block font-semibold text-noct-ink">{fmt1(active.v)} sobre 100</span>
          {fmtDayHour(hours[active.i])}
        </Tip>
      )}
    </div>
  );
}

export function CurrentRisk({ data, error, selected, onSelect }: { data: CurrentRiskResponse | null; error: unknown; selected: string | null; onSelect: (code: string) => void }) {
  const scored = useMemo(() => (data?.rows ?? []).filter((r) => r.score !== null), [data]);
  const mapValues = useMemo(
    () => new Map<string, NoctMapValue>(scored.map((r) => [r.ine_code, { color: BAND_COLOR[r.band.id], label: `${fmt1(r.score)} puntos, riesgo estimado ${r.band.label.toLowerCase()}` }])),
    [scored],
  );
  const current: CurrentRiskRow | null = scored.find((r) => r.ine_code === selected) ?? scored[0] ?? null;
  const counts = (data?.bands ?? []).map((b) => ({ ...b, n: scored.filter((r) => r.band.id === b.id).length }));
  const top = counts.find((b) => b.n > 0);

  return (
    <section aria-labelledby="now-h" className="border-b border-noct-line py-12">
      <div className="grid gap-x-12 gap-y-3 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)] lg:items-end">
        <div>
          <h2 id="now-h" className="text-4xl leading-tight md:text-5xl">Riesgo estimado hoy</h2>
          <p className="mt-3 max-w-2xl text-[15px] leading-relaxed text-noct-ink2">
            Dónde coinciden territorio de riesgo oficial alto y el tiempo más favorable al fuego previsto en las próximas 24 horas. Es una estimación de ESCUDO, no un dato oficial.
          </p>
        </div>
        {data?.issued_at_latest && <p className="text-sm text-noct-ink3 lg:text-right">Predicción AEMET elaborada el {fmtDayHour(data.issued_at_latest)}. {data.coverage} de {data.rows.length} municipios calculados.</p>}
      </div>

      {error ? (
        <p role="alert" className="py-8 text-sm text-noct-ink2">No se ha podido calcular la estimación. Vuelve a intentarlo en unos segundos.</p>
      ) : !data || (data.status === "warming" && !scored.length) ? (
        <p role="status" className="py-8 text-sm text-noct-ink2">Recibiendo la predicción de AEMET{data ? `: ${data.received} de ${data.total || data.rows.length} municipios` : ""}…</p>
      ) : !current ? (
        <p role="status" className="py-8 text-sm text-noct-ink2">Estimación no disponible: no hay predicción vigente de AEMET y no se muestran valores de sustitución.</p>
      ) : (
        <>
          <div className="mt-7">
            <div className="flex h-3 gap-[2px]" aria-hidden>
              {counts.filter((b) => b.n).map((b) => <span key={b.id} style={{ flexGrow: b.n, background: BAND_COLOR[b.id] }} />)}
            </div>
            <ul className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-sm text-noct-ink2">
              {counts.map((b) => (
                <li key={b.id} className="flex items-center gap-1.5">
                  <span className="h-2.5 w-2.5" style={{ background: BAND_COLOR[b.id] }} aria-hidden />
                  {b.label} <span className="font-semibold tabular-nums text-noct-ink">{b.n}</span>
                </li>
              ))}
            </ul>
            {top && <p className="mt-3 text-sm text-noct-ink2">El nivel más alto que se alcanza hoy es <strong className="font-semibold text-noct-ink">{top.label.toLowerCase()}</strong>.</p>}
          </div>

          <div className="mt-8 grid gap-10 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
            <div className="min-w-0">
              <h3 className="text-xl">Los diez valores más altos</h3>
              <ol className="mt-3 divide-y divide-noct-line border-y border-noct-line">
                {scored.slice(0, 10).map((r) => (
                  <li key={r.ine_code}>
                    <button type="button" aria-pressed={r.ine_code === current.ine_code} onClick={() => onSelect(r.ine_code)}
                      className={`grid w-full grid-cols-[1.75rem_minmax(0,1fr)_3rem] items-center gap-x-3 px-2 py-2.5 text-left hover:bg-noct-surface sm:grid-cols-[2rem_minmax(0,1fr)_minmax(0,9rem)_minmax(0,9rem)_3rem] ${r.ine_code === current.ine_code ? "bg-noct-raise" : ""}`}>
                      <span className="font-display text-lg tabular-nums text-noct-ink3">{r.rank}</span>
                      <span className="truncate font-medium">{r.name}</span>
                      <span className="hidden sm:block"><Factor label="Territorio" value={r.high_share ?? 0} text={fmtShare(r.high_share)} color={TERRITORY} /></span>
                      <span className="hidden sm:block"><Factor label="Meteorología" value={(r.ffwi_max_24h ?? 0) / 100} text={fmt1(r.ffwi_max_24h)} color={WEATHER} /></span>
                      <span className="justify-self-end rounded-sm px-1.5 py-0.5 text-center font-semibold tabular-nums text-noct-bg" style={{ background: BAND_COLOR[r.band.id] }} title={`Riesgo estimado ${r.band.label.toLowerCase()}`}>{Math.round(r.score ?? 0)}</span>
                    </button>
                  </li>
                ))}
              </ol>
            </div>

            <div className="min-w-0">
              <NoctMap ariaLabel="Mapa de municipios por riesgo estimado hoy" values={mapValues} selected={current.ine_code} onSelect={onSelect} className="h-[300px]" legendTitle="Riesgo estimado" legend={data.bands.map((b) => ({ color: BAND_COLOR[b.id], label: b.label }))} />
              <div className="bg-noct-surface p-5">
                <div className="flex items-baseline justify-between gap-3">
                  <h3 className="truncate text-2xl">{current.name}</h3>
                  <span className="shrink-0 text-sm text-noct-ink2"><span className="font-display text-3xl tabular-nums text-noct-ink">{Math.round(current.score ?? 0)}</span> {current.band.label.toLowerCase()}</span>
                </div>
                <h4 className="mt-3 text-sm font-medium">Por qué hoy</h4>
                <ul className="mt-1 space-y-1 text-sm leading-snug text-noct-ink2">
                  {current.reasons.map((x) => <li key={x}>{x}.</li>)}
                  <li>{current.limiting === "weather" ? "Lo que más limita el valor hoy es el tiempo previsto." : "Lo que más limita el valor hoy es la parte del término en riesgo alto."}</li>
                </ul>
                <h4 className="mb-1 mt-4 text-sm font-medium">Índice de Fosberg previsto</h4>
                <FosbergTrack hours={data.hours} values={current.ffwi_hourly} name={current.name} />
                {current.rain_from && <p className="mt-1 text-xs text-noct-ink3">La línea termina al empezar la lluvia prevista.</p>}
                {current.gust_max_24h_kmh !== null && <p className="mt-1 text-xs text-noct-ink3">Racha máxima prevista en 24 horas: {fmtNumber(current.gust_max_24h_kmh)} km/h. El índice usa el viento medio.</p>}
              </div>
            </div>
          </div>

          <details className="mt-6 text-sm text-noct-ink2">
            <summary className="cursor-pointer font-medium text-noct-ink">Ver método y fuentes de la estimación</summary>
            <p className="mt-2 max-w-3xl leading-relaxed">{data.definition}</p>
            <p className="mt-2 max-w-3xl leading-relaxed">{data.caveat}</p>
            <p className="mt-2 max-w-3xl leading-relaxed">{data.reference} {data.attribution}</p>
          </details>
        </>
      )}
    </section>
  );
}
