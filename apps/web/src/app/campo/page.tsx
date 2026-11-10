"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState, useSyncExternalStore } from "react";
import { ApiError, apiFetch, getToken } from "@/lib/api";
import { useSessionToken } from "@/lib/browser-store";
import type { Area, ChecklistQuestion } from "@/lib/api-types";
import { newClientUuid, queue, type QueuedInspection } from "@/lib/offline-queue";

const ANSWERS = [
  { v: "si", l: "Sí" },
  { v: "parcial", l: "Parcial" },
  { v: "no", l: "No" },
  { v: "na", l: "No aplica" },
];
const CACHE_KEY = "escudo.campo.ref"; // ámbitos y lista de comprobación de la última conexión (no son datos de inspección)

interface RefData {
  areas: Pick<Area, "id" | "name" | "municipality_code">[];
  checklist: ChecklistQuestion[];
  saved_at: string;
}

const REF_EVENT = "escudo-campo-ref";

function readRefRaw(): string | null {
  try {
    return window.localStorage.getItem(CACHE_KEY);
  } catch {
    return null;
  }
}

function writeRef(r: RefData) {
  try {
    window.localStorage.setItem(CACHE_KEY, JSON.stringify(r));
    window.dispatchEvent(new Event(REF_EVENT));
  } catch {
    /* sin almacenamiento: el formulario solo funcionará con conexión */
  }
}

function subscribeRef(cb: () => void) {
  window.addEventListener(REF_EVENT, cb);
  window.addEventListener("storage", cb);
  return () => {
    window.removeEventListener(REF_EVENT, cb);
    window.removeEventListener("storage", cb);
  };
}

function subscribeOnline(cb: () => void) {
  window.addEventListener("online", cb);
  window.addEventListener("offline", cb);
  return () => {
    window.removeEventListener("online", cb);
    window.removeEventListener("offline", cb);
  };
}

