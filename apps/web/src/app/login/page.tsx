"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { apiFetch, setToken } from "@/lib/api";
import type { LoginResponse } from "@/lib/api-types";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const r = await apiFetch<LoginResponse>("/v1/auth/login", {
        method: "POST",
        auth: false,
        body: JSON.stringify({ email, password }),
      });
      setToken(r.access_token);
      router.push("/app");
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se ha podido iniciar sesión");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto w-full max-w-sm px-4 py-12">
      <h1 className="font-cond text-2xl font-semibold text-ink">Iniciar sesión</h1>
      <p className="mt-1 text-sm text-ink-600">
        Acceso para gestores de urbanizaciones, personal técnico y responsables municipales. Cada cuenta solo ve los datos de su
        organización.
      </p>
      <form onSubmit={submit} className="panel mt-5 space-y-3" noValidate>
        <div>
          <label htmlFor="email" className="label">Correo electrónico</label>
          <input id="email" type="email" autoComplete="username" required className="field" value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div>
          <label htmlFor="password" className="label">Contraseña</label>
          <input id="password" type="password" autoComplete="current-password" required className="field" value={password} onChange={(e) => setPassword(e.target.value)} />
        </div>
        {error && <p role="alert" className="text-sm text-rust">{error}</p>}
        <button type="submit" className="btn-primary w-full" disabled={busy || !email || !password}>
          {busy ? "Iniciando sesión…" : "Iniciar sesión"}
        </button>
      </form>
      <p className="mt-4 text-xs text-ink-500">
        En el entorno local de demostración las cuentas ficticias están definidas en <code>fixtures/synthetic/demo_seed.json</code>.
        Para ver el recorrido sin cuenta, abre el caso guiado.
      </p>
    </div>
  );
}
