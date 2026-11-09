"""Tests de la actualización verificable (ROADMAP 2.4) con transporte HTTP simulado: no toca datos reales."""

from __future__ import annotations

import hashlib
import json

import httpx
import pytest

from escudo_pipelines import refresh


@pytest.fixture()
def sandbox(tmp_path, monkeypatch):
    raw = tmp_path / "raw"
    (raw / "CAM-XX").mkdir(parents=True)
    old = b"a;b\n1;2\n"
    (raw / "CAM-XX" / "datos.csv").write_bytes(old)
    (raw / "CAM-XX" / "manifest.json").write_text(json.dumps({
        "source_id": "CAM-XX", "file": "datos.csv", "sha256": hashlib.sha256(old).hexdigest(), "bytes": len(old),
        "extracted_at": "2026-11-06T00:00:00+00:00", "resource_url": "https://example.test/datos.csv"}), encoding="utf-8")
    monkeypatch.setattr(refresh, "RAW_DIR", raw)
    monkeypatch.setattr(refresh, "LOG_PATH", tmp_path / "refresh_log.json")
    monkeypatch.setattr(refresh, "_resolver", lambda sid: lambda client: {
        "url": "https://example.test/datos.csv", "file": "datos.csv", "portal_metadata_modified": "2026-11-09",
        "resource_last_modified": None})
    return raw, old


def _client(body: bytes | None, status: int = 200) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(status, content=body or b"")))


def test_unchanged_source_records_check_only(sandbox):
    raw, old = sandbox
    rec = refresh.check_source(_client(old), "CAM-XX", apply=True)
    m = json.loads((raw / "CAM-XX" / "manifest.json").read_text(encoding="utf-8"))
    assert rec["result"] == "unchanged" and m["last_check_result"] == "unchanged" and m["last_checked_at"]
    assert m["extracted_at"] == "2026-11-06T00:00:00+00:00" and "previous_versions" not in m
    assert not (raw / "CAM-XX" / ".refresh.tmp").exists()


def test_changed_without_apply_never_touches_data_in_use(sandbox):
    raw, old = sandbox
    rec = refresh.check_source(_client(b"a;b\n1;3\n"), "CAM-XX", apply=False)
    m = json.loads((raw / "CAM-XX" / "manifest.json").read_text(encoding="utf-8"))
    assert rec["result"] == "changed" and rec["applied"] is False
    assert m["sha256"] == hashlib.sha256(old).hexdigest() and m["last_check_result"] == "changed_pending"
    assert (raw / "CAM-XX" / "datos.csv").read_bytes() == old


def test_changed_with_apply_versions_and_keeps_history(sandbox):
    raw, old = sandbox
    new = b"a;b\n1;3\n"
    rec = refresh.check_source(_client(new), "CAM-XX", apply=True)
    m = json.loads((raw / "CAM-XX" / "manifest.json").read_text(encoding="utf-8"))
    assert rec["applied"] and m["sha256"] == hashlib.sha256(new).hexdigest()
    assert m["previous_versions"][0]["sha256"] == hashlib.sha256(old).hexdigest()
    assert (raw / "CAM-XX" / "datos.csv").read_bytes() == new and m["portal_metadata_modified"] == "2026-11-09"


def test_failed_download_is_explicit_and_keeps_previous_version(sandbox):
    raw, old = sandbox
    rec = refresh.check_source(_client(None, status=503), "CAM-XX", apply=True)
    m = json.loads((raw / "CAM-XX" / "manifest.json").read_text(encoding="utf-8"))
    assert rec["result"] == "failed" and "503" in rec["error"]
    assert m["last_check_result"] == "failed" and m["sha256"] == hashlib.sha256(old).hexdigest()
    assert (raw / "CAM-XX" / "datos.csv").read_bytes() == old


def test_run_log_is_bounded(sandbox, monkeypatch):
    for i in range(refresh.LOG_KEEP + 5):
        refresh.append_log({"started_at": str(i), "results": []})
    runs = json.loads(refresh.LOG_PATH.read_text(encoding="utf-8"))
    assert len(runs) == refresh.LOG_KEEP and runs[-1]["started_at"] == str(refresh.LOG_KEEP + 4)


def test_reordered_csv_is_flagged_as_same_content(sandbox):
    raw, old = sandbox
    (raw / "CAM-XX" / "datos.csv").write_bytes(b"a;b\n1;2\n3;4\n")
    rec = refresh.check_source(_client(b"a;b\r\n3;4\r\n1;2\r\n"), "CAM-XX", apply=False)
    assert rec["result"] == "changed" and rec["content"] == "same_rows_reordered"
    rec2 = refresh.check_source(_client(b"a;b\n3;5\n1;2\n"), "CAM-XX", apply=False)
    assert rec2["content"] == "different"


@pytest.mark.parametrize("bad", ["https://x.test/..", "https://x.test/a/..%5C..%5Cevil.csv", "..\\evil.csv",
                                 "C:evil.csv", "https://x.test/", ".hidden"])
def test_remote_filenames_cannot_escape_raw_dir(bad):
    from escudo_pipelines.fetch import safe_filename

    with pytest.raises(ValueError):
        safe_filename(bad)


def test_safe_filename_accepts_portal_names(tmp_path):
    from escudo_pipelines.fetch import inside, safe_filename

    url = "https://datos.comunidad.madrid/dataset/x/resource/y/download/densidad-de-poblacion.-municipios.csv"
    assert safe_filename(url) == "densidad-de-poblacion.-municipios.csv"
    assert inside(tmp_path, "datos.csv") == (tmp_path / "datos.csv").resolve()
