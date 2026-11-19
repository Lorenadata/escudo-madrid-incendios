"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/", label: "Explorador" },
  { href: "/ranking", label: "Ranking" },
  { href: "/meteo", label: "Meteo" },
  { href: "/comparar", label: "Comparar" },
  { href: "/analisis", label: "Análisis" },
  { href: "/demo", label: "Caso guiado" },
  { href: "/normativa", label: "Normativa" },
  { href: "/avance", label: "Avance" },
  { href: "/fuentes", label: "Fuentes" },
  { href: "/app", label: "Área de trabajo" },
];

export function SiteHeader() {
  const path = usePathname();
  return (
    <header className="border-b border-brass/35 bg-pine-900 text-white">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:bg-white focus:p-2 focus:text-ink">
        Saltar al contenido
      </a>
      <div className="mx-auto flex max-w-[1600px] flex-wrap items-stretch gap-x-6 px-4">
        <Link href="/" className="flex items-center gap-2 py-2.5" aria-label="ESCUDO MADRID, inicio">
          <svg width="24" height="24" viewBox="0 0 22 22" aria-hidden>
            <path d="M11 1.5 19.5 5v6.2c0 4.6-3.6 8-8.5 9.3-4.9-1.3-8.5-4.7-8.5-9.3V5Z" fill="none" stroke="#D8B76A" strokeWidth="1.2" />
            <path d="M5.5 13.5c2-1.5 3.7-1.5 5.5 0s3.5 1.5 5.5 0" stroke="#F4EFE3" strokeWidth="1" fill="none" />
            <path d="M5.5 10c2-1.5 3.7-1.5 5.5 0s3.5 1.5 5.5 0" stroke="#D8B76A" strokeWidth="1" fill="none" />
          </svg>
          <span className="font-display text-[19px] leading-none tracking-[0.08em]">ESCUDO MADRID</span>
        </Link>
        <nav aria-label="Principal" className="-mx-4 flex min-w-0 basis-full overflow-x-auto px-4 sm:mx-0 sm:basis-auto sm:px-0">
          {NAV.map((n) => {
            const active = n.href === "/" ? path === "/" : path.startsWith(n.href);
            return (
              <Link
                key={n.href}
                href={n.href}
                aria-current={active ? "page" : undefined}
                className={`flex items-center whitespace-nowrap border-b-2 px-2.5 pb-2.5 pt-3 text-sm ${
                  active ? "border-brass font-medium text-white" : "border-transparent text-white/75 hover:border-brass/40 hover:text-white"
                }`}
              >
                {n.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="border-t border-line bg-white px-4 py-3 text-xs leading-relaxed text-ink-600">
      <div className="mx-auto flex max-w-[1600px] flex-wrap justify-between gap-x-8 gap-y-1">
        <p className="max-w-3xl">
          ESCUDO MADRID es una herramienta de apoyo a la planificación preventiva. No sustituye a ASEM 112, AEMET, INFOMA ni a
          personal técnico competente. No emite alertas, rutas de evacuación ni aprobaciones.
        </p>
        <p>
          Proyecto para DATAMAD 2026, no oficial. <Link href="/fuentes" className="underline underline-offset-2">Fuentes y licencias</Link>
        </p>
      </div>
    </footer>
  );
}
