// Tipos y cálculo en cliente de la puntuación de atención preventiva (misma fórmula que escudo_api.attention).

export type BlockId = "territory" | "history" | "residential" | "planning";
export type Weights = Record<BlockId, number>;

export interface RankingReason {
  block: BlockId | "context";
  text: string;
  points: number;
}

export interface RankingRow {
  ine_code: string;
  name: string;
  population_total: number | null;
  age_65_plus_share: number | null;
  high_share: number | null;
  risk_classes: { code: string | null; label: string; share: number }[];
  burnt_ha: number;
  zar: boolean | null;
  fires_total: number | null;
  plan_required: boolean | null;
  plan_approved: boolean | null;
  non_main_share: number | null;
  single_dwelling_building_share: number | null;
  components: Record<BlockId, number | null>;
  score: number | null;
  band: { id: string; label: string };
  reasons: RankingReason[];
  rank: number | null;
  stability_top20: number | null;
}

export interface RankingGap {
  municipalities: number;
  high_majority: number;
  high_majority_in_zar: number;
  high_majority_outside_zar: number;
  outside_zar_required_plan: number;
  outside_zar_population: number;
  outside_zar_codes: string[];
  plan_required: number;
  plan_required_approved: number;
  plan_required_not_approved: number;
  plan_required_blank: number;
}

export interface RankingResponse {
  status: string;
  weights: Weights;
  bands: { min: number; id: string; label: string }[];
  top_n: number;
  sources: string[];
  definition: string;
  caveat: string;
  gap: RankingGap;
  count: number;
  rows: RankingRow[];
}

/** Escala térmica de la puntuación, distinta de la rampa oficial de riesgo. Validada en superficie oscura. */
export const BAND_COLOR: Record<string, string> = {
  very_low: "#4C7FD1",
  low: "#3FC5CF",
  medium: "#E8C547",
  high: "#EE8233",
  very_high: "#EA3A54",
  unavailable: "#5B665F",
};

export const BANDS = [
  { id: "very_high", label: "Muy alta", min: 80 },
  { id: "high", label: "Alta", min: 60 },
  { id: "medium", label: "Media", min: 40 },
  { id: "low", label: "Baja", min: 20 },
  { id: "very_low", label: "Muy baja", min: 0 },
];

export const BLOCKS: { id: BlockId; label: string; help: string; color: string }[] = [
  { id: "territory", label: "Territorio", help: "Parte del término en riesgo alto o muy alto del mapa oficial.", color: "#D9663F" },
  { id: "history", label: "Historial", help: "Posición en siniestros 2015–2024 y superficie quemada, por km².", color: "#5B8DEF" },
  { id: "residential", label: "Contexto residencial", help: "Posición en población mayor, vivienda no principal y unifamiliar.", color: "#C9A040" },
  { id: "planning", label: "Planificación", help: "Territorio en esas clases si no consta plan municipal aprobado.", color: "#A67BE8" },
];

export function scoreWith(c: Record<BlockId, number | null>, w: Weights): number | null {
  if (c.territory === null) return null;
  let sum = 0;
  let total = 0;
  for (const b of BLOCKS) {
    const v = c[b.id];
    if (v !== null) {
      sum += v * w[b.id];
      total += w[b.id];
    }
  }
  return total > 0 ? (100 * sum) / total : null;
}

export function bandOf(score: number | null) {
  if (score === null) return { id: "unavailable", label: "No disponible" };
  return BANDS.find((b) => score >= b.min) ?? BANDS[BANDS.length - 1];
}

export interface LiveRow extends RankingRow {
  liveScore: number | null;
  liveBand: { id: string; label: string };
  liveRank: number | null;
}

/** Recalcula puntuación, banda y puesto con los pesos elegidos en pantalla. */
export function applyWeights(rows: RankingRow[], w: Weights): LiveRow[] {
  const scored = rows.map((r) => {
    const liveScore = scoreWith(r.components, w);
    return { ...r, liveScore, liveBand: bandOf(liveScore), liveRank: null as number | null };
  });
  scored.sort((a, b) => (b.liveScore ?? -1) - (a.liveScore ?? -1) || a.ine_code.localeCompare(b.ine_code));
  scored.forEach((r, i) => {
    r.liveRank = r.liveScore === null ? null : i + 1;
  });
  return scored;
}

