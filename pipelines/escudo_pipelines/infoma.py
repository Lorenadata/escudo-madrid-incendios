"""DOC-02 · Decreto 59/2017, de 6 de junio, Plan Especial de Protección Civil de Emergencia por Incendios Forestales
en la Comunidad de Madrid (INFOMA). BOCM núm. 136, de 9 de junio de 2017.

Se usa como referencia normativa del expediente de autoprotección (M15): Anexo 5 (contenido mínimo del plan de
autoprotección) y Anexo 6 (obligaciones de las urbanizaciones sin continuidad inmediata con la trama urbana).
Texto original publicado; existe corrección de errores (BOCM 25/08/2017): comprobar la versión consolidada antes
de cualquier uso formal.

    python -m escudo_pipelines.infoma fetch
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime

import httpx

from .fetch import RAW_DIR, USER_AGENT
from .sources import SourceSpec

SOURCE_ID = "DOC-02"
URL = "https://www.bocm.es/boletin/CM_Orden_BOCM/2017/06/09/BOCM-20170609-1.PDF"
PDF_NAME = "BOCM-20170609-1.PDF"

SPEC = SourceSpec(
    source_id=SOURCE_ID,
    portal="CAM-DOC",
    ckan_id=None,
    title="Decreto 59/2017, de 6 de junio, Plan Especial de Protección Civil de Emergencia por Incendios Forestales "
          "en la Comunidad de Madrid (INFOMA)",
    producer="Comunidad de Madrid — Consejo de Gobierno (BOCM núm. 136, 09/06/2017)",
    catalog_url=URL,
    license="Norma publicada en boletín oficial (cita obligatoria)",
    spatial_scope="Comunidad de Madrid (normativa)",
    temporal_scope="vigente desde 2017; texto original publicado",
    use_in_product="Lista de comprobación del expediente de autoprotección (Anexos 5 y 6), con apartado y página",
    caveats=("Texto original publicado; existe corrección de errores (BOCM 25/08/2017). ESCUDO no interpreta ni "
             "aplica la norma: lista sus requisitos con cita para que la organización y su técnico los revisen."),
    resource_format="PDF",
)


def fetch() -> dict:
    out = RAW_DIR / SOURCE_ID
    out.mkdir(parents=True, exist_ok=True)
    r = httpx.get(URL, timeout=120, follow_redirects=True, headers={"User-Agent": USER_AGENT})
    r.raise_for_status()
    (out / PDF_NAME).write_bytes(r.content)
    m = {"source_id": SOURCE_ID, "ckan_id": None, "title": SPEC.title, "catalog_url": URL, "resource_url": URL,
         "format": "PDF", "file": PDF_NAME, "bytes": len(r.content), "sha256": hashlib.sha256(r.content).hexdigest(),
         "license_id": "boletin-oficial", "license_title": SPEC.license,
         "resource_last_modified": r.headers.get("last-modified"),
         "extracted_at": datetime.now(UTC).isoformat(timespec="seconds"),
         "pages_used": {"anexo_5": "BOCM págs. 71–74 (PDF 62–65)", "anexo_6": "BOCM págs. 74–76 (PDF 65–67)"}}
    (out / "manifest.json").write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
    return m


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    m = fetch()
    print(f"OK {SOURCE_ID} {m['bytes']} B sha256={m['sha256'][:12]}")
