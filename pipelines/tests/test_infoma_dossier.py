"""M15 (DOC-02): cada punto del expediente cita literalmente el Decreto 59/2017 (INFOMA) con apartado y página."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DEF = ROOT / "data" / "reference" / "infoma_dossier.json"
PDF = ROOT / "data" / "raw" / "DOC-02" / "BOCM-20170609-1.PDF"
CATALOG = ROOT / "data" / "reference" / "measures_catalog.json"


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace("­", "")).strip()


def test_definition_is_complete_and_never_claims_approval():
    d = json.loads(DEF.read_text(encoding="utf-8"))
    codes = [i["code"] for i in d["items"]]
    assert len(codes) == len(set(codes)) == 15
    assert {i["group"] for i in d["items"]} == {"anexo5", "anexo6"}
    assert all(re.search(r"Anexo [56], ap\. [\d.a-z]+ · BOCM págs?\. \d+", i["citation"]) for i in d["items"])
    assert "no redacta, no aprueba, no registra y no certifica" in d["notice"]
    known = {m["code"] for m in json.loads(CATALOG.read_text(encoding="utf-8"))["measures"]}
    assert all(c in known for i in d["items"] for c in i["linked_measures"])
    assert all(len(i["excerpt"]) <= 200 for i in d["items"])


@pytest.mark.skipif(not PDF.exists(), reason="ejecute python -m escudo_pipelines.infoma")
def test_excerpts_are_literal_in_official_bocm_text():
    from pypdf import PdfReader

    logging.getLogger("pypdf").setLevel(logging.ERROR)
    d = json.loads(DEF.read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "data/raw/DOC-02/manifest.json").read_text(encoding="utf-8"))
    assert manifest["sha256"] == d["sha256"]
    reader = PdfReader(PDF)
    text = _norm(" ".join((reader.pages[i].extract_text() or "") for i in range(61, 67)))
    for it in d["items"]:
        for part in it["excerpt"].split("[…]"):
            assert _norm(part).strip(" .") in text, it["code"]
