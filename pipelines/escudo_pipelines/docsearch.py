"""M19 · Asistente documental con citas (ROADMAP 4.4) — búsqueda EXTRACTIVA, sin IA generativa.

Indexa el texto de los documentos oficiales ya ingeridos (DOC-01 Plan Anual 2026, DOC-02 Decreto INFOMA) en
fragmentos con su página, y los ordena por BM25 frente a la pregunta. Nunca redacta una respuesta: devuelve
fragmentos LITERALES con documento y página, para que la persona lea la fuente. No responde decisiones operativas.

    python -m escudo_pipelines.docsearch build      # data/processed/docs/passages.jsonl
    python -m escudo_pipelines.docsearch "¿cuándo empieza la época de peligro alto?"
"""

from __future__ import annotations

import json
import logging
import math
import re
import sys
import unicodedata
from collections import Counter
from functools import lru_cache

from .fetch import RAW_DIR, REPO_ROOT

OUT = REPO_ROOT / "data" / "processed" / "docs" / "passages.jsonl"
PAGES = REPO_ROOT / "data" / "processed" / "docs" / "pages.json"
EVAL_SET = REPO_ROOT / "data" / "reference" / "docsearch_eval.json"
EVAL_OUT = REPO_ROOT / "data" / "processed" / "docs" / "eval.json"
CONTEXT = 30  # palabras de contexto a cada lado del fragmento ganador al mostrarlo
DOCS = {
    "DOC-01": {"file": RAW_DIR / "DOC-01" / "plan_anual_iiff_2026.pdf",
               "title": "Plan Anual de Prevención, Vigilancia y Extinción de Incendios Forestales de la Comunidad de "
                        "Madrid 2026",
               "url": "https://www.comunidad.madrid/transparencia/sites/default/files/plan_anual_iiff_2026.pdf"},
    "DOC-02": {"file": RAW_DIR / "DOC-02" / "BOCM-20170609-1.PDF",
               "title": "Decreto 59/2017 (INFOMA), BOCM núm. 136, 09/06/2017",
               "url": "https://www.bocm.es/boletin/CM_Orden_BOCM/2017/06/09/BOCM-20170609-1.PDF"},
}
WINDOW, STEP = 60, 25  # palabras por fragmento y avance (solape de 35)
K1, B = 1.2, 0.75
STOP = set("""a al algo ante antes como con contra cual cuales cuando de del desde donde dos e el ella ellas ellos
en entre era es esa esas ese eso esos esta estan estas este esto estos fue ha han hay hasta la las le les lo los mas
me mi muy ni no nos o os otra otras otro otros para pero por porque que quien quienes se sea segun ser si sin sobre
son su sus tambien tiene tienen todo todos tras u un una unas uno unos y ya cual que como cuanto cuantos cuantas
debe deben puede pueden qué cómo cuándo dónde""".split())
DISCLAIMER = ("Búsqueda extractiva: se muestran fragmentos literales de documentos oficiales con su página, sin "
              "redactar respuestas. Lea el documento completo y consulte al personal técnico competente. No sirve "
              "para decisiones operativas ni de emergencia (ASEM 112).")
HEADER = re.compile(r"^(PLAN ANUAL DE PREVENCIÓN.*?2026|VIERNES 9 DE JUNIO DE 2017.*?BOCM|BOCM-20170609-1|"
                    r"BOLETÍN OFICIAL DE LA COMUNIDAD DE MADRID)\s*", re.M)