/** M21 · Inspección en campo: formulario que funciona sin conexión y sincroniza al volver la red. */
export default function CampoPage() {
  const online = useSyncExternalStore(subscribeOnline, () => navigator.onLine, () => true);
  const token = useSessionToken();
  const [expired, setExpired] = useState(false);
  const hasToken = !!token && !expired;
  const refRaw = useSyncExternalStore(subscribeRef, readRefRaw, () => null);
  const ref = useMemo<RefData | null>(() => {
    try {
      return refRaw ? (JSON.parse(refRaw) as RefData) : null;
    } catch {
      return null;
    }
  }, [refRaw]);
  const [pending, setPending] = useState<QueuedInspection[]>([]);
  const [msg, setMsg] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [areaId, setAreaId] = useState("");
  const [inspector, setInspector] = useState("");
  const [answers, setAnswers] = useState<Record<string, { answer: string; observation: string }>>({});
  const [photos, setPhotos] = useState<File[]>([]);

  const reloadQueue = useCallback(() => queue.all().then(setPending).catch(() => setPending([])), []);

  // Con conexión y sesión: refresca ámbitos y lista de comprobación para poder trabajar luego sin red.
  useEffect(() => {
    if (!online || !hasToken) return;
    Promise.all([apiFetch<Area[]>("/v1/areas"), apiFetch<ChecklistQuestion[]>("/v1/checklist")])
      .then(([areas, checklist]) => {
        const r = { areas: areas.map((a) => ({ id: a.id, name: a.name, municipality_code: a.municipality_code })), checklist, saved_at: new Date().toISOString() };
        writeRef(r);
      })
      .catch((e) => {
        if (e instanceof ApiError && e.status === 401) setExpired(true);
      });
  }, [online, hasToken]);

  const sync = useCallback(async () => {
    if (!navigator.onLine) return setMsg("Sin conexión: las inspecciones siguen guardadas en este dispositivo.");
    if (!getToken()) return setMsg("Inicia sesión para enviar las inspecciones guardadas.");
    setSyncing(true);
    setMsg(null);
    let sent = 0;
    for (const q of await queue.all()) {
      try {
        if (!q.inspection_id) {
          const r = await apiFetch<{ id: string }>("/v1/inspections", { method: "POST", body: JSON.stringify(q.body) });
          q.inspection_id = String(r.id);
          await queue.put(q);
        }
        for (const ph of q.photos) {
          const fd = new FormData();
          fd.append("file", new File([ph.blob], ph.name, { type: ph.type }));
          await apiFetch(`/v1/inspections/${q.inspection_id}/evidence`, { method: "POST", body: fd });
        }
        await queue.remove(q.client_uuid);
        sent += 1;
      } catch (e) {
        if (e instanceof ApiError && e.status === 401) {
          setExpired(true);
          setMsg("La sesión ha caducado: inicia sesión para terminar de enviar.");
          break;
        }
        if (e instanceof ApiError && e.status !== 0) {
          q.error = e.message;
          await queue.put(q);
        } else {
          break; // fallo de red: se reintentará
        }
      }
    }
    setSyncing(false);
    await reloadQueue();
    if (sent) setMsg(`${sent} inspección${sent === 1 ? "" : "es"} enviada${sent === 1 ? "" : "s"} y registrada${sent === 1 ? "" : "s"}.`);
  }, [reloadQueue]);

  // Arranque: registra el service worker, carga la cola local y sincroniza al recuperar la conexión.
  useEffect(() => {
    if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js").catch(() => undefined);
    queue.all().then((list) => {
      setPending(list);
      if (list.length && navigator.onLine && getToken()) sync();
    }).catch(() => setPending([]));
    const onOnline = () => {
      if (getToken()) sync();
    };
    window.addEventListener("online", onOnline);
    return () => window.removeEventListener("online", onOnline);
  }, [sync]);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (!ref) return;
    const area = ref.areas.find((a) => String(a.id) === areaId);
    if (!area) return setMsg("Elige un ámbito.");
    const client_uuid = newClientUuid();
    const items = ref.checklist
      .filter((c) => answers[c.code]?.answer)
      .map((c) => ({ checklist_code: c.code, answer: answers[c.code].answer, observation: answers[c.code].observation.slice(0, 2000) }));
    if (!items.length) return setMsg("Responde al menos un punto de la lista.");
    const q: QueuedInspection = {
      client_uuid, created_at: new Date().toISOString(), area_id: String(area.id), area_name: area.name,
      body: { area_id: String(area.id), inspected_on: new Date().toISOString().slice(0, 10), inspector_name: inspector.trim(), items, client_uuid },
      photos: photos.slice(0, 5).map((f) => ({ name: f.name, type: f.type, blob: f })),
    };
    try {
      await queue.put(q);
    } catch (err) {
      return setMsg(err instanceof Error ? err.message : "No se pudo guardar en el dispositivo.");
    }
    setAnswers({});
    setPhotos([]);
    await reloadQueue();
    setMsg(navigator.onLine ? "Inspección guardada; enviando…" : "Inspección guardada en el dispositivo. Se enviará al recuperar la conexión.");
    if (navigator.onLine) sync();
  }

  return (
    <div className="mx-auto w-full max-w-lg space-y-4 px-4 py-4">
      <header>
        <h1 className="font-cond text-2xl font-semibold text-ink">Inspección en campo</h1>
        <p className="text-sm text-ink-600">Registra la inspección aunque no haya cobertura. Se envía sola al recuperar la conexión.</p>
      </header>

      <div role="status" className={`flex flex-wrap items-center gap-2 rounded border p-2 text-sm ${online ? "border-pine bg-pine-50" : "border-ochre bg-ochre-50"}`}>
        <strong>{online ? "Con conexión" : "Sin conexión"}</strong>
        <span>· {pending.length} pendiente{pending.length === 1 ? "" : "s"} de enviar</span>
        <button type="button" className="ml-auto text-slate underline" disabled={syncing || !pending.length} onClick={sync}>
          {syncing ? "Enviando…" : "Enviar ahora"}
        </button>
      </div>
      {msg && <p role="alert" className="text-sm text-ink-800">{msg}</p>}

      {!hasToken && (
        <p className="rounded border border-line bg-white p-3 text-sm">
          Para descargar tus ámbitos y enviar inspecciones, <Link className="text-slate underline" href="/login?next=/campo">inicia sesión</Link>.
          {ref && " Puedes seguir registrando inspecciones con los datos guardados en este dispositivo."}
        </p>
      )}

      {!ref ? (
        <p className="text-sm text-ink-600">
          Abre esta página una vez con conexión y sesión iniciada para guardar tus ámbitos en el dispositivo.
        </p>
      ) : (
        <form onSubmit={save} className="space-y-4">
          <p className="text-xs text-ink-500">Ámbitos y lista guardados el {new Date(ref.saved_at).toLocaleString("es-ES")}.</p>
          <div>
            <label htmlFor="campo-area" className="label">Ámbito</label>
            <select id="campo-area" className="field" value={areaId} onChange={(e) => setAreaId(e.target.value)} required>
              <option value="">Elige un ámbito…</option>
              {ref.areas.map((a) => <option key={a.id} value={String(a.id)}>{a.name}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="campo-inspector" className="label">Persona que inspecciona</label>
            <input id="campo-inspector" className="field" minLength={2} maxLength={200} required value={inspector} onChange={(e) => setInspector(e.target.value)} />
          </div>
          <fieldset className="space-y-3">
            <legend className="label">Lista de comprobación</legend>
            {ref.checklist.map((c) => (
              <div key={c.code} className="rounded border border-line bg-white p-2">
                <p className="text-sm font-medium text-ink">{c.question}</p>
                <div className="mt-1 flex flex-wrap gap-1" role="radiogroup" aria-label={c.question}>
                  {ANSWERS.map((a) => (
                    <label key={a.v} className={`cursor-pointer rounded border px-3 py-2 text-sm ${answers[c.code]?.answer === a.v ? "border-pine bg-pine-50 font-semibold" : "border-line"}`}>
                      <input type="radio" className="sr-only" name={`q-${c.code}`} value={a.v} checked={answers[c.code]?.answer === a.v}
                        onChange={() => setAnswers((s) => ({ ...s, [c.code]: { answer: a.v, observation: s[c.code]?.observation ?? "" } }))} />
                      {a.l}
                    </label>
                  ))}
                </div>
                {answers[c.code]?.answer && (
                  <input className="field mt-1 text-sm" maxLength={2000} placeholder="Observación (opcional)" aria-label={`Observación: ${c.question}`}
                    value={answers[c.code].observation}
                    onChange={(e) => setAnswers((s) => ({ ...s, [c.code]: { ...s[c.code], observation: e.target.value } }))} />
                )}
              </div>
            ))}
          </fieldset>
          <div>
            <label htmlFor="campo-fotos" className="label">Fotos (JPG o PNG, hasta 5)</label>
            <input id="campo-fotos" type="file" accept="image/jpeg,image/png" capture="environment" multiple
              onChange={(e) => setPhotos(Array.from(e.target.files ?? []).slice(0, 5))} />
            {photos.length > 0 && <p className="text-xs text-ink-600">{photos.length} foto{photos.length === 1 ? "" : "s"} seleccionada{photos.length === 1 ? "" : "s"}</p>}
          </div>
          <button type="submit" className="btn-primary w-full py-3">Guardar inspección</button>
        </form>
      )}

      {pending.length > 0 && (
        <section aria-labelledby="pend-h" className="space-y-1">
          <h2 id="pend-h" className="font-cond text-base font-semibold">Pendientes de enviar</h2>
          <ul className="space-y-1 text-sm">
            {pending.map((q) => (
              <li key={q.client_uuid} className="rounded border border-line bg-white p-2">
                {q.area_name} · {new Date(q.created_at).toLocaleString("es-ES")} · {q.body.items.length} puntos · {q.photos.length} foto(s)
                {q.error && <span className="block text-xs text-rust">No aceptada por el servidor: {q.error}</span>}
              </li>
            ))}
          </ul>
        </section>
      )}
      <p className="text-xs text-ink-500">
        Las inspecciones quedan «pendientes de revisión técnica». Esta herramienta no sustituye a ASEM 112 ni emite alertas.
      </p>
    </div>
  );
}
