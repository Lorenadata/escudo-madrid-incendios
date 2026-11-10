"use client";

import { useState } from "react";
import { CommentItem, CommentThread, type CommentEntry } from "@/components/CommentThread";
import { ErrorState, Loading, Empty } from "@/components/States";
import { useApi } from "@/lib/useApi";

interface DecisionLog {
  area_id: string;
  count: number;
  entries: CommentEntry[];
  notice: string;
}

const ORIGIN = { area: "Ámbito", inspection: "Inspección", plan_action: "Actuación del plan" } as const;

/** M17 · Registro de decisiones del ámbito (de todas sus inspecciones y actuaciones), con autor y fecha. */
export function DecisionsPanel({ areaId, canWrite }: { areaId: string; canWrite: boolean }) {
  const [kind, setKind] = useState<"decision" | "all">("decision");
  const log = useApi<DecisionLog>(`/v1/areas/${encodeURIComponent(areaId)}/decisions?kind=${kind}`);
  return (
    <section aria-labelledby="decisions-h" className="max-w-3xl space-y-3">
      <div className="flex flex-wrap items-center gap-3">
        <h3 id="decisions-h" className="font-cond text-lg font-semibold">Registro de decisiones</h3>
        <label className="ml-auto flex items-center gap-2 text-sm">
          <input type="checkbox" checked={kind === "all"} onChange={(e) => setKind(e.target.checked ? "all" : "decision")} />
          Incluir comentarios
        </label>
        <button type="button" className="text-xs text-slate underline" onClick={log.reload}>Actualizar registro</button>
      </div>
      {log.loading && !log.data && <Loading label="Cargando registro" />}
      {!!log.error && <ErrorState error={log.error} onRetry={log.reload} />}
      {log.data && (
        <>
          <p className="text-xs text-ink-500">{log.data.notice}</p>
          {log.data.count === 0 ? (
            <Empty title="Sin decisiones registradas">Registra decisiones desde una actuación, una inspección o aquí mismo.</Empty>
          ) : (
            <ol className="space-y-1">
              {log.data.entries.map((c) => (
                <div key={c.id}>
                  <p className="text-xs text-ink-500">{ORIGIN[c.entity_type]}</p>
                  <CommentItem c={c} />
                </div>
              ))}
            </ol>
          )}
        </>
      )}
      <div className="panel">
        <CommentThread entityType="area" entityId={areaId} canWrite={canWrite} label="Comentarios y decisiones sobre el ámbito" />
      </div>
    </section>
  );
}