export interface RegionalRow {
  ine_code: string;
  name: string;
  status: string;
  issued_at: string | null;
  gust_max_24h_kmh: number | null;
  gust_max_at: string | null;
  wind_dir_at_gust_max: string | null;
  precip_24h_mm: number | null;
  precip_total_mm: number | null;
  rh_min_24h_pct: number | null;
  temp_max_24h_c: number | null;
  gust_hourly_kmh: (number | null)[];
}

export interface RegionalWeather {
  status: "ok" | "warming" | "unavailable";
  refreshing: boolean;
  coverage: number;
  received: number;
  total: number;
  issued_at_latest: string | null;
  hours: string[];
  rows: RegionalRow[];
  disclaimer: string;
  attribution: string;
  method: string;
}

export interface CurrentRiskRow {
  ine_code: string;
  name: string;
  high_share: number | null;
  ffwi_max_24h: number | null;
  ffwi_max_at: string | null;
  rain_from: string | null;
  temp_c: number | null;
  rh_pct: number | null;
  wind_kmh: number | null;
  precip_24h_mm: number | null;
  gust_max_24h_kmh: number | null;
  ffwi_hourly: (number | null)[];
  score: number | null;
  band: { id: string; label: string };
  limiting: "territory" | "weather" | null;
  reasons: string[];
  rank: number | null;
}

export interface CurrentRiskResponse {
  status: "derived" | "warming" | "unavailable";
  refreshing: boolean;
  coverage: number;
  received: number;
  total: number;
  issued_at_latest: string | null;
  hours: string[];
  bands: { min: number; id: string; label: string }[];
  sources: string[];
  definition: string;
  caveat: string;
  attribution: string;
  reference: string;
  rows: CurrentRiskRow[];
}

const hourFmt = new Intl.DateTimeFormat("es-ES", { timeZone: "Europe/Madrid", hour: "2-digit", minute: "2-digit" });
const dayFmt = new Intl.DateTimeFormat("es-ES", { timeZone: "Europe/Madrid", weekday: "short", day: "numeric" });
const fullFmt = new Intl.DateTimeFormat("es-ES", { timeZone: "Europe/Madrid", weekday: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });

export const fmtHour = (iso: string) => hourFmt.format(new Date(iso));
export const fmtDay = (iso: string) => dayFmt.format(new Date(iso));
export const fmtDayHour = (iso: string) => fullFmt.format(new Date(iso));

/** Interpola en una rampa de colores hexadecimales (t entre 0 y 1). */
export function rampColor(ramp: string[], t: number): string {
  const c = Math.max(0, Math.min(0.9999, t)) * (ramp.length - 1);
  const i = Math.floor(c);
  const f = c - i;
  const ch = (h: string, o: number) => parseInt(h.slice(o, o + 2), 16);
  const mix = (o: number) => Math.round(ch(ramp[i], o) + (ch(ramp[i + 1], o) - ch(ramp[i], o)) * f);
  return `rgb(${mix(1)},${mix(3)},${mix(5)})`;
}

export const WIND_RAMP = ["#14302F", "#1C5E66", "#2A9AA6", "#7AD7D3", "#E3FFF8"];
export const WIND_MAX_KMH = 100; // escala fija: los colores significan lo mismo cada día
export const RAIN_STEPS = [
  { min: 15, color: "#BBDDFF", label: "15 mm o más" },
  { min: 5, color: "#5AA5EE", label: "5–15 mm" },
  { min: 1, color: "#2F76B8", label: "1–5 mm" },
  { min: 0.1, color: "#25527E", label: "0,1–1 mm" },
  { min: 0, color: "#1B2C33", label: "Sin lluvia medible" },
];
export const GUST_STEPS = [
  { min: 80, color: rampColor(WIND_RAMP, 0.9), label: "80 km/h o más" },
  { min: 60, color: rampColor(WIND_RAMP, 0.7), label: "60–80 km/h" },
  { min: 40, color: rampColor(WIND_RAMP, 0.5), label: "40–60 km/h" },
  { min: 20, color: rampColor(WIND_RAMP, 0.3), label: "20–40 km/h" },
  { min: 0, color: rampColor(WIND_RAMP, 0.1), label: "Menos de 20 km/h" },
];
