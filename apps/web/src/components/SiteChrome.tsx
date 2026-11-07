"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/", label: "Explorador" },
  { href: "/comparar", label: "Comparar" },
  { href: "/analisis", label: "Análisis" },
  { href: "/demo", label: "Caso guiado" },
  { href: "/fuentes", label: "Fuentes" },
  { href: "/app", label: "Área de trabajo" },
];

export function SiteHeader() {
  const path = usePathname();
  return (
    <header className="border-b border-ink/15 bg-white">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:bg-white focus:p-2">
        Saltar al contenido
      </a>
      <div className="mx-auto flex max-w-[1600px] flex-wrap items-center gap-x-6 gap-y-1 px-4 py-2">
        <Link href="/" className="flex items-center gap-2" aria-label="ESCUDO MADRID, inicio">
          <svg width="22" height="22" viewBox="0 0 22 22" aria-hidden>
            <path d="M11 1.5 19.5 5v6.2c0 4.6-3.6 8-8.5 9.3-4.9-1.3-8.5-4.7-8.5-9.3V5Z" fill="#1E3B2F" />
            <path d="M5 13.5c2.2-1.6 4-1.6 6 0s3.8 1.6 6 0" stroke="#EEF1EF" strokeWidth="1.4" fill="none" />
            <path d="M5 10c2.2-1.6 4-1.6 6 0s3.8 1.6 6 0" stroke="#EEF1EF" strokeWidth="1.4" fill="none" opacity=".6" />
          </svg>
          <span className="font-cond text-lg font-bold tracking-tight text-ink">ESCUDO MADRID</span>
        </Link>
        <nav aria-label="Principal" className="flex flex-wrap gap-1">
          {NAV.map((n) => {
            const active = n.href === "/" ? path === "/" : path.startsWith(n.href);
            return (
              <Link
                key={n.href}
                href={n.href}
                aria-current={active ? "page" : undefined}
                className={`rounded px-2.5 py-1 text-sm ${active ? "bg-pine text-white" : "text-ink-700 hover:bg-granite"}`}
              >
                {n.label}
              </Link>
            );
          })}
        </nav>
        <span className="ml-auto hidden text-xs text-ink-500 lg:inline">
          Planificación preventiva de incendios forestales · proyecto DATAMAD 2026, no oficial
        </span>
      </div>
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="border-t border-ink/15 bg-white px-4 py-2.5 text-xs leading-relaxed text-ink-600">
      <p className="mx-auto max-w-[1600px]">
        ESCUDO MADRID es una herramienta de apoyo a la planificación. No sustituye a ASEM 112, AEMET, INFOMA ni a
        personal técnico competente. No emite alertas, rutas de evacuación ni aprobaciones.
      </p>
    </footer>
  );
}
