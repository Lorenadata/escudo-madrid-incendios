"""Transformación reproducible de los recursos CAM descargados (data/raw/CAM-*).

Salidas en data/processed/cam/:
  municipalities.geojson        Geometría municipal (disolución de secciones censales CAM-08), EPSG:4326
  municipal_indicators.csv      Indicadores municipales del último año disponible (CAM-01/02/03)
  municipal_population_series.csv  Serie anual de población total y ≥65 por municipio (CAM-01)
  municipal_density_series.csv  Serie anual de densidad por municipio (CAM-02)
  fire_history.csv              Serie regional de incendios (CAM-05) — ámbito REGIONAL
  land_use_regional.csv         Superficie por usos (CAM-07) — ámbito REGIONAL
  reforestation.csv             Repoblaciones forestales por grupo vegetal (CAM-06) — REGIONAL
  protected_spaces.csv          Listado de espacios protegidos (CAM-04) — sin geometría
  quality.json                  Controles de calidad ejecutados y resultado

Uso: python -m escudo_pipelines.cam_transform
"""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

import shapefile
import shapely
from pyproj import Transformer
from shapely import make_valid
from shapely.geometry import mapping, shape
from shapely.ops import unary_union

from .fetch import RAW_DIR, REPO_ROOT

OUT_DIR = REPO_ROOT / "data" / "processed" / "cam"
SIMPLIFY_TOLERANCE_M = 25.0
EXPECTED_MUNICIPALITIES = 179

_TR = Transformer.from_crs("EPSG:25830", "EPSG:4326", always_xy=True)


def _to_wgs84(geom):
    return shapely.transform(geom, lambda xy: __import__('numpy').column_stack(_TR.transform(xy[:, 0], xy[:, 1])))


def cam_code_to_ine(code: str) -> str:
    """Código CAM de 4 dígitos (3 de municipio + dígito de control) → INE 5 dígitos '28xxx'."""
    code = code.strip()
    if not re.fullmatch(r"\d{4}", code):
        raise ValueError(f"código territorial CAM inesperado: {code!r}")
    return "28" + code[:3]


def parse_number(raw: str) -> float | None:
    raw = (raw or "").strip()
    if raw in {"", "-", "..", "."}:
        return None
    return float(raw.replace(",", "."))


