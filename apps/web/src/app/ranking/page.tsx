"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { CurrentRisk } from "@/components/viz/CurrentRisk";
import { NoctMap, type NoctMapValue } from "@/components/viz/NoctMap";
import { RiskClassBar, ScoreConstellation, ScoreGauge, ScoreStack, Waffle } from "@/components/viz/ScoreCharts";
import { fmtNumber, fmtShare } from "@/lib/format";
import { applyWeights, BAND_COLOR, BANDS, BLOCKS, type CurrentRiskResponse, type LiveRow, type RankingResponse, type RegionalWeather, type Weights } from "@/lib/ranking";
import { useApi } from "@/lib/useApi";

type Scope = "all" | "zar" | "outside" | "noplan";
type Sort = "score" | "today" | "risk" | "fires" | "burnt" | "gust";

const SCOPES: { id: Scope; label: string }[] = [
  { id: "all", label: "Los 179" },
  { id: "zar", label: "Zonas de Alto Riesgo" },
  { id: "outside", label: "Más de la mitad en riesgo, fuera de esas zonas" },
  { id: "noplan", label: "Obligados sin plan aprobado" },
];
const SORTS: { id: Sort; label: string }[] = [
  { id: "score", label: "Puntuación de atención" },
  { id: "today", label: "Riesgo estimado hoy" },
  { id: "risk", label: "Riesgo oficial alto y muy alto" },
  { id: "fires", label: "Siniestros 2015–2024" },
  { id: "burnt", label: "Hectáreas quemadas" },
  { id: "gust", label: "Racha prevista en 24 h" },
];

const fmtScore = (v: number | null) => (v === null ? "—" : v.toFixed(1).replace(".", ","));
const contours = [
  "M-40 210C120 120 250 250 420 170S720 60 900 150 1240 250 1500 120",
  "M-40 250C130 170 270 290 440 215S730 110 910 195 1250 290 1500 170",
  "M-40 292C140 220 280 330 455 262S740 165 920 242 1255 330 1500 222",
  "M-40 335C150 270 295 370 470 310S750 220 930 290 1260 370 1500 275",
  "M-40 170C110 75 240 205 405 125S710 10 890 105 1230 205 1500 70",
];

function State({ role = "status", children }: { role?: string; children: React.ReactNode }) {
  return <p role={role} className="py-10 text-sm text-noct-ink2">{children}</p>;
}

