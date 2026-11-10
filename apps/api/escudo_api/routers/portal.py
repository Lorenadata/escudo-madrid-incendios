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
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import AreaOfInterest, DossierItem, Municipality, MunicipalSeries
from .municipal import _area_status

router = APIRouter(prefix="/v1/public", tags=["portal público"])

MIN_AREAS, MIN_ORGS = 3, 2
NOTICE = (f"Agregados de gestión preventiva, no de riesgo. Solo incluyen ámbitos cuya organización ha autorizado "
          f"compartirlos, y un municipio solo se publica con al menos {MIN_AREAS} ámbitos de {MIN_ORGS} organizaciones "
          f"distintas. No se publican nombres, costes ni ubicaciones. Una actuación «hecha» es lo que declara la "
          f"organización; no implica verificación técnica ni cumplimiento normativo.")


def _share(n: int, d: int) -> float | None:
    return round(n / d, 4) if d else None


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
        if len(group) < MIN_AREAS or len(orgs) < MIN_ORGS:
            withheld.append({"ine_code": ine, "name": names.get(ine), "reason": "por debajo del umbral de privacidad"})
            continue
        st = [_area_status(session, a) for a in group]
        tot = sum(x["actions_total"] for x in st)
        done = sum(x["actions_done"] for x in st)
        doc = sum(x["actions_documented"] for x in st)
        overdue = sum(x["actions_overdue"] for x in st)
        recent = sum(1 for x in st if x["last_inspection_on"] and x["last_inspection_on"] >= year_ago)
        ids = [a.id for a in group]
        dossier_ok = session.scalar(select(func.count()).select_from(DossierItem).where(
            DossierItem.area_id.in_(ids), DossierItem.status == "available")) or 0
        published.append({
            "ine_code": ine, "name": names.get(ine), "zar_declared": ine in zar,
            "areas": len(group), "organizations": len(orgs),
            "synthetic": any(a.record_status == "synthetic" for a in group),
            "actions_total": tot, "actions_done_share": _share(done, tot),
            "actions_documented_share": _share(doc, tot), "actions_overdue_share": _share(overdue, tot),
            "areas_inspected_last_12m_share": _share(recent, len(group)),
            "dossier_points_available": int(dossier_ok), "status": "derived"})
    return {"notice": NOTICE, "thresholds": {"min_areas": MIN_AREAS, "min_organizations": MIN_ORGS},
            "published": published, "withheld": withheld,
            "method": ("Suma de los ámbitos autorizados de cada municipio: actuaciones del último plan de cada ámbito "
                       "(hechas / documentadas con evidencia / vencidas sin hacer) e inspecciones en los últimos 12 "
                       "meses. Calculado en el momento de la consulta.")}
