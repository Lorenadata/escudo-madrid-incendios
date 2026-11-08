"use client";

import type { HousingContext, MunicipalityProfile, OfficialLayerSummary, WeatherContext } from "@/lib/api-types";
import { fmtDate, fmtShare } from "@/lib/format";
import { IndicatorValue } from "./IndicatorValue";
import { SeriesPanel } from "./SeriesPanel";
import { StatusBadge } from "./StatusBadge";

const DEFAULT_WEATHER_DISCLAIMER =
  "Predicción meteorológica oficial de AEMET, solo informativa: no es un índice de peligro de incendio, ni pronóstico de ignición, ni alerta operativa.";

export function WeatherPanel({ weather }: { weather: WeatherContext | null | undefined }) {
  const status = weather?.status ?? "unavailable";
  return (
    <section aria-labelledby="weather-h" className="border-t border-line pt-4">
      <div className="flex items-center justify-between gap-2">
        <h3 id="weather-h" className="font-cond text-base font-semibold text-ink">Contexto meteorológico AEMET</h3>
        <StatusBadge status={status === "ok" ? "official" : status} />
      </div>
      {status === "unavailable" && (
        <p className="mt-2 rounded bg-ash-50 p-2 text-sm text-ink-700">
          Datos meteorológicos no disponibles.
          {weather?.last_valid_at
            ? ` Último dato válido: ${fmtDate(weather.last_valid_at, true)}.`
            : " No hay ningún dato válido registrado."}
        </p>
      )}
      {status === "stale" && (
        <p className="mt-2 rounded bg-rust-50 p-2 text-sm text-ink-800">
          El dato ha caducado. Emitido {fmtDate(weather?.issued_at, true)}, vigente hasta {fmtDate(weather?.valid_to, true)}.
          Consulta aemet.es para información actual.
        </p>
      )}
      {weather && status !== "unavailable" && (
        <>
          <p className="mt-2 text-xs text-ink-500">
            Emisión {fmtDate(weather.issued_at, true)} · validez {fmtDate(weather.valid_from, true)} – {fmtDate(weather.valid_to, true)}
          </p>
          {weather.reference_location && (
            <p className="text-xs text-ink-500">
              Referencia:{" "}
              {typeof weather.reference_location === "string"
                ? weather.reference_location
                : `${weather.reference_location.name ?? ""} — ${weather.reference_location.type ?? ""}`}
              {typeof weather.reference_location !== "string" && weather.reference_location.aemet_url && (
                <>
                  {" · "}
                  <a href={weather.reference_location.aemet_url} target="_blank" rel="noopener noreferrer" className="text-slate underline">
                    ver en aemet.es
                  </a>
                </>
              )}
            </p>
          )}
          {weather.fire_danger && <IndicatorValue indicator={weather.fire_danger} />}
          <div className="grid grid-cols-2 gap-x-4">
            {weather.variables.map((v) => (
              <IndicatorValue key={v.indicator_id} indicator={v} compact />
            ))}
          </div>
        </>
      )}
      {weather?.message && <p className="mt-2 text-xs text-ink-600">{weather.message}</p>}
      <p className="mt-2 text-xs italic text-ink-600">{weather?.disclaimer || DEFAULT_WEATHER_DISCLAIMER}</p>
      {weather?.attribution && <p className="mt-1 text-[11px] text-ink-500">{weather.attribution}</p>}
    </section>
  );
}

const LAYER_TITLES: Record<string, string> = {
  risk: "Riesgo por incendios forestales",
  hazard: "Peligrosidad por incendios forestales",
  vulnerability: "Vulnerabilidad por incendios forestales",
};