export default function RankingPage() {
  const api = useApi<RankingResponse>("/v1/analysis/attention-ranking");
  const meteo = useApi<RegionalWeather>("/v1/weather/regional");
  const risk = useApi<CurrentRiskResponse>("/v1/analysis/current-risk");
  const [weights, setWeights] = useState<Weights | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [scope, setScope] = useState<Scope>("all");
  const [sort, setSort] = useState<Sort>("score");
  const [q, setQ] = useState("");
  const [all, setAll] = useState(false);
  const d = api.data;
  const w = weights ?? d?.weights ?? null;
  const reloadMeteo = meteo.reload;
  const warming = !!meteo.data && (meteo.data.status === "warming" || (meteo.data.refreshing && meteo.data.received < meteo.data.total));
  useEffect(() => {
    if (!warming) return;
    const t = setInterval(reloadMeteo, 3000);
    return () => clearInterval(t);
  }, [warming, reloadMeteo]);

  const reloadRisk = risk.reload;
  const riskWarming = !!risk.data && (risk.data.status === "warming" || (risk.data.refreshing && risk.data.received < risk.data.total));
  useEffect(() => {
    if (!riskWarming) return;
    const t = setInterval(reloadRisk, 3000);
    return () => clearInterval(t);
  }, [riskWarming, reloadRisk]);

  const rows = useMemo(() => (d && w ? applyWeights(d.rows, w) : []), [d, w]);
  const riskBy = useMemo(() => new Map((risk.data?.rows ?? []).map((r) => [r.ine_code, r])), [risk.data]);
  const byCode = useMemo(() => new Map(rows.map((r) => [r.ine_code, r])), [rows]);
  const gust = useMemo(() => new Map((meteo.data?.rows ?? []).map((r) => [r.ine_code, r])), [meteo.data]);
  const current = (selected ? byCode.get(selected) : null) ?? rows[0] ?? null;

  const list = useMemo(() => {
    const needle = q.trim().toLocaleLowerCase("es");
    const outside = new Set(d?.gap.outside_zar_codes ?? []);
    const value = (r: LiveRow): number | null =>
      sort === "score" ? r.liveScore : sort === "today" ? (riskBy.get(r.ine_code)?.score ?? null) : sort === "risk" ? r.high_share : sort === "fires" ? r.fires_total : sort === "burnt" ? r.burnt_ha : (gust.get(r.ine_code)?.gust_max_24h_kmh ?? null);
    return rows
      .filter((r) => (scope === "zar" ? r.zar === true : scope === "outside" ? outside.has(r.ine_code) : scope === "noplan" ? r.plan_required === true && r.plan_approved !== true : true))
      .filter((r) => !needle || r.name.toLocaleLowerCase("es").includes(needle))
      .sort((a, b) => (value(b) ?? -1) - (value(a) ?? -1));
  }, [rows, scope, sort, q, d, gust, riskBy]);
  const visible = all ? list : list.slice(0, 20);

  const mapValues = useMemo(
    () => new Map<string, NoctMapValue>(rows.map((r) => [r.ine_code, { color: BAND_COLOR[r.liveBand.id], label: `${fmtScore(r.liveScore)} puntos, atención ${r.liveBand.label.toLowerCase()}` }])),
    [rows],
  );

  const gap = d?.gap;
  const required = rows.filter((r) => r.plan_required === true);
  const high = gap ? gap.outside_zar_codes.flatMap((c) => byCode.get(c) ?? []) : [];
  const inZar = rows.filter((r) => (r.high_share ?? 0) > 0.5 && r.zar === true);
  const weightSum = w ? Object.values(w).reduce((a, b) => a + b, 0) || 1 : 1;
  const currentMeteo = current ? gust.get(current.ine_code) : undefined;

  return (
    <div className="noct flex-1">
      <section className="relative overflow-hidden border-b border-noct-line">
        <svg className="pointer-events-none absolute inset-0 h-full w-full" viewBox="0 0 1440 420" preserveAspectRatio="xMidYMid slice" aria-hidden>
          {contours.map((p) => <path key={p} d={p} fill="none" stroke="#D8B76A" strokeOpacity="0.13" />)}
        </svg>
        <div className="relative mx-auto max-w-[1400px] px-4 pb-7 pt-12 md:px-8 md:pt-16">
          <h1 className="max-w-4xl text-[44px] leading-[1.02] md:text-[76px]">Dónde mirar primero</h1>
          <p className="mt-4 max-w-2xl text-[17px] leading-relaxed text-noct-ink2">
            Los 179 municipios de Madrid, ordenados por cuánta atención preventiva merecen según datos oficiales. Cada punto es un municipio: ábrelo para ver por qué está ahí.
          </p>
          <div className="mt-8">
            {api.error ? (
              <State role="alert">No se ha podido cargar el ranking. Vuelve a intentarlo en unos segundos.</State>
            ) : !d ? (
              <State>Calculando el ranking…</State>
            ) : (
              <ScoreConstellation rows={rows} selected={current?.ine_code ?? null} onSelect={setSelected} />
            )}
          </div>
        </div>
      </section>

      {d && gap && w && current && (
        <div className="mx-auto max-w-[1400px] px-4 md:px-8">
          <CurrentRisk data={risk.data} error={risk.error} selected={selected} onSelect={setSelected} />

          <section aria-labelledby="gap-h" className="grid gap-x-12 gap-y-8 border-b border-noct-line py-12 lg:grid-cols-[minmax(0,5fr)_minmax(0,6fr)_minmax(0,6fr)]">
            <div>
              <h2 id="gap-h" className="text-4xl leading-tight">Lo que aparece al cruzar los datos</h2>
              <p className="mt-3 text-sm leading-relaxed text-noct-ink2">
                Mapa oficial de riesgo, lista de Zonas de Alto Riesgo y planes municipales del Plan Anual 2026. No indica un error: la lista recoge el tercio de municipios con mayor valor en otro índice oficial.
              </p>
            </div>
            <div>
              <p className="font-display text-[64px] leading-none tabular-nums">{gap.high_majority_outside_zar}</p>
              <h3 className="mb-4 mt-2 text-lg leading-snug">
                municipios con más de la mitad del término en riesgo alto o muy alto están fuera de las Zonas de Alto Riesgo
              </h3>
              <Waffle onSelect={setSelected} groups={[
                { label: "fuera de esas zonas, sin obligación de plan municipal", color: "#EA3A54", rows: high },
                { label: "dentro de esas zonas", color: "#3B5148", rows: inZar },
              ]} />
              <p className="mt-2 text-xs text-noct-ink3">En esos {gap.high_majority_outside_zar} viven {fmtNumber(gap.outside_zar_population)} personas (padrón 2025, todo el municipio).</p>
            </div>
            <div>
              <p className="font-display text-[64px] leading-none tabular-nums">{gap.plan_required_approved}<span className="text-3xl text-noct-ink3"> de {gap.plan_required}</span></p>
              <h3 className="mb-4 mt-2 text-lg leading-snug">municipios obligados figuran con su plan de actuación aprobado en pleno</h3>
              <Waffle onSelect={setSelected} groups={[
                { label: "aprobado", color: "#3FC5CF", rows: required.filter((r) => r.plan_approved === true) },
                { label: "sin aprobar", color: "#EE8233", rows: required.filter((r) => r.plan_approved === false) },
                { label: "casilla vacía en el documento", hatch: true, rows: required.filter((r) => r.plan_approved === null) },
              ]} />
              <p className="mt-2 text-xs text-noct-ink3">Fuente: Plan Anual 2026, Anexos II y VI. Un plan aprobado después puede no figurar.</p>
            </div>
          </section>

          <section aria-labelledby="rank-h" className="grid gap-10 py-12 lg:grid-cols-[minmax(0,1fr)_440px]">
            <div className="min-w-0">
              <h2 id="rank-h" className="text-4xl">El ranking</h2>
              <div className="mt-5 flex flex-wrap items-end gap-3">
                <label className="min-w-44 flex-1 text-sm text-noct-ink2">Buscar municipio
                  <input value={q} onChange={(e) => setQ(e.target.value)} className="mt-1 block w-full rounded-sm border border-noct-line bg-noct-surface px-2.5 py-1.5 text-noct-ink" />
                </label>
                <label className="min-w-52 text-sm text-noct-ink2">Ordenar por
                  <select value={sort} onChange={(e) => setSort(e.target.value as Sort)} className="mt-1 block w-full rounded-sm border border-noct-line bg-noct-surface px-2.5 py-[7px] text-noct-ink">
                    {SORTS.map((s) => <option key={s.id} value={s.id}>{s.label}</option>)}
                  </select>
                </label>
              </div>
              <div className="mt-3 flex flex-wrap gap-1.5" role="group" aria-label="Filtrar municipios">
                {SCOPES.map((s) => (
                  <button key={s.id} type="button" aria-pressed={scope === s.id} onClick={() => setScope(s.id)}
                    className={`rounded-full border px-3 py-1 text-[13px] ${scope === s.id ? "border-brass bg-brass text-noct-bg" : "border-noct-line text-noct-ink2 hover:border-noct-ink3"}`}>{s.label}</button>
                ))}
              </div>

              <p className="mt-4 text-sm text-noct-ink3" aria-live="polite">{list.length} municipios</p>
              <ol className="mt-1 divide-y divide-noct-line border-y border-noct-line">
                {visible.map((r) => {
                  const on = r.ine_code === current.ine_code;
                  const lead = r.reasons.find((x) => x.block !== "territory" && x.block !== "context") ?? r.reasons[0];
                  return (
                    <li key={r.ine_code}>
                      <button type="button" aria-pressed={on} onClick={() => setSelected(r.ine_code)}
                        className={`grid w-full grid-cols-[2.25rem_minmax(0,1fr)_3.5rem] items-center gap-x-3 px-2 py-3 text-left hover:bg-noct-surface sm:grid-cols-[2.5rem_minmax(0,1fr)_minmax(0,11rem)_5rem_3.5rem] ${on ? "bg-noct-raise" : ""}`}>
                        <span className="font-display text-xl tabular-nums text-noct-ink3">{r.liveRank}</span>
                        <span className="min-w-0">
                          <span className="block truncate font-medium">{r.name}</span>
                          <span className="block truncate text-[13px] text-noct-ink3">{lead?.text}</span>
                        </span>
                        <span className="hidden sm:block"><ScoreStack row={r} weights={w} /></span>
                        <span className="hidden text-right text-[13px] tabular-nums text-noct-ink2 sm:block">{fmtShare(r.high_share)}<span className="block text-[11px] text-noct-ink3">riesgo oficial</span></span>
                        <span className="justify-self-end rounded-sm px-1.5 py-0.5 text-center font-semibold tabular-nums text-noct-bg" style={{ background: BAND_COLOR[r.liveBand.id] }} title={`Atención ${r.liveBand.label.toLowerCase()}`}>
                          {r.liveScore === null ? "—" : Math.round(r.liveScore)}
                        </span>
                      </button>
                    </li>
                  );
                })}
              </ol>
              {!list.length && <p className="py-6 text-sm text-noct-ink2">Ningún municipio cumple este filtro. Prueba con otro nombre o quita el filtro.</p>}
              {list.length > 20 && (
                <button type="button" onClick={() => setAll((v) => !v)} className="mt-4 rounded-sm border border-noct-ink3 px-3.5 py-1.5 text-sm hover:border-brass">{all ? "Ver solo los 20 primeros" : `Ver los ${list.length}`}</button>
              )}

              <ul className="mt-6 flex flex-wrap gap-x-4 gap-y-1 text-xs text-noct-ink2">
                {BLOCKS.map((b) => <li key={b.id} className="flex items-center gap-1.5"><span className="h-2 w-3" style={{ background: b.color }} aria-hidden />{b.label}</li>)}
              </ul>
              <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-noct-ink2">
                {BANDS.map((b) => <li key={b.id} className="flex items-center gap-1.5"><span className="h-2 w-3" style={{ background: BAND_COLOR[b.id] }} aria-hidden />{b.label}{b.min ? ` (${b.min} o más)` : " (menos de 20)"}</li>)}
              </ul>

              <details className="mt-8 border-t border-noct-line pt-4">
                <summary className="cursor-pointer font-medium">Cambiar los pesos de la puntuación</summary>
                <p className="mt-2 max-w-2xl text-sm text-noct-ink2">Los pesos son una decisión, no un dato. Muévelos y el ranking se recalcula al momento.</p>
                <div className="mt-4 grid gap-x-8 gap-y-4 sm:grid-cols-2">
                  {BLOCKS.map((b) => (
                    <label key={b.id} className="block text-sm">
                      <span className="flex justify-between"><span>{b.label}</span><span className="tabular-nums text-noct-ink2">{Math.round((w[b.id] / weightSum) * 100)} %</span></span>
                      <input type="range" min={0} max={60} step={5} value={w[b.id]} onChange={(e) => setWeights({ ...w, [b.id]: Number(e.target.value) })} className="mt-1 w-full" />
                      <span className="block text-xs text-noct-ink3">{b.help}</span>
                    </label>
                  ))}
                </div>
                <button type="button" onClick={() => setWeights(null)} className="mt-4 rounded-sm border border-noct-ink3 px-3 py-1 text-sm hover:border-brass">Restablecer pesos</button>
              </details>
              <details className="mt-4 border-t border-noct-line pt-4 text-sm text-noct-ink2">
                <summary className="cursor-pointer font-medium text-noct-ink">Ver método y fuentes</summary>
                <p className="mt-2 max-w-3xl leading-relaxed">{d.definition}</p>
                <p className="mt-2 max-w-3xl leading-relaxed">{d.caveat}</p>
                <p className="mt-2">Fuentes: {d.sources.join(", ")}. <Link href="/fuentes" className="text-brass underline underline-offset-2">Procedencia y licencias</Link></p>
              </details>
            </div>

            <aside aria-label={`Detalle de ${current.name}`} className="lg:sticky lg:top-3 lg:max-h-[calc(100vh-1.5rem)] lg:self-start lg:overflow-y-auto">
              <NoctMap ariaLabel="Mapa de municipios por puntuación de atención" values={mapValues} selected={current.ine_code} onSelect={setSelected} className="h-[300px]" legendTitle="Atención" legend={BANDS.map((b) => ({ color: BAND_COLOR[b.id], label: b.label }))} />
              <div className="mt-px bg-noct-surface p-5">
                <p className="text-sm text-noct-ink3">Puesto {current.liveRank} de {rows.length}</p>
                <h2 className="text-[32px] leading-tight">{current.name}</h2>
                <div className="mt-3 flex items-center gap-4">
                  <ScoreGauge score={current.liveScore} band={current.liveBand} />
                  <ul className="min-w-0 flex-1 space-y-1.5 text-xs">
                    {BLOCKS.map((b) => {
                      const v = current.components[b.id];
                      const total = BLOCKS.reduce((s, x) => s + (current.components[x.id] === null ? 0 : w[x.id]), 0) || 1;
                      return (
                        <li key={b.id}>
                          <span className="flex justify-between text-noct-ink2"><span>{b.label}</span><span className="tabular-nums">{v === null ? "—" : fmtScore((v * w[b.id] * 100) / total)}</span></span>
                          <span className="mt-0.5 block h-1 bg-noct-raise"><span className="block h-1" style={{ width: `${(v ?? 0) * 100}%`, background: b.color }} /></span>
                        </li>
                      );
                    })}
                  </ul>
                </div>
                <h3 className="mt-5 text-base">Por qué está aquí</h3>
                <ul className="mt-1.5 space-y-1.5 text-sm leading-snug text-noct-ink2">
                  {current.reasons.map((x) => (
                    <li key={x.text} className="flex gap-2"><span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: BLOCKS.find((b) => b.id === x.block)?.color ?? "#D8B76A" }} aria-hidden />{x.text}</li>
                  ))}
                </ul>
                <h3 className="mb-1.5 mt-5 text-base">Riesgo oficial del término</h3>
                <RiskClassBar classes={current.risk_classes} />
                {currentMeteo?.status === "ok" && (
                  <p className="mt-4 text-sm text-noct-ink2">
                    Previsión AEMET a 24 h: racha de {fmtNumber(currentMeteo.gust_max_24h_kmh)} km/h, {fmtNumber(currentMeteo.precip_24h_mm)} mm de lluvia y humedad mínima del {fmtNumber(currentMeteo.rh_min_24h_pct)} %.
                  </p>
                )}
                {current.stability_top20 !== null && current.stability_top20 > 0 && (
                  <p className="mt-3 text-xs leading-relaxed text-noct-ink3">Sigue entre los {d.top_n} primeros en el {Math.round(current.stability_top20 * 100)} % de las 81 combinaciones de pesos probadas.</p>
                )}
                <p className="mt-4 flex flex-wrap gap-x-4 gap-y-1 text-sm">
                  <Link href={`/meteo#${current.ine_code}`} className="text-brass underline underline-offset-4">Ver su meteorología</Link>
                  <Link href={`/#${current.ine_code}`} className="text-brass underline underline-offset-4">Abrir su ficha</Link>
                </p>
              </div>
            </aside>
          </section>

          <p className="border-t border-noct-line py-5 text-xs leading-relaxed text-noct-ink3">
            La puntuación y la estimación de hoy orientan la revisión preventiva. No son el riesgo oficial, ni una probabilidad de incendio, ni una alerta. Ante una emergencia, llama al 112.
          </p>
        </div>
      )}
    </div>
  );
}
