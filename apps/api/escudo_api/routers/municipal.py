"""Flujo B (PRD §3.2): responsable municipal.

Un ayuntamiento ve SOLO los ámbitos de su término municipal cuya organización propietaria ha autorizado
expresamente compartirlos (`shared_with_municipality`). Acceso de solo lectura (expediente). Ninguna población
de ámbito: los indicadores demográficos siguen siendo municipales.
"""

from __future__ import annotations

import hashlib
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import (
    ActionPlan,
    AreaOfInterest,
    EvidenceFile,
    Inspection,
    Municipality,
    Organization,
    Report,
    Scenario,
)
from ..security import Principal, current_principal
from ..services import audit, municipality_summary, official_layers_for, sources_health
from . import private

router = APIRouter(prefix="/v1", tags=["municipal"])

NOTICE = ("Vista municipal de solo lectura. Incluye únicamente los ámbitos cuya organización ha autorizado "
          "compartirlos con el ayuntamiento. No es un expediente administrativo oficial ni aprueba PAIF.")


def _municipal_scope(p: Principal) -> tuple[str, str]:
    """(organization_id, municipality_code) de la pertenencia municipal del usuario; 403 si no la tiene."""
    for m in p.memberships:
        org = m.organization
        if m.role == "municipal" and org.kind == "municipio" and org.municipality_code:
            return org.id, org.municipality_code
    raise HTTPException(403, "Requiere rol de responsable municipal en una organización de tipo municipio")


def _shared_areas(session: Session, ine: str) -> list[AreaOfInterest]:
    return list(session.scalars(
        select(AreaOfInterest).where(AreaOfInterest.municipality_code == ine,
                                     AreaOfInterest.shared_with_municipality.is_(True))
        .order_by(AreaOfInterest.name)))


def _area_status(session: Session, a: AreaOfInterest) -> dict[str, Any]:
    org = session.get(Organization, a.organization_id)
    insp = session.scalars(select(Inspection).where(Inspection.area_id == a.id)).all()
    scen = session.scalar(select(Scenario).where(Scenario.area_id == a.id).order_by(Scenario.created_at.desc()))
    plan = scen and session.scalar(select(ActionPlan).where(ActionPlan.scenario_id == scen.id)
                                   .order_by(ActionPlan.created_at.desc()))
    actions = list(plan.actions) if plan else []
    today = date.today()
    documented = sum(1 for x in actions if session.scalar(
        select(func.count()).select_from(EvidenceFile).where(EvidenceFile.plan_action_id == x.id)))
    optimized = None
    if scen and scen.results:
        optimized = next((s for s in scen.results[-1].result.get("strategies", []) if s.get("strategy") == "optimized"), None)
    planned = sum(float(x.planned_cost_eur) for x in actions)
    return {
        "area_id": a.id, "name": a.name, "organization": org.name, "record_status": a.record_status,
        "inspections_total": len(insp),
        "inspections_pending_review": sum(1 for i in insp if i.review_status == "pending_technical_review"),
        "last_inspection_on": max((i.inspected_on for i in insp), default=None),
        "scenario": None if not scen else {
            "id": scen.id, "name": scen.name, "budget_eur": float(scen.budget_eur), "is_demo_budget": scen.is_demo_budget,
            "optimized_priority_coverage": optimized and optimized.get("priority_coverage_share"),
            "optimized_cost_eur": optimized and optimized.get("total_cost_eur"),
        },
        "actions_total": len(actions),
        "actions_done": sum(1 for x in actions if x.status == "done"),
        "actions_overdue": sum(1 for x in actions if x.due_date and x.due_date < today and x.status != "done"),
        "actions_documented": documented,
        "planned_cost_eur": round(planned, 2),
        "actual_cost_eur": round(sum(float(x.actual_cost_eur) for x in actions if x.actual_cost_eur is not None), 2),
        "budget_coverage_share": (round(planned / float(scen.budget_eur), 4)
                                  if scen and float(scen.budget_eur) > 0 else None),
    }