function OfficialLayerBlock({ kind, layer }: { kind: string; layer: OfficialLayerSummary | null }) {
  const title = LAYER_TITLES[kind] ?? kind;
  if (!layer || layer.status === "unavailable") {
    return (
      <div className="py-2">
        <div className="flex items-baseline justify-between gap-2">
          <span className="text-sm text-ink-700">{title}</span>
          <StatusBadge status="unavailable" />
        </div>
        <p className="text-xs text-ink-500">{layer?.reason ?? "Capa oficial no integrada todavía para este municipio."}</p>
      </div>
    );
  }
  return (
    <div className="py-2">
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-sm text-ink-700">{title}</span>
        <StatusBadge status={layer.status} />
      </div>
      <p className="mt-0.5 font-cond text-lg font-semibold text-ink">
        {layer.dominant_class ?? "Sin clase dominante"}
        <span className="ml-2 text-xs font-normal text-ink-500">clase dominante · {layer.source_id}{layer.version ? ` · ${layer.version}` : ""}</span>
      </p>
      {layer.classes.length > 0 && (
        <table className="mt-1 w-full text-xs">
          <caption className="sr-only">Reparto de superficie por clase literal de la fuente</caption>
          <thead>
            <tr className="text-left text-ink-500">
              <th className="font-normal">Clase (literal de la fuente)</th>
              <th className="text-right font-normal">Superficie municipal <StatusBadge status="derived" className="ml-1" /></th>
            </tr>
          </thead>
          <tbody>
            {layer.classes.map((c) => (
              <tr key={c.class_label} className="border-t border-line/60">
                <td className="py-0.5">{c.class_label}</td>
                <td className="py-0.5 text-right tabular-nums">{fmtShare(c.area_share)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export function OfficialFirePanel({ profile }: { profile: MunicipalityProfile }) {
  const of = profile.official_fire;
  return (
    <section aria-labelledby="official-h" className="border-t border-line pt-4">
      <h3 id="official-h" className="font-cond text-base font-semibold text-ink">Cartografía oficial de incendios</h3>
      <p className="text-xs text-ink-500">
        Tres capas distintas; no se combinan ni se recalculan.
      </p>
      <OfficialLayerBlock kind="risk" layer={of?.risk ?? null} />
      <OfficialLayerBlock kind="hazard" layer={of?.hazard ?? null} />
      <OfficialLayerBlock kind="vulnerability" layer={of?.vulnerability ?? null} />
    </section>
  );
}

export function HousingPanel({ housing }: { housing: HousingContext | null | undefined }) {
  return (
    <section aria-labelledby="housing-h" className="border-t border-line pt-4">
      <h3 id="housing-h" className="font-cond text-base font-semibold text-ink">
        Vivienda y ocupación (Censo {housing?.census_year ?? 2021})
      </h3>
      {!housing ? (
        <p className="py-2 text-sm text-ink-500">Indicadores de vivienda no disponibles.</p>
      ) : (
        <>
          <p className="text-xs leading-relaxed text-ink-500">{housing.caveat}</p>
          <div className="divide-y divide-line/70">
            {housing.indicators.map((i) => (
              <IndicatorValue key={i.indicator_id} indicator={i} />
            ))}
          </div>
          <p className="text-xs text-ink-500">Fuentes: {housing.sources.join(", ")} (Portal de Datos Abiertos CAM).</p>
        </>
      )}
    </section>
  );
}

export function MunicipalityProfileView({ profile, showWeather = true }: { profile: MunicipalityProfile; showWeather?: boolean }) {
  return (
    <div className="space-y-4">
      <header>
        <p className="text-xs text-ink-500">Municipio · INE {profile.ine_code}</p>
        <h2 className="font-cond text-2xl font-semibold leading-tight text-ink">{profile.name}</h2>
      </header>
      <p className="rounded border-l-4 border-slate bg-slate-50 p-2 text-xs leading-relaxed text-ink-700">
        {profile.scale_notice}
      </p>
      <section aria-labelledby="demo-h">
        <h3 id="demo-h" className="font-cond text-base font-semibold text-ink">Indicadores municipales</h3>
        <div className="divide-y divide-line/70">
          <IndicatorValue indicator={profile.population} />
          <IndicatorValue indicator={profile.density} />
          <IndicatorValue indicator={profile.age_65_plus_share} />
          <IndicatorValue indicator={profile.altitude_m} />
          <IndicatorValue indicator={profile.area_km2} />
          <IndicatorValue indicator={profile.forest_share} />
        </div>
      </section>
      <SeriesPanel ine={profile.ine_code} />
      <HousingPanel housing={profile.housing} />
      <p className="text-xs text-ink-500">
        Histórico de incendios y repoblaciones (solo regional, CAM-05/CAM-06):{" "}
        <a className="text-slate underline underline-offset-2" href="/analisis#contexto-regional">ver contexto regional</a>.
      </p>
      <OfficialFirePanel profile={profile} />
      {showWeather && <WeatherPanel weather={profile.weather} />}
      {profile.sources?.length > 0 && (
        <p className="border-t border-line pt-3 text-xs text-ink-500">
          Fuentes utilizadas: {profile.sources.join(", ")}
        </p>
      )}
    </div>
  );
}
