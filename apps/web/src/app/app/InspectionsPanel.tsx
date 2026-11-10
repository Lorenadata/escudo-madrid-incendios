"use client";

import { useState } from "react";
import { CommentThread } from "@/components/CommentThread";
import { Empty, ErrorState, Loading } from "@/components/States";
import { StatusBadge } from "@/components/StatusBadge";
import { apiFetch } from "@/lib/api";
import type { ChecklistQuestion, Inspection } from "@/lib/api-types";
import { fmtDate } from "@/lib/format";
import { useApi } from "@/lib/useApi";

const ANSWERS = [
  { v: "si", l: "Sí" },
  { v: "parcial", l: "Parcial" },
  { v: "no", l: "No" },
  { v: "na", l: "No aplica" },
];

function NewInspection({ areaId, checklist, onCreated }: { areaId: string; checklist: ChecklistQuestion[]; onCreated: () => void }) {
  const today = new Date().toISOString().slice(0, 10);
  const [date, setDate] = useState(today);
  const [inspector, setInspector] = useState("");
  const [answers, setAnswers] = useState<Record<string, { answer: string; observation: string }>>({});
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await apiFetch("/v1/inspections", {
        method: "POST",
        body: JSON.stringify({
          area_id: areaId,
          inspected_on: date,
          inspector_name: inspector,
          items: Object.entries(answers)
            .filter(([, v]) => v.answer)
            .map(([code, v]) => ({ checklist_code: code, answer: v.answer, observation: v.observation })),
        }),
      });
      setAnswers({});
      onCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="panel space-y-3">
      <h3 className="font-cond text-lg font-semibold">Registrar inspección</h3>
      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <label htmlFor="idate" className="label">Fecha de la inspección</label>
          <input id="idate" type="date" className="field" value={date} max={today} onChange={(e) => setDate(e.target.value)} required />
        </div>
        <div>
          <label htmlFor="iname" className="label">Persona que inspecciona</label>
          <input id="iname" className="field" value={inspector} onChange={(e) => setInspector(e.target.value)} required minLength={2} />
        </div>
      </div>
      <fieldset className="space-y-3">
        <legend className="label">Lista de comprobación</legend>
        {checklist.map((q) => (
          <div key={q.code} className="rounded border border-line p-2.5">
            <p className="text-sm">{q.question}</p>
            <div role="radiogroup" aria-label={q.question} className="mt-1.5 flex flex-wrap gap-3">
              {ANSWERS.map((a) => (
                <label key={a.v} className="flex items-center gap-1.5 text-sm">
                  <input
                    type="radio"
                    name={`q-${q.code}`}
                    className="accent-pine"
                    checked={answers[q.code]?.answer === a.v}
                    onChange={() => setAnswers((s) => ({ ...s, [q.code]: { answer: a.v, observation: s[q.code]?.observation ?? "" } }))}
                  />
                  {a.l}
                </label>
              ))}
            </div>
            <input
              aria-label={`Observación: ${q.question}`}
              placeholder="Observación (opcional)"
              className="field mt-1.5"
              value={answers[q.code]?.observation ?? ""}
              onChange={(e) => setAnswers((s) => ({ ...s, [q.code]: { answer: s[q.code]?.answer ?? "", observation: e.target.value } }))}
            />
          </div>
        ))}
      </fieldset>
      <p className="text-xs text-ink-500">La inspección queda «pendiente de revisión técnica» hasta que la valide personal técnico competente.</p>
      {error && <p role="alert" className="text-sm text-rust">{error}</p>}
      <button type="submit" className="btn-primary" disabled={busy || inspector.length < 2}>
        {busy ? "Guardando…" : "Guardar inspección"}
      </button>
    </form>
  );
}

const VERDICTS = [
  { v: "util", l: "Útil" },
  { v: "requiere_revision", l: "Requiere revisión" },
  { v: "redundante", l: "Redundante" },
  { v: "inviable", l: "Inviable" },
];

