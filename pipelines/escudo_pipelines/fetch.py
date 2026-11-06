"""Descarga reproducible de recursos del Portal CKAN de la Comunidad de Madrid.

Para cada fuente: consulta `package_show`, elige el recurso del formato pedido,
descarga a `data/raw/<source_id>/`, calcula SHA-256 y escribe `manifest.json` con
URL, fecha de extracción, fecha de modificación declarada por el portal y licencia.

Uso:  python -m escudo_pipelines.fetch [CAM-01 CAM-02 ...]
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx

from .sources import ALL_SOURCES, CKAN_BASE, SourceSpec

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw"
USER_AGENT = "escudo-madrid-etl/0.1 (+https://github.com/; DATAMAD 2026)"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_resource(client: httpx.Client, spec: SourceSpec) -> tuple[dict, dict]:
    r = client.get(f"{CKAN_BASE}/package_show", params={"id": spec.ckan_id})
    r.raise_for_status()
    pkg = r.json()["result"]
    candidates = [res for res in pkg["resources"] if (res.get("format") or "").upper() == spec.resource_format]
    if spec.resource_name_hint:
        candidates = [c for c in candidates if spec.resource_name_hint in (c.get("name") or "")] or candidates
    if not candidates:
        raise RuntimeError(f"{spec.source_id}: sin recurso {spec.resource_format} en {spec.ckan_id}")
    return pkg, candidates[0]


def fetch_source(client: httpx.Client, spec: SourceSpec) -> dict:
    pkg, res = resolve_resource(client, spec)
    out_dir = RAW_DIR / spec.source_id
    out_dir.mkdir(parents=True, exist_ok=True)
    url = res["url"]
    filename = url.rsplit("/", 1)[-1]
    target = out_dir / filename
    with client.stream("GET", url) as resp:
        resp.raise_for_status()
        with target.open("wb") as f:
            for chunk in resp.iter_bytes():
                f.write(chunk)
    manifest = {
        "source_id": spec.source_id,
        "ckan_id": spec.ckan_id,
        "title": pkg.get("title"),
        "catalog_url": spec.catalog_url,
        "resource_id": res.get("id"),
        "resource_url": url,
        "format": res.get("format"),
        "file": filename,
        "bytes": target.stat().st_size,
        "sha256": sha256_file(target),
        "license_id": pkg.get("license_id"),
        "license_title": pkg.get("license_title"),
        "portal_metadata_modified": pkg.get("metadata_modified"),
        "resource_last_modified": res.get("last_modified") or res.get("created"),
        "extracted_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main(argv: list[str]) -> int:
    ids = argv or list(ALL_SOURCES)
    failures = 0
    with httpx.Client(timeout=120, follow_redirects=True, headers={"User-Agent": USER_AGENT}) as client:
        for sid in ids:
            try:
                m = fetch_source(client, ALL_SOURCES[sid])
                print(f"OK   {sid}  {m['bytes']:>10} B  sha256={m['sha256'][:12]}  {m['file']}")
            except Exception as exc:  # documentar y continuar con otras fuentes
                failures += 1
                print(f"FAIL {sid}: {exc}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
