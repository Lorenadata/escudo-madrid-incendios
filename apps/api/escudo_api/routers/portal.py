"""M18 · Portal público de avance (ROADMAP 4.5): agregados por municipio SIN datos privados.

Reglas de privacidad (todas obligatorias, comprobadas por test):
- solo cuentan ámbitos cuya organización ha autorizado compartirlos (`shared_with_municipality`);
- un municipio se publica solo con al menos MIN_AREAS ámbitos de al menos MIN_ORGS organizaciones distintas;
  si no, figura como «no se publica» sin ninguna cifra;
- nunca se publican nombres de ámbitos u organizaciones, costes, ubicaciones ni textos libres.
Son indicadores de GESTIÓN (actuaciones hechas, documentadas, inspecciones recientes), nunca de riesgo.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import AreaOfInterest, Municipality, MunicipalSeries
from .municipal import _area_status

router = APIRouter(prefix="/v1/public", tags=["portal público"])

MIN_AREAS, MIN_ORGS = 3, 3
MAX_ORG_SHARE = 0.5      # regla de dominancia: ninguna organización aporta más de la mitad de las actuaciones
SHARE_BIN, COUNT_BIN = 0.10, 5
NOTICE = (f"Agregados de gestión preventiva, no de riesgo. Solo incluyen ámbitos cuya organización ha autorizado "
          f"compartirlos. Un municipio solo se publica con al menos {MIN_AREAS} ámbitos de {MIN_ORGS} organizaciones "
          f"distintas y si ninguna aporta más de la mitad de las actuaciones; los porcentajes se redondean a tramos "
          f"de 10 puntos y los totales a múltiplos de {COUNT_BIN}, para que ninguna organización pueda deducir las cifras "
          f"de otra. No se publican nombres, costes ni ubicaciones. Una actuación «hecha» es lo que declara la "
          f"organización; no implica verificación técnica ni cumplimiento normativo.")


def _share(n: int, d: int) -> float | None:
    """Proporción redondeada al tramo de 10 puntos más cercano (agregado grueso, anti-diferencias)."""
    return round(round((n / d) / SHARE_BIN) * SHARE_BIN, 2) if d else None


def _coarse(n: int) -> int:
    return int(round(n / COUNT_BIN) * COUNT_BIN)


@router.get("/progress")
def public_progress(session: Session = Depends(get_session)) -> dict[str, Any]:
    areas = list(session.scalars(select(AreaOfInterest).where(AreaOfInterest.shared_with_municipality.is_(True))))
    by_muni: dict[str, list[AreaOfInterest]] = defaultdict(list)
    for a in areas:
        by_muni[a.municipality_code].append(a)
    names = dict(session.execute(select(Municipality.ine_code, Municipality.name)).all())
    zar = {c for (c,) in session.execute(select(MunicipalSeries.ine_code).where(
        MunicipalSeries.indicator_id == "municipality_zar_declared", MunicipalSeries.value == 1))}
    year_ago = date.today() - timedelta(days=365)
    published, withheld = [], []
    for ine, group in sorted(by_muni.items()):
        orgs = {a.organization_id for a in group}
        st = [_area_status(session, a) for a in group] if len(group) >= MIN_AREAS and len(orgs) >= MIN_ORGS else []
        tot = sum(x["actions_total"] for x in st)
        per_org: dict[str, int] = defaultdict(int)
        for a, x in zip(group, st, strict=False):
            per_org[a.organization_id] += x["actions_total"]
        dominant = bool(tot) and max(per_org.values()) / tot > MAX_ORG_SHARE
        if not st or dominant:
            withheld.append({"ine_code": ine, "name": names.get(ine), "reason": "por debajo del umbral de privacidad"})
            continue
        done = sum(x["actions_done"] for x in st)
        doc = sum(x["actions_documented"] for x in st)
        overdue = sum(x["actions_overdue"] for x in st)
        recent = sum(1 for x in st if x["last_inspection_on"] and x["last_inspection_on"] >= year_ago)
        published.append({
            "ine_code": ine, "name": names.get(ine), "zar_declared": ine in zar,
            "areas_band": f"{MIN_AREAS} o más" if len(group) < 10 else "10 o más",
            "synthetic": any(a.record_status == "synthetic" for a in group),
            "actions_total_approx": _coarse(tot), "actions_done_share": _share(done, tot),
            "actions_documented_share": _share(doc, tot), "actions_overdue_share": _share(overdue, tot),
            "areas_inspected_last_12m_share": _share(recent, len(group)), "status": "derived"})
    return {"notice": NOTICE,
            "thresholds": {"min_areas": MIN_AREAS, "min_organizations": MIN_ORGS, "max_org_share": MAX_ORG_SHARE,
                           "share_bin": SHARE_BIN, "count_bin": COUNT_BIN},
            "published": published, "withheld": withheld,
            "method": ("Suma de los ámbitos autorizados de cada municipio: actuaciones del último plan de cada ámbito "
                       "(hechas / documentadas con evidencia / vencidas sin hacer) e inspecciones en los últimos 12 "
                       "meses, con umbral, regla de dominancia y redondeo. Calculado en el momento de la consulta.")}