@router.get("/municipal/overview")
def overview(p: Principal = Depends(current_principal), session: Session = Depends(get_session)) -> dict[str, Any]:
    org_id, ine = _municipal_scope(p)
    m = session.get(Municipality, ine)
    if m is None:
        raise HTTPException(404, "Municipio no encontrado")
    areas = [_area_status(session, a) for a in _shared_areas(session, ine)]
    ok, total = sources_health(session)

    def tot(k: str) -> float:
        return sum(a[k] or 0 for a in areas)

    audit(session, org_id=org_id, user_id=p.user.id, action="view", entity="municipal_overview", entity_id=ine)
    session.commit()
    return {
        "notice": NOTICE,
        "municipality": municipality_summary(m),
        "official_fire": official_layers_for(session, ine),
        "sources": {"ok": ok, "total": total},
        "areas": areas,
        "totals": {
            "areas_shared": len(areas),
            "inspections_pending_review": int(tot("inspections_pending_review")),
            "actions_total": int(tot("actions_total")),
            "actions_done": int(tot("actions_done")),
            "actions_overdue": int(tot("actions_overdue")),
            "actions_documented": int(tot("actions_documented")),
            "planned_cost_eur": round(tot("planned_cost_eur"), 2),
            "actual_cost_eur": round(tot("actual_cost_eur"), 2),
        },
        "kpi_caveat": "Indicadores de gestión de los ámbitos compartidos; no miden reducción de riesgo.",
    }


def _shared_area_or_404(session: Session, p: Principal, area_id: str) -> tuple[str, AreaOfInterest]:
    org_id, ine = _municipal_scope(p)
    a = session.get(AreaOfInterest, area_id)
    if a is None or a.municipality_code != ine or not a.shared_with_municipality:
        raise HTTPException(404, "Recurso no encontrado")
    return org_id, a


@router.get("/municipal/areas/{area_id}")
def area_file(area_id: str, p: Principal = Depends(current_principal),
              session: Session = Depends(get_session)) -> dict[str, Any]:
    """Expediente de solo lectura de un ámbito compartido."""
    org_id, a = _shared_area_or_404(session, p, area_id)
    scen = session.scalar(select(Scenario).where(Scenario.area_id == a.id).order_by(Scenario.created_at.desc()))
    plan = scen and session.scalar(select(ActionPlan).where(ActionPlan.scenario_id == scen.id)
                                   .order_by(ActionPlan.created_at.desc()))
    audit(session, org_id=org_id, user_id=p.user.id, action="view", entity="municipal_area", entity_id=a.id)
    session.commit()
    return {
        "notice": NOTICE,
        "area": private.area_dict(session, a, detail=False),
        "status": _area_status(session, a),
        "inspections": [private.inspection_dict(i) for i in session.scalars(
            select(Inspection).where(Inspection.area_id == a.id).order_by(Inspection.inspected_on.desc()))],
        "scenario": private.scenario_dict(scen) if scen else None,
        "plan": private.plan_dict(session, plan) if plan else None,
    }


@router.get("/municipal/areas/{area_id}/report.pdf")
def area_report(area_id: str, p: Principal = Depends(current_principal),
                session: Session = Depends(get_session)) -> Response:
    from escudo_reporting import build_scenario_report

    org_id, a = _shared_area_or_404(session, p, area_id)
    scen = session.scalar(select(Scenario).where(Scenario.area_id == a.id).order_by(Scenario.created_at.desc()))
    if scen is None or not scen.results:
        raise HTTPException(409, "El ámbito no tiene un escenario resuelto")
    pdf = build_scenario_report(private.report_context(session, scen))
    digest = hashlib.sha256(pdf).hexdigest()
    session.add(Report(organization_id=org_id, scenario_id=scen.id, sha256=digest, bytes=len(pdf)))
    audit(session, org_id=org_id, user_id=p.user.id, action="report", entity="municipal_area", entity_id=a.id,
          detail={"sha256": digest})
    session.commit()
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="escudo-expediente-{a.id[:8]}.pdf"',
                             "X-Report-SHA256": digest})


class ShareIn(BaseModel):
    shared_with_municipality: bool


@router.patch("/areas/{area_id}/sharing", tags=["ámbitos"])
def set_sharing(area_id: str, body: ShareIn, p: Principal = Depends(current_principal),
                session: Session = Depends(get_session)) -> dict[str, Any]:
    """La organización propietaria autoriza (o revoca) que el ayuntamiento del término consulte el ámbito."""
    a = session.get(AreaOfInterest, area_id)
    if a is None or a.organization_id not in p.org_ids:
        raise HTTPException(404, "Recurso no encontrado")
    m = p.require_org(a.organization_id)
    if m.role not in ("gestor", "admin"):
        raise HTTPException(403, "Solo la gestión de la organización puede autorizar compartir el ámbito")
    a.shared_with_municipality = body.shared_with_municipality
    audit(session, org_id=a.organization_id, user_id=p.user.id, action="sharing", entity="area", entity_id=a.id,
          detail={"shared_with_municipality": body.shared_with_municipality})
    session.commit()
    return {"area_id": a.id, "shared_with_municipality": a.shared_with_municipality}

