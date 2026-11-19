"use client";

import { useEffect, useMemo, useState } from "react";
import { FireDangerMap } from "@/components/ProfilePanels";
import { NoctMap, type NoctMapValue } from "@/components/viz/NoctMap";
import { DayStrip, GustHeatmap, HourlyPanel, WindRose, type DayPoint, type HourPoint } from "@/components/viz/WeatherCharts";
import type { WeatherContext } from "@/lib/api-types";
import { fmtDate, fmtNumber } from "@/lib/format";
import { fmtDayHour, GUST_STEPS, RAIN_STEPS, type RankingResponse, type RegionalRow, type RegionalWeather } from "@/lib/ranking";
import { useApi } from "@/lib/useApi";

interface Hourly {
  status: "ok" | "stale" | "unavailable";
  municipality_name: string;
  issued_at: string | null;
  points: HourPoint[];
  daily: DayPoint[];
  summary: { gust_max_24h_kmh: number | null; gust_max_at: string | null; wind_dir_at_gust_max: string | null; precip_24h_mm: number | null; precip_total_mm: number | null; rh_min_24h_pct: number | null; temp_max_24h_c: number | null } | null;
  message: string | null;
  disclaimer: string;
  attribution: string;
  caveat: string;
  source_url: string;
}

type Metric = "gust" | "rain";
type Group = "top" | "attention";

const stepFor = <T extends { min: number }>(steps: T[], v: number) => steps.find((s) => v >= s.min) ?? steps[steps.length - 1];

function Record({ value, unit, label, place }: { value: number | null; unit: string; label: string; place?: string }) {
  return (
    <div className="border-t border-noct-line pt-3">
      <p className="font-display text-[46px] leading-none tabular-nums">{fmtNumber(value)}<span className="ml-1 font-sans text-base text-noct-ink3">{unit}</span></p>
      <p className="mt-1.5 text-sm text-noct-ink">{label}</p>
      {place && <p className="text-[13px] text-noct-ink3">{place}</p>}
    </div>
  );
}

