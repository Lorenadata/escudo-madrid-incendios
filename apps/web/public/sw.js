// M21 · Service worker de ESCUDO MADRID «Inspección en campo».
// Solo guarda en caché la página /campo y los recursos estáticos de Next.js para poder abrirla sin conexión.
// NUNCA guarda respuestas de la API (datos privados): las peticiones a la API pasan directamente a la red.
const CACHE = "escudo-campo-v1";
const SHELL = ["/campo", "/manifest.webmanifest", "/icon-escudo.svg"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k.startsWith("escudo-campo-") && k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return; // API (otro origen) y terceros: sin caché
  if (url.pathname.startsWith("/api/")) return; // API detrás del proxy del Space: sin caché
  if (req.mode === "navigate" && url.pathname === "/campo") {
    // red primero; sin conexión, la última copia guardada
    event.respondWith(
      fetch(req)
        .then((res) => { const copy = res.clone(); caches.open(CACHE).then((c) => c.put("/campo", copy)); return res; })
        .catch(() => caches.match("/campo")),
    );
    return;
  }
  if (url.pathname.startsWith("/_next/static/") || SHELL.includes(url.pathname)) {
    event.respondWith(
      caches.match(req).then((hit) => hit || fetch(req).then((res) => {
        if (res.ok) { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(req, copy)); }
        return res;
      })),
    );
  }
});
