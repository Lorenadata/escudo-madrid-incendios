"""M16 · Calendario preventivo (ROADMAP 4.1).

Reúne, para las organizaciones del usuario: vencimientos de actuaciones del plan (dato aportado por la organización),
revisión anual sugerida de cada inspección (recordatorio derivado, no obligación legal) y las épocas de peligro
oficiales de la Comunidad de Madrid (DOC-01, Plan Anual 2026, pág. 18, conforme al Decreto INFOMA).

Son recordatorios de planificación NO críticos: no son alertas, avisos de riesgo ni instrucciones operativas.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import ActionPlan, AreaOfInterest, Inspection, MeasureCatalog, PlanAction, Scenario
from ..security import Principal, current_principal

router = APIRouter(prefix="/v1", tags=["calendario"])

NOTICE = ("Recordatorios de planificación, no críticos. No son alertas ni avisos de riesgo: para el peligro de "
          "incendio del día consulte AEMET y ASEM 112. La revisión anual de inspecciones es una sugerencia de "
          "ESCUDO, no una obligación legal.")
DANGER_SOURCE = "DOC-01 · Plan Anual 2026, pág. 18 (épocas de peligro reguladas en el Decreto INFOMA)"
# (mes, día) inicio y fin, ambos incluidos — literal del documento oficial
DANGER_PERIODS = (
    ("medio", (5, 16), (6, 14)),
    ("alto", (6, 15), (9, 30)),
    ("medio", (10, 1), (10, 31)),
    ("bajo", (11, 1), (12, 31)),
    ("bajo", (1, 1), (5, 15)),
)
STATUS_LABEL = {"pending": "pendiente", "in_progress": "en curso", "done": "hecha", "blocked": "bloqueada"}


def danger_periods(year: int) -> list[dict[str, Any]]:
    out = []
    for level, (m1, d1), (m2, d2) in DANGER_PERIODS:
        out.append({"id": f"danger-{year}-{m1:02d}{d1:02d}", "kind": "danger_period", "level": level,
                    "start": date(year, m1, d1).isoformat(), "end": date(year, m2, d2).isoformat(),
                    "title": f"Época de peligro {level} de incendios forestales", "status": "official",
                    "source": DANGER_SOURCE, "area_name": None, "overdue": False,
                    "detail": "Periodo oficial con medidas preventivas del Anexo 2 del Decreto INFOMA."})
    return out


def build_events(session: Session, p: Principal, start: date, end: date, today: date | None = None) -> list[dict]:
    today = today or date.today()
    orgs = p.org_ids
    names = dict(session.execute(select(MeasureCatalog.code, MeasureCatalog.name)).all())
    events: list[dict[str, Any]] = []

    rows = session.execute(
        select(PlanAction, AreaOfInterest.name)
        .join(ActionPlan, ActionPlan.id == PlanAction.plan_id)
        .join(Scenario, Scenario.id == ActionPlan.scenario_id)
        .join(AreaOfInterest, AreaOfInterest.id == Scenario.area_id)
        .where(ActionPlan.organization_id.in_(orgs), PlanAction.due_date.is_not(None),
               PlanAction.due_date >= start, PlanAction.due_date <= end)).all()
    for a, area_name in rows:
        overdue = a.due_date < today and a.status != "done"
        events.append({
            "id": f"action-{a.id}", "kind": "action_due", "start": a.due_date.isoformat(), "end": a.due_date.isoformat(),
            "title": f"Vence: {names.get(a.measure_code, a.measure_code)}", "area_name": area_name,
            "status": "user_reported", "action_status": a.status, "overdue": overdue,
            "detail": (f"Actuación {a.measure_code} · estado {STATUS_LABEL.get(a.status, a.status)}"
                       + (f" · responsable {a.responsible}" if a.responsible else "")),
            "source": "Plan de actuaciones de la organización"})

    last: dict[str, tuple[date, str]] = {}
    for insp, area_name in session.execute(
            select(Inspection, AreaOfInterest.name).join(AreaOfInterest, AreaOfInterest.id == Inspection.area_id)
            .where(Inspection.organization_id.in_(orgs))).all():
        if insp.area_id not in last or insp.inspected_on > last[insp.area_id][0]:
            last[insp.area_id] = (insp.inspected_on, area_name)
    for area_id, (when, area_name) in last.items():
        due = when + timedelta(days=365)
        if start <= due <= end:
            events.append({
                "id": f"review-{area_id}-{due.isoformat()}", "kind": "inspection_review", "start": due.isoformat(),
                "end": due.isoformat(), "title": "Revisión anual sugerida de la inspección", "area_name": area_name,
                "status": "derived", "overdue": due < today,
                "detail": f"Última inspección registrada: {when.isoformat()} (+365 días). Sugerencia, no obligación legal.",
                "source": "ESCUDO (derivado de la fecha de la última inspección)"})

    for y in range(start.year, end.year + 1):
        for ev in danger_periods(y):
            if date.fromisoformat(ev["end"]) >= start and date.fromisoformat(ev["start"]) <= end:
                events.append(ev)
    events.sort(key=lambda e: (e["start"], e["kind"] != "danger_period", e["title"]))
    return events


def _range(from_: date | None, to: date | None) -> tuple[date, date]:
    start = from_ or (date.today() - timedelta(days=30))
    end = to or (start + timedelta(days=395))
    if end < start or (end - start).days > 3 * 366:
        raise HTTPException(422, "Rango de fechas no válido (máximo 3 años)")
    return start, end


@router.get("/calendar")
def calendar(from_: date | None = Query(None, alias="from"), to: date | None = None,
             p: Principal = Depends(current_principal), session: Session = Depends(get_session)) -> dict[str, Any]:
    start, end = _range(from_, to)
    events = build_events(session, p, start, end)
    return {"from": start.isoformat(), "to": end.isoformat(), "notice": NOTICE, "events": events,
            "counts": {k: sum(1 for e in events if e["kind"] == k) for k in ("action_due", "inspection_review",
                                                                                 "danger_period")},
            "overdue": sum(1 for e in events if e["overdue"])}


def _ics_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _fold(line: str) -> str:
    """Plegado RFC 5545: líneas de ≤75 octetos, continuación con un espacio."""
    out, cur = [], ""
    for ch in line:
        if len((cur + ch).encode("utf-8")) > 75:
            out.append(cur)
            cur = " " + ch
        else:
            cur += ch
    out.append(cur)
    return "\r\n".join(out)


def to_ics(events: list[dict], now: datetime | None = None) -> str:
    stamp = (now or datetime.now(UTC)).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//ESCUDO MADRID//Calendario preventivo//ES", "CALSCALE:GREGORIAN",
             "X-WR-CALNAME:ESCUDO MADRID · calendario preventivo"]
    for e in events:
        start = date.fromisoformat(e["start"])
        end = date.fromisoformat(e["end"]) + timedelta(days=1)  # DTEND exclusivo en eventos de día completo
        summary = e["title"] + (f" · {e['area_name']}" if e.get("area_name") else "")
        desc = f"{e['detail']}\nFuente: {e['source']}\n{NOTICE}"
        lines += ["BEGIN:VEVENT", f"UID:{e['id']}@escudo-madrid", f"DTSTAMP:{stamp}",
                  f"DTSTART;VALUE=DATE:{start.strftime('%Y%m%d')}", f"DTEND;VALUE=DATE:{end.strftime('%Y%m%d')}",
                  f"SUMMARY:{_ics_escape(summary)}", f"DESCRIPTION:{_ics_escape(desc)}",
                  "TRANSP:TRANSPARENT", "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\r\n".join(_fold(x) for x in lines) + "\r\n"


@router.get("/calendar.ics")
def calendar_ics(from_: date | None = Query(None, alias="from"), to: date | None = None,
                 p: Principal = Depends(current_principal), session: Session = Depends(get_session)) -> Response:
    start, end = _range(from_, to)
    return Response(to_ics(build_events(session, p, start, end)), media_type="text/calendar; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="escudo-calendario.ics"'})
