"use client";

import { useState } from "react";
import { ErrorState, Loading } from "@/components/States";
import { StatusBadge } from "@/components/StatusBadge";
import { apiFetch } from "@/lib/api";
import { fmtDate } from "@/lib/format";
import { useApi } from "@/lib/useApi";

type ItemStatus = "pending" | "in_progress" | "available" | "not_applicable";

interface DossierItem {
  code: string;
  group: "anexo5" | "anexo6";
  title: string;
  excerpt: string;
  citation: string;
  responsible_party: string;
  escudo_support?: string;
  status: ItemStatus;
  note: string;
  updated_at: string | null;
  data_status: string;
  linked_actions: { measure_code: string; in_plan: boolean; action_status: string | null; due_date: string | null }[];
}

interface Dossier {
  source_id: string;
  reference: string;
  review_status: string;
  notice: string;
  counts: Record<ItemStatus, number>;
  items: DossierItem[];
}

const STATUS_LABEL: Record<ItemStatus, string> = {
  pending: "Pendiente",
  in_progress: "En preparación",
  available: "Disponible (declarado)",
  not_applicable: "No aplica (declarado)",
};
const ACTION_LABEL: Record<string, string> = { pending: "pendiente", in_progress: "en curso", done: "hecha", blocked: "bloqueada" };
const GROUPS: { id: DossierItem["group"]; title: string }[] = [
  { id: "anexo6", title: "Obligaciones de la urbanización (INFOMA, Anexo 6)" },
  { id: "anexo5", title: "Contenido mínimo del plan de autoprotección (INFOMA, Anexo 5)" },
];

/** M15 · Expediente de autoprotección: lista de comprobación con cita literal del INFOMA. Nunca aprueba. */
export function DossierPanel({ areaId, canEdit }: { areaId: string; canEdit: boolean }) {
  const d = useApi<Dossier>(`/v1/areas/${encodeURIComponent(areaId)}/dossier`);
  const [msg, setMsg] = useState<string | null>(null);

  async function save(code: string, status: ItemStatus, note: string) {
    setMsg(null);
    try {
      await apiFetch(`/v1/areas/${encodeURIComponent(areaId)}/dossier/${encodeURIComponent(code)}`, {
        method: "PATCH",
        body: JSON.stringify({ status, note }),
      });
      setMsg("Estado guardado y registrado en la auditoría.");
      d.reload();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "No se pudo guardar.");
    }
  }

  if (d.loading && !d.data) return <Loading label="Cargando expediente" />;
  if (d.error) return <ErrorState error={d.error} onRetry={d.reload} />;
  if (!d.data) return null;
  const total = d.data.items.length;
  return (
    <section aria-labelledby="dossier-h" className="space-y-4">
      <div>
        <h3 id="dossier-h" className="font-cond text-lg font-semibold">Expediente de autoprotección</h3>
        <p className="text-sm text-ink-700">
          {d.data.counts.available} de {total} puntos declarados disponibles · {d.data.counts.in_progress} en preparación ·{" "}
          {d.data.counts.pending} pendientes · {d.data.counts.not_applicable} no aplican
        </p>
        <p role="note" className="mt-2 rounded border-l-4 border-ochre bg-ochre-50 p-2 text-xs text-ink-800">{d.data.notice}</p>
        <p className="mt-1 text-xs text-ink-500">
          Referencia: {d.data.reference} ({d.data.source_id}). Lista pendiente de revisión técnica.
        </p>
      </div>
      {msg && <p role="status" className="text-sm text-ink-700">{msg}</p>}
      {GROUPS.map((g) => (
        <div key={g.id}>
          <h4 className="font-cond text-base font-semibold text-ink">{g.title}</h4>
          <ul className="mt-2 space-y-2">
            {d.data!.items.filter((i) => i.group === g.id).map((i) => (
              <DossierRow key={i.code} item={i} canEdit={canEdit} onSave={save} />
            ))}
          </ul>
        </div>
      ))}
    </section>
  );
}

function DossierRow({ item, canEdit, onSave }: { item: DossierItem; canEdit: boolean; onSave: (c: string, s: ItemStatus, n: string) => void }) {
  const [status, setStatus] = useState<ItemStatus>(item.status);
  const [note, setNote] = useState(item.note);
  const dirty = status !== item.status || note !== item.note;
  return (
    <li className="rounded border border-line bg-white p-3 text-sm">
      <div className="flex flex-wrap items-start gap-2">
        <p className="font-medium text-ink">{item.title}</p>
        <span className="ml-auto text-xs font-semibold text-ink-700">{STATUS_LABEL[item.status]}</span>
        {item.data_status === "user_reported" && <StatusBadge status="user_reported" />}
      </div>
      <blockquote className="mt-1 border-l-2 border-line pl-2 text-xs italic text-ink-600">«{item.excerpt}»</blockquote>
      <p className="text-xs text-ink-500">{item.citation} · Corresponde a: {item.responsible_party}</p>
      {item.escudo_support && <p className="mt-1 text-xs text-ink-600">{item.escudo_support}</p>}
      {item.linked_actions.length > 0 && (
        <p className="mt-1 text-xs text-ink-700">
          Plan de actuaciones:{" "}
          {item.linked_actions.map((a, k) => (
            <span key={a.measure_code}>
              {k > 0 && " · "}
              <code className="font-mono">{a.measure_code}</code>{" "}
              {a.in_plan ? `${ACTION_LABEL[a.action_status ?? ""] ?? a.action_status}${a.due_date ? `, vence ${fmtDate(a.due_date)}` : ""}` : "no incluida en el plan"}
            </span>
          ))}
        </p>
      )}
      {item.updated_at && <p className="text-xs text-ink-500">Actualizado: {fmtDate(item.updated_at, true)}{item.note ? ` · ${item.note}` : ""}</p>}
      {canEdit && (
        <div className="mt-2 flex flex-wrap items-end gap-2">
          <label className="text-xs">
            <span className="sr-only">Estado de «{item.title}»</span>
            <select className="field py-1 text-xs" value={status} onChange={(e) => setStatus(e.target.value as ItemStatus)} aria-label={`Estado de ${item.title}`}>
              {(Object.keys(STATUS_LABEL) as ItemStatus[]).map((s) => <option key={s} value={s}>{STATUS_LABEL[s]}</option>)}
            </select>
          </label>
          <input
            className="field min-w-[12rem] flex-1 py-1 text-xs"
            maxLength={2000}
            placeholder="Nota (documento, técnico, fecha…)"
            aria-label={`Nota de ${item.title}`}
            value={note}
            onChange={(e) => setNote(e.target.value)}
          />
          <button type="button" className="btn-secondary py-1 text-xs" disabled={!dirty} onClick={() => onSave(item.code, status, note)}>
            Guardar
          </button>
        </div>
      )}
    </li>
  );
}
