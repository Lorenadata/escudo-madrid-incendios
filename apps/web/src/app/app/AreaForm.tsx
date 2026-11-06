"use client";

import { useState } from "react";
import { apiFetch } from "@/lib/api";
import type { Area, MunicipalitySummary } from "@/lib/api-types";

export function AreaForm({ municipalities, onCreated }: { municipalities: MunicipalitySummary[]; onCreated: (a: Area) => void }) {
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const a = await apiFetch<Area>("/v1/areas", {
        method: "POST",
        body: JSON.stringify({ name, municipality_code: code, description }),
      });
      onCreated(a);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="panel space-y-2">
      <div>
        <label htmlFor="an" className="label">Nombre del ámbito</label>
        <input id="an" className="field" required minLength={2} value={name} onChange={(e) => setName(e.target.value)} />
      </div>
      <div>
        <label htmlFor="am" className="label">Municipio</label>
        <select id="am" className="field" required value={code} onChange={(e) => setCode(e.target.value)}>
          <option value="">Elige un municipio</option>
          {municipalities.map((m) => <option key={m.ine_code} value={m.ine_code}>{m.name}</option>)}
        </select>
      </div>
      <div>
        <label htmlFor="ad" className="label">Descripción</label>
        <textarea id="ad" className="field" rows={2} value={description} onChange={(e) => setDescription(e.target.value)} />
      </div>
      <p className="text-xs text-ink-500">No incluyas direcciones exactas ni datos personales.</p>
      {error && <p role="alert" className="text-sm text-rust">{error}</p>}
      <button type="submit" className="btn-primary" disabled={busy || name.length < 2 || !code}>
        {busy ? "Guardando…" : "Guardar ámbito"}
      </button>
    </form>
  );
}
