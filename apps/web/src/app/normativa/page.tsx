"use client";

import { useState } from "react";
import { ErrorState, Loading, Empty } from "@/components/States";
import { StatusBadge } from "@/components/StatusBadge";
import { useApi } from "@/lib/useApi";

interface DocResult {
  doc_id: string;
  doc_title: string;
  pdf_page: number;
  printed_page: number | null;
  text: string;
  url: string;
  score: number;
  matched_terms: string[];
}

interface SearchResponse {
  query: string;
  status: string;
  disclaimer: string;
  sources: string[];
  results: DocResult[];
}

interface Evaluation {
  status: string;
  k?: number;
  hits: number | null;
  total: number | null;
  method?: string;
  items: { q: string; expect: string; doc: string; hit: boolean; top_pages: string[] }[];
}

const EXAMPLES = [
  "¿Cuándo es la época de peligro alto?",
  "¿Qué anchura debe tener la faja perimetral de una urbanización?",
  "¿Quién inspecciona las medidas de prevención en las urbanizaciones?",
  "¿Se pueden hacer quemas en época de peligro bajo?",
];

function fold(s: string) {
  return s.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();
}

/** Resalta las palabras del texto cuya raíz coincide con un término buscado (solo visual). */
function Highlighted({ text, terms }: { text: string; terms: string[] }) {
  if (!terms.length) return <>{text}</>;
  return (
    <>
      {text.split(/(\s+)/).map((w, i) => {
        const f = fold(w).replace(/[^a-z0-9]/g, "");
        return terms.some((t) => t.length > 2 && f.startsWith(t)) ? (
          <mark key={i} className="rounded bg-ochre-50 px-0.5 text-ink">{w}</mark>
        ) : (
          <span key={i}>{w}</span>
        );
      })}
    </>
  );
}

export default function NormativaPage() {
  const [input, setInput] = useState("");
  const [q, setQ] = useState("");
  const res = useApi<SearchResponse>(q.length >= 3 ? `/v1/docs/search?q=${encodeURIComponent(q)}&k=5` : null);
  const ev = useApi<Evaluation>("/v1/docs/evaluation");

  return (
    <div className="mx-auto w-full max-w-4xl space-y-5 px-4 py-6">
      <header className="max-w-prose">
        <h1 className="font-cond text-2xl font-semibold text-ink">Normativa con citas</h1>
        <p className="text-sm text-ink-600">
          Busca en el Plan Anual de Prevención, Vigilancia y Extinción de Incendios Forestales 2026 y en el Decreto INFOMA.
          Se muestran <strong>fragmentos literales</strong> con documento y página: no se redactan respuestas.
        </p>
      </header>

      <form
        className="flex flex-wrap gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          setQ(input.trim());
        }}
      >
        <label htmlFor="docq" className="sr-only">Pregunta o términos de búsqueda</label>
        <input
          id="docq"
          className="field min-w-[16rem] flex-1"
          maxLength={300}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ej.: ¿cuándo es la época de peligro alto?"
        />
        <button type="submit" className="btn-primary" disabled={input.trim().length < 3}>Buscar en la normativa</button>
      </form>
      <div className="flex flex-wrap gap-2 text-xs">
        {EXAMPLES.map((ex) => (
          <button key={ex} type="button" className="rounded border border-line bg-white px-2 py-1 text-slate hover:bg-granite"
            onClick={() => { setInput(ex); setQ(ex); }}>
            {ex}
          </button>
        ))}
      </div>

      {res.loading && <Loading label="Buscando" />}
      {!!res.error && <ErrorState error={res.error} onRetry={res.reload} />}
      {res.data && (
        <section aria-label="Resultados" className="space-y-3">
          <p role="note" className="rounded border-l-4 border-ochre bg-ochre-50 p-2 text-xs text-ink-800">{res.data.disclaimer}</p>
          {res.data.results.length === 0 ? (
            <Empty title="Sin fragmentos relevantes">Prueba con otras palabras. No se muestra nada que no esté en los documentos.</Empty>
          ) : (
            <ol className="space-y-3">
              {res.data.results.map((r, i) => (
                <li key={`${r.doc_id}-${r.pdf_page}`} className="panel space-y-2">
                  <div className="flex flex-wrap items-center gap-2 text-xs">
                    <span className="font-semibold text-ink">{i + 1}. {r.doc_title}</span>
                    <StatusBadge status="official" className="ml-auto" />
                  </div>
                  <blockquote className="border-l-2 border-line pl-3 text-sm leading-relaxed text-ink-800">
                    <Highlighted text={r.text} terms={r.matched_terms} />
                  </blockquote>
                  <p className="text-xs text-ink-500">
                    {r.doc_id} · página {r.pdf_page} del PDF{r.printed_page ? ` (BOCM pág. ${r.printed_page})` : ""} ·{" "}
                    <a className="text-slate underline" href={r.url} target="_blank" rel="noopener noreferrer">Abrir el documento en esa página</a>
                  </p>
                </li>
              ))}
            </ol>
          )}
        </section>
      )}

      {ev.data && ev.data.total && (
        <details className="panel text-sm">
          <summary className="cursor-pointer font-medium">
            Cómo se ha evaluado: {ev.data.hits} de {ev.data.total} preguntas con la respuesta entre los {ev.data.k ?? 3} primeros fragmentos
          </summary>
          <p className="mt-2 text-xs text-ink-600">{ev.data.method}</p>
          <ul className="mt-2 space-y-1 text-xs">
            {ev.data.items.map((it) => (
              <li key={it.q} className={it.hit ? "text-ink-700" : "text-rust"}>
                {it.hit ? "✓" : "✗"} {it.q} <span className="text-ink-500">— esperado: «{it.expect}» ({it.doc})</span>
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}
