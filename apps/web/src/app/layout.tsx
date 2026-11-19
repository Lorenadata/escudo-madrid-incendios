import type { Metadata } from "next";
import { Archivo, Bodoni_Moda } from "next/font/google";
import { Suspense } from "react";
import "maplibre-gl/dist/maplibre-gl.css";
import "./globals.css";
import { SiteFooter, SiteHeader } from "@/components/SiteChrome";

// Archivo: grotesca con eje de anchura. Una sola familia: rótulos estrechos (como los de un mapa
// topográfico) y texto a anchura normal.
const archivo = Archivo({
  variable: "--font-archivo",
  subsets: ["latin"],
  axes: ["wdth"],
});

// Bodoni Moda solo para títulos y grandes cifras: el contraste de sus trazos da el tono de la publicación.
const bodoni = Bodoni_Moda({
  variable: "--font-bodoni",
  subsets: ["latin"],
  axes: ["opsz"],
});

export const metadata: Metadata = {
  title: "ESCUDO MADRID — Planificación preventiva de incendios forestales",
  description:
    "Datos abiertos de la Comunidad de Madrid, cartografía oficial y AEMET al servicio de la planificación preventiva. Proyecto DATAMAD 2026, no oficial.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="es" className={`${archivo.variable} ${bodoni.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col">
        <Suspense fallback={<div className="h-14 bg-pine-900" />}>
          <SiteHeader />
        </Suspense>
        <main id="main" className="flex flex-1 flex-col">
          {children}
        </main>
        <SiteFooter />
      </body>
    </html>
  );
}
