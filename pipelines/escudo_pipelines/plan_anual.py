"""DOC-01 · Plan Anual de Prevención, Vigilancia y Extinción de Incendios Forestales de la Comunidad de Madrid 2026.

Documento oficial (PDF) publicado en el Portal de Transparencia de la Comunidad de Madrid. De él se extraen,
de forma LITERAL y con página citada:

- Anexo II (pág. 59): términos municipales declarados Zonas de Alto Riesgo (ZAR). El texto (pág. 16) declara 59.
- Anexo I (págs. 54–58): número de siniestros por término municipal de origen y causa, 2015–2024 (fuente EGIF).

No se corrige ningún valor. Las erratas de nombre del documento se emparejan con el municipio INE mediante una
tabla explícita (`NAME_FIXES`) y quedan registradas; las filas cuyo total publicado no coincide con la suma de
causas se marcan (`total_matches_causes = false`); las filas incompletas no se interpretan (null).

    python -m escudo_pipelines.plan_anual fetch       # descarga + manifest (SHA-256)
    python -m escudo_pipelines.plan_anual transform   # data/processed/plan/
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
import unicodedata
from datetime import UTC, datetime

import httpx

from .fetch import RAW_DIR, REPO_ROOT
from .sources import SourceSpec

SOURCE_ID = "DOC-01"
URL = "https://www.comunidad.madrid/transparencia/sites/default/files/plan_anual_iiff_2026.pdf"
PDF_NAME = "plan_anual_iiff_2026.pdf"
OUT_DIR = REPO_ROOT / "data" / "processed" / "plan"
MUNICIPALITIES_CSV = REPO_ROOT / "data" / "processed" / "cam" / "municipal_indicators.csv"

ZAR_PAGE = 59          # numeración del PDF (1-based)
ZAR_COUNT_PAGE = 16
FIRES_PAGES = range(54, 59)
ZAR_DECLARED = 59
FIRES_PERIOD = "2015-2024"
CAUSES = ("rayo", "negligencia_accidente", "intencionado", "desconocida", "reproducido")

SPEC = SourceSpec(
    source_id=SOURCE_ID,
    portal="CAM-DOC",
    ckan_id=None,
    title="Plan Anual de Prevención, Vigilancia y Extinción de Incendios Forestales de la Comunidad de Madrid 2026",
    producer="Comunidad de Madrid (Consejería de Medio Ambiente, Agricultura e Interior)",
    catalog_url=URL,
    license="Documento oficial público CAM (cita obligatoria)",  # ≤64 (data_sources.license)
    spatial_scope="término municipal",
    temporal_scope="ZAR vigentes en 2026; siniestros 2015–2024",
    use_in_product="Municipios declarados Zona de Alto Riesgo (Anexo II) y siniestros por municipio y causa 2015–2024 (Anexo I)",
    caveats=("Extracción literal del PDF con página citada. El Anexo I contiene filas cuyo total no coincide con la "
             "suma de causas y filas incompletas: se muestran tal cual y marcadas. Fuente original del Anexo I: EGIF."),
    resource_format="PDF",
)

# Erratas / variantes del documento → nombre CAM-01 (se registran en quality.json)
NAME_FIXES = {
    "torredolones": "torrelodones",
    "san maria de la alameda": "santa maria de la alameda",
    "horcajo de la sierra-aoslos": "horcajo de la sierra-aoslos",
    "canencia de la sierra": "canencia",
    "colmenar de arroyo": "colmenar del arroyo",
    "lozoya del valle": "lozoya",
    "fresnedilla de la oliva": "fresnedillas de la oliva",
    "gargantilla del lozoya": "gargantilla del lozoya y pinilla de buitrago",
}
OUTSIDE_REGION = {"real sitio de san ildefonso", "almorox"}  # municipios de Segovia y Toledo en el Anexo I


def norm(name: str) -> str:
    """Clave de emparejamiento: sin tildes, minúsculas, artículo pospuesto («Acebeda, La» / «Acebeda (La)» → «la acebeda»)."""
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower().strip()
    s = re.sub(r"\s+", " ", s)
    m = re.fullmatch(r"(.+?)\s*(?:,\s*|\()\s*(el|la|los|las)\)?", s)
    if m:
        s = f"{m.group(2)} {m.group(1)}"
    return NAME_FIXES.get(s, s)


def municipality_index() -> dict[str, tuple[str, str]]:
    with MUNICIPALITIES_CSV.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    idx = {norm(r["name"]): (r["ine_code"], r["name"]) for r in rows}
    # NAME_FIXES puede apuntar a un nombre que, normalizado, ya es la clave CAM-01
    return idx


def parse_zar(text: str) -> list[tuple[int, str]]:
    """Líneas «N Nombre [N Nombre]» del Anexo II → [(n, nombre literal)]."""
    out = []
    for line in text.splitlines():
        for n, name in re.findall(r"(\d{1,2}) (\D+?)(?=\s+\d{1,2} |\s*$)", line.strip()):
            out.append((int(n), name.strip()))
    return sorted(set(out))


_NAME = re.compile(r"^([A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ ,.'\-]+?)(?=\s+\d|\s*$)")
_SKIP = ("PLAN ANUAL", "ANEXO", "NÚMERO", "COMUNIDAD", "Término", "TOTALES", "FUENTE EGIF", "2025")


def parse_fire_rows(text: str) -> list[dict]:
    """Filas del Anexo I: NOMBRE [población] rayo neglig intenc descon reprod total.

    Tras el nombre: 7 cifras = población + 6 valores; 6 cifras = sin población (municipios de fuera de la región);
    cualquier otro número de cifras = fila incompleta en el documento (no se interpreta).
    """
    out = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(_SKIP):
            continue
        m = _NAME.match(line)
        if not m:
            continue
        tokens = line[m.end():].split()
        if not all(re.fullmatch(r"\d{1,3}(?:\.\d{3})*|\d+", t) for t in tokens):
            continue
        if len(tokens) == 7:
            vals = [int(t) for t in tokens[1:]]
        elif len(tokens) == 6 and all("." not in t for t in tokens):
            vals = [int(t) for t in tokens]
        else:
            vals = None
        # fila incompleta: la 1.ª cifra es la población; el resto son siniestros que no se pueden asignar a una causa
        loose = 0 if vals is not None else sum(int(t.replace(".", "")) for t in tokens[1:])
        out.append({"name_literal": m.group(1).strip(), "values": vals, "complete": vals is not None, "loose": loose})
    return out


def column_totals(text: str) -> list[int] | None:
    """Fila «TOTALES» del documento (control de extracción)."""
    m = re.search(r"TOTALES\s+((?:\d+\s+){5}\d+)", text)
    return [int(x) for x in m.group(1).split()] if m else None


def fetch() -> dict:
    out_dir = RAW_DIR / SOURCE_ID
    out_dir.mkdir(parents=True, exist_ok=True)
    r = httpx.get(URL, timeout=120, follow_redirects=True)
    r.raise_for_status()
    target = out_dir / PDF_NAME
    target.write_bytes(r.content)
    manifest = {
        "source_id": SOURCE_ID, "ckan_id": None, "title": SPEC.title, "catalog_url": URL, "resource_url": URL,
        "format": "PDF", "file": PDF_NAME, "bytes": len(r.content), "sha256": hashlib.sha256(r.content).hexdigest(),
        "license_id": "documento-publico-oficial", "license_title": SPEC.license,
        "resource_last_modified": r.headers.get("last-modified"),
        "extracted_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "pages_used": {"zar_annex_II": ZAR_PAGE, "zar_count_text": ZAR_COUNT_PAGE, "fires_annex_I": list(FIRES_PAGES)},
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def transform() -> dict:
    from pypdf import PdfReader

    pdf = RAW_DIR / SOURCE_ID / PDF_NAME
    if not pdf.exists():
        raise FileNotFoundError("ejecute antes `python -m escudo_pipelines.plan_anual fetch`")
    manifest = json.loads((RAW_DIR / SOURCE_ID / "manifest.json").read_text(encoding="utf-8"))
    reader = PdfReader(pdf)
    idx = municipality_index()
    checks: list[dict] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "passed": bool(ok), "detail": detail})

    # --- Anexo II: ZAR
    zar_text = reader.pages[ZAR_PAGE - 1].extract_text() or ""
    count_text = reader.pages[ZAR_COUNT_PAGE - 1].extract_text() or ""
    zar = parse_zar(zar_text.split("Alto Riesgo", 1)[-1])
    check("zar_titulo_anexo_II", "ANEXO II" in zar_text and "Zonas de Alto Riesgo" in zar_text, f"pág. {ZAR_PAGE}")
    check("zar_texto_declara_59", f"un total de \n{ZAR_DECLARED}" in count_text or f"un total de {ZAR_DECLARED}" in count_text,
          f"pág. {ZAR_COUNT_PAGE}: «son un total de {ZAR_DECLARED}»")
    check("zar_numeracion_1_a_59", [n for n, _ in zar] == list(range(1, ZAR_DECLARED + 1)), f"{len(zar)} entradas extraídas")
    zar_rows, fixes, unmatched = [], [], []
    for n, literal in zar:
        key = norm(literal)
        raw_key = unicodedata.normalize("NFKD", literal).encode("ascii", "ignore").decode().lower()
        if key not in idx:
            unmatched.append(literal)
            continue
        ine, cam_name = idx[key]
        if norm(cam_name) != norm(literal) or raw_key.strip() in NAME_FIXES:
            fixes.append({"literal": literal, "ine_code": ine, "cam_name": cam_name})
        zar_rows.append({"order": n, "name_literal": literal, "ine_code": ine, "cam_name": cam_name,
                         "source_id": SOURCE_ID, "page": ZAR_PAGE})
    check("zar_emparejados_ine", not unmatched and len({r["ine_code"] for r in zar_rows}) == ZAR_DECLARED,
          f"sin emparejar: {unmatched}; correcciones de nombre registradas: {len(fixes)}")

    # --- Anexo I: siniestros por municipio y causa 2015–2024
    fire_rows, outside, fire_unmatched = [], [], []
    for page in FIRES_PAGES:
        for r in parse_fire_rows(reader.pages[page - 1].extract_text() or ""):
            key = norm(r["name_literal"])
            if key in OUTSIDE_REGION:
                outside.append(r["name_literal"])
                continue
            if key not in idx:
                fire_unmatched.append(r["name_literal"])
                continue
            ine, cam_name = idx[key]
            v = r["values"]
            row = {"ine_code": ine, "cam_name": cam_name, "name_literal": r["name_literal"], "period": FIRES_PERIOD,
                   "page": page, "row_complete": r["complete"]}
            if v:
                row.update(dict(zip(CAUSES, v[:5], strict=True)))
                row["total_published"] = v[5]
                row["total_matches_causes"] = sum(v[:5]) == v[5]
            else:
                row.update({c: "" for c in CAUSES})
                row["total_published"] = ""
                row["total_matches_causes"] = ""
            fire_rows.append(row)
    parsed_all = [x for page in FIRES_PAGES for x in parse_fire_rows(reader.pages[page - 1].extract_text() or "")]
    doc_totals = column_totals(reader.pages[FIRES_PAGES[-1] - 1].extract_text() or "")
    sums = [sum(x["values"][i] for x in parsed_all if x["values"]) for i in range(6)]
    loose = sum(x["loose"] for x in parsed_all)
    diff = [d - e for d, e in zip(doc_totals or [0] * 6, sums, strict=True)]
    check("siniestros_extraccion_cuadra_con_TOTALES", doc_totals is not None and diff[5] == 0 and sum(diff[:5]) == loose,
          f"suma por columna de lo extraído {sums} vs fila TOTALES del documento {doc_totals}; la diferencia "
          f"{diff} se explica por {loose} siniestro(s) en filas incompletas que no se pueden asignar a una causa")
    by_ine = {r["ine_code"]: r for r in fire_rows}
    check("siniestros_cobertura", len(by_ine) == len(fire_rows) and len(by_ine) >= 170,
          f"{len(by_ine)} municipios de la CAM; sin emparejar: {fire_unmatched}; fuera de la región (excluidos): {outside}")
    complete = [r for r in fire_rows if r["row_complete"]]
    mism = [r["cam_name"] for r in complete if not r["total_matches_causes"]]
    check("siniestros_filas_completas", len(complete) >= 170,
          f"{len(complete)} filas completas; incompletas (no interpretadas): "
          f"{[r['cam_name'] for r in fire_rows if not r['row_complete']]}")
    check("siniestros_total_vs_causas_informativo", True,
          f"{len(mism)} filas con total publicado ≠ suma de causas (se muestran marcadas, sin corregir)")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, rows in (("zar_municipalities.csv", zar_rows), ("municipal_fires_2015_2024.csv", fire_rows)):
        with (OUT_DIR / name).open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    report = {"inputs": {SOURCE_ID: {k: manifest[k] for k in ("sha256", "extracted_at", "resource_url")}},
              "name_fixes": fixes, "fires_total_mismatch": mism, "outside_region_excluded": outside,
              "checks": checks, "all_passed": all(c["passed"] for c in checks)}
    (OUT_DIR / "quality.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    cmd = sys.argv[1] if len(sys.argv) > 1 else "transform"
    if cmd == "fetch":
        m = fetch()
        print(f"OK {SOURCE_ID} {m['bytes']} B sha256={m['sha256'][:12]}")
        raise SystemExit(0)
    rep = transform()
    for c in rep["checks"]:
        print(("PASS " if c["passed"] else "FAIL ") + c["check"] + " — " + c["detail"])
    raise SystemExit(0 if rep["all_passed"] else 1)
