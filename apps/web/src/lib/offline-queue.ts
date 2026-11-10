// M21 · Cola local de inspecciones para el modo sin conexión (IndexedDB en el propio dispositivo).
// Solo guarda borradores pendientes de enviar; al sincronizar, el servidor deduplica por `client_uuid`.

export interface QueuedPhoto {
  name: string;
  type: string;
  blob: Blob;
}

export interface QueuedInspection {
  client_uuid: string;
  created_at: string;
  area_id: string;
  area_name: string;
  body: {
    area_id: string;
    inspected_on: string;
    inspector_name: string;
    items: { checklist_code: string; answer: string; observation: string }[];
    client_uuid: string;
  };
  photos: QueuedPhoto[];
  inspection_id?: string; // ya creada en el servidor, faltan fotos
  error?: string;
}

const DB = "escudo-campo";
const STORE = "queue";

function open(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (typeof indexedDB === "undefined") return reject(new Error("Este navegador no permite guardar sin conexión"));
    const req = indexedDB.open(DB, 1);
    req.onupgradeneeded = () => req.result.createObjectStore(STORE, { keyPath: "client_uuid" });
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error ?? new Error("No se pudo abrir el almacenamiento local"));
  });
}

async function tx<T>(mode: IDBTransactionMode, fn: (s: IDBObjectStore) => IDBRequest<T>): Promise<T> {
  const db = await open();
  return new Promise<T>((resolve, reject) => {
    const t = db.transaction(STORE, mode);
    const r = fn(t.objectStore(STORE));
    r.onsuccess = () => resolve(r.result);
    r.onerror = () => reject(r.error ?? new Error("Error del almacenamiento local"));
    t.oncomplete = () => db.close();
  });
}

export const queue = {
  all: () => tx<QueuedInspection[]>("readonly", (s) => s.getAll() as IDBRequest<QueuedInspection[]>),
  put: (q: QueuedInspection) => tx("readwrite", (s) => s.put(q)),
  remove: (id: string) => tx("readwrite", (s) => s.delete(id)),
};

export function newClientUuid(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) return crypto.randomUUID();
  // reserva para navegadores antiguos (no criptográfico, solo identificador de reenvío)
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
  });
}