def _fold(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def _stem(t: str) -> str:
    """Stemming ligero en español: plurales y vocal final (faja/fajas, ancho/anchura no se igualan a propósito)."""
    if t.isdigit():
        return t
    for suf in ("ciones", "siones"):
        if t.endswith(suf) and len(t) > len(suf) + 2:
            return t[: -len(suf)] + suf[0] + "ion"
    for suf in ("es", "s"):
        if len(t) > len(suf) + 3 and t.endswith(suf):
            t = t[: -len(suf)]
            break
    if len(t) > 4 and t[-1] in "aoe":
        t = t[:-1]
    return t


def tokenize(s: str) -> list[str]:
    return [_stem(t) for t in re.findall(r"[a-z0-9]+", _fold(s)) if t not in STOP and len(t) > 1]


def _clean(text: str) -> str:
    text = text.replace("­", "")
    text = re.sub(r"-\n(?=[a-zñáéíóú])", "", text)  # palabras partidas a final de línea
    return re.sub(r"\s+", " ", text).strip()


def build() -> int:
    from pypdf import PdfReader

    logging.getLogger("pypdf").setLevel(logging.ERROR)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    pages: dict[str, str] = {}
    with OUT.open("w", encoding="utf-8") as f:
        for doc_id, meta in DOCS.items():
            if not meta["file"].exists():
                raise FileNotFoundError(f"{doc_id}: falta {meta['file']} (ejecute su fetch)")
            for i, page in enumerate(PdfReader(meta["file"]).pages, start=1):
                raw = page.extract_text() or ""
                printed = re.search(r"P[áa]g\.\s*(\d+)", raw[:200])
                words = _clean(HEADER.sub("", raw)).split()
                if len(words) < 12:
                    continue
                pages[f"{doc_id}|{i}"] = " ".join(words)
                for start in range(0, max(1, len(words) - 30), STEP):
                    chunk = " ".join(words[start:start + WINDOW])
                    f.write(json.dumps({"doc_id": doc_id, "pdf_page": i, "start": start,
                                        "printed_page": int(printed.group(1)) if printed and doc_id == "DOC-02" else None,
                                        "text": chunk}, ensure_ascii=False) + "\n")
                    n += 1
    PAGES.write_text(json.dumps(pages, ensure_ascii=False), encoding="utf-8")
    return n


@lru_cache(maxsize=1)
def _pages() -> dict[str, list[str]]:
    if not PAGES.exists():
        return {}
    return {k: v.split() for k, v in json.loads(PAGES.read_text(encoding="utf-8")).items()}


def context_text(p: dict) -> str:
    """Fragmento ganador ampliado con CONTEXT palabras a cada lado (texto literal de la misma página)."""
    words = _pages().get(f"{p['doc_id']}|{p['pdf_page']}")
    if not words or "start" not in p:
        return p["text"]
    a, b = max(0, p["start"] - CONTEXT), min(len(words), p["start"] + WINDOW + CONTEXT)
    return ("… " if a > 0 else "") + " ".join(words[a:b]) + (" …" if b < len(words) else "")


@lru_cache(maxsize=1)
def _index() -> tuple[list[dict], list[Counter], list[int], dict[str, int], float]:
    if not OUT.exists():
        return [], [], [], {}, 0.0
    passages = [json.loads(line) for line in OUT.read_text(encoding="utf-8").splitlines() if line.strip()]
    tfs = [Counter(tokenize(p["text"])) for p in passages]
    lens = [sum(tf.values()) for tf in tfs]
    df: Counter = Counter()
    for tf in tfs:
        df.update(tf.keys())
    return passages, tfs, lens, dict(df), (sum(lens) / len(lens) if lens else 0.0)


PAIR_BONUS = 2.0


@lru_cache(maxsize=4096)
def _seq(i: int) -> frozenset[tuple[str, str]]:
    toks = tokenize(_index()[0][i]["text"])
    return frozenset(zip(toks, toks[1:], strict=False))


def search(query: str, k: int = 5) -> list[dict]:
    passages, tfs, lens, df, avg = _index()
    q = list(dict.fromkeys(tokenize(query)))
    if not passages or not q:
        return []
    n = len(passages)
    q_pairs = list(zip(q, q[1:], strict=False))
    scores = []
    for i, tf in enumerate(tfs):
        s = 0.0
        for t in q:
            f = tf.get(t)
            if f:
                idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
                s += idf * f * (K1 + 1) / (f + K1 * (1 - B + B * lens[i] / avg))
        if s > 0 and q_pairs:  # proximidad: términos consecutivos de la pregunta también consecutivos en el texto
            seq = _seq(i)
            s += PAIR_BONUS * sum(1 for a, b in q_pairs if (a, b) in seq)
        if s > 0:
            scores.append((s, i))
    scores.sort(key=lambda x: (-x[0], x[1]))
    out, seen = [], set()
    for s, i in scores:
        p = passages[i]
        key = (p["doc_id"], p["pdf_page"])
        if key in seen:  # un resultado por página
            continue
        seen.add(key)
        meta = DOCS[p["doc_id"]]
        out.append({**p, "text": context_text(p), "score": round(s, 3), "doc_title": meta["title"],
                    "url": f"{meta['url']}#page={p['pdf_page']}", "matched_terms": [t for t in q if t in tfs[i]]})
        if len(out) == k:
            break
    return out


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", _fold(s)).strip()


def evaluate(k: int = 3) -> dict:
    """Acierto@k sobre el conjunto fijo: algún resultado de los k primeros contiene la frase literal esperada."""
    items = json.loads(EVAL_SET.read_text(encoding="utf-8"))["items"]
    rows = []
    for it in items:
        top = search(it["q"], k)
        hit = next((r for r in top if _norm(it["expect"]) in _norm(r["text"])), None)
        rows.append({"q": it["q"], "expect": it["expect"], "doc": it["doc"], "hit": hit is not None,
                     "hit_page": hit["pdf_page"] if hit else None,
                     "top_pages": [f"{r['doc_id']} p.{r['pdf_page']}" for r in top]})
    hits = sum(r["hit"] for r in rows)
    return {"k": k, "hits": hits, "total": len(rows), "hit_rate": round(hits / len(rows), 3), "items": rows,
            "method": json.loads(EVAL_SET.read_text(encoding="utf-8"))["method"]}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if sys.argv[1:] == ["build"]:
        print(f"{build()} fragmentos → {OUT.relative_to(REPO_ROOT)}")
    elif sys.argv[1:] == ["evaluate"]:
        ev = evaluate()
        EVAL_OUT.write_text(json.dumps(ev, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"acierto@{ev['k']}: {ev['hits']}/{ev['total']}")
        for r in ev["items"]:
            if not r["hit"]:
                print("  ✗", r["q"], r["top_pages"])
    else:
        for r in search(" ".join(sys.argv[1:]), 3):
            pg = f"pág. PDF {r['pdf_page']}" + (f" (BOCM pág. {r['printed_page']})" if r["printed_page"] else "")
            print(f"[{r['doc_id']} {pg} · {r['score']}] {r['text'][:220]}…")
