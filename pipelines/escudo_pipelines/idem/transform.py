"""Transformación de las capas oficiales IDEM GEO-01..03 (rásteres GeoTIFF 5 m, EPSG:25830).

Salidas (contrato A3 → A6, ver docs/spatial-method.md):
  data/processed/idem/{risk,hazard,vulnerability}.geojson   EPSG:4326, generalizado SOLO para visualización
  data/processed/idem/municipal_class_shares.csv            reparto de clases por municipio (ráster completo 5 m)
  data/processed/idem/layers_meta.json                      metadatos, clases literales, controles

Los valores de clase y sus etiquetas son los de la leyenda oficial del WMS IDEM
(guardada en data/raw/<GEO-XX>/legend.json); no se recalculan ni se renombran.

Uso:  python -m escudo_pipelines.idem.transform [--web-cell 100] [--layers risk hazard vulnerability]
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections.abc import Iterable
from pathlib import Path

import numpy as np
import rasterio
import shapely
from pyproj import Transformer
from rasterio import features
from rasterio.enums import Resampling
from rasterio.windows import Window
from shapely import make_valid
from shapely.geometry import mapping, shape

from escudo_pipelines.fetch import RAW_DIR, REPO_ROOT

from .sources import IDEM_LAYERS, IdemLayer

OUT_DIR = REPO_ROOT / "data" / "processed" / "idem"
MUNICIPALITIES = REPO_ROOT / "data" / "processed" / "cam" / "municipalities.geojson"
NODATA = 255
STRIP_ROWS = 2048
WEB_CELL_M = 200          # celda de generalización para la capa web (moda de celdas de 5 m)
SIMPLIFY_TOL_M = 40       # tolerancia de simplificación tras vectorizar (m, EPSG:25830)
COORD_DECIMALS = 4        # ~10 m: suficiente para celdas de 200 m
SHARE_EPSILON = 0.01

TO_25830 = Transformer.from_crs("EPSG:4326", "EPSG:25830", always_xy=True)
TO_4326 = Transformer.from_crs("EPSG:25830", "EPSG:4326", always_xy=True)


# ---------------------------------------------------------------- utilidades
def _vec(tr: Transformer):
    """Adaptador vectorizado de pyproj para shapely.transform (array N×2)."""
    def f(xy: np.ndarray) -> np.ndarray:
        x, y = tr.transform(xy[:, 0], xy[:, 1])
        return np.column_stack([x, y])
    return f


def load_legend(layer: IdemLayer, raw_dir: Path = RAW_DIR) -> list[dict]:
    manifest = json.loads((raw_dir / layer.spec.source_id / "manifest.json").read_text(encoding="utf-8"))
    return manifest["legend_classes"]


def raster_uri(layer: IdemLayer, raw_dir: Path = RAW_DIR) -> str:
    zip_path = (raw_dir / layer.spec.source_id / layer.zip_name).as_posix()
    return f"zip://{zip_path}!{layer.tif_name}"


def fix_geometry(geom):
    """Devuelve (geometría válida, si hubo que corregirla)."""
    if geom.is_valid:
        return geom, False
    return make_valid(geom), True


def round_coords(obj, nd: int = COORD_DECIMALS):
    if isinstance(obj, (list, tuple)):
        if obj and isinstance(obj[0], (int, float)):
            return [round(float(v), nd) for v in obj]
        return [round_coords(v, nd) for v in obj]
    return obj


def load_municipalities(path: Path = MUNICIPALITIES) -> tuple[list[dict], int]:
    """Municipios reproyectados a EPSG:25830, validados. Devuelve (lista, nº corregidos)."""
    fc = json.loads(path.read_text(encoding="utf-8"))
    out, fixed = [], 0
    for f in fc["features"]:
        g = shapely.transform(shape(f["geometry"]), _vec(TO_25830))
        g, was_fixed = fix_geometry(g)
        fixed += was_fixed
        out.append({"ine_code": f["properties"]["ine_code"], "name": f["properties"].get("name"), "geom": g})
    return out, fixed


# ------------------------------------------------- reparto de clases municipal
def municipal_class_counts(
    uris: dict[str, str],
    munis: list[dict],
    strip_rows: int = STRIP_ROWS,
) -> tuple[dict[str, np.ndarray], float]:
    """Cuenta píxeles (municipio × clase) para cada capa, sobre la malla nativa común.

    Devuelve ({layer: matriz [n_munis+1, 256]}, área de píxel en m²). La fila 0 = fuera de
    cualquier municipio. Se rasteriza cada municipio por centro de píxel (all_touched=False).
    """
    if len(munis) > 65000:
        raise ValueError("demasiados municipios para uint16")
    datasets = {k: rasterio.open(u) for k, u in uris.items()}
    try:
        ref = next(iter(datasets.values()))
        for k, ds in datasets.items():
            if ds.transform != ref.transform or ds.shape != ref.shape or ds.crs != ref.crs:
                raise ValueError(f"la capa {k} no comparte malla con las demás")
        if ref.crs.to_epsg() != 25830:
            raise ValueError(f"CRS inesperado {ref.crs}")
        pixel_area = abs(ref.transform.a * ref.transform.e)
        n = len(munis) + 1
        counts = {k: np.zeros((n, 256), dtype=np.int64) for k in datasets}
        shapes = [(m["geom"], i + 1) for i, m in enumerate(munis)]
        for row in range(0, ref.height, strip_rows):
            h = min(strip_rows, ref.height - row)
            win = Window(0, row, ref.width, h)
            wt = ref.window_transform(win)
            mid = features.rasterize(shapes, out_shape=(h, ref.width), transform=wt, fill=0, dtype="uint16")
            mid_flat = mid.ravel().astype(np.int64)
            for k, ds in datasets.items():
                cls = ds.read(1, window=win).ravel().astype(np.int64)
                counts[k] += np.bincount(mid_flat * 256 + cls, minlength=n * 256).reshape(n, 256)
        return counts, pixel_area
    finally:
        for ds in datasets.values():
            ds.close()


def shares_rows(layer: str, counts: np.ndarray, pixel_area: float, munis: list[dict],
                legend: list[dict]) -> list[dict]:
    labels = {c["class_code"]: c["class_label"] for c in legend}
    rows = []
    for i, m in enumerate(munis, start=1):
        muni_area = m["geom"].area
        for code in range(256):
            c = int(counts[i, code])
            if c == 0 or code == NODATA:
                continue
            if code not in labels:
                raise ValueError(f"{layer}: valor {code} sin etiqueta en la leyenda oficial")
            area_m2 = c * pixel_area
            rows.append({
                "ine_code": m["ine_code"],
                "layer": layer,
                "class_label": labels[code],
                "class_code": code,
                "area_ha": round(area_m2 / 10_000, 2),
                "area_share": round(area_m2 / muni_area, 6) if muni_area > 0 else None,
            })
    return rows


# ------------------------------------------------------ vectorización web
def vectorize_for_web(uri: str, legend: list[dict], cell_m: float = WEB_CELL_M,
                      simplify_tol_m: float = SIMPLIFY_TOL_M,
                      coord_decimals: int = COORD_DECIMALS) -> tuple[dict, int, dict]:
    labels = {c["class_code"]: c["class_label"] for c in legend}
    with rasterio.open(uri) as ds:
        factor = cell_m / ds.res[0]
        out_h, out_w = int(round(ds.height / factor)), int(round(ds.width / factor))
        data = ds.read(1, out_shape=(out_h, out_w), resampling=Resampling.mode)
        tr = ds.transform * ds.transform.scale(ds.width / out_w, ds.height / out_h)
    mask = data != NODATA
    feats, fixed = [], 0
    for geom, value in features.shapes(data, mask=mask, transform=tr, connectivity=4):
        code = int(value)
        g = shape(geom).simplify(simplify_tol_m, preserve_topology=True)
        g, was_fixed = fix_geometry(g)
        fixed += was_fixed
        if g.is_empty:
            continue
        g4326 = shapely.transform(g, _vec(TO_4326))
        gj = mapping(g4326)
        feats.append({
            "type": "Feature",
            "properties": {"class_code": code, "class_label": labels[code]},
            "geometry": {"type": gj["type"], "coordinates": round_coords(gj["coordinates"], coord_decimals)},
        })
    fc = {"type": "FeatureCollection", "name": "", "features": feats}
    info = {"web_cell_m": cell_m, "web_resampling": "mode", "simplification_tolerance_m": simplify_tol_m,
            "web_grid": [out_w, out_h], "coord_decimals": coord_decimals}
    return fc, fixed, info


def regional_pixel_counts(uri: str, strip_rows: int = STRIP_ROWS) -> tuple[dict[int, int], float]:
    with rasterio.open(uri) as ds:
        tot = np.zeros(256, dtype=np.int64)
        for row in range(0, ds.height, strip_rows):
            h = min(strip_rows, ds.height - row)
            tot += np.bincount(ds.read(1, window=Window(0, row, ds.width, h)).ravel(), minlength=256)
        return {i: int(c) for i, c in enumerate(tot) if c and i != NODATA}, abs(ds.transform.a * ds.transform.e)


# ---------------------------------------------------------------- orquestación
def run(layers: Iterable[str] | None = None, web_cell_m: float = WEB_CELL_M, web_only: bool = False,
        raw_dir: Path = RAW_DIR, out_dir: Path = OUT_DIR, municipalities: Path = MUNICIPALITIES) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    selected = [lyr for lyr in IDEM_LAYERS if layers is None or lyr.layer in set(layers)]
    uris = {lyr.layer: raster_uri(lyr, raw_dir) for lyr in selected}
    legends = {lyr.layer: load_legend(lyr, raw_dir) for lyr in selected}

    meta: dict = {"generated_by": "escudo_pipelines.idem.transform", "layers": {}}
    munis, muni_fixed = load_municipalities(municipalities)
    meta["municipalities"] = {"source": str(municipalities.relative_to(REPO_ROOT)) if municipalities.is_relative_to(REPO_ROOT) else str(municipalities),
                              "n": len(munis), "n_invalid_fixed": muni_fixed}

    prev_meta_path = out_dir / "layers_meta.json"
    prev_meta = json.loads(prev_meta_path.read_text(encoding="utf-8")) if prev_meta_path.exists() else {}
    if web_only and (out_dir / "municipal_class_shares.csv").exists() and prev_meta:
        print("[idem] --web-only: se conserva municipal_class_shares.csv existente", flush=True)
        counts = None
    else:
        print(f"[idem] reparto municipal sobre ráster nativo ({len(munis)} municipios)…", flush=True)
        counts, pixel_area = municipal_class_counts(uris, munis)
        all_rows: list[dict] = []
        for lyr in selected:
            all_rows += shares_rows(lyr.layer, counts[lyr.layer], pixel_area, munis, legends[lyr.layer])
        with (out_dir / "municipal_class_shares.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["ine_code", "layer", "class_label", "class_code", "area_ha", "area_share"])
            w.writeheader()
            w.writerows(all_rows)

    for lyr in selected:
        print(f"[idem] {lyr.layer}: vectorización web (celda {web_cell_m} m)…", flush=True)
        fc, fixed, info = vectorize_for_web(uris[lyr.layer], legends[lyr.layer], web_cell_m)
        fc["name"] = f"{lyr.spec.source_id} {lyr.spec.title}"
        path = out_dir / f"{lyr.layer}.geojson"
        path.write_text(json.dumps(fc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        manifest = json.loads((raw_dir / lyr.spec.source_id / "manifest.json").read_text(encoding="utf-8"))
        regional, pixel_area = regional_pixel_counts(uris[lyr.layer])
        with rasterio.open(uris[lyr.layer]) as ds:
            raster_info = {"width": ds.width, "height": ds.height, "resolution_m": list(ds.res),
                           "bounds_25830": list(ds.bounds), "nodata": ds.nodata, "dtype": ds.dtypes[0]}
        present = set(regional)
        legend_codes = {c["class_code"] for c in legends[lyr.layer]}
        if not present <= legend_codes:
            raise ValueError(f"{lyr.layer}: valores {present - legend_codes} fuera de leyenda")
        if counts is not None:
            outside = int(counts[lyr.layer][0].sum() - counts[lyr.layer][0, NODATA])
        else:
            outside = prev_meta["layers"][lyr.layer]["pixels_with_data_outside_municipalities"]
        meta["layers"][lyr.layer] = {
            "source_id": lyr.spec.source_id,
            "title": lyr.spec.title,
            "license": manifest["license_title"],
            "version_or_date": {
                "revision": manifest["iso_metadata"]["citation_dates"].get("revision"),
                "creation": manifest["iso_metadata"]["citation_dates"].get("creation"),
                "metadata_date_stamp": manifest["iso_metadata"]["metadata_date_stamp"],
            },
            "raw_sha256": manifest["sha256"],
            "crs_original": "EPSG:25830",
            "raster": raster_info,
            "output_file": path.name,
            "output_bytes": path.stat().st_size,
            "n_features": len(fc["features"]),
            "n_invalid_fixed": fixed,
            "classes": [
                {"class_code": c["class_code"], "class_label": c["class_label"], "color_suggestion": c["color"],
                 "transparent_in_official_style": c["transparent_in_official_style"],
                 "present_in_raster": c["class_code"] in present,
                 "regional_area_ha": round(regional.get(c["class_code"], 0) * pixel_area / 10_000, 1)}
                for c in legends[lyr.layer]
            ],
            "simplification_tolerance_m": info["simplification_tolerance_m"],
            "web_generalization": info,
            "pixels_with_data_outside_municipalities": outside,
        }
        print(f"[idem] {lyr.layer}: {len(fc['features'])} polígonos, {path.stat().st_size/1e6:.1f} MB", flush=True)

    (out_dir / "layers_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--web-cell", type=float, default=WEB_CELL_M)
    p.add_argument("--layers", nargs="*", default=None)
    p.add_argument("--web-only", action="store_true", help="regenerar solo las capas web (conserva el CSV)")
    a = p.parse_args(argv)
    run(a.layers, a.web_cell, a.web_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
