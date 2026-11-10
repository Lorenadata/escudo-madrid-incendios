"""Endpoints privados multi-organización (Flujos A y B). Toda consulta filtra por organization_id."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, is_dataclass
from datetime import date
from typing import Any, Literal

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from pydantic import BaseModel, Field
from shapely.geometry import MultiPolygon, shape
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_session
from ..models import (
    ActionPlan,
    AreaOfInterest,
    AuditEvent,
    EvidenceFile,
    Inspection,
    InspectionItem,
    MeasureCatalog,
    Municipality,
    PlanAction,
    Report,
    Scenario,
    ScenarioOption,
    ScenarioResultRow,
    User,
)
from ..security import Principal, create_token, current_principal, verify_password
from ..services import audit, municipality_profile, official_layers_for, utcnow

router = APIRouter(prefix="/v1")

CHECKLIST = {
    "franja_perimetral": "¿Existe franja perimetral de protección desbrozada y mantenida?",
    "vegetacion_viviendas": "¿Vegetación separada de edificaciones y sin continuidad hacia cubiertas?",
    "restos_vegetales": "¿Ausencia de acumulación de restos vegetales y combustibles?",
    "hidrantes": "¿Hidrantes/puntos de agua señalizados, accesibles y revisados?",
    "accesos": "¿Viales de acceso transitables y sin obstáculos para vehículos de emergencia?",
    "plan_autoproteccion": "¿Dispone de plan de autoprotección/PAIF vigente o en tramitación?",
    "informacion_vecinal": "¿Se ha informado a residentes sobre medidas preventivas oficiales?",
}

# ---------------------------------------------------------------- auth


class LoginIn(BaseModel):
    email: str = Field(min_length=3, max_length=254, pattern=r"^[^@\s]+@[^@\s]+$")
    password: str = Field(min_length=1, max_length=200)


def _user_dict(u: User) -> dict[str, Any]:
    return {"id": u.id, "email": u.email, "full_name": u.full_name, "record_status": u.record_status,
            "memberships": [{"organization_id": m.organization_id, "organization_name": m.organization.name,
                             "organization_status": m.organization.record_status, "organization_kind": m.organization.kind,
                             "municipality_code": m.organization.municipality_code, "role": m.role,
                             "technical_qualification_verified": m.technical_qualification_verified}
                            for m in u.memberships]}


@router.post("/auth/login", tags=["acceso"])
def login(body: LoginIn, session: Session = Depends(get_session)) -> dict[str, Any]:
    u = session.scalar(select(User).where(User.email == body.email.lower()))
    if u is None or not verify_password(body.password, u.password_hash):
        raise HTTPException(401, "Credenciales no válidas")
    audit(session, org_id=None, user_id=u.id, action="login", entity="user", entity_id=u.id)
    session.commit()
    return {"access_token": create_token(u.id), "token_type": "bearer", "user": _user_dict(u)}


@router.get("/me", tags=["acceso"])
def me(p: Principal = Depends(current_principal)) -> dict[str, Any]:
    return _user_dict(p.user)


@router.get("/checklist", tags=["inspecciones"])
def checklist() -> list[dict[str, str]]:
    return [{"code": k, "question": v} for k, v in CHECKLIST.items()]


# ---------------------------------------------------------------- áreas (M05)


class AreaIn(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    municipality_code: str = Field(pattern=r"^28\d{3}$")
    description: str = Field("", max_length=2000)
    geometry: dict | None = None
    organization_id: str | None = None


def _area_geojson(session: Session, a: AreaOfInterest) -> dict:
    """Geometría leída de la columna en BD (nunca el valor en memoria, que puede ser WKT de texto)."""
    return json.loads(session.scalar(select(func.ST_AsGeoJSON(AreaOfInterest.geom, 6)).where(AreaOfInterest.id == a.id)))


def area_dict(session: Session, a: AreaOfInterest, *, detail: bool = False) -> dict[str, Any]:
    d: dict[str, Any] = {"id": a.id, "organization_id": a.organization_id, "name": a.name,
                         "municipality_code": a.municipality_code, "description": a.description,
                         "has_geometry": a.geom is not None, "record_status": a.record_status,
                         "shared_with_municipality": a.shared_with_municipality}
    if a.geom is not None:
        d["geometry"] = _area_geojson(session, a)
    if detail:
        m = session.get(Municipality, a.municipality_code)
        d["municipality_profile"] = municipality_profile(session, m) if m else None
        d["official_layers_scope"] = "municipio"
        d["official_layers_area"] = _area_official_layers(session, a) if a.geom is not None else None
        d["population_notice"] = ("ESCUDO no estima población de áreas: el censo CAM-01 es municipal y no se "
                                  "reparte entre urbanizaciones (PRD §5.1).")
    return d


def _area_official_layers(session: Session, a: AreaOfInterest) -> dict[str, Any]:
    """Reparto ORIENTATIVO de clases oficiales en el área (capa web 200 m). Status derived, nunca official."""
    from ..models import OfficialLayerPolygon

    out: dict[str, Any] = {}
    for layer in ("risk", "hazard", "vulnerability"):
        rows = session.execute(
            select(OfficialLayerPolygon.class_label,
                   func.sum(func.ST_Area(func.ST_Transform(func.ST_Intersection(OfficialLayerPolygon.geom, AreaOfInterest.geom), 25830))))
            .join(AreaOfInterest, func.ST_Intersects(OfficialLayerPolygon.geom, AreaOfInterest.geom))
            .where(OfficialLayerPolygon.layer == layer, AreaOfInterest.id == a.id)
            .group_by(OfficialLayerPolygon.class_label)).all()
        total = sum(r[1] or 0 for r in rows)
        out[layer] = {"status": "derived" if rows else "unavailable",
                      "resolution": "generalización web de 200 m (ADR-0003)",
                      "caveat": ("Reparto orientativo calculado sobre la capa web generalizada a 200 m: sirve para "
                                 "visualizar, no para consultar una parcela. Las clases son literales de la fuente; "
                                 "el reparto exacto a 5 m solo está disponible a escala municipal."),
                      "classes": [{"class_label": lbl, "area_share": round((ar or 0) / total, 4) if total else None}
                                  for lbl, ar in sorted(rows, key=lambda r: -(r[1] or 0))]}
    return out


def _org_for_write(p: Principal, requested: str | None) -> str:
    org = requested or p.default_org_id
    p.require_org(org)
    return org


def _get_area(session: Session, p: Principal, area_id: str) -> AreaOfInterest:
    a = session.get(AreaOfInterest, area_id)
    if a is None or a.organization_id not in p.org_ids:
        raise HTTPException(404, "Recurso no encontrado")
    return a


@router.get("/areas", tags=["ámbitos"])
def list_areas(p: Principal = Depends(current_principal), session: Session = Depends(get_session)) -> list[dict]:
    rows = session.scalars(select(AreaOfInterest).where(AreaOfInterest.organization_id.in_(p.org_ids))
                           .order_by(AreaOfInterest.name)).all()
    return [area_dict(session, a) for a in rows]


@router.post("/areas", tags=["ámbitos"], status_code=201)
def create_area(body: AreaIn, p: Principal = Depends(current_principal), session: Session = Depends(get_session)) -> dict:
    org = _org_for_write(p, body.organization_id)
    if session.get(Municipality, body.municipality_code) is None:
        raise HTTPException(422, "Municipio desconocido")
    geom_wkt = None
    if body.geometry:
        try:
            g = shape(body.geometry)
        except Exception as exc:
            raise HTTPException(422, "Geometría GeoJSON no válida") from exc
        if g.geom_type == "Polygon":
            g = MultiPolygon([g])
        if g.geom_type != "MultiPolygon" or not g.is_valid:
            raise HTTPException(422, "La geometría debe ser un (Multi)Polygon válido en EPSG:4326")
        geom_wkt = f"SRID=4326;{g.wkt}"
    a = AreaOfInterest(organization_id=org, name=body.name, municipality_code=body.municipality_code,
                       description=body.description, geom=geom_wkt)
    session.add(a)
    session.flush()
    audit(session, org_id=org, user_id=p.user.id, action="create", entity="area", entity_id=a.id)
    session.commit()
    return area_dict(session, a)


@router.get("/areas/{area_id}.geojson", tags=["exportación"])
def export_area_geojson(area_id: str, p: Principal = Depends(current_principal),
                        session: Session = Depends(get_session)) -> Response:
    """Export M10 de un ámbito autorizado. Datos privados de la organización: no se expone población."""
    a = _get_area(session, p, area_id)
    feature = {
        "type": "Feature",
        "geometry": _area_geojson(session, a) if a.geom is not None else None,
        "properties": {"id": a.id, "name": a.name, "municipality_code": a.municipality_code,
                       "record_status": a.record_status, "official_layers": _area_official_layers(session, a) if a.geom is not None else None,
                       "notice": "Ámbito registrado por la organización. Las clases oficiales se muestran sin recalcular; no es aprobación administrativa."},
    }
    audit(session, org_id=a.organization_id, user_id=p.user.id, action="export", entity="area", entity_id=a.id)
    session.commit()
    body = json.dumps({"type": "FeatureCollection", "features": [feature]}, ensure_ascii=False)
    return Response(body, media_type="application/geo+json",
                    headers={"Content-Disposition": f'attachment; filename="escudo-ambito-{a.id[:8]}.geojson"',
                             "Cache-Control": "private, no-store"})


@router.get("/areas/{area_id}", tags=["ámbitos"])
def get_area(area_id: str, p: Principal = Depends(current_principal), session: Session = Depends(get_session)) -> dict:
    return area_dict(session, _get_area(session, p, area_id), detail=True)


# ---------------------------------------------------------------- inspecciones (M06)


class InspectionItemIn(BaseModel):
    checklist_code: str
    answer: Literal["si", "no", "parcial", "na"]
    observation: str = Field("", max_length=2000)


class InspectionIn(BaseModel):
    area_id: str
    inspected_on: date
    inspector_name: str = Field(min_length=2, max_length=200)
    items: list[InspectionItemIn] = Field(default_factory=list, max_length=100)
    client_uuid: str | None = Field(None, pattern=r"^[0-9a-fA-F-]{36}$")  # M21: idempotencia sin conexión


def inspection_dict(i: Inspection) -> dict[str, Any]:
    return {"id": i.id, "area_id": i.area_id, "inspected_on": i.inspected_on.isoformat(),
            "inspector_name": i.inspector_name, "review_status": i.review_status, "record_status": i.record_status,
            "items": [{"checklist_code": it.checklist_code, "question": CHECKLIST.get(it.checklist_code, ""),
                       "answer": it.answer, "observation": it.observation} for it in i.items],
            "evidence": [evidence_dict(e) for e in i.evidence]}


def evidence_dict(e: EvidenceFile) -> dict[str, Any]:
    return {"id": e.id, "original_name": e.original_name, "content_type": e.content_type, "bytes": e.bytes,
            "sha256": e.sha256, "uploaded_at": e.uploaded_at.isoformat(), "record_status": e.record_status}


@router.get("/inspections", tags=["inspecciones"])
def list_inspections(area_id: str | None = None, p: Principal = Depends(current_principal),
                     session: Session = Depends(get_session)) -> list[dict]:
    stmt = select(Inspection).where(Inspection.organization_id.in_(p.org_ids))
    if area_id:
        stmt = stmt.where(Inspection.area_id == area_id)
    return [inspection_dict(i) for i in session.scalars(stmt.order_by(Inspection.inspected_on.desc()))]


@router.post("/inspections", tags=["inspecciones"], status_code=201)
def create_inspection(body: InspectionIn, response: Response, p: Principal = Depends(current_principal),
                      session: Session = Depends(get_session)) -> dict:
    area = _get_area(session, p, body.area_id)
    if body.client_uuid:  # reenvío desde el modo sin conexión: devuelve la ya creada, no duplica
        prev = session.scalar(select(Inspection).where(Inspection.organization_id == area.organization_id,
                                                       Inspection.client_uuid == body.client_uuid))
        if prev is not None:
            if prev.area_id != area.id:
                raise HTTPException(409, "Identificador de dispositivo ya usado en otro ámbito")
            response.status_code = 200
            return {**inspection_dict(prev), "replayed": True}
    unknown = [it.checklist_code for it in body.items if it.checklist_code not in CHECKLIST]
    if unknown:
        raise HTTPException(422, f"Códigos de checklist desconocidos: {unknown}")
    i = Inspection(organization_id=area.organization_id, area_id=area.id, inspected_on=body.inspected_on,
                   inspector_name=body.inspector_name, client_uuid=body.client_uuid,
                   items=[InspectionItem(**it.model_dump()) for it in body.items])
    session.add(i)
    session.flush()
    audit(session, org_id=area.organization_id, user_id=p.user.id, action="create", entity="inspection", entity_id=i.id)
    session.commit()
    return inspection_dict(i)


ALLOWED_TYPES = {"image/jpeg": b"\xff\xd8\xff", "image/png": b"\x89PNG", "application/pdf": b"%PDF"}


def _store_evidence(session: Session, p: Principal, org_id: str, file: UploadFile, **links: str) -> EvidenceFile:
    data = file.file.read(settings.max_evidence_bytes + 1)
    if len(data) > settings.max_evidence_bytes:
        raise HTTPException(413, "Archivo demasiado grande (máx. 10 MB)")
    magic = ALLOWED_TYPES.get(file.content_type or "")
    if magic is None or not data.startswith(magic):
        raise HTTPException(415, "Solo se admiten JPEG, PNG o PDF válidos")
    digest = hashlib.sha256(data).hexdigest()
    key = f"{org_id}/{digest}"
    path = settings.escudo_evidence_dir / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    e = EvidenceFile(organization_id=org_id, original_name=(file.filename or "evidencia")[:200],
                     content_type=file.content_type, bytes=len(data), sha256=digest, storage_key=key, **links)
    session.add(e)
    session.flush()
    audit(session, org_id=org_id, user_id=p.user.id, action="upload", entity="evidence", entity_id=e.id,
          detail={"sha256": digest, **links})
    return e


@router.post("/inspections/{inspection_id}/evidence", tags=["inspecciones"], status_code=201)
def upload_inspection_evidence(inspection_id: str, file: UploadFile = File(...),
                               p: Principal = Depends(current_principal), session: Session = Depends(get_session)) -> dict:
    i = session.get(Inspection, inspection_id)
    if i is None or i.organization_id not in p.org_ids:
        raise HTTPException(404, "Recurso no encontrado")
    data = file.file.read(settings.max_evidence_bytes + 1)
    file.file.seek(0)
    dup = session.scalar(select(EvidenceFile).where(EvidenceFile.inspection_id == i.id,
                                                    EvidenceFile.sha256 == hashlib.sha256(data).hexdigest()))
    if dup is not None:  # misma foto reenviada (sincronización sin conexión): no se duplica
        return {**evidence_dict(dup), "replayed": True}
    e = _store_evidence(session, p, i.organization_id, file, inspection_id=i.id)
    session.commit()
    return evidence_dict(e)


@router.get("/evidence/{evidence_id}", tags=["inspecciones"])
def download_evidence(evidence_id: str, p: Principal = Depends(current_principal),
                      session: Session = Depends(get_session)) -> Response:
    e = session.get(EvidenceFile, evidence_id)
    if e is None or e.organization_id not in p.org_ids:
        raise HTTPException(404, "Recurso no encontrado")
    path = settings.escudo_evidence_dir / e.storage_key
    if not path.exists():
        raise HTTPException(410, "Archivo no disponible en almacenamiento")
    return Response(path.read_bytes(), media_type=e.content_type,
                    headers={"Content-Disposition": f'attachment; filename="{e.id}"', "Cache-Control": "private, no-store"})


class ReviewIn(BaseModel):
    verdict: Literal["util", "inviable", "redundante", "requiere_revision"]
    note: str = Field("", max_length=4000)


@router.post("/inspections/{inspection_id}/reviews", tags=["inspecciones"], status_code=201)
def review_inspection(inspection_id: str, body: ReviewIn, p: Principal = Depends(current_principal),
                      session: Session = Depends(get_session)) -> dict:
    """Revisión técnica (PRD §2.4): solo rol «tecnico» con cualificación VERIFICADA. No es aprobación administrativa."""
    from ..models import ProfessionalReview

    i = session.get(Inspection, inspection_id)
    if i is None or i.organization_id not in p.org_ids:
        raise HTTPException(404, "Recurso no encontrado")
    m = p.require_org(i.organization_id)
    if m.role != "tecnico" or not m.technical_qualification_verified:
        raise HTTPException(403, "Solo personal técnico con cualificación verificada puede registrar la revisión")
    r = ProfessionalReview(organization_id=i.organization_id, inspection_id=i.id, reviewer_user_id=p.user.id,
                           verdict=body.verdict, note=body.note)
    session.add(r)
    i.review_status = "reviewed"
    audit(session, org_id=i.organization_id, user_id=p.user.id, action="review", entity="inspection", entity_id=i.id,
          detail={"verdict": body.verdict})
    session.commit()
    return {"inspection_id": i.id, "verdict": r.verdict, "review_status": i.review_status,
            "notice": "La revisión técnica no equivale a aprobación administrativa ni a informe favorable de PAIF."}


# ---------------------------------------------------------------- escenarios (M08)


class OptionIn(BaseModel):
    measure_code: str
    quantity: float = Field(gt=0, le=1e7)
    unit_cost_eur: float = Field(ge=0, le=1e8)
    technical_priority: int = Field(ge=1, le=5)
    coverage_weight: float = Field(1.0, gt=0, le=100)
    cost_status: Literal["reference", "user_quote", "scenario"] = "scenario"
    mandatory: bool = False
    manual_rank: int | None = Field(None, ge=1)


class ScenarioIn(BaseModel):
    area_id: str
    name: str = Field(min_length=2, max_length=200)
    budget_eur: float = Field(ge=0, le=1e9)
    is_demo_budget: bool = True
    options: list[OptionIn] = Field(min_length=1, max_length=200)


def scenario_dict(s: Scenario) -> dict[str, Any]:
    return {"id": s.id, "area_id": s.area_id, "name": s.name, "budget_eur": float(s.budget_eur),
            "is_demo_budget": s.is_demo_budget, "record_status": s.record_status,
            "options": [{"option_id": o.id, "measure_code": o.measure_code, "quantity": o.quantity,
                         "unit_cost_eur": float(o.unit_cost_eur), "total_cost_eur": round(o.quantity * float(o.unit_cost_eur), 2),
                         "technical_priority": o.technical_priority, "coverage_weight": o.coverage_weight,
                         "cost_status": o.cost_status, "mandatory": o.mandatory, "manual_rank": o.manual_rank}
                        for o in s.options],
            "latest_result": s.results[-1].result if s.results else None}


def _get_scenario(session: Session, p: Principal, scenario_id: str) -> Scenario:
    s = session.get(Scenario, scenario_id)
    if s is None or s.organization_id not in p.org_ids:
        raise HTTPException(404, "Recurso no encontrado")
    return s


@router.get("/scenarios", tags=["escenarios"])
def list_scenarios(area_id: str | None = None, p: Principal = Depends(current_principal),
                   session: Session = Depends(get_session)) -> list[dict]:
    stmt = select(Scenario).where(Scenario.organization_id.in_(p.org_ids))
    if area_id:
        stmt = stmt.where(Scenario.area_id == area_id)
    return [scenario_dict(s) for s in session.scalars(stmt.order_by(Scenario.created_at.desc()))]


@router.post("/scenarios", tags=["escenarios"], status_code=201)
def create_scenario(body: ScenarioIn, p: Principal = Depends(current_principal),
                    session: Session = Depends(get_session)) -> dict:
    area = _get_area(session, p, body.area_id)
    codes = {o.measure_code for o in body.options}
    known = set(session.scalars(select(MeasureCatalog.code).where(MeasureCatalog.code.in_(codes))))
    if codes - known:
        raise HTTPException(422, f"Medidas desconocidas: {sorted(codes - known)}")
    s = Scenario(organization_id=area.organization_id, area_id=area.id, name=body.name, budget_eur=body.budget_eur,
                 is_demo_budget=body.is_demo_budget,
                 options=[ScenarioOption(position=i, **o.model_dump()) for i, o in enumerate(body.options)])
    session.add(s)
    session.flush()
    audit(session, org_id=area.organization_id, user_id=p.user.id, action="create", entity="scenario", entity_id=s.id,
          detail={"budget_eur": body.budget_eur, "is_demo_budget": body.is_demo_budget})
    session.commit()
    return scenario_dict(s)


@router.get("/scenarios/{scenario_id}", tags=["escenarios"])
def get_scenario(scenario_id: str, p: Principal = Depends(current_principal),
                 session: Session = Depends(get_session)) -> dict:
    return scenario_dict(_get_scenario(session, p, scenario_id))


def _to_plain(obj: Any) -> Any:
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    if is_dataclass(obj):
        return json.loads(json.dumps(asdict(obj), default=str))
    return obj


def solve_scenario(session: Session, s: Scenario) -> dict[str, Any]:
    from escudo_optimizer import OptionInput, SolveRequest, solve

    catalog = {m.code: m for m in session.scalars(select(MeasureCatalog))}
    by_code: dict[str, list[str]] = {}
    for o in s.options:
        by_code.setdefault(o.measure_code, []).append(o.id)
    inputs = []
    for o in s.options:
        m = catalog[o.measure_code]
        requires = [oid for code in (m.prerequisites or []) for oid in by_code.get(code, [])]
        excludes = [oid for code in (m.excludes or []) for oid in by_code.get(code, [])]
        inputs.append(OptionInput(option_id=o.id, measure_code=o.measure_code, quantity=o.quantity,
                                  unit_cost_eur=float(o.unit_cost_eur), technical_priority=o.technical_priority,
                                  coverage_weight=o.coverage_weight, mandatory=o.mandatory, eligible=True,
                                  requires=requires, excludes=excludes, manual_rank=o.manual_rank))
    req = SolveRequest(budget_eur=float(s.budget_eur), options=inputs, is_demo_budget=s.is_demo_budget)
    result = _to_plain(solve(req))
    input_hash = hashlib.sha256(json.dumps(_to_plain(req), sort_keys=True, default=str).encode()).hexdigest()
    result["input_hash"] = input_hash
    session.add(ScenarioResultRow(scenario_id=s.id, input_hash=input_hash, result=result))
    return result


@router.post("/scenarios/{scenario_id}/solve", tags=["escenarios"])
def solve_endpoint(scenario_id: str, p: Principal = Depends(current_principal),
                   session: Session = Depends(get_session)) -> dict:
    s = _get_scenario(session, p, scenario_id)
    result = solve_scenario(session, s)
    audit(session, org_id=s.organization_id, user_id=p.user.id, action="solve", entity="scenario", entity_id=s.id,
          detail={"input_hash": result["input_hash"], "status": result.get("status")})
    session.commit()
    return result


# ---------------------------------------------------------------- planes (M09)


class PlanIn(BaseModel):
    scenario_id: str
    strategy: Literal["optimized", "manual", "cheapest_first"] = "optimized"


class ActionPatch(BaseModel):
    status: Literal["pending", "in_progress", "done", "blocked"] | None = None
    responsible: str | None = Field(None, max_length=200)
    due_date: date | None = None
    actual_cost_eur: float | None = Field(None, ge=0, le=1e9)
    note: str | None = Field(None, max_length=2000)


def action_dict(session: Session, a: PlanAction) -> dict[str, Any]:
    n = session.scalar(select(func.count()).select_from(EvidenceFile).where(EvidenceFile.plan_action_id == a.id)) or 0
    return {"id": a.id, "measure_code": a.measure_code, "status": a.status, "responsible": a.responsible,
            "due_date": a.due_date.isoformat() if a.due_date else None, "planned_cost_eur": float(a.planned_cost_eur),
            "actual_cost_eur": float(a.actual_cost_eur) if a.actual_cost_eur is not None else None,
            "evidence_count": n, "history": a.history}


def plan_dict(session: Session, plan: ActionPlan) -> dict[str, Any]:
    return {"id": plan.id, "scenario_id": plan.scenario_id, "created_at": plan.created_at.isoformat(),
            "record_status": plan.record_status, "actions": [action_dict(session, a) for a in plan.actions]}


def create_plan_from(session: Session, s: Scenario, strategy: str, user_id: str | None) -> ActionPlan:
    if not s.results:
        raise HTTPException(409, "Resuelva el escenario antes de crear el plan")
    res = s.results[-1].result
    strat = next((x for x in res.get("strategies", []) if x.get("strategy") == strategy), None)
    if strat is None:
        raise HTTPException(409, f"Estrategia {strategy} no disponible en el resultado")
    selected_ids = strat.get("selected_option_ids")
    opts = [o for o in s.options if (o.id in selected_ids if selected_ids is not None else o.measure_code in strat["selected"])]
    plan = ActionPlan(organization_id=s.organization_id, scenario_id=s.id, record_status=s.record_status)
    session.add(plan)
    session.flush()
    for i, o in enumerate(opts):
        session.add(PlanAction(plan_id=plan.id, position=i, measure_code=o.measure_code,
                               planned_cost_eur=round(o.quantity * float(o.unit_cost_eur), 2),
                               history=[{"at": utcnow().isoformat(), "by": user_id, "change": "created",
                                         "strategy": strategy}]))
    session.flush()
    session.refresh(plan)
    return plan


@router.post("/action-plans", tags=["planes"], status_code=201)
def create_plan(body: PlanIn, p: Principal = Depends(current_principal), session: Session = Depends(get_session)) -> dict:
    s = _get_scenario(session, p, body.scenario_id)
    plan = create_plan_from(session, s, body.strategy, p.user.id)
    audit(session, org_id=s.organization_id, user_id=p.user.id, action="create", entity="action_plan", entity_id=plan.id)
    session.commit()
    return plan_dict(session, plan)


def _get_plan(session: Session, p: Principal, plan_id: str) -> ActionPlan:
    plan = session.get(ActionPlan, plan_id)
    if plan is None or plan.organization_id not in p.org_ids:
        raise HTTPException(404, "Recurso no encontrado")
    return plan


@router.get("/action-plans", tags=["planes"])
def list_plans(p: Principal = Depends(current_principal), session: Session = Depends(get_session)) -> list[dict]:
    return [plan_dict(session, x) for x in session.scalars(
        select(ActionPlan).where(ActionPlan.organization_id.in_(p.org_ids)).order_by(ActionPlan.created_at.desc()))]


@router.get("/action-plans/{plan_id}", tags=["planes"])
def get_plan(plan_id: str, p: Principal = Depends(current_principal), session: Session = Depends(get_session)) -> dict:
    return plan_dict(session, _get_plan(session, p, plan_id))


@router.patch("/action-plans/{plan_id}/actions/{action_id}", tags=["planes"])
def patch_action(plan_id: str, action_id: str, body: ActionPatch, p: Principal = Depends(current_principal),
                 session: Session = Depends(get_session)) -> dict:
    plan = _get_plan(session, p, plan_id)
    a = next((x for x in plan.actions if x.id == action_id), None)
    if a is None:
        raise HTTPException(404, "Acción no encontrada")
    changes = body.model_dump(exclude_unset=True)
    note = changes.pop("note", None)
    before = {k: getattr(a, k) for k in changes}
    for k, v in changes.items():
        setattr(a, k, v)
    a.history = [*a.history, {"at": utcnow().isoformat(), "by": p.user.id, "change": "update",
                              "before": json.loads(json.dumps(before, default=str)),
                              "after": json.loads(json.dumps(changes, default=str)), "note": note}]
    audit(session, org_id=plan.organization_id, user_id=p.user.id, action="update", entity="plan_action",
          entity_id=a.id, detail=json.loads(json.dumps(changes, default=str)))
    session.commit()
    return action_dict(session, a)


@router.post("/action-plans/{plan_id}/actions/{action_id}/evidence", tags=["planes"], status_code=201)
def upload_action_evidence(plan_id: str, action_id: str, file: UploadFile = File(...),
                           p: Principal = Depends(current_principal), session: Session = Depends(get_session)) -> dict:
    plan = _get_plan(session, p, plan_id)
    if not any(x.id == action_id for x in plan.actions):
        raise HTTPException(404, "Acción no encontrada")
    e = _store_evidence(session, p, plan.organization_id, file, plan_action_id=action_id)
    session.commit()
    return evidence_dict(e)


# ---------------------------------------------------------------- informes (M10), impacto (M12), auditoría


def report_context(session: Session, s: Scenario) -> dict[str, Any]:
    from ..models import DataSource
    from .public import _source_dict, measure_dict

    area = session.get(AreaOfInterest, s.area_id)
    muni = session.get(Municipality, area.municipality_code)
    catalog = {m.code: measure_dict(m) for m in session.scalars(select(MeasureCatalog))}
    plan = session.scalar(select(ActionPlan).where(ActionPlan.scenario_id == s.id).order_by(ActionPlan.created_at.desc()))
    return {
        "generated_at": utcnow().isoformat(timespec="seconds"),
        "scenario": scenario_dict(s),
        "area": {"name": area.name, "record_status": area.record_status, "municipality_code": area.municipality_code},
        "municipality": municipality_profile(session, muni, with_weather=False) if muni else None,
        "official_layers": official_layers_for(session, area.municipality_code),
        "catalog": catalog,
        "plan": plan_dict(session, plan) if plan else None,
        "sources": [_source_dict(x) for x in session.scalars(select(DataSource).order_by(DataSource.source_id))],
        "inspections": [inspection_dict(i) for i in session.scalars(
            select(Inspection).where(Inspection.area_id == area.id).order_by(Inspection.inspected_on.desc()))],
    }


@router.get("/reports/scenario/{scenario_id}.pdf", tags=["informes"])
def scenario_report(scenario_id: str, p: Principal = Depends(current_principal),
                    session: Session = Depends(get_session)) -> Response:
    from escudo_reporting import build_scenario_report

    s = _get_scenario(session, p, scenario_id)
    if not s.results:
        raise HTTPException(409, "Resuelva el escenario antes de generar el informe")
    pdf = build_scenario_report(report_context(session, s))
    digest = hashlib.sha256(pdf).hexdigest()
    session.add(Report(organization_id=s.organization_id, scenario_id=s.id, sha256=digest, bytes=len(pdf)))
    audit(session, org_id=s.organization_id, user_id=p.user.id, action="report", entity="scenario", entity_id=s.id,
          detail={"sha256": digest})
    session.commit()
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="escudo-escenario-{s.id[:8]}.pdf"',
                             "X-Report-SHA256": digest})


def impact_kpis(session: Session, org_ids: set[str]) -> dict[str, Any]:
    """KPIs operativos permitidos (PRD §5.5). Nunca impacto físico."""
    actions = session.scalars(select(PlanAction).join(ActionPlan).where(ActionPlan.organization_id.in_(org_ids))).all()
    n = len(actions)
    done = sum(1 for a in actions if a.status == "done")
    with_ev = sum(1 for a in actions if session.scalar(
        select(func.count()).select_from(EvidenceFile).where(EvidenceFile.plan_action_id == a.id)))
    overdue = sum(1 for a in actions if a.due_date and a.due_date < date.today() and a.status != "done")
    insp = session.scalars(select(Inspection).where(Inspection.organization_id.in_(org_ids))).all()
    scen = session.scalars(select(Scenario).where(Scenario.organization_id.in_(org_ids))).all()
    solved = [s for s in scen if s.results]
    reproducible = sum(1 for s in solved if len({r.input_hash for r in s.results}) >= 1 and s.results[-1].result.get("deterministic"))
    planned = sum(float(a.planned_cost_eur) for a in actions)
    actual = sum(float(a.actual_cost_eur) for a in actions if a.actual_cost_eur is not None)

    def k(kid: str, label: str, value: Any, unit: str) -> dict[str, Any]:
        return {"indicator_id": kid, "label": label, "value": value, "unit": unit, "status": "derived",
                "spatial_scope": "organización", "source_id": "ESCUDO",
                "caveat": "KPI operativo de gestión; no mide reducción de riesgo ni incendios evitados."}

    return {
        "kpis": [
            k("actions_total", "Actuaciones planificadas", n, "actuaciones"),
            k("actions_done_share", "Actuaciones completadas", round(done / n, 4) if n else None, "proporción"),
            k("actions_documented_share", "Actuaciones con evidencia", round(with_ev / n, 4) if n else None, "proporción"),
            k("actions_overdue", "Actuaciones vencidas", overdue, "actuaciones"),
            k("inspections_total", "Inspecciones registradas", len(insp), "inspecciones"),
            k("inspections_pending_review", "Inspecciones pendientes de revisión técnica",
              sum(1 for i in insp if i.review_status == "pending_technical_review"), "inspecciones"),
            k("scenarios_reproducible_share", "Escenarios resueltos de forma determinista",
              round(reproducible / len(solved), 4) if solved else None, "proporción"),
            k("planned_cost_eur", "Coste planificado", round(planned, 2), "€"),
            k("actual_cost_eur", "Coste real registrado", round(actual, 2), "€"),
        ],
        "notice": "Indicadores de gestión preventiva. ESCUDO no estima incendios evitados ni reducción de riesgo.",
    }


@router.get("/impact", tags=["impacto"])
def impact(p: Principal = Depends(current_principal), session: Session = Depends(get_session)) -> dict:
    return impact_kpis(session, p.org_ids)


@router.get("/audit", tags=["auditoría"])
def audit_log(entity: str | None = None, p: Principal = Depends(current_principal),
              session: Session = Depends(get_session)) -> list[dict]:
    stmt = select(AuditEvent).where(AuditEvent.organization_id.in_(p.org_ids))
    if entity:
        stmt = stmt.where(AuditEvent.entity == entity)
    return [{"at": e.at.isoformat(), "user_id": e.user_id, "action": e.action, "entity": e.entity,
             "entity_id": e.entity_id, "detail": e.detail}
            for e in session.scalars(stmt.order_by(AuditEvent.at.desc()).limit(200))]
