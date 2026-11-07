---
title: ESCUDO MADRID
emoji: 🌲
colorFrom: green
colorTo: yellow
sdk: docker
app_port: 7860
startup_duration_timeout: 1h
short_description: Planificación preventiva de incendios forestales (DATAMAD)
---

# ESCUDO MADRID · demo pública

Plataforma abierta de **planificación preventiva de incendios forestales** para municipios y urbanizaciones de la Comunidad de Madrid (DATAMAD 2026). Participante: **Lorena Marcos**.

- Código fuente (EUPL-1.2): https://github.com/Lorenadata/escudo-madrid-incendios
- Este Space construye el repositorio público en un commit fijo (`Dockerfile`) y ejecuta PostGIS, la API y la web en un único contenedor.
- Datos reales del Portal de Datos Abiertos de la Comunidad de Madrid, la cartografía IDEM y AEMET, con su fuente y licencia visibles.
- La organización, la urbanización, la inspección y los presupuestos de la demo son **ficticios y están etiquetados**. Cada reinicio restaura la demo; no subas datos ni fotos reales.

Cuentas ficticias (contraseña `demo-escudo-2026`): `gestor@demo.escudo.local`, `tecnico@demo.escudo.local`, `municipal@demo.escudo.local`. Caso guiado sin cuenta: `/demo`.

> Herramienta de apoyo a la planificación. No sustituye a ASEM 112, AEMET, INFOMA ni a personal técnico competente. No emite alertas, rutas de evacuación ni aprobaciones de PAIF.
