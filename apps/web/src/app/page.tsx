"use client";

import { useCallback, useMemo, useState } from "react";
import { CHOROPLETH_OPTIONS, MapExplorer, type ChoroplethKey, type LegendSpec } from "@/components/MapExplorer";
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
  const [legend, setLegend] = useState<LegendSpec[]>([]);
  const [mapError, setMapError] = useState<string | null>(null);

  const params = new URLSearchParams();
  if (q.trim()) params.set("q", q.trim());
  if (minD) params.set("min_density", minD);
  if (maxD) params.set("max_density", maxD);
  params.set("sort", "name");
  const list = useApi<MunicipalitySummary[]>(`/v1/municipalities?${params.toString()}`);
  const layers = useApi<Layer[]>("/v1/layers");
  const profile = useApi<MunicipalityProfile>(selected ? `/v1/municipalities/${selected}/profile` : null);

  const filtering = !!(q.trim() || minD || maxD);
  const highlight = useMemo(
    () => (filtering && list.data ? new Set(list.data.map((m) => m.ine_code)) : null),
    [filtering, list.data],
  );
  const officialLayers = useMemo(
    () => (layers.data ?? []).filter((l) => l.name !== "municipalities"),
    [layers.data],
  );

  const select = useCallback((ine: string) => {
    setPicked(ine);
    history.replaceState(null, "", `#${ine}`);
  }, []);

  return (
    <div className="flex flex-1 flex-col lg:flex-row">
      <aside className="order-2 w-full shrink-0 overflow-y-auto border-r border-line bg-white lg:order-1 lg:h-[calc(100vh-6.5rem)] lg:w-[400px]">
        <div className="space-y-4 p-4">
          <div>
            <h1 className="font-cond text-xl font-semibold text-ink">Explorador regional</h1>
            <p className="text-sm text-ink-600">
              Municipios de la Comunidad de Madrid con datos de su Portal de Datos Abiertos. Selecciona uno en el mapa o en la lista.
            </p>
          </div>

          <fieldset className="space-y-2">
            <legend className="label">Colorear municipios por</legend>
            {(Object.keys(CHOROPLETH_OPTIONS) as ChoroplethKey[]).map((k) => (
              <label key={k} className="flex items-center gap-2 text-sm">
                <input type="radio" name="choro" checked={choropleth === k} onChange={() => setChoropleth(k)} className="accent-pine" />
                {CHOROPLETH_OPTIONS[k].label} <span className="text-xs text-ink-500">{CHOROPLETH_OPTIONS[k].source}</span>
              </label>
            ))}
          </fieldset>

          <fieldset className="space-y-2">
            <legend className="label">Cartografía oficial de incendios</legend>
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

          {selected && (
            <div className="border-t border-line pt-4">
              <button type="button" className="mb-2 text-xs text-slate underline" onClick={() => { setPicked(null); history.replaceState(null, "", " "); window.dispatchEvent(new HashChangeEvent("hashchange")); }}>
                Cerrar ficha
              </button>
              {profile.loading && <Loading label="Cargando ficha" />}
              {!!profile.error && <ErrorState error={profile.error} onRetry={profile.reload} />}
              {profile.data && <MunicipalityProfileView profile={profile.data} />}
            </div>
          )}

          <div className="space-y-2 border-t border-line pt-4">
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
            {list.loading && <Loading label="Cargando municipios" />}
            {!!list.error && <ErrorState error={list.error} onRetry={list.reload} />}
            {!selected && list.data && (
              <p className="text-xs text-ink-500">Haz clic en el mapa o en la lista para abrir la ficha territorial.</p>
            )}
            {list.data && (
              <>
                <p className="text-xs text-ink-500" aria-live="polite">{list.data.length} municipios</p>
                {list.data.length === 0 ? (
                  <Empty title="Ningún municipio cumple el filtro">Amplía el rango de densidad o cambia la búsqueda.</Empty>
                ) : (
                  <ul className="max-h-56 overflow-y-auto rounded border border-line">
                    {list.data.map((m) => (
                      <li key={m.ine_code}>
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
          </div>

        </div>
      </aside>

      <section className="relative order-1 h-[60vh] flex-1 lg:order-2 lg:h-auto" aria-label="Mapa">
        <MapExplorer
          choropleth={choropleth}
          selected={selected}
          highlight={highlight}
          officialLayers={officialLayers}
          activeOfficial={activeOfficial}
          onSelect={select}
          onLegend={setLegend}
          onError={setMapError}
        />
        {mapError && (
          <div role="alert" className="absolute left-3 right-3 top-3 rounded border-l-4 border-rust bg-white p-2 text-sm shadow">
            {mapError}
          </div>
        )}
        <div className="absolute bottom-8 left-3 max-w-[18rem] space-y-3 rounded border border-line bg-white/95 p-3 text-xs shadow-sm">
          {legend.map((l) => (
            <div key={l.title}>
              <p className="mb-1 font-cond text-sm font-semibold text-ink">{l.title}</p>
              <ul className="space-y-0.5">
                {l.items.map((it) => (
                  <li key={it.label} className="flex items-center gap-2">
                    <span className="inline-block h-3 w-5 rounded-sm border border-ink/20" style={{ background: it.color }} aria-hidden />
                    {it.label}
                  </li>
                ))}
              </ul>
              <p className="mt-1 text-ink-500">{l.note}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
