"""EFF-01 · EFFIS (Copernicus EMS / JRC) — áreas quemadas cartografiadas por satélite (MODIS, Rapid Damage Assessment).

Licencia CC BY 4.0 — «© Unión Europea, 1995-2026, EFFIS». Avisos del productor (readme.txt del paquete), que se
muestran siempre junto al dato:
- estimación a partir de MODIS a 250 m; se cartografían áreas de unas 30 ha o más (puede haber algunas menores);
- no distingue incendios forestales de quemas agrícolas o prescritas;
- las fechas de inicio y última actualización pueden no coincidir con la ignición y la extinción;
- dos incendios entre actualizaciones pueden fusionarse en un único perímetro.

Se conservan los perímetros que intersecan la Comunidad de Madrid (geometría y atributos literales). El reparto por
municipio es DERIVADO: intersección del perímetro con los límites municipales (CAM-08) calculada en EPSG:25830.

    python -m escudo_pipelines.effis fetch       # ~262 MB (toda Europa), manifest con SHA-256
    python -m escudo_pipelines.effis transform   # data/processed/effis/
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
import zipfile
from datetime import UTC, datetime

import httpx
import shapely
from pyproj import Transformer
from shapely.geometry import mapping, shape
from shapely.ops import unary_union

from .fetch import RAW_DIR, REPO_ROOT, USER_AGENT
from .sources import SourceSpec

SOURCE_ID = "EFF-01"
URL = "https://forest-fire.emergency.copernicus.eu/downloads/data.request.form/effis_layer.zip"
ZIP_NAME = "effis_layer.zip"
SHP_BASE = "effis_layer/modis.ba.poly"
OUT_DIR = REPO_ROOT / "data" / "processed" / "effis"
MUNI_GEOJSON = REPO_ROOT / "data" / "processed" / "cam" / "municipalities.geojson"
LICENSE = "CC BY 4.0 — © Unión Europea, EFFIS"
PRODUCER_NOTES = (
    "Estimación por satélite (MODIS, 250 m): se cartografían áreas quemadas de unas 30 ha o más. No distingue "
    "incendios forestales de quemas agrícolas o prescritas; las fechas pueden no coincidir con la ignición y la "
    "extinción; dos incendios cercanos pueden fusionarse en un perímetro. Fuente: EFFIS (Copernicus EMS, JRC)."
)

SPEC = SourceSpec(
    source_id=SOURCE_ID,
    portal="EFFIS",
    ckan_id=None,
    title="EFFIS — Áreas quemadas cartografiadas (MODIS Burnt Areas, Rapid Damage Assessment)",
    producer="Comisión Europea — Joint Research Centre / Copernicus Emergency Management Service (EFFIS)",
    catalog_url="https://forest-fire.emergency.copernicus.eu/applications/data-and-services",
    license=LICENSE,
    spatial_scope="perímetros (resolución 250 m); reparto municipal derivado",
    temporal_scope="campañas disponibles en la capa (actualización diaria)",
    use_in_product="Perímetros de áreas quemadas en el mapa y lista por municipio con fecha y superficie",
    caveats=PRODUCER_NOTES,
    resource_format="SHP (ZIP)",
)

_TO_UTM = Transformer.from_crs("EPSG:4326", "EPSG:25830", always_xy=True)
LANDCOVER = ("BROADLEA", "CONIFER", "MIXED", "SCLEROPH", "TRANSIT", "OTHERNATLC", "AGRIAREAS", "ARTIFSURF", "OTHERLC")


def _utm(g):
    import numpy as np

    return shapely.transform(g, lambda xy: np.column_stack(_TO_UTM.transform(xy[:, 0], xy[:, 1])))


def fetch() -> dict:
    out = RAW_DIR / SOURCE_ID
    out.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256()
    n = 0
    with httpx.Client(timeout=900, follow_redirects=True, headers={"User-Agent": USER_AGENT}) as c, \
            c.stream("GET", URL) as r, (out / ZIP_NAME).open("wb") as f:
        r.raise_for_status()
        last_modified = r.headers.get("last-modified")
        for chunk in r.iter_bytes(1 << 20):
            h.update(chunk)
            n += len(chunk)
            f.write(chunk)
    m = {"source_id": SOURCE_ID, "ckan_id": None, "title": SPEC.title, "catalog_url": SPEC.catalog_url,
         "resource_url": URL, "format": "SHP (ZIP)", "file": ZIP_NAME, "bytes": n, "sha256": h.hexdigest(),
         "license_id": "CC-BY-4.0", "license_title": LICENSE, "resource_last_modified": last_modified,
         "extracted_at": datetime.now(UTC).isoformat(timespec="seconds")}
    (out / "manifest.json").write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
    return m


def _date(v: str) -> str | None:
    v = (v or "").strip()
    return v[:10] if len(v) >= 10 else None


def transform() -> dict:
    import shapefile

    zpath = RAW_DIR / SOURCE_ID / ZIP_NAME
    if not zpath.exists():
        raise FileNotFoundError("ejecute antes `python -m escudo_pipelines.effis fetch`")
    manifest = json.loads((RAW_DIR / SOURCE_ID / "manifest.json").read_text(encoding="utf-8"))
    geo = json.loads(MUNI_GEOJSON.read_text(encoding="utf-8"))
    munis = {f["properties"]["ine_code"]: (f["properties"]["name"], shape(f["geometry"])) for f in geo["features"]}
    region = unary_union([g for _, g in munis.values()]).buffer(0)
    minx, miny, maxx, maxy = region.bounds
    munis_utm = {k: (n, _utm(g).buffer(0)) for k, (n, g) in munis.items()}

    checks: list[dict] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "passed": bool(ok), "detail": detail})

    features, rows, fixed = [], [], 0
    with zipfile.ZipFile(zpath) as z:
        with z.open(SHP_BASE + ".shp") as shp, z.open(SHP_BASE + ".dbf") as dbf, z.open(SHP_BASE + ".shx") as shx:
            reader = shapefile.Reader(shp=shp, dbf=dbf, shx=shx, encoding="utf-8")
            total = reader.numRecords
            for sr in reader.iterShapeRecords():
                x0, y0, x1, y1 = sr.shape.bbox
                if x1 < minx or x0 > maxx or y1 < miny or y0 > maxy:
                    continue
                g = shape(sr.shape.__geo_interface__)
                if not g.is_valid:
                    g = g.buffer(0)
                    fixed += 1
                if not g.intersects(region):
                    continue
                d = sr.record.as_dict()
                gu = _utm(g)
                area_calc = gu.area / 1e4
                in_region = gu.intersection(_utm(region)).area / 1e4
                props = {
                    "effis_id": str(d["id"]), "fire_date": _date(d["FIREDATE"]), "final_date": _date(d["FINALDATE"]),
                    "last_update": _date(d["LASTUPDATE"]), "year": int(str(d["FIREDATE"])[:4]),
                    "commune_literal": d["COMMUNE"], "province_literal": d["PROVINCE"], "country": d["COUNTRY"],
                    "area_ha_effis": float(d["AREA_HA"]), "area_ha_in_region_derived": round(in_region, 1),
                    "class": d["CLASS"], "natura2000_pct": round(float(d["PERCNA2K"] or 0), 1),
                    **{f"lc_{k.lower()}_pct": round(float(d[k] or 0), 1) for k in LANDCOVER},
                    "source_id": SOURCE_ID, "status": "official",
                }
                features.append({"type": "Feature", "properties": props,
                                 "geometry": json.loads(json.dumps(mapping(g)))})
                for ine, (name, mg) in munis_utm.items():
                    if not mg.intersects(gu):
                        continue
                    a = mg.intersection(gu).area / 1e4
                    if a >= 0.5:  # descarta astillas de borde por diferencias de límites
                        rows.append({"ine_code": ine, "name": name, "effis_id": props["effis_id"], "year": props["year"],
                                     "fire_date": props["fire_date"], "area_ha_in_municipality": round(a, 1),
                                     "area_ha_effis_perimeter": props["area_ha_effis"],
                                     "commune_literal": props["commune_literal"]})
                props["_area_calc_ha"] = round(area_calc, 1)

    features.sort(key=lambda f: (f["properties"]["fire_date"] or "", f["properties"]["effis_id"]))
    rows.sort(key=lambda r: (r["ine_code"], r["fire_date"] or "", r["effis_id"]))
    devs = [abs(f["properties"].pop("_area_calc_ha") - f["properties"]["area_ha_effis"]) /
            max(f["properties"]["area_ha_effis"], 1) for f in features if f["properties"]["area_ha_effis"] >= 30]
    devs.sort()
    check("effis_registros_leidos", total > 1000, f"{total} perímetros en el paquete europeo")
    check("effis_perimetros_region", len(features) > 0, f"{len(features)} perímetros intersecan la Comunidad de "
          f"Madrid ({fixed} geometrías corregidas con buffer(0) en la lectura)")
    check("effis_area_calculada_vs_publicada", not devs or devs[len(devs) // 2] < 0.10,
          f"desviación mediana entre AREA_HA publicada y área geodésica calculada (perímetros ≥30 ha): "
          f"{devs[len(devs) // 2]:.1%}" if devs else "sin perímetros ≥30 ha")
    check("effis_reparto_municipal", all(r["ine_code"] in munis for r in rows),
          f"{len(rows)} pares perímetro×municipio en {len({r['ine_code'] for r in rows})} municipios")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "burnt_areas_madrid.geojson").write_text(json.dumps({
        "type": "FeatureCollection", "name": "effis_burnt_areas_madrid", "source_id": SOURCE_ID, "license": LICENSE,
        "producer_notes": PRODUCER_NOTES, "crs_note": "EPSG:4326", "features": features},
        ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    with (OUT_DIR / "municipal_burnt_areas.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["ine_code", "name", "effis_id", "year", "fire_date", "area_ha_in_municipality",
                                          "area_ha_effis_perimeter", "commune_literal"])
        w.writeheader()
        w.writerows(rows)
    years = sorted({f["properties"]["year"] for f in features})
    report = {"inputs": {SOURCE_ID: {k: manifest[k] for k in ("sha256", "extracted_at", "resource_url")}},
              "years": years, "features": len(features), "checks": checks,
              "all_passed": all(c["passed"] for c in checks)}
    (OUT_DIR / "quality.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if (sys.argv[1:] or ["transform"])[0] == "fetch":
        m = fetch()
        print(f"OK {SOURCE_ID} {m['bytes']} B sha256={m['sha256'][:12]}")
        raise SystemExit(0)
    rep = transform()
    for c in rep["checks"]:
        print(("PASS " if c["passed"] else "FAIL ") + c["check"] + " — " + c["detail"])
    print("años:", rep["years"])
    raise SystemExit(0 if rep["all_passed"] else 1)
