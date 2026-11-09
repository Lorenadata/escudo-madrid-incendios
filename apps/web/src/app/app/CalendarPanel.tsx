"use client";

import { useState } from "react";
import { ErrorState, Loading, Empty } from "@/components/States";
import { StatusBadge } from "@/components/StatusBadge";
import { apiDownload } from "@/lib/api";
import { fmtDate } from "@/lib/format";
import { useApi } from "@/lib/useApi";

interface CalendarEvent {
  id: string;
  kind: "action_due" | "inspection_review" | "danger_period";
  start: string;
  end: string;
  title: string;
  area_name: string | null;
  status: string;
  overdue: boolean;
  detail: string;
  source: string;
  level?: "alto" | "medio" | "bajo";
}

interface CalendarResponse {
  from: string;
  to: string;
  notice: string;
  events: CalendarEvent[];
  counts: Record<string, number>;
  overdue: number;
}

const KIND_LABEL: Record<CalendarEvent["kind"], string> = {
  action_due: "Vencimiento",
  inspection_review: "Revisión sugerida",
  danger_period: "Época de peligro",
};

/** M16 · Calendario preventivo: vencimientos del plan, revisiones sugeridas y épocas de peligro oficiales. */
export function CalendarPanel() {
  const cal = useApi<CalendarResponse>("/v1/calendar");
  const [all, setAll] = useState(false);
  const [dlError, setDlError] = useState<string | null>(null);
  const today = new Date().toISOString().slice(0, 10);
  // Las épocas «bajo» cubren medio año: solo se listan las de peligro medio y alto.
  const events = (cal.data?.events ?? []).filter((e) => e.kind !== "danger_period" || e.level !== "bajo");
  const upcoming = events.filter((e) => e.end >= today || e.overdue);
  const shown = all ? upcoming : upcoming.slice(0, 6);

  return (
    <section aria-labelledby="cal-h" className="panel">
      <h2 id="cal-h" className="font-cond text-lg font-semibold">Calendario preventivo</h2>
      {cal.loading && <Loading label="Cargando calendario" />}
      {!!cal.error && <ErrorState error={cal.error} onRetry={cal.reload} />}
      {cal.data && (
        <>
          {cal.data.overdue > 0 && (
            <p className="mt-1 rounded border-l-4 border-ochre bg-ochre-50 p-2 text-xs text-ink-800">
              {cal.data.overdue} recordatorio{cal.data.overdue === 1 ? "" : "s"} con fecha pasada sin completar.
            </p>
          )}
          {upcoming.length === 0 ? (
            <Empty title="Sin recordatorios próximos">Asigna fechas límite a las actuaciones del plan.</Empty>
          ) : (
            <ol className="mt-2 space-y-2" aria-label="Próximos recordatorios">
              {shown.map((e) => (
                <li key={e.id} className={`rounded border p-2 text-xs ${e.overdue ? "border-ochre bg-ochre-50" : "border-line bg-white"}`}>
                  <div className="flex items-center gap-1.5">
                    <span className="font-semibold text-ink">
                      {fmtDate(e.start)}
                      {e.end !== e.start ? ` – ${fmtDate(e.end)}` : ""}
                    </span>
                    <StatusBadge status={e.status} className="ml-auto" />
                  </div>
                  <p className="mt-0.5 text-ink-800">
                    {e.kind !== "danger_period" && (
                      <span className="text-ink-500">{KIND_LABEL[e.kind]}{e.overdue ? " · fecha pasada" : ""}: </span>
                    )}
                    {e.title.replace(/^Vence: /, "")}
                  </p>
                  {e.area_name && <p className="text-ink-500">{e.area_name}</p>}
                  <details className="mt-0.5">
                    <summary className="cursor-pointer text-slate">Detalle y fuente</summary>
                    <p className="text-ink-600">{e.detail}</p>
                    <p className="text-ink-500">Fuente: {e.source}</p>
                  </details>
                </li>
              ))}
            </ol>
          )}
          {upcoming.length > 6 && (
            <button type="button" className="mt-2 text-xs text-slate underline" onClick={() => setAll((v) => !v)}>
              {all ? "Ver menos" : `Ver los ${upcoming.length} recordatorios`}
            </button>
          )}
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <button
              type="button"
              className="btn-secondary text-xs"
              onClick={() => {
                setDlError(null);
                apiDownload("/v1/calendar.ics", "escudo-calendario.ics").catch((err: Error) => setDlError(err.message));
              }}
            >
              Exportar a calendario (.ics)
            </button>
          </div>
          {dlError && <p role="alert" className="mt-1 text-xs text-rust">{dlError}</p>}
          <p className="mt-2 text-xs text-ink-500">{cal.data.notice}</p>
        </>
      )}
    </section>
  );
}