export default function MeteoPage() {
  const regional = useApi<RegionalWeather>("/v1/weather/regional");
  const ranking = useApi<RankingResponse>("/v1/analysis/attention-ranking");
  const [picked, setPicked] = useState<string | null>(() => {
    if (typeof window === "undefined") return null;
    const h = window.location.hash.slice(1);
    return /^\d{5}$/.test(h) ? h : null;
  });
  const [metric, setMetric] = useState<Metric>("gust");
  const [group, setGroup] = useState<Group>("top");
  const r = regional.data;
  const reload = regional.reload;
  const warming = !!r && (r.status === "warming" || (r.refreshing && r.received < r.total));
  useEffect(() => {
    if (!warming) return;
    const t = setInterval(reload, 3000);
    return () => clearInterval(t);
  }, [warming, reload]);

  const okRows = useMemo(() => (r?.rows ?? []).filter((x) => x.status === "ok"), [r]);
  const topRanked = ranking.data?.rows[0]?.ine_code ?? null;
  const code = picked ?? topRanked;
  const hourly = useApi<Hourly>(code ? `/v1/weather/hourly?municipality_code=${code}` : null);
  const context = useApi<WeatherContext>("/v1/weather/context?municipality_code=28079");
  const h = hourly.data;

  const names = useMemo(() => [...(ranking.data?.rows ?? [])].sort((a, b) => a.name.localeCompare(b.name, "es")), [ranking.data]);
  const attention = useMemo(() => new Set((ranking.data?.rows ?? []).filter((x) => x.band.id === "very_high" || x.band.id === "high").map((x) => x.ine_code)), [ranking.data]);
  const heat = useMemo(() => {
    const base = group === "attention" ? okRows.filter((x) => attention.has(x.ine_code)) : okRows;
    const chosen = base.slice(0, 14);
    const sel = code ? okRows.find((x) => x.ine_code === code) : undefined;
    return sel && !chosen.includes(sel) ? [...chosen, sel] : chosen;
  }, [okRows, group, attention, code]);

  const peak = (pick: (x: RegionalRow) => number | null, dir: 1 | -1 = 1) =>
    okRows.reduce<RegionalRow | null>((best, x) => {
      const v = pick(x);
      if (v === null) return best;
      const b = best ? pick(best) : null;
      return b === null || v * dir > b * dir ? x : best;
    }, null);
  const gustTop = peak((x) => x.gust_max_24h_kmh);
  const rainTop = peak((x) => x.precip_24h_mm);
  const rhLow = peak((x) => x.rh_min_24h_pct, -1);

  const values = useMemo(() => new Map<string, NoctMapValue>(okRows.flatMap((x) => {
    const v = metric === "gust" ? x.gust_max_24h_kmh : x.precip_24h_mm;
    if (v === null) return [];
    const s = stepFor(metric === "gust" ? GUST_STEPS : RAIN_STEPS, v);
    return [[x.ine_code, { color: s.color, label: metric === "gust" ? `racha de ${fmtNumber(v)} km/h` : `${fmtNumber(v)} mm` }] as [string, NoctMapValue]];
  })), [okRows, metric]);

  const select = (c: string) => {
    setPicked(c);
    window.history.replaceState(null, "", `#${c}`);
  };
  const toggle = (on: boolean) => `rounded-full border px-3 py-1 text-[13px] ${on ? "border-brass bg-brass text-noct-bg" : "border-noct-line text-noct-ink2 hover:border-noct-ink3"}`;

  return (
    <div className="noct flex-1">
      <div className="mx-auto max-w-[1400px] px-4 md:px-8">
        <header className="border-b border-noct-line pb-8 pt-12 md:pt-16">
          <h1 className="text-[44px] leading-[1.02] md:text-[76px]">Viento y lluvia, hora a hora</h1>
          <p className="mt-4 max-w-2xl text-[17px] leading-relaxed text-noct-ink2">
            La predicción de AEMET para los 179 municipios de Madrid. Sirve para planificar trabajos preventivos; no indica peligro de incendio ni sustituye los avisos oficiales.
          </p>
          <p className="mt-3 text-sm text-noct-ink3" aria-live="polite">
            {!r ? "Conectando con AEMET…" : r.status === "unavailable" ? "AEMET no ha devuelto datos válidos." : `${r.coverage} de ${r.total || 179} municipios recibidos${r.issued_at_latest ? `, predicción elaborada el ${fmtDayHour(r.issued_at_latest)}` : ""}.`}
          </p>
          {regional.error != null && <p role="alert" className="mt-2 text-sm text-noct-ink">No se ha podido consultar la predicción regional.</p>}
          {okRows.length > 0 && (
            <div className="mt-8 grid gap-6 sm:grid-cols-3">
              <Record value={gustTop?.gust_max_24h_kmh ?? null} unit="km/h" label="Racha más fuerte en 24 horas" place={gustTop ? `${gustTop.name}${gustTop.gust_max_at ? `, ${fmtDayHour(gustTop.gust_max_at)}` : ""}` : undefined} />
              <Record value={rainTop?.precip_24h_mm ?? null} unit="mm" label="Mayor lluvia acumulada en 24 horas" place={rainTop?.precip_24h_mm ? rainTop.name : "Sin lluvia medible"} />
              <Record value={rhLow?.rh_min_24h_pct ?? null} unit="%" label="Humedad relativa más baja" place={rhLow?.name} />
            </div>
          )}
        </header>

        {okRows.length > 0 && (
          <section aria-labelledby="reg-h" className="grid gap-8 border-b border-noct-line py-10 xl:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
            <div>
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <h2 id="reg-h" className="text-3xl">La región hoy</h2>
                <div className="flex gap-1.5" role="group" aria-label="Variable del mapa">
                  <button type="button" aria-pressed={metric === "gust"} onClick={() => setMetric("gust")} className={toggle(metric === "gust")}>Rachas</button>
                  <button type="button" aria-pressed={metric === "rain"} onClick={() => setMetric("rain")} className={toggle(metric === "rain")}>Lluvia</button>
                </div>
              </div>
              <NoctMap
                ariaLabel={metric === "gust" ? "Mapa de racha máxima prevista en 24 horas" : "Mapa de lluvia prevista en 24 horas"}
                values={values} selected={code} onSelect={select} className="h-[460px]"
                legendTitle={metric === "gust" ? "Racha máxima, 24 h" : "Lluvia, 24 h"}
                legend={(metric === "gust" ? GUST_STEPS : RAIN_STEPS).map((s) => ({ color: s.color, label: s.label }))}
              />
            </div>
            <div className="min-w-0">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <h2 className="text-3xl">Las rachas, hora a hora</h2>
                <div className="flex gap-1.5" role="group" aria-label="Municipios del gráfico">
                  <button type="button" aria-pressed={group === "top"} onClick={() => setGroup("top")} className={toggle(group === "top")}>Rachas más fuertes</button>
                  <button type="button" aria-pressed={group === "attention"} onClick={() => setGroup("attention")} className={toggle(group === "attention")}>Atención alta</button>
                </div>
              </div>
              <GustHeatmap rows={heat} hours={r?.hours ?? []} selected={code} onSelect={select} />
              <p className="mt-2 text-xs text-noct-ink3">Color más claro, racha más fuerte, con una escala fija de 0 a 100 km/h. {r?.method}</p>
            </div>
          </section>
        )}

        <section aria-labelledby="mun-h" className="py-10">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <h2 id="mun-h" className="text-4xl">{h?.municipality_name ?? "Municipio"}</h2>
            <label className="min-w-60 text-sm text-noct-ink2">Elegir municipio
              <select value={code ?? ""} onChange={(e) => select(e.target.value)} className="mt-1 block w-full rounded-sm border border-noct-line bg-noct-surface px-2.5 py-[7px] text-noct-ink">
                {names.map((n) => <option key={n.ine_code} value={n.ine_code}>{n.name}</option>)}
              </select>
            </label>
          </div>
          {hourly.error != null && <p role="alert" className="mt-4 text-sm">No se ha podido consultar la predicción de este municipio.</p>}
          {!h && !hourly.error && <p role="status" className="mt-4 text-sm text-noct-ink2">Cargando la predicción…</p>}
          {h?.status === "unavailable" && <p className="hatch-dark mt-4 rounded-sm border border-noct-line p-4 text-sm">{h.message}. No se muestran valores de sustitución.</p>}
          {h && h.points.length > 0 && (
            <>
              {h.status === "stale" && <p className="mt-4 rounded-sm border border-[#EE8233] p-3 text-sm">{h.message}</p>}
              <div className="mt-6 grid gap-10 lg:grid-cols-[minmax(0,1fr)_270px]">
                <HourlyPanel points={h.points} />
                <div className="space-y-6">
                  <WindRose points={h.points} />
                  {h.summary && (
                    <dl className="grid grid-cols-2 gap-x-4 gap-y-3 border-t border-noct-line pt-4 text-sm">
                      <div><dt className="text-noct-ink3">Racha máx. 24 h</dt><dd className="font-display text-2xl tabular-nums">{fmtNumber(h.summary.gust_max_24h_kmh)} <span className="font-sans text-xs">km/h</span></dd></div>
                      <div><dt className="text-noct-ink3">Lluvia 24 h</dt><dd className="font-display text-2xl tabular-nums">{fmtNumber(h.summary.precip_24h_mm)} <span className="font-sans text-xs">mm</span></dd></div>
                      <div><dt className="text-noct-ink3">Humedad mín.</dt><dd className="font-display text-2xl tabular-nums">{fmtNumber(h.summary.rh_min_24h_pct)} <span className="font-sans text-xs">%</span></dd></div>
                      <div><dt className="text-noct-ink3">Temp. máx.</dt><dd className="font-display text-2xl tabular-nums">{fmtNumber(h.summary.temp_max_24h_c)} <span className="font-sans text-xs">°C</span></dd></div>
                    </dl>
                  )}
                </div>
              </div>
              <h3 className="mb-3 mt-10 text-lg">Próximos días</h3>
              <DayStrip days={h.daily} />
            </>
          )}
        </section>

        {context.data?.fire_danger?.value && (
          <section aria-labelledby="fd-h" className="border-t border-noct-line py-10">
            <h2 id="fd-h" className="text-3xl">Mapa oficial de peligro meteorológico</h2>
            <p className="mb-3 mt-1 max-w-2xl text-sm text-noct-ink2">Publicado por AEMET para toda la Península y Baleares. Se muestra tal cual: no se extrae ningún valor por municipio.</p>
            <div className="max-w-2xl"><FireDangerMap indicator={context.data.fire_danger} /></div>
          </section>
        )}

        <footer className="border-t border-noct-line py-5 text-xs leading-relaxed text-noct-ink3">
          <p>{h?.disclaimer ?? r?.disclaimer} {h?.caveat}</p>
          <p className="mt-1">{h?.attribution ?? r?.attribution}{h?.issued_at ? ` Elaborada el ${fmtDate(h.issued_at, true)}.` : ""}</p>
        </footer>
      </div>
    </div>
  );
}
