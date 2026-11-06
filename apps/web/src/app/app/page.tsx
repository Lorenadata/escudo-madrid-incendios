"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useSessionToken } from "@/lib/browser-store";
import { MunicipalityProfileView } from "@/components/ProfilePanels";
import { Empty, ErrorState, Loading } from "@/components/States";
import { SyntheticBadge } from "@/components/StatusBadge";
import { ApiError, setToken } from "@/lib/api";
import type { AreaDetail, Area, Measure, MunicipalitySummary, User } from "@/lib/api-types";
import { useApi } from "@/lib/useApi";
import { AreaForm } from "./AreaForm";
import { AuditPanel, ImpactPanel } from "./ImpactPanel";
import { InspectionsPanel } from "./InspectionsPanel";
import { ScenariosPanel } from "./ScenariosPanel";

const TABS = [
  { id: "contexto", label: "Contexto" },
  { id: "inspecciones", label: "Inspecciones" },
  { id: "escenarios", label: "Escenarios y plan" },
] as const;

export default function WorkspacePage() {
  const router = useRouter();
  const token = useSessionToken();
  const hasToken = token === undefined ? null : !!token;

  const me = useApi<User>(hasToken ? "/v1/me" : null);
  const areas = useApi<Area[]>(hasToken ? "/v1/areas" : null);
  const measures = useApi<Measure[]>(hasToken ? "/v1/measures" : null);
  const munis = useApi<MunicipalitySummary[]>(hasToken ? "/v1/municipalities?sort=name" : null);
  const [pickedArea, setAreaId] = useState<string | null>(null);
  const [tab, setTab] = useState<(typeof TABS)[number]["id"]>("contexto");
  const [showNewArea, setShowNewArea] = useState(false);
  const areaId = pickedArea ?? (areas.data?.length ? String(areas.data[0].id) : null);
  const area = useApi<AreaDetail>(areaId ? `/v1/areas/${areaId}` : null);

  useEffect(() => {
    if (hasToken === false) router.replace("/login");
  }, [hasToken, router]);

  useEffect(() => {
    if (me.error instanceof ApiError && me.error.status === 401) {
      setToken(null);
      router.replace("/login");
    }
  }, [me.error, router]);

  if (hasToken === null || (hasToken && me.loading)) return <div className="px-4"><Loading label="Comprobando sesión" /></div>;
  if (!hasToken) return null;

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-cond text-2xl font-semibold text-ink">Área de trabajo</h1>
          {me.data && (
            <p className="text-sm text-ink-600">
              {me.data.full_name ?? me.data.email} ·{" "}
              {me.data.memberships.map((m) => `${m.organization_name ?? m.organization_id} (${m.role})`).join(", ")}
            </p>
          )}
        </div>
        <button
          type="button"
          className="btn-secondary"
          onClick={() => {
            setToken(null);
            router.push("/login");
          }}
        >
          Cerrar sesión
        </button>
      </header>
      {!!me.error && !(me.error instanceof ApiError && me.error.status === 401) && <ErrorState error={me.error} onRetry={me.reload} />}

      <div className="mt-5 grid gap-6 lg:grid-cols-[17rem_1fr]">
        <aside aria-label="Ámbitos de la organización" className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="font-cond text-lg font-semibold">Ámbitos</h2>
            <button type="button" className="text-sm text-slate underline" onClick={() => setShowNewArea((v) => !v)}>
              {showNewArea ? "Cancelar" : "Añadir ámbito"}
            </button>
          </div>
          {showNewArea && munis.data && (
            <AreaForm
              municipalities={munis.data}
              onCreated={(a) => {
                setShowNewArea(false);
                areas.reload();
                setAreaId(String(a.id));
              }}
            />
          )}
          {areas.loading && <Loading label="Cargando ámbitos" />}
          {!!areas.error && <ErrorState error={areas.error} onRetry={areas.reload} />}
          {areas.data && areas.data.length === 0 && (
            <Empty title="Tu organización no tiene ámbitos">Añade una urbanización o zona para empezar a planificar.</Empty>
          )}
          <ul className="space-y-1">
            {areas.data?.map((a) => (
              <li key={a.id}>
                <button
                  type="button"
                  aria-pressed={String(a.id) === areaId}
                  onClick={() => setAreaId(String(a.id))}
                  className={`w-full rounded border px-3 py-2 text-left text-sm ${String(a.id) === areaId ? "border-pine bg-pine-50" : "border-line bg-white hover:bg-granite"}`}
                >
                  <span className="font-medium">{a.name}</span>
                  <span className="mt-0.5 flex items-center gap-1.5 text-xs text-ink-500">
                    INE {a.municipality_code}
                    {a.record_status === "synthetic" && <SyntheticBadge />}
                  </span>
                </button>
              </li>
            ))}
          </ul>
          <ImpactPanel />
        </aside>

        <section aria-label="Ámbito seleccionado" className="min-w-0">
          {!areaId && <Empty title="Selecciona un ámbito">Elige un ámbito de la lista o crea uno nuevo.</Empty>}
          {areaId && area.loading && <Loading label="Cargando ámbito" />}
          {areaId && !!area.error && <ErrorState error={area.error} onRetry={area.reload} />}
          {area.data && (
            <>
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="font-cond text-xl font-semibold">{area.data.name}</h2>
                {area.data.record_status === "synthetic" && (
                  <>
                    <SyntheticBadge />
                    <span className="text-xs font-semibold text-ochre-800">Ámbito ficticio de demostración</span>
                  </>
                )}
              </div>
              {area.data.description && <p className="text-sm text-ink-600">{area.data.description}</p>}
              <div role="tablist" aria-label="Secciones del ámbito" className="mt-4 flex gap-1 border-b border-line">
                {TABS.map((t) => (
                  <button
                    key={t.id}
                    role="tab"
                    type="button"
                    id={`tab-${t.id}`}
                    aria-selected={tab === t.id}
                    aria-controls={`panel-${t.id}`}
                    onClick={() => setTab(t.id)}
                    className={`-mb-px border-b-2 px-3 py-2 text-sm ${tab === t.id ? "border-pine font-semibold text-ink" : "border-transparent text-ink-600 hover:text-ink"}`}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
              <div role="tabpanel" id={`panel-${tab}`} aria-labelledby={`tab-${tab}`} className="pt-4">
                {tab === "contexto" && (
                  area.data.municipality_profile ? (
                    <div className="panel max-w-2xl space-y-3">
                      {area.data.population_notice && <p className="text-xs text-ink-600">{area.data.population_notice}</p>}
                      <MunicipalityProfileView profile={area.data.municipality_profile} />
                    </div>
                  ) : (
                    <Empty title="Ficha municipal no disponible" />
                  )
                )}
                {tab === "inspecciones" && <InspectionsPanel areaId={String(area.data.id)} />}
                {tab === "escenarios" && <ScenariosPanel areaId={String(area.data.id)} measures={measures.data ?? []} />}
              </div>
            </>
          )}
          <div className="mt-8"><AuditPanel /></div>
          <p className="mt-4 text-xs text-ink-500">
            ¿Buscas el contexto regional? Abre el <Link href="/" className="underline">explorador</Link>.
          </p>
        </section>
      </div>
    </div>
  );
}
