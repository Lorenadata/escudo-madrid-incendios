"""Aplicación FastAPI de ESCUDO MADRID."""

from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .db import get_session
from .models import ActionPlan, AreaOfInterest, Inspection, Organization, Scenario
from .routers import private, public

logging.basicConfig(level=logging.INFO, format='{"ts":"%(asctime)s","lvl":"%(levelname)s","logger":"%(name)s","msg":%(message)r}')
log = logging.getLogger("escudo.api")

app = FastAPI(
    title="ESCUDO MADRID API",
    version=settings.version,
    description=(
        "API de planificación preventiva de incendios forestales (DATAMAD 2026). Datos del Portal de Datos Abiertos "
        "de la Comunidad de Madrid, cartografía oficial IDEM y AEMET. No es un sistema de emergencias."
    ),
)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(","), allow_methods=["*"],
                   allow_headers=["*"], expose_headers=["X-Report-SHA256"])


@app.middleware("http")
async def access_log(request: Request, call_next):  # M22 observabilidad: latencia por petición
    t0 = time.perf_counter()
    response = await call_next(request)
    log.info("%s %s %s %.1fms", request.method, request.url.path, response.status_code, (time.perf_counter() - t0) * 1000)
    return response


app.include_router(public.router)
app.include_router(private.router)


def _demo_scenario(session: Session) -> Scenario:
    org = session.scalar(select(Organization).where(Organization.record_status == "synthetic",
                                                    Organization.name.like("%DEMO%")).order_by(Organization.name))
    s = org and session.scalar(select(Scenario).where(Scenario.organization_id == org.id,
                                                      Scenario.record_status == "synthetic")
                               .order_by(Scenario.created_at))
    if not s:
        raise HTTPException(404, "Caso guiado no cargado (ejecute escudo_api.etl_load)")
    return s


@app.get("/v1/demo/guided", tags=["demo"])
def demo_guided(session: Session = Depends(get_session)) -> dict[str, Any]:
    """Flujo C: caso guiado de solo lectura. Todo lo privado es FICTICIO y está etiquetado."""
    s = _demo_scenario(session)
    area = session.get(AreaOfInterest, s.area_id)
    org = session.get(Organization, s.organization_id)
    plan = session.scalar(select(ActionPlan).where(ActionPlan.scenario_id == s.id))
    inspections = session.scalars(select(Inspection).where(Inspection.area_id == area.id)).all()
    return {
        "notice": ("Caso de demostración. Organización, ámbito, inspección, evidencias, costes y presupuesto son "
                   "FICTICIOS. Los indicadores municipales, las capas oficiales y la meteorología proceden de fuentes reales."),
        "organization": {"name": org.name, "record_status": org.record_status},
        "area": private.area_dict(session, area, detail=True),
        "inspections": [private.inspection_dict(i) for i in inspections],
        "measures": public.list_measures(session),
        "scenario": private.scenario_dict(s),
        "plan": private.plan_dict(session, plan) if plan else None,
        "report_url": "/v1/demo/report.pdf",
    }


@app.get("/v1/demo/report.pdf", tags=["demo"])
def demo_report(session: Session = Depends(get_session)) -> Response:
    from escudo_reporting import build_scenario_report

    s = _demo_scenario(session)
    pdf = build_scenario_report(private.report_context(session, s))
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="escudo-demo-ficticio.pdf"'})
