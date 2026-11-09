"""M15 · Expediente de autoprotección (ROADMAP 4.2).

Lista de comprobación de la información que el INFOMA (Decreto 59/2017, DOC-02) exige o recomienda: Anexo 5
(contenido mínimo del plan de autoprotección) y Anexo 6 (obligaciones de las urbanizaciones), cada punto con su cita
literal y página del BOCM. La organización declara el estado de cada punto; las obligaciones del Anexo 6 se enlazan
con las actuaciones del plan de ESCUDO.

ESCUDO MADRID nunca redacta, aprueba, registra ni certifica un plan de autoprotección.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_session
from ..models import ActionPlan, DossierItem, PlanAction, Scenario
from ..security import Principal, current_principal
from ..services import audit
from .private import _get_area

router = APIRouter(prefix="/v1", tags=["expediente"])

STATUSES = ("pending", "in_progress", "available", "not_applicable")
EDIT_ROLES = ("gestor", "admin", "tecnico")


@lru_cache(maxsize=1)
def definition() -> dict[str, Any]:
    return json.loads((settings.data_dir / "reference" / "infoma_dossier.json").read_text(encoding="utf-8"))


def _latest_plan_actions(session: Session, area_id: str) -> dict[str, PlanAction]:
    plan = session.scalar(select(ActionPlan).join(Scenario, Scenario.id == ActionPlan.scenario_id)
                          .where(Scenario.area_id == area_id).order_by(ActionPlan.created_at.desc()))
    return {a.measure_code: a for a in plan.actions} if plan else {}


def build_dossier(session: Session, area_id: str) -> dict[str, Any]:
    d = definition()
    rows = {r.item_code: r for r in session.scalars(select(DossierItem).where(DossierItem.area_id == area_id))}
    actions = _latest_plan_actions(session, area_id)
    items = []
    for it in d["items"]:
        r = rows.get(it["code"])
        linked = [{"measure_code": c, "in_plan": c in actions,
                   "action_status": actions[c].status if c in actions else None,
                   "due_date": actions[c].due_date.isoformat() if c in actions and actions[c].due_date else None}
                  for c in it.get("linked_measures", [])]
        items.append({**it, "status": r.status if r else "pending", "note": r.note if r else "",
                      "updated_at": r.updated_at.isoformat() if r else None, "linked_actions": linked,
                      "data_status": "user_reported" if r else "unavailable"})
    counts = {s: sum(1 for i in items if i["status"] == s) for s in STATUSES}
    return {"area_id": area_id, "source_id": d["source_id"], "reference": d["reference"],
            "review_status": d["review_status"], "notice": d["notice"], "counts": counts, "items": items}


class DossierPatch(BaseModel):
    status: Literal["pending", "in_progress", "available", "not_applicable"]
    note: str = Field("", max_length=2000)


@router.get("/areas/{area_id}/dossier")
def get_dossier(area_id: str, p: Principal = Depends(current_principal),
                session: Session = Depends(get_session)) -> dict[str, Any]:
    area = _get_area(session, p, area_id)
    return build_dossier(session, area.id)


@router.patch("/areas/{area_id}/dossier/{item_code}")
def patch_dossier_item(area_id: str, item_code: str, body: DossierPatch, p: Principal = Depends(current_principal),
                       session: Session = Depends(get_session)) -> dict[str, Any]:
    area = _get_area(session, p, area_id)
    if item_code not in {i["code"] for i in definition()["items"]}:
        raise HTTPException(404, "Punto del expediente desconocido")
    m = p.require_org(area.organization_id)
    if m.role not in EDIT_ROLES:
        raise HTTPException(403, "Tu rol no puede modificar el expediente")
    row = session.scalar(select(DossierItem).where(DossierItem.area_id == area.id, DossierItem.item_code == item_code))
    now = datetime.now(UTC)
    if row is None:
        row = DossierItem(organization_id=area.organization_id, area_id=area.id, item_code=item_code, history=[])
        session.add(row)
    prev = row.status
    row.status, row.note, row.updated_by, row.updated_at = body.status, body.note, p.user.id, now
    row.history = [*(row.history or []), {"at": now.isoformat(), "by": p.user.id, "from": prev, "to": body.status}]
    audit(session, org_id=area.organization_id, user_id=p.user.id, action="dossier_update", entity="area",
          entity_id=area.id, detail={"item": item_code, "from": prev, "to": body.status})
    session.commit()
    return next(i for i in build_dossier(session, area.id)["items"] if i["code"] == item_code)
