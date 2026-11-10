"""M17 · Colaboración (ROADMAP 4.3): comentarios y registro de decisiones con autor y fecha.

Sobre un ámbito, una inspección o una actuación del plan. Las entradas son inmutables (no se editan ni se borran):
una corrección se registra como entrada nueva. Solo la organización propietaria las lee y escribe (T08).
"""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import ActionPlan, AreaOfInterest, Comment, Inspection, PlanAction, Scenario
from ..security import Principal, current_principal
from ..services import audit

router = APIRouter(prefix="/v1", tags=["colaboración"])

EntityType = Literal["area", "inspection", "plan_action"]
WRITE_ROLES = ("gestor", "admin", "tecnico")


def _clean(text: str) -> str:
    """Normaliza saltos de línea y elimina caracteres de control (salvo salto de línea y tabulador)."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return "".join(ch for ch in text if ch in "\n\t" or (ord(ch) >= 0x20 and ord(ch) != 0x7F)).strip()


def resolve_entity(session: Session, p: Principal, entity_type: str, entity_id: str) -> tuple[str, str]:
    """(organization_id, area_id) del elemento, comprobando que pertenece a una organización del usuario (404 si no)."""
    org = area = None
    if entity_type == "area":
        a = session.get(AreaOfInterest, entity_id)
        if a:
            org, area = a.organization_id, a.id
    elif entity_type == "inspection":
        i = session.get(Inspection, entity_id)
        if i:
            org, area = i.organization_id, i.area_id
    elif entity_type == "plan_action":
        row = session.execute(select(ActionPlan.organization_id, Scenario.area_id)
                              .join(PlanAction, PlanAction.plan_id == ActionPlan.id)
                              .join(Scenario, Scenario.id == ActionPlan.scenario_id)
                              .where(PlanAction.id == entity_id)).first()
        if row:
            org, area = row
    if org is None or org not in p.org_ids:
        raise HTTPException(404, "Recurso no encontrado")
    return org, area


def comment_dict(c: Comment) -> dict[str, Any]:
    return {"id": c.id, "entity_type": c.entity_type, "entity_id": c.entity_id, "area_id": c.area_id, "kind": c.kind,
            "body": c.body, "author_name": c.author_name, "created_at": c.created_at.isoformat(),
            "status": "user_reported"}


class CommentIn(BaseModel):
    entity_type: EntityType
    entity_id: str = Field(min_length=1, max_length=36)
    kind: Literal["comment", "decision"] = "comment"
    body: str = Field(min_length=1, max_length=2000)

    @field_validator("body")
    @classmethod
    def _body(cls, v: str) -> str:
        v = _clean(v)
        if not v:
            raise ValueError("El texto no puede estar vacío")
        return v


@router.get("/comments")
def list_comments(entity_type: EntityType, entity_id: str, p: Principal = Depends(current_principal),
                  session: Session = Depends(get_session)) -> list[dict[str, Any]]:
    resolve_entity(session, p, entity_type, entity_id)
    rows = session.scalars(select(Comment).where(Comment.entity_type == entity_type, Comment.entity_id == entity_id,
                                                 Comment.record_status == "active").order_by(Comment.created_at))
    return [comment_dict(c) for c in rows]


@router.post("/comments", status_code=201)
def create_comment(body: CommentIn, p: Principal = Depends(current_principal),
                   session: Session = Depends(get_session)) -> dict[str, Any]:
    org, area = resolve_entity(session, p, body.entity_type, body.entity_id)
    if p.require_org(org).role not in WRITE_ROLES:
        raise HTTPException(403, "Tu rol no puede escribir en esta organización")
    c = Comment(organization_id=org, area_id=area, entity_type=body.entity_type, entity_id=body.entity_id,
                kind=body.kind, body=body.body, author_id=p.user.id,
                author_name=p.user.full_name or p.user.email)
    session.add(c)
    session.flush()
    audit(session, org_id=org, user_id=p.user.id, action=f"{body.kind}_create", entity=body.entity_type,
          entity_id=body.entity_id, detail={"comment_id": c.id})
    session.commit()
    return comment_dict(c)


@router.get("/areas/{area_id}/decisions")
def area_decisions(area_id: str, kind: Literal["decision", "all"] = Query("decision"),
                   p: Principal = Depends(current_principal), session: Session = Depends(get_session)) -> dict[str, Any]:
    """Registro de decisiones del ámbito (de todas sus inspecciones y actuaciones), con autor y fecha."""
    resolve_entity(session, p, "area", area_id)
    stmt = select(Comment).where(Comment.area_id == area_id, Comment.record_status == "active")
    if kind == "decision":
        stmt = stmt.where(Comment.kind == "decision")
    rows = [comment_dict(c) for c in session.scalars(stmt.order_by(Comment.created_at.desc()))]
    return {"area_id": area_id, "count": len(rows), "entries": rows,
            "notice": ("Registro inmutable aportado por la organización: cada entrada conserva autor y fecha; "
                       "las correcciones se añaden como entradas nuevas.")}
