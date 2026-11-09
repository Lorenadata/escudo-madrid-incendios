"""Actualización verificable de fuentes (ROADMAP 2.4).

Vuelve a descargar cada fuente, calcula su SHA-256 y lo compara con el manifest vigente:

    python -m escudo_pipelines.refresh                 # solo comprueba (no toca los datos en uso)
    python -m escudo_pipelines.refresh --apply         # además guarda las versiones nuevas
    python -m escudo_pipelines.refresh --apply --rebuild   # y regenera procesados + carga en PostGIS
    python -m escudo_pipelines.refresh CAM-02 DOC-01   # solo esas fuentes

Cada comprobación queda en el manifest (`last_checked_at`, `last_check_result`) y en
`data/processed/refresh_log.json`. Una versión nueva conserva la anterior en `previous_versions`;
la carga (`escudo_api.etl_load`) registra cada SHA-256 distinto en la tabla `dataset_versions`.
Sin `--apply` nunca se modifica un dato en uso. IDEM (≈49 MB) se comprueba solo con `--include-idem`.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import httpx

from .fetch import RAW_DIR, REPO_ROOT, USER_AGENT, resolve_resource
from .sources import ALL_SOURCES

LOG_PATH = REPO_ROOT / "data" / "processed" / "refresh_log.json"
LOG_KEEP = 50
RESULTS = ("unchanged", "changed", "failed")


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _manifest_path(sid: str) -> Path:
    return RAW_DIR / sid / "manifest.json"


def _download(client: httpx.Client, url: str, target: Path) -> tuple[str, int]:
    h = hashlib.sha256()
    n = 0
    with client.stream("GET", url) as resp:
        resp.raise_for_status()
        with target.open("wb") as f:
            for chunk in resp.iter_bytes():
                h.update(chunk)
                n += len(chunk)
                f.write(chunk)
    return h.hexdigest(), n


def compare_content(old: Path, new: Path) -> str:
    """Para CSV: «same_rows_reordered» si contienen exactamente las mismas filas en otro orden; si no, «different»."""
    if old.suffix.lower() != ".csv" or not old.exists():
        return "different"
    a = old.read_bytes().splitlines()  # splitlines() trata igual \n y \r\n
    b = new.read_bytes().splitlines()
    return "same_rows_reordered" if a[:1] == b[:1] and sorted(a[1:]) == sorted(b[1:]) else "different"


def _resolver(sid: str) -> Callable[[httpx.Client], dict]:
    """Devuelve una función que obtiene {url, file, portal_metadata_modified, resource_last_modified} de la fuente."""
    if sid in ALL_SOURCES:
        spec = ALL_SOURCES[sid]

        def cam(client: httpx.Client) -> dict:
            pkg, res = resolve_resource(client, spec)
            return {"url": res["url"], "file": res["url"].rsplit("/", 1)[-1],
                    "portal_metadata_modified": pkg.get("metadata_modified"),
                    "resource_last_modified": res.get("last_modified") or res.get("created")}
        return cam
    if sid == "DOC-01":
        from .plan_anual import PDF_NAME, URL

        return lambda client: {"url": URL, "file": PDF_NAME, "portal_metadata_modified": None,
                               "resource_last_modified": None}
    if sid.startswith("GEO-"):
        from .idem.sources import IDEM_LAYERS

        layer = next(x for x in IDEM_LAYERS if x.spec.source_id == sid)
        return lambda client: {"url": layer.download_url, "file": layer.zip_name, "portal_metadata_modified": None,
                               "resource_last_modified": None}
    raise KeyError(sid)


def check_source(client: httpx.Client, sid: str, *, apply: bool) -> dict:
    """Comprueba una fuente. Devuelve el registro de la comprobación (y actualiza el manifest)."""
    mpath = _manifest_path(sid)
    manifest = json.loads(mpath.read_text(encoding="utf-8")) if mpath.exists() else {"source_id": sid}
    rec: dict = {"source_id": sid, "checked_at": _now(), "previous_sha256": manifest.get("sha256")}
    tmp = RAW_DIR / sid / ".refresh.tmp"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    try:
        info = _resolver(sid)(client)
        sha, size = _download(client, info["url"], tmp)
        rec.update({"sha256": sha, "bytes": size, "resource_url": info["url"]})
        if sha == manifest.get("sha256"):
            rec["result"] = "unchanged"
        else:
            rec["result"] = "changed"
            if manifest.get("file"):
                rec["content"] = compare_content(RAW_DIR / sid / manifest["file"], tmp)
            if apply:
                target = RAW_DIR / sid / info["file"]
                old = RAW_DIR / sid / manifest["file"] if manifest.get("file") else None
                if old and old.exists() and old != target:
                    old.unlink()
                tmp.replace(target)
                prev = {k: manifest.get(k) for k in ("sha256", "bytes", "extracted_at", "resource_url",
                                                      "portal_metadata_modified") if manifest.get(k) is not None}
                history = (manifest.get("previous_versions") or []) + ([prev] if prev.get("sha256") else [])
                manifest.update({"resource_url": info["url"], "file": info["file"], "bytes": size, "sha256": sha,
                                 "extracted_at": rec["checked_at"], "previous_versions": history})
                for k in ("portal_metadata_modified", "resource_last_modified"):
                    if info.get(k):
                        manifest[k] = info[k]
                rec["applied"] = True
            else:
                rec["applied"] = False
    except Exception as exc:  # una fuente caída no detiene el resto; nunca se reutiliza en silencio
        rec.update({"result": "failed", "error": f"{type(exc).__name__}: {exc}"[:300]})
    finally:
        if tmp.exists():
            tmp.unlink()
    manifest["last_checked_at"] = rec["checked_at"]
    manifest["last_check_result"] = rec["result"] if rec["result"] != "changed" or rec.get("applied") else "changed_pending"
    if mpath.exists() or rec["result"] != "failed":
        mpath.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return rec


def append_log(run: dict) -> None:
    runs = json.loads(LOG_PATH.read_text(encoding="utf-8")) if LOG_PATH.exists() else []
    runs = (runs + [run])[-LOG_KEEP:]
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text(json.dumps(runs, ensure_ascii=False, indent=2), encoding="utf-8")


def default_ids(include_idem: bool) -> list[str]:
    ids = list(ALL_SOURCES) + ["DOC-01"]
    if include_idem:
        ids += ["GEO-01", "GEO-02", "GEO-03"]
    return ids


def rebuild(changed: list[str]) -> None:
    py = sys.executable
    steps = []
    if any(s.startswith("CAM-") for s in changed):
        steps.append([py, "-m", "escudo_pipelines.cam_transform"])
    if "DOC-01" in changed:
        steps.append([py, "-m", "escudo_pipelines.plan_anual", "transform"])
    if any(s.startswith("GEO-") for s in changed):
        steps.append([py, "-m", "escudo_pipelines.idem.transform"])
    steps.append([py, "-m", "escudo_api.etl_load"] + ([] if any(s.startswith("GEO-") for s in changed) else ["--skip-idem"]))
    for cmd in steps:
        print("  →", " ".join(cmd[1:]))
        subprocess.run(cmd, check=True, cwd=REPO_ROOT)


def main(argv: list[str]) -> int:
    apply = "--apply" in argv
    do_rebuild = "--rebuild" in argv
    ids = [a for a in argv if not a.startswith("--")] or default_ids("--include-idem" in argv)
    run = {"started_at": _now(), "apply": apply, "results": []}
    with httpx.Client(timeout=180, follow_redirects=True, headers={"User-Agent": USER_AGENT}) as client:
        for sid in ids:
            rec = check_source(client, sid, apply=apply)
            run["results"].append(rec)
            mark = {"unchanged": "=", "changed": "≠", "failed": "!"}[rec["result"]]
            extra = rec.get("error") or (f"{(rec['previous_sha256'] or '—')[:12]} → {rec['sha256'][:12]}"
                                         + (" (aplicada)" if rec.get("applied") else " (sin aplicar)")
                                         + (" · mismas filas, otro orden" if rec.get("content") == "same_rows_reordered" else "")
                                         if rec["result"] == "changed" else rec["sha256"][:12])
            print(f"{mark} {sid:7} {rec['result']:9} {extra}")
    run["finished_at"] = _now()
    run["summary"] = {r: sum(1 for x in run["results"] if x["result"] == r) for r in RESULTS}
    append_log(run)
    changed = [x["source_id"] for x in run["results"] if x.get("applied")]
    print(f"Resumen: {run['summary']}")
    if changed and do_rebuild:
        rebuild(changed)
    elif changed:
        print("Versiones nuevas guardadas. Regenere y cargue: python -m escudo_pipelines.refresh --apply --rebuild")
    return 1 if run["summary"]["failed"] else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main(sys.argv[1:]))