def _read(path: Path, encoding: str = "utf-8-sig") -> list[dict[str, str]]:
    with path.open(encoding=encoding, newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def _only_csv(source_id: str) -> Path:
    files = sorted((RAW_DIR / source_id).glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"{source_id}: ejecute antes `python -m escudo_pipelines.fetch {source_id}`")
    return files[0]


def _manifest(source_id: str) -> dict:
    return json.loads((RAW_DIR / source_id / "manifest.json").read_text(encoding="utf-8"))


AGE_65_PLUS = re.compile(r"De (\d+)")


def _is_65_plus(age_label: str) -> bool:
    m = AGE_65_PLUS.match(age_label)
    return bool(m) and int(m.group(1)) >= 65


def build_population(rows: list[dict[str, str]]) -> tuple[dict[str, str], dict[tuple[str, int], dict]]:
    """Devuelve nombres por INE y {(ine, año): {total, age65}} a partir de CAM-01."""
    names: dict[str, str] = {}
    acc: dict[tuple[str, int], dict] = defaultdict(lambda: {"total": None, "age65": 0.0})
    for r in rows:
        if r["Tipo territorio"] != "Municipios" or r["Nacionalidad"] != "Total" or r["Sexo"] != "Total":
            continue
        ine = cam_code_to_ine(r["Código territorio"])
        names[ine] = r["Territorio"].strip()
        key = (ine, int(r["Año"]))
        val = parse_number(r["Valor"])
        if r["Edad"] == "Total":
            acc[key]["total"] = val
        elif _is_65_plus(r["Edad"]) and val is not None:
            acc[key]["age65"] += val
    return names, dict(acc)


def build_simple_municipal(rows: list[dict[str, str]]) -> dict[tuple[str, int], float | None]:
    out: dict[tuple[str, int], float | None] = {}
    for r in rows:
        if r["Tipo territorio"] != "Municipios":
            continue
        out[(cam_code_to_ine(r["Código territorio"]), int(r["Año"]))] = parse_number(r["Valor"])
    return out


def latest(series: dict[tuple[str, int], object], ine: str) -> tuple[int | None, object]:
    years = [y for (i, y) in series if i == ine]
    if not years:
        return None, None
    y = max(years)
    return y, series[(ine, y)]


def build_municipal_geometries(shp_path: Path) -> tuple[dict[str, object], dict]:
    reader = shapefile.Reader(str(shp_path), encoding="latin1")
    parts: dict[str, list] = defaultdict(list)
    invalid = 0
    for sr in reader.iterShapeRecords():
        geom = shape(sr.shape.__geo_interface__)
        if not geom.is_valid:
            invalid += 1
            geom = make_valid(geom)
        parts["28" + sr.record["CDMUNI"]].append(geom)
    merged = {ine: make_valid(unary_union(gs)) for ine, gs in parts.items()}
    return merged, {"sections": len(reader), "invalid_sections_fixed": invalid}


def run() -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    checks: list[dict] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "passed": bool(ok), "detail": detail})

    # --- CAM-01 población
    names, pop = build_population(_read(_only_csv("CAM-01")))
    # --- CAM-02 densidad, CAM-03 altitud
    dens = build_simple_municipal(_read(_only_csv("CAM-02")))
    alt = build_simple_municipal(_read(_only_csv("CAM-03")))

    # --- CAM-08 geometría
    shp = next((RAW_DIR / "CAM-08" / "extracted").glob("*.shp"), None)
    if shp is None:
        import zipfile

        zipfile.ZipFile(next((RAW_DIR / "CAM-08").glob("*.zip"))).extractall(RAW_DIR / "CAM-08" / "extracted")
        shp = next((RAW_DIR / "CAM-08" / "extracted").glob("*.shp"))
    geoms, geom_stats = build_municipal_geometries(shp)

    ine_codes = sorted(names)
    check("municipios_cam01", len(ine_codes) == EXPECTED_MUNICIPALITIES, f"{len(ine_codes)} municipios en CAM-01")
    check("municipios_geometria", len(geoms) == EXPECTED_MUNICIPALITIES, f"{len(geoms)} municipios en CAM-08")
    missing_geom = sorted(set(ine_codes) - set(geoms))
    check("codigos_coinciden", not missing_geom and set(geoms) == set(ine_codes),
          f"sin geometría: {missing_geom}; sin datos: {sorted(set(geoms) - set(ine_codes))}")
    check("geometrias_validas", all(g.is_valid for g in geoms.values()),
          f"{geom_stats['invalid_sections_fixed']} secciones inválidas corregidas con make_valid")

    # --- municipios GeoJSON + indicadores
    features = []
    indicators = []
    for ine in ine_codes:
        g = geoms.get(ine)
        area_km2 = g.area / 1e6 if g is not None else None
        py, p = latest(pop, ine)
        dy, d = latest(dens, ine)
        ay, a = latest(alt, ine)
        total = p["total"] if p else None
        share65 = (p["age65"] / total) if p and total else None
        row = {
            "ine_code": ine,
            "name": names[ine],
            "population_total": int(total) if total is not None else "",
            "population_65_plus": int(p["age65"]) if p else "",
            "age_65_plus_share": round(share65, 6) if share65 is not None else "",
            "population_year": py or "",
            "density_hab_km2": d if d is not None else "",
            "density_year": dy or "",
            "altitude_m": a if a is not None else "",
            "altitude_year": ay or "",
            "area_km2": round(area_km2, 4) if area_km2 is not None else "",
        }
        indicators.append(row)
        if g is not None:
            web = _to_wgs84(g.simplify(SIMPLIFY_TOLERANCE_M, preserve_topology=True))
            web = make_valid(web)
            features.append({
                "type": "Feature",
                "properties": {"ine_code": ine, "name": names[ine]},
                "geometry": json.loads(json.dumps(mapping(web), default=float)),
            })

    # comprobación de coherencia: densidad publicada vs población/área calculada (solo informativa)
    deviations = []
    for row in indicators:
        if row["density_hab_km2"] != "" and row["population_total"] != "" and row["area_km2"]:
            if row["density_year"] == row["population_year"]:
                calc = row["population_total"] / row["area_km2"]
                dev = abs(calc - row["density_hab_km2"]) / max(row["density_hab_km2"], 1e-9)
                deviations.append((dev, row["ine_code"]))
    deviations.sort(reverse=True)
    if deviations:
        med = deviations[len(deviations) // 2][0]
        check("coherencia_densidad", med < 0.05,
              f"desviación mediana densidad publicada vs pob/área(secciones) = {med:.2%}; máx {deviations[0][0]:.2%} ({deviations[0][1]})")

    check("rango_share65", all(r["age_65_plus_share"] == "" or 0 <= r["age_65_plus_share"] <= 1 for r in indicators),
          "proporción ≥65 en [0,1]")

    def write_csv(name: str, rows: list[dict]) -> None:
        with (OUT_DIR / name).open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

    (OUT_DIR / "municipalities.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "name": "municipios_cam", "crs_note": "EPSG:4326",
                    "source_id": "CAM-08", "simplify_tolerance_m": SIMPLIFY_TOLERANCE_M, "features": features},
                   ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    write_csv("municipal_indicators.csv", indicators)
    write_csv("municipal_population_series.csv", [
        {"ine_code": i, "year": y, "population_total": int(v["total"]) if v["total"] is not None else "",
         "population_65_plus": int(v["age65"])}
        for (i, y), v in sorted(pop.items())])
    write_csv("municipal_density_series.csv", [
        {"ine_code": i, "year": y, "density_hab_km2": v if v is not None else ""} for (i, y), v in sorted(dens.items())])

    # --- CAM-05 incendios (regional)
    fires: dict[int, dict] = defaultdict(dict)
    for r in _read(_only_csv("CAM-05")):
        fires[int(r["Año"])][r["Concepto"].strip()] = parse_number(r["Valor"])
    concept_map = {
        "Número total de siniestros forestales": "total_siniestros",
        "Conatos": "conatos",
        "Incendios": "incendios",
        "Siniestros que llegan a incendios": "siniestros_que_llegan_a_incendio",
        "Total superficie afectada por incendios": "superficie_total_ha",
        "Superficie arbolada afectada por incendios": "superficie_arbolada_ha",
        "Superficie desarbolada afectada por incendios": "superficie_desarbolada_ha",
        "Superficie desarbolada leñosa afectada por incendios": "superficie_desarbolada_lenosa_ha",
        "Superficie desarbolada herbácea afectada por incendios": "superficie_desarbolada_herbacea_ha",
    }
    unknown = {c for v in fires.values() for c in v} - set(concept_map)
    check("cam05_conceptos_conocidos", not unknown, f"conceptos no mapeados: {sorted(unknown)}")
    write_csv("fire_history.csv", [
        {"year": y, "scope": "Comunidad de Madrid (agregado regional)",
         **{col: ("" if fires[y].get(c) is None else fires[y].get(c)) for c, col in concept_map.items()}}
        for y in sorted(fires)])

    # --- CAM-07 usos (regional)
    land = [
        {"year": int(r["Año"]), "concept": r["Concepto"].strip(), "value_ha": "" if parse_number(r["Valor"]) is None else parse_number(r["Valor"]),
         "scope": "Comunidad de Madrid (agregado regional)"}
        for r in _read(_only_csv("CAM-07"))]
    write_csv("land_use_regional.csv", land)

    # --- CAM-06 repoblaciones (latin1)
    refo = [{"year": int(r["año"]), "vegetation_group": r["grupo_vegetal"].strip(),
             "area_ha": parse_number(r["superficie_hectarea"])} for r in _read(_only_csv("CAM-06"), "latin1")]
    write_csv("reforestation.csv", refo)

    # --- CAM-04 espacios protegidos (latin1, listado)
    prot = [{"category": r["espacio_prot_categoria"].strip(), "figure": r["espacio_prot_figura"].strip(),
             "name": r["espacio_prot_nombre"].strip(), "area_ha": parse_number(r["espacio_prot_superficie_ha"]),
             "declared_on": r["espacio_prot_fecha_declaracion"].strip(), "norm_url": r["espacio_prot_normativa"].strip()}
            for r in _read(_only_csv("CAM-04"), "latin1")]
    write_csv("protected_spaces.csv", prot)
    check("cam04_sin_geometria", True, f"{len(prot)} espacios; recurso tabular, no se cruza espacialmente")

    report = {
        "inputs": {sid: {k: _manifest(sid)[k] for k in ("sha256", "extracted_at", "resource_url")}
                   for sid in ("CAM-01", "CAM-02", "CAM-03", "CAM-04", "CAM-05", "CAM-06", "CAM-07", "CAM-08")},
        "geometry": {**geom_stats, "simplify_tolerance_m": SIMPLIFY_TOLERANCE_M, "crs_source": "EPSG:25830",
                     "crs_output": "EPSG:4326"},
        "checks": checks,
        "all_passed": all(c["passed"] for c in checks),
    }
    (OUT_DIR / "quality.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    rep = run()
    for c in rep["checks"]:
        print(("PASS " if c["passed"] else "FAIL ") + c["check"] + " — " + c["detail"])
    raise SystemExit(0 if rep["all_passed"] else 1)
