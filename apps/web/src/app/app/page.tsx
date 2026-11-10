"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useSessionToken } from "@/lib/browser-store";
import { MunicipalityProfileView } from "@/components/ProfilePanels";
import { Empty, ErrorState, Loading } from "@/components/States";
import { StatusBadge, SyntheticBadge } from "@/components/StatusBadge";
import { fmtShare } from "@/lib/format";
import { ApiError, apiFetch, setToken } from "@/lib/api";
import type { AreaDetail, Area, Measure, MunicipalitySummary, User } from "@/lib/api-types";
import { useApi } from "@/lib/useApi";
import { AreaForm } from "./AreaForm";
import { CalendarPanel } from "./CalendarPanel";
import { DecisionsPanel } from "./DecisionsPanel";
import { DossierPanel } from "./DossierPanel";
import { AuditPanel, ImpactPanel } from "./ImpactPanel";
import { InspectionsPanel } from "./InspectionsPanel";
import { MunicipalPanel } from "./MunicipalPanel";
import { ScenariosPanel } from "./ScenariosPanel";

const TABS = [
  { id: "contexto", label: "Contexto" },
  { id: "inspecciones", label: "Inspecciones" },
  { id: "escenarios", label: "Escenarios y plan" },
  { id: "expediente", label: "Expediente" },
  { id: "decisiones", label: "Decisiones" },
] as const;

type AreaLayersData = Record<string, { status: string; resolution?: string; caveat?: string; classes: { class_label: string; area_share: number | null }[] }>;

const LAYER_NAMES: Record<string, string> = { risk: "Riesgo (GEO-01)", hazard: "Peligrosidad (GEO-02)", vulnerability: "Vulnerabilidad (GEO-03)" };

function AreaLayers({ layers }: { layers: AreaLayersData }) {
  const caveat = Object.values(layers).find((l) => l.caveat)?.caveat;
  return (
    <section aria-labelledby="area-layers-h" className="rounded border border-line bg-granite/40 p-3">
      <div className="flex flex-wrap items-center gap-2">
        <h3 id="area-layers-h" className="font-cond text-base font-semibold">Clases oficiales dentro del ámbito dibujado</h3>
        <StatusBadge status="derived" />
      </div>
      <div className="mt-2 grid gap-3 sm:grid-cols-3">
        {Object.entries(layers).map(([k, l]) => (
          <div key={k} className="text-sm">
            <p className="font-medium">{LAYER_NAMES[k] ?? k}</p>
            {l.status === "unavailable" || l.classes.length === 0 ? (
              <p className="text-ink-500">Sin intersección con la capa</p>
            ) : (
              <ul>
                {l.classes.slice(0, 3).map((c) => (
                  <li key={c.class_label} className="flex justify-between gap-2"><span>{c.class_label}</span><span className="tabular-nums">{fmtShare(c.area_share)}</span></li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
      {caveat && <p className="mt-2 text-xs text-ink-600">{caveat}</p>}
    </section>
  );
}

export default function WorkspacePage() {
  const router = useRouter();
  const token = useSessionToken();
  const hasToken = token === undefined ? null : !!token;

  const me = useApi<User>(hasToken ? "/v1/me" : null);
  const isMunicipal = !!me.data?.memberships.some((m) => m.role === "municipal");
  const isManager = !!me.data?.memberships.some((m) => m.role === "gestor" || m.role === "admin");
  const canEditDossier = !!me.data?.memberships.some((m) => ["gestor", "admin", "tecnico"].includes(m.role));
  const orgReady = hasToken && !!me.data && !isMunicipal;
  const areas = useApi<Area[]>(orgReady ? "/v1/areas" : null);
  const measures = useApi<Measure[]>(orgReady ? "/v1/measures" : null);
  const munis = useApi<MunicipalitySummary[]>(orgReady ? "/v1/municipalities?sort=name" : null);
  const [shareMsg, setShareMsg] = useState<string | null>(null);
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

      {isMunicipal && <MunicipalPanel />}
      {orgReady && <div className="mt-5 grid gap-6 lg:grid-cols-[17rem_1fr]">
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
          <CalendarPanel />
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
              {isManager && (
                <div className="mt-2 flex flex-wrap items-center gap-2 text-sm">
                  <label className="inline-flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={!!area.data.shared_with_municipality}
                      onChange={async (e) => {
                        setShareMsg(null);
                        try {
                          await apiFetch(`/v1/areas/${area.data!.id}/sharing`, {
                            method: "PATCH",
                            body: JSON.stringify({ shared_with_municipality: e.target.checked }),
                          });
                          setShareMsg(e.target.checked ? "El ayuntamiento del término puede consultar este ámbito (solo lectura)." : "Autorización retirada.");
                          area.reload();
                        } catch (err) {
                          setShareMsg(err instanceof Error ? err.message : "No se pudo cambiar la autorización.");
                        }
                      }}
                    />
                    Autorizar al ayuntamiento del término a consultar este ámbito
                  </label>
                  {shareMsg && <span role="status" className="text-xs text-ink-600">{shareMsg}</span>}
                </div>
              )}
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
                      {area.data.has_geometry && area.data.official_layers_area && <AreaLayers layers={area.data.official_layers_area as AreaLayersData} />}
                      <MunicipalityProfileView profile={area.data.municipality_profile} />
                    </div>
                  ) : (
                    <Empty title="Ficha municipal no disponible" />
                  )
                )}
                {tab === "inspecciones" && <InspectionsPanel areaId={String(area.data.id)} />}
                {tab === "escenarios" && <ScenariosPanel areaId={String(area.data.id)} measures={measures.data ?? []} />}
                {tab === "expediente" && <DossierPanel areaId={String(area.data.id)} canEdit={canEditDossier} />}
                {tab === "decisiones" && <DecisionsPanel areaId={String(area.data.id)} canWrite={canEditDossier} />}
              </div>
            </>
          )}
          <div className="mt-8"><AuditPanel /></div>
          <p className="mt-4 text-xs text-ink-500">
            ¿Buscas el contexto regional? Abre el <Link href="/" className="underline">explorador</Link>.
          </p>
        </section>
      </div>}
    </div>
  );
}
