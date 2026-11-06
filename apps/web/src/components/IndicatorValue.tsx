"use client";

import Link from "next/link";
import { useId, useState } from "react";
import type { Indicator } from "@/lib/api-types";
import { fmtIndicatorValue, unitLabel } from "@/lib/format";
import { StatusBadge } from "./StatusBadge";

export function MethodPopover({ indicator }: { indicator: Indicator }) {
  const [open, setOpen] = useState(false);
  const id = useId();
  return (
    <div className="relative">
      <button
        type="button"
        aria-expanded={open}
        aria-controls={id}
        onClick={() => setOpen((v) => !v)}
        className="text-xs font-medium text-slate underline decoration-slate/40 underline-offset-2 hover:decoration-slate"
      >
        {open ? "Ocultar método" : "Ver método y fuentes"}
      </button>
      {open && (
        <div
          id={id}
          role="region"
          aria-label={`Método y fuentes de ${indicator.label}`}
          className="mt-2 space-y-1.5 rounded border border-line bg-white p-3 text-xs leading-relaxed text-ink-700 shadow-sm"
        >
          {indicator.method && (
            <p><span className="font-semibold text-ink">Método. </span>{indicator.method}</p>
          )}
          {indicator.caveat && (
            <p><span className="font-semibold text-ink">Límite. </span>{indicator.caveat}</p>
          )}
          <p>
            <span className="font-semibold text-ink">Escala. </span>
            {indicator.spatial_scope || "—"}
            {indicator.temporal_scope ? `, ${indicator.temporal_scope}` : ""}
          </p>
          <p>
            <span className="font-semibold text-ink">Fuente. </span>
            {indicator.source_id ? (
              <Link className="text-slate underline" href={`/fuentes#${encodeURIComponent(indicator.source_id)}`}>
                {indicator.source_id}
              </Link>
            ) : (
              "Sin fuente asociada"
            )}
          </p>
          <p className="text-ink-500">Identificador: <code>{indicator.indicator_id}</code></p>
        </div>
      )}
    </div>
  );
}

export function IndicatorValue({ indicator, compact = false }: { indicator: Indicator | null | undefined; compact?: boolean }) {
  if (!indicator) {
    return (
      <div className="py-2 text-sm text-ink-500">
        Indicador no devuelto por la API. <StatusBadge status="unavailable" />
      </div>
    );
  }
  const unavailable = indicator.status === "unavailable" || indicator.value === null;
  const u = unitLabel(indicator.unit);
  return (
    <div className={compact ? "py-1.5" : "py-2.5"}>
      <div className="flex items-baseline justify-between gap-3">
        <span className="text-sm text-ink-600">{indicator.label}</span>
        <StatusBadge status={unavailable ? "unavailable" : indicator.status} />
      </div>
      <div className="mt-0.5 flex items-baseline gap-1.5">
        <span className={`font-cond tabular-nums ${compact ? "text-lg" : "text-2xl"} font-semibold ${unavailable ? "text-ash-800" : "text-ink"}`}>
          {fmtIndicatorValue(indicator.value, indicator.unit)}
        </span>
        {!unavailable && u && <span className="text-sm text-ink-500">{u}</span>}
        {indicator.temporal_scope && !unavailable && (
          <span className="ml-auto text-xs text-ink-500">{indicator.temporal_scope}</span>
        )}
      </div>
      {!compact && <div className="mt-1"><MethodPopover indicator={indicator} /></div>}
    </div>
  );
}
