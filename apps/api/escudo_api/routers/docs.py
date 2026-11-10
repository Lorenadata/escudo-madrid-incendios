"""M19 · Asistente documental con citas (ROADMAP 4.4): búsqueda extractiva en documentos oficiales.

Devuelve fragmentos LITERALES con documento y página; nunca redacta respuestas ni da indicaciones operativas.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Query

router = APIRouter(prefix="/v1/docs", tags=["normativa"])


@router.get("/search")
def docs_search(q: str = Query(min_length=3, max_length=300), k: int = Query(5, ge=1, le=10)) -> dict[str, Any]:
    from escudo_pipelines.docsearch import DISCLAIMER, search

    results = search(q, k)
    return {"query": q, "status": "official" if results else "unavailable", "disclaimer": DISCLAIMER,
            "sources": ["DOC-01", "DOC-02"], "results": [
                {"doc_id": r["doc_id"], "doc_title": r["doc_title"], "pdf_page": r["pdf_page"],
                 "printed_page": r["printed_page"], "text": r["text"], "url": r["url"], "score": r["score"],
                 "matched_terms": r["matched_terms"]} for r in results]}


@router.get("/evaluation")
def docs_evaluation() -> dict[str, Any]:
    from escudo_pipelines.docsearch import EVAL_OUT

    if not EVAL_OUT.exists():
        return {"status": "unavailable", "hits": None, "total": None, "items": []}
    return {"status": "derived", **json.loads(EVAL_OUT.read_text(encoding="utf-8"))}
