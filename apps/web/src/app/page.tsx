"use client";

import { useCallback, useMemo, useState } from "react";
import { CHOROPLETH_OPTIONS, MapExplorer, type ChoroplethKey, type LegendSpec } from "@/components/MapExplorer";
import { MapLegend } from "@/components/MapLegend";
import { MunicipalityProfileView } from "@/components/ProfilePanels";
import { Empty, ErrorState, Loading } from "@/components/States";
import { StatusBadge } from "@/components/StatusBadge";
import type { Layer, MunicipalityProfile, MunicipalitySummary } from "@/lib/api-types";
import { fmtIndicatorValue } from "@/lib/format";
import { useApi } from "@/lib/useApi";
import { useHash } from "@/lib/browser-store";

export default function ExplorerPage() {
  const [choropleth, setChoropleth] = useState<ChoroplethKey>("density");
  const [q, setQ] = useState("");
  const [minD, setMinD] = useState("");
  const [maxD, setMaxD] = useState("");
  const [picked, setPicked] = useState<string | null>(null);
  const hash = useHash();
  const selected = picked ?? (/^\d{5}$/.test(hash) ? hash : null);
  const [activeOfficial, setActiveOfficial] = useState<string | null>(null);
  const [showBurnt, setShowBurnt] = useState(false);
  const [legend, setLegend] = useState<LegendSpec[]>([]);
  const [mapError, setMapError] = useState<string | null>(null);

  const params = new URLSearchParams();
  if (q.trim()) params.set("q", q.trim());
  if (minD) params.set("min_density", minD);
  if (maxD) params.set("max_density", maxD);
  params.set("sort", "name");
  const list = useApi<MunicipalitySummary[]>(`/v1/municipalities?${params.toString()}`);
  const all = useApi<MunicipalitySummary[]>("/v1/municipalities?sort=name");
  const layers = useApi<Layer[]>("/v1/layers");
  const profile = useApi<MunicipalityProfile>(selected ? `/v1/municipalities/${selected}/profile` : null);

  const filtering = !!(q.trim() || minD || maxD);
  const highlight = useMemo(
    () => (filtering && list.data ? new Set(list.data.map((m) => m.ine_code)) : null),
    [filtering, list.data],
  );
  const officialLayers = useMemo(
    () => (layers.data ?? []).filter((l) => l.name !== "municipalities" && !l.overlay),
    [layers.data],
  );
  const burnt = (layers.data ?? []).find((l) => l.name === "burnt_areas");

  const select = useCallback((ine: string) => {
    setPicked(ine);
    history.replaceState(null, "", `#${ine}`);
  }, []);

  const closeProfile = () => {
    setPicked(null);
    history.replaceState(null, "", " ");
    window.dispatchEvent(new HashChangeEvent("hashchange"));
  };

  const clearFilter = () => {
    setQ("");
    setMinD("");
    setMaxD("");
  };

  return (
    <div className="flex flex-1 flex-col lg:flex-row">
      <aside className="order-2 w-full shrink-0 overflow-y-auto border-r border-line bg-white lg:order-1 lg:h-[calc(100vh-5.75rem)] lg:w-[400px]">
        <div className="border-b border-line px-4 pb-4 pt-5">
          <h1 className="font-cond text-2xl font-bold leading-tight text-ink">Explorador regional</h1>
          <p className="mt-1 text-sm leading-relaxed text-ink-600">
            Los municipios de la Comunidad de Madrid con datos de su Portal de Datos Abiertos y la cartografía oficial de
            incendios. Pulsa un municipio en el mapa o en la lista para abrir su ficha.
          </p>
        </div>

        {selected && (
          <div className="border-b border-line bg-granite/40 p-4">
            <button type="button" className="btn-secondary mb-3" onClick={closeProfile}>
              Cerrar ficha
            </button>
            {profile.loading && <Loading label="Cargando ficha" />}
            {!!profile.error && <ErrorState error={profile.error} onRetry={profile.reload} />}
            {profile.data && <MunicipalityProfileView profile={profile.data} />}
          </div>
        )}

        <div className="space-y-6 p-4">
          <section aria-labelledby="filtro-h" className="space-y-2">
            <h2 id="filtro-h" className="font-cond text-base font-semibold text-ink">Buscar y filtrar</h2>
            <label htmlFor="q" className="label">Buscar municipio</label>
            <input id="q" className="field" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Nombre del municipio" />
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label htmlFor="mind" className="label">Densidad mín. (hab/km²)</label>
                <input id="mind" type="number" min={0} inputMode="numeric" className="field" value={minD} onChange={(e) => setMinD(e.target.value)} />
              </div>
              <div>
                <label htmlFor="maxd" className="label">Densidad máx. (hab/km²)</label>
                <input id="maxd" type="number" min={0} inputMode="numeric" className="field" value={maxD} onChange={(e) => setMaxD(e.target.value)} />
              </div>
            </div>
            <p className="text-xs leading-relaxed text-ink-500">
              Los municipios que cumplen el filtro llevan borde ocre en el mapa; el resto se atenúa.
            </p>
          </section>

          <fieldset className="space-y-2">
            <legend className="mb-2 font-cond text-base font-semibold text-ink">Colorear municipios por</legend>
            {(Object.keys(CHOROPLETH_OPTIONS) as ChoroplethKey[]).map((k) => (
              <label key={k} className="flex items-center gap-2 text-sm">
                <input type="radio" name="choro" checked={choropleth === k} onChange={() => setChoropleth(k)} className="accent-pine" />
                {CHOROPLETH_OPTIONS[k].label} <span className="text-xs text-ink-500">{CHOROPLETH_OPTIONS[k].source}</span>
              </label>
            ))}
          </fieldset>

          <fieldset className="space-y-2">
            <legend className="mb-2 font-cond text-base font-semibold text-ink">Cartografía oficial de incendios</legend>
            {layers.loading && <Loading label="Cargando capas" />}
            {!!layers.error && <ErrorState error={layers.error} onRetry={layers.reload} />}
            {layers.data && officialLayers.length === 0 && (
              <p className="text-sm text-ink-500">Ninguna capa oficial integrada todavía.</p>
            )}
            <label className="flex items-center gap-2 text-sm">
              <input type="radio" name="official" checked={activeOfficial === null} onChange={() => setActiveOfficial(null)} className="accent-pine" />
              Ninguna
            </label>
            {officialLayers.map((l) => (
              <label key={l.name} className={`flex items-center gap-2 text-sm ${l.available ? "" : "text-ink-500"}`}>
                <input
                  type="radio"
                  name="official"
                  disabled={!l.available}
                  checked={activeOfficial === l.name}
                  onChange={() => setActiveOfficial(l.name)}
                  className="accent-pine"
                />
                {l.title ?? l.label ?? l.name}
                <StatusBadge status={l.available ? (l.status ?? "official") : "unavailable"} className="ml-auto" />
              </label>
            ))}
          </fieldset>

          {burnt && (
            <fieldset className="space-y-2">
              <legend className="mb-2 font-cond text-base font-semibold text-ink">Histórico observado por satélite</legend>
              <label className={`flex items-center gap-2 text-sm ${burnt.available ? "" : "text-ink-500"}`}>
                <input type="checkbox" disabled={!burnt.available} checked={showBurnt} onChange={(e) => setShowBurnt(e.target.checked)} className="accent-pine" />
                {burnt.label ?? burnt.name}
                <StatusBadge status={burnt.available ? "official" : "unavailable"} className="ml-auto" />
              </label>
            </fieldset>
          )}

          <section aria-labelledby="lista-h" className="space-y-2 border-t border-line pt-4">
            <h2 id="lista-h" className="font-cond text-base font-semibold text-ink">Municipios</h2>
            {list.loading && <Loading label="Cargando municipios" />}
            {!!list.error && <ErrorState error={list.error} onRetry={list.reload} />}
            {list.data && (
              <>
                <p className="text-xs text-ink-500" aria-live="polite">{list.data.length} municipios</p>
                {list.data.length === 0 ? (
                  <Empty title="Ningún municipio cumple el filtro">Amplía el rango de densidad o cambia la búsqueda.</Empty>
                ) : (
                  <ul className="max-h-72 overflow-y-auto rounded border border-line">
                    {list.data.map((m) => (
                      <li key={m.ine_code} className="border-b border-line last:border-b-0">
                        <button
                          type="button"
                          onClick={() => select(m.ine_code)}
                          aria-pressed={selected === m.ine_code}
                          className={`flex w-full items-baseline justify-between gap-2 px-2.5 py-1.5 text-left text-sm hover:bg-granite ${selected === m.ine_code ? "bg-pine-50 font-semibold" : ""}`}
                        >
                          <span>{m.name}</span>
                          <span className="tabular-nums text-xs text-ink-500">
                            {fmtIndicatorValue(m.density?.value ?? null, m.density?.unit)} hab/km²
                          </span>
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </>
            )}
          </section>
        </div>
      </aside>

      <section className="relative order-1 h-[62vh] flex-1 lg:order-2 lg:h-auto" aria-label="Mapa">
        <MapExplorer
          choropleth={choropleth}
          selected={selected}
          highlight={highlight}
          officialLayers={officialLayers}
          activeOfficial={activeOfficial}
          showBurnt={showBurnt}
          onSelect={select}
          onLegend={setLegend}
          onError={setMapError}
        />
        {mapError && (
          <div role="alert" className="absolute left-3 right-3 top-3 z-10 rounded border-l-4 border-rust bg-white p-2 text-sm shadow">
            {mapError}
          </div>
        )}
        {filtering && list.data && (
          <div className="absolute left-3 right-14 top-3 z-[5] flex flex-wrap items-center gap-x-3 gap-y-1 rounded-sm border border-ochre bg-white/95 px-3 py-1.5 text-sm shadow-sm sm:right-auto">
            <span className="inline-block h-3 w-3 border-2 border-ochre" aria-hidden />
            <span>
              <strong className="tabular-nums">{list.data.length}</strong>
              {all.data ? <> de <span className="tabular-nums">{all.data.length}</span></> : null} municipios cumplen el filtro
            </span>
            <button type="button" onClick={clearFilter} className="text-slate underline underline-offset-2">Quitar filtro</button>
          </div>
        )}
        <MapLegend specs={legend} className="absolute bottom-8 left-3 max-h-[70%] max-w-[17rem]" />
      </section>
    </div>
  );
}
