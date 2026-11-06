"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "./api";

interface State<T> {
  key: string | null;
  path: string | null;
  data: T | null;
  error: unknown;
}

/** GET contra la API con estados de carga/error. Mantiene el último dato del mismo path mientras recarga. */
export function useApi<T>(path: string | null) {
  const [tick, setTick] = useState(0);
  const key = path ? `${path}#${tick}` : null;
  const [state, setState] = useState<State<T>>({ key: null, path: null, data: null, error: null });

  const reload = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    if (!path || !key) return;
    let cancelled = false;
    apiFetch<T>(path)
      .then((data) => {
        if (!cancelled) setState({ key, path, data, error: null });
      })
      .catch((error) => {
        if (!cancelled) setState({ key, path, data: null, error });
      });
    return () => {
      cancelled = true;
    };
  }, [key, path]);

  const samePath = state.path === path;
  return {
    data: samePath ? state.data : null,
    error: state.key === key ? state.error : null,
    loading: !!key && state.key !== key,
    reload,
  };
}
