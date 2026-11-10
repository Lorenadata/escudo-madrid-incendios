"""M19: búsqueda extractiva evaluada con un conjunto fijo de 20 preguntas (frase literal esperada en el top 3)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from escudo_pipelines import docsearch as ds

ROOT = Path(__file__).resolve().parents[2]


def test_tokenize_folds_accents_stopwords_and_plurals():
    assert ds.tokenize("¿Cuándo es la época de peligro?") == ds.tokenize("EPOCA peligros") == ["epoc", "peligr"]
    assert ds.tokenize("fajas") == ds.tokenize("faja") and ds.tokenize("urbanizaciones") == ds.tokenize("urbanización")
    assert ds.tokenize("59 de 2026") == ["59", "2026"]


@pytest.mark.skipif(not ds.OUT.exists(), reason="ejecute python -m escudo_pipelines.docsearch build")
def test_results_are_literal_with_page_and_link():
    ds._index.cache_clear()
    r = ds.search("época de peligro alto", 3)
    assert r and all(x["doc_id"] in ds.DOCS and x["pdf_page"] >= 1 and "#page=" in x["url"] for x in r)
    pages = {k: " ".join(v) for k, v in ds._pages().items()}
    for x in r:  # el texto mostrado es literal de esa página (sin las elipsis de contexto)
        assert x["text"].strip("… ").split(" … ")[0][:120] in pages[f"{x['doc_id']}|{x['pdf_page']}"]
    assert ds.search("de la el", 3) == []  # solo palabras vacías: no inventa resultados


@pytest.mark.skipif(not ds.OUT.exists(), reason="ejecute python -m escudo_pipelines.docsearch build")
def test_fixed_evaluation_set_and_stored_result_match():
    ds._index.cache_clear()
    live = ds.evaluate()
    assert live["total"] == 20 and live["hits"] >= 18, [i["q"] for i in live["items"] if not i["hit"]]
    stored = json.loads(ds.EVAL_OUT.read_text(encoding="utf-8"))
    assert stored["hits"] == live["hits"]  # lo que se publica coincide con lo que se mide