function ReviewForm({ ins, onDone }: { ins: Inspection; onDone: () => void }) {
  const [verdict, setVerdict] = useState("util");
  const [note, setNote] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setMsg(null);
    try {
      const r = await apiFetch<{ notice?: string }>(`/v1/inspections/${ins.id}/reviews`, {
        method: "POST",
        body: JSON.stringify({ verdict, note }),
      });
      setMsg(r.notice ?? "Revisión registrada.");
      onDone();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }
  return (
    <details className="rounded border border-line p-2.5 text-sm">
      <summary className="cursor-pointer text-slate">Registrar revisión técnica</summary>
      <form onSubmit={submit} className="mt-2 space-y-2">
        <p className="text-xs text-ink-500">
          Solo personal técnico con cualificación verificada. La revisión no equivale a aprobación administrativa ni a informe de PAIF.
        </p>
        <div className="grid gap-2 sm:grid-cols-[12rem_1fr]">
          <select aria-label="Valoración técnica" className="field" value={verdict} onChange={(e) => setVerdict(e.target.value)}>
            {VERDICTS.map((v) => <option key={v.v} value={v.v}>{v.l}</option>)}
          </select>
          <input aria-label="Nota de la revisión" className="field" placeholder="Nota (opcional)" value={note} onChange={(e) => setNote(e.target.value)} />
        </div>
        <button type="submit" className="btn-secondary" disabled={busy}>{busy ? "Registrando…" : "Registrar revisión"}</button>
        {msg && <p role="status" className="text-sm text-ink-700">{msg}</p>}
      </form>
    </details>
  );
}

export function InspectionsPanel({ areaId }: { areaId: string }) {
  const list = useApi<Inspection[]>(`/v1/inspections?area_id=${encodeURIComponent(areaId)}`);
  const checklist = useApi<ChecklistQuestion[]>("/v1/checklist");
  const [uploadMsg, setUploadMsg] = useState<string | null>(null);

  async function upload(ins: Inspection, file: File) {
    setUploadMsg(null);
    const fd = new FormData();
    fd.append("file", file);
    try {
      await apiFetch(`/v1/inspections/${ins.id}/evidence`, { method: "POST", body: fd });
      setUploadMsg(`Evidencia «${file.name}» adjuntada.`);
      list.reload();
    } catch (err) {
      setUploadMsg(`No se ha adjuntado la evidencia: ${err instanceof Error ? err.message : String(err)}`);
    }
  }

  return (
    <div className="space-y-4">
      {list.loading && <Loading label="Cargando inspecciones" />}
      {!!list.error && <ErrorState error={list.error} onRetry={list.reload} />}
      {list.data && list.data.length === 0 && <Empty title="Sin inspecciones">Registra la primera inspección del ámbito.</Empty>}
      {uploadMsg && <p role="status" className="text-sm text-ink-700">{uploadMsg}</p>}
      {list.data?.map((ins) => (
        <article key={ins.id} className="panel space-y-2">
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <strong>{fmtDate(ins.inspected_on)}</strong> · {ins.inspector_name}
            <StatusBadge status="user_reported" />
            <span className="text-xs text-ink-600">
              {ins.review_status === "reviewed" ? "Revisada por técnico" : "Pendiente de revisión técnica"}
            </span>
            {ins.record_status === "synthetic" && <span className="text-xs font-semibold text-ochre-800">Ficticia</span>}
          </div>
          <ul className="divide-y divide-line text-sm">
            {ins.items.map((it) => (
              <li key={it.checklist_code} className="flex justify-between gap-3 py-1">
                <span>{it.question || it.checklist_code}{it.observation && <span className="block text-xs text-ink-500">{it.observation}</span>}</span>
                <span className="font-semibold">{ANSWERS.find((a) => a.v === it.answer)?.l ?? it.answer}</span>
              </li>
            ))}
          </ul>
          {ins.review_status !== "reviewed" && <ReviewForm ins={ins} onDone={list.reload} />}
          <CommentThread entityType="inspection" entityId={String(ins.id)} />
          <div className="flex flex-wrap items-center gap-3 text-xs text-ink-600">
            <span>Evidencias: {ins.evidence.length ? ins.evidence.map((e) => e.original_name ?? e.filename).join(", ") : "ninguna"}</span>
            <label className="cursor-pointer text-slate underline">
              Adjuntar evidencia (JPG, PNG o PDF, máx. 10 MB)
              <input
                type="file"
                className="sr-only"
                accept="image/jpeg,image/png,application/pdf"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) upload(ins, f);
                  e.target.value = "";
                }}
              />
            </label>
          </div>
        </article>
      ))}
      {checklist.data && <NewInspection areaId={areaId} checklist={checklist.data} onCreated={list.reload} />}
      {!!checklist.error && <ErrorState error={checklist.error} onRetry={checklist.reload} />}
    </div>
  );
}
