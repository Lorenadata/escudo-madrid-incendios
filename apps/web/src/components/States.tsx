import type { ReactNode } from "react";

export function Loading({ label = "Cargando datos" }: { label?: string }) {
  return (
    <div role="status" aria-live="polite" className="flex items-center gap-2 py-6 text-sm text-ink-600">
      <span className="inline-block h-3 w-3 animate-pulse rounded-full bg-pine" aria-hidden />
      {label}…
    </div>
  );
}

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const msg = error instanceof Error ? error.message : String(error);
  return (
    <div role="alert" className="my-3 rounded border-l-4 border-rust bg-rust-50 p-3 text-sm text-ink-800">
      <p className="font-semibold text-rust">No se han podido cargar los datos</p>
      <p className="mt-1">{msg}</p>
      {onRetry && (
        <button type="button" onClick={onRetry} className="btn-secondary mt-2">
          Reintentar
        </button>
      )}
    </div>
  );
}

export function Empty({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="my-3 rounded border border-dashed border-line p-4 text-sm text-ink-600">
      <p className="font-semibold text-ink">{title}</p>
      {children && <div className="mt-1">{children}</div>}
    </div>
  );
}
