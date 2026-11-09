const nf = new Intl.NumberFormat("es-ES", { maximumFractionDigits: 1 });
const nf0 = new Intl.NumberFormat("es-ES", { maximumFractionDigits: 0 });
const eur = new Intl.NumberFormat("es-ES", { style: "currency", currency: "EUR", maximumFractionDigits: 0 });

export function fmtNumber(v: number | null | undefined, digits?: number): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  if (digits !== undefined) return new Intl.NumberFormat("es-ES", { maximumFractionDigits: digits }).format(v);
  return Math.abs(v) >= 100 ? nf0.format(v) : nf.format(v);
}

export function fmtEur(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return eur.format(v);
}

export function fmtShare(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return `${nf.format(v * 100)} %`;
}

/** Formatea el valor de un indicador: proporciones (unit "share"/"proporción"/0-1) se muestran en %. */
export function fmtIndicatorValue(value: number | string | null, unit?: string | null): string {
  if (value === null || value === undefined) return "No disponible";
  if (typeof value === "string") return value;
  const u = (unit || "").toLowerCase();
  if (u === "share" || u === "proporción" || u === "proporcion" || u === "ratio" || u === "0-1") return fmtShare(value);
  if (u === "%") return `${fmtNumber(value)} %`;
  if (u === "eur" || u === "€") return fmtEur(value);
  return fmtNumber(value);
}

export function unitLabel(unit?: string | null): string {
  if (!unit) return "";
  const u = unit.toLowerCase();
  if (["share", "proporción", "proporcion", "ratio", "0-1", "%", "eur", "€", "sí/no"].includes(u)) return "";
  return unit;
}

export function fmtDate(iso: string | null | undefined, withTime = false): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString("es-ES", withTime
    ? { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" }
    : { day: "2-digit", month: "short", year: "numeric" });
}
