import type { Metadata } from "next";
import { Archivo } from "next/font/google";
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

export const metadata: Metadata = {
  title: "ESCUDO MADRID — Planificación preventiva de incendios forestales",
  description:
    "Datos abiertos de la Comunidad de Madrid, cartografía oficial y AEMET al servicio de la planificación preventiva. Proyecto DATAMAD 2026, no oficial.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="es" className={`${archivo.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col">
        <Suspense fallback={<div className="h-12 bg-pine" />}>
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
