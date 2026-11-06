"use client";

import { useSyncExternalStore } from "react";
import { getToken } from "./api";

const noop = () => () => {};

function subscribeHash(cb: () => void) {
  window.addEventListener("hashchange", cb);
  return () => window.removeEventListener("hashchange", cb);
}

/** Hash de la URL (sin «#»); cadena vacía en el servidor. */
export function useHash(): string {
  return useSyncExternalStore(subscribeHash, () => window.location.hash.replace(/^#/, ""), () => "");
}

/** Token de sesión: `undefined` mientras no se ha hidratado (servidor), `null` si no hay sesión. */
export function useSessionToken(): string | null | undefined {
  return useSyncExternalStore(noop, () => getToken(), () => undefined);
}
