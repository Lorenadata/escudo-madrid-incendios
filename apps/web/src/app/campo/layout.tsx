import type { Metadata, Viewport } from "next";

export const metadata: Metadata = {
  title: "Inspección en campo · ESCUDO MADRID",
  description: "Registro de inspecciones preventivas sin conexión, con sincronización al recuperar la red.",
  manifest: "/manifest.webmanifest",
  icons: { icon: "/icon-escudo.svg", apple: "/icon-escudo.svg" },
};

export const viewport: Viewport = { themeColor: "#1E3B2F", width: "device-width", initialScale: 1 };

export default function CampoLayout({ children }: { children: React.ReactNode }) {
  return children;
}
