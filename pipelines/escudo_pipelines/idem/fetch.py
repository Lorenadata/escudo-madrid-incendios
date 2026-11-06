"""Descarga reproducible de las capas IDEM GEO-01..03.

Descarga el ZIP SHP y el XML de metadatos ISO 19139 a `data/raw/<GEO-XX>/` y escribe
`manifest.json` con el mismo formato que `escudo_pipelines.fetch` (SHA-256, fechas, licencia).

Uso:  python -m escudo_pipelines.idem.fetch [GEO-01 GEO-02 GEO-03]
"""

from __future__ import annotations

import json
import re
import sys
from datetime import UTC, datetime

import httpx

from escudo_pipelines.fetch import RAW_DIR, USER_AGENT, sha256_file

from .sources import IDEM_BY_SOURCE, IdemLayer


def _download(client: httpx.Client, url: str, target) -> None:
    with client.stream("GET", url) as resp:
        resp.raise_for_status()
        with target.open("wb") as f:
            for chunk in resp.iter_bytes():
                f.write(chunk)


def parse_iso_metadata(xml_text: str) -> dict:
    """Extrae del XML ISO 19139 las fechas tipificadas, CRS y licencia declarada."""
    dates: dict[str, str] = {}
    for block in re.findall(r"<gmd:CI_Date>(.*?)</gmd:CI_Date>", xml_text, re.S):
        value = re.search(r"<gco:Date(?:Time)?>(.*?)</gco:Date", block)
        kind = re.search(r'codeListValue="([A-Za-z]+)"', block)
        if value and kind:
            dates.setdefault(kind.group(1), value.group(1))
    stamp = re.search(r"<gmd:dateStamp>\s*<gco:Date(?:Time)?>(.*?)</gco:Date", xml_text, re.S)
    crs = re.search(r"EPSG:(\d+)", xml_text)
    lic = re.search(r'creativecommons\.org/licenses/([^"]+)"[^>]*>([^<]+)<', xml_text)
    scale = re.search(r"<gmd:denominator>\s*<gco:Integer>(\d+)</gco:Integer>", xml_text, re.S)
    return {
        "metadata_date_stamp": stamp.group(1) if stamp else None,
        "citation_dates": dates,
        "crs_declared": f"EPSG:{crs.group(1)}" if crs else None,
        "license_url": f"https://creativecommons.org/licenses/{lic.group(1)}" if lic else None,
        "license_title": lic.group(2).strip() if lic else None,
        "scale_denominator": int(scale.group(1)) if scale else None,
    }


def parse_legend(legend: dict) -> list[dict]:
    """Clases de la leyenda GeoServer: [{class_code, class_label, color}] con etiqueta literal."""
    out: list[dict] = []
    for item in legend["Legend"]:
        for rule in item["rules"]:
            for sym in rule["symbolizers"]:
                for e in sym.get("Raster", {}).get("colormap", {}).get("entries", []):
                    out.append({
                        "class_code": int(float(e["quantity"])),
                        "class_label": e["label"],
                        "color": e.get("color"),
                        "transparent_in_official_style": float(e.get("opacity", "1")) == 0.0,
                    })
    if not out:
        raise ValueError("leyenda sin entradas de colormap")
    return out


def fetch_layer(client: httpx.Client, layer: IdemLayer) -> dict:
    spec = layer.spec
    out_dir = RAW_DIR / spec.source_id
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / layer.zip_name
    _download(client, layer.download_url, target)
    meta_path = out_dir / f"{layer.metadata_record}.iso19139.xml"
    _download(client, layer.metadata_url, meta_path)
    iso = parse_iso_metadata(meta_path.read_text(encoding="utf-8", errors="replace"))
    legend_path = out_dir / "legend.json"
    _download(client, layer.legend_url, legend_path)
    legend_classes = parse_legend(json.loads(legend_path.read_text(encoding="utf-8")))
    manifest = {
        "source_id": spec.source_id,
        "ckan_id": None,
        "title": spec.title,
        "catalog_url": spec.catalog_url,
        "resource_id": layer.metadata_record,
        "resource_url": layer.download_url,
        "format": "GeoTIFF uint8 (ZIP)",
        "file": layer.zip_name,
        "bytes": target.stat().st_size,
        "sha256": sha256_file(target),
        "license_id": "CC-BY-4.0",
        "license_title": iso["license_title"] or spec.license,
        "portal_metadata_modified": iso["metadata_date_stamp"],
        "resource_last_modified": iso["citation_dates"].get("revision") or iso["citation_dates"].get("publication"),
        "extracted_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "metadata_file": meta_path.name,
        "metadata_sha256": sha256_file(meta_path),
        "iso_metadata": iso,
        "legend_url": layer.legend_url,
        "legend_file": legend_path.name,
        "legend_sha256": sha256_file(legend_path),
        "legend_classes": legend_classes,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main(argv: list[str]) -> int:
    ids = argv or list(IDEM_BY_SOURCE)
    failures = 0
    with httpx.Client(timeout=300, follow_redirects=True, headers={"User-Agent": USER_AGENT}) as client:
        for sid in ids:
            try:
                m = fetch_layer(client, IDEM_BY_SOURCE[sid])
                print(f"OK   {sid}  {m['bytes']:>10} B  sha256={m['sha256'][:12]}  {m['file']}")
            except Exception as exc:
                failures += 1
                print(f"FAIL {sid}: {exc}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
