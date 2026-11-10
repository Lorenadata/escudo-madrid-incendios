"use client";

import { useState } from "react";
import { apiFetch } from "@/lib/api";
import { fmtDate } from "@/lib/format";
import { useApi } from "@/lib/useApi";
import { ErrorState } from "./States";

export interface CommentEntry {
  id: string;
  entity_type: "area" | "inspection" | "plan_action";
  entity_id: string;
  kind: "comment" | "decision";
  body: string;
  author_name: string;
  created_at: string;
}

const KIND_LABEL = { comment: "Comentario", decision: "Decisión" } as const;

export function CommentItem({ c }: { c: CommentEntry }) {
  return (
    <li className={`rounded border p-2 text-xs ${c.kind === "decision" ? "border-slate bg-slate-50" : "border-line bg-white"}`}>
      <p className="text-ink-500">
        <span className="font-semibold text-ink-800">{KIND_LABEL[c.kind]}</span> · {c.author_name} · {fmtDate(c.created_at, true)}
      </p>
      <p className="mt-0.5 whitespace-pre-line text-ink-800">{c.body}</p>
    </li>
  );
}

/** M17 · Hilo de comentarios y decisiones de un elemento. Las entradas son inmutables (autor y fecha). */
export function CommentThread({
  entityType,
  entityId,
  canWrite = true,
  label,
}: {
  entityType: CommentEntry["entity_type"];
  entityId: string;
  canWrite?: boolean;
  label?: string;
}) {
  const [open, setOpen] = useState(false);
  const list = useApi<CommentEntry[]>(
    open ? `/v1/comments?entity_type=${entityType}&entity_id=${encodeURIComponent(entityId)}` : null,
  );
  const [body, setBody] = useState("");
  const [kind, setKind] = useState<CommentEntry["kind"]>("comment");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function send() {
    setErr(null);
    setBusy(true);
    try {
      await apiFetch("/v1/comments", { method: "POST", body: JSON.stringify({ entity_type: entityType, entity_id: entityId, kind, body }) });
      setBody("");
      list.reload();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "No se pudo guardar.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <details className="text-xs" onToggle={(e) => setOpen((e.target as HTMLDetailsElement).open)}>
      <summary className="cursor-pointer text-slate">{label ?? "Comentarios y decisiones"}</summary>
      <div className="mt-1 space-y-2">
        {!!list.error && <ErrorState error={list.error} onRetry={list.reload} />}
        {list.data && list.data.length === 0 && <p className="text-ink-500">Sin entradas todavía.</p>}
        {list.data && list.data.length > 0 && (
          <ol className="space-y-1">
            {list.data.map((c) => <CommentItem key={c.id} c={c} />)}
          </ol>
        )}
        {canWrite && (
          <div className="space-y-1">
            <textarea
              className="field min-h-[3.5rem] w-full py-1 text-xs"
              maxLength={2000}
              value={body}
              onChange={(e) => setBody(e.target.value)}
              aria-label={`Nueva entrada (${label ?? "comentarios y decisiones"})`}
              placeholder="Escribe un comentario o registra una decisión (no se puede editar después)"
            />
            <div className="flex flex-wrap items-center gap-2">
              <select className="field w-auto py-1 text-xs" value={kind} onChange={(e) => setKind(e.target.value as CommentEntry["kind"])} aria-label="Tipo de entrada">
                <option value="comment">Comentario</option>
                <option value="decision">Decisión</option>
              </select>
              <button type="button" className="btn-secondary py-1 text-xs" disabled={busy || !body.trim()} onClick={send}>
                Añadir entrada
              </button>
              {err && <span role="alert" className="text-rust">{err}</span>}
            </div>
          </div>
        )}
      </div>
    </details>
  );
}
