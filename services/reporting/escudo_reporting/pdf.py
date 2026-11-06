"""Informe PDF de escenario: fuentes, fecha, método, supuestos, distinción real/simulado y
validación profesional pendiente (test T09)."""

from __future__ import annotations

from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

STATUS_LABEL = {
    "official": "OFICIAL",
    "derived": "DERIVADO",
    "scenario": "ESCENARIO",
    "user_reported": "APORTADO POR USUARIO",
    "unavailable": "NO DISPONIBLE",
    "stale": "DESACTUALIZADO",
    "synthetic": "FICTICIO (DEMO)",
}

DISCLAIMER = (
    "ESCUDO MADRID es una herramienta de apoyo a la planificación preventiva. Este informe no es un PAIF, "
    "no constituye aprobación administrativa ni certificado oficial, no contiene instrucciones de extinción ni "
    "de evacuación y no sustituye a ASEM 112, AEMET, INFOMA ni al personal técnico competente. "
    "La selección de actuaciones maximiza una función objetivo acordada (prioridad técnica × cobertura); "
    "NO cuantifica reducción del riesgo de incendio."
)


def _fmt_eur(v: float | None) -> str:
    if v is None:
        return "—"
    return f"{v:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def _ind(ind: dict | None) -> str:
    if not ind:
        return "—"
    val = ind.get("value")
    if val is None:
        return f"no disponible [{ind.get('source_id')}]"
    if ind.get("unit") == "proporción":
        val = f"{val * 100:.1f} %"
    elif isinstance(val, float):
        val = f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{val} {'' if ind.get('unit') == 'proporción' else ind.get('unit', '')} · {STATUS_LABEL.get(ind.get('status'), ind.get('status'))} · {ind.get('source_id')} ({ind.get('temporal_scope') or 's/f'})"


def build_scenario_report(ctx: dict[str, Any]) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm,
                            bottomMargin=16 * mm, title="ESCUDO MADRID — Informe de escenario",
                            author="ESCUDO MADRID (generado automáticamente)")
    ss = getSampleStyleSheet()
    h1, h2, body = ss["Title"], ss["Heading2"], ss["BodyText"]
    small = ParagraphStyle("small", parent=body, fontSize=8, leading=10)
    warn = ParagraphStyle("warn", parent=body, fontSize=8.5, leading=11, textColor=colors.HexColor("#7a2e00"),
                          backColor=colors.HexColor("#fff4e5"), borderPadding=5)
    tstyle = TableStyle([("FONTSIZE", (0, 0), (-1, -1), 8), ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                         ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8ecef")),
                         ("VALIGN", (0, 0), (-1, -1), "TOP")])
    sc = ctx["scenario"]
    res = sc.get("latest_result") or {}
    area = ctx["area"]
    synthetic = area.get("record_status") == "synthetic" or sc.get("record_status") == "synthetic"
    story: list = [Paragraph("ESCUDO MADRID — Informe de escenario preventivo", h1),
                   Paragraph(f"Generado: {ctx['generated_at']} (UTC) · Escenario <b>{sc['name']}</b> · id {sc['id']}", small),
                   Spacer(1, 4), Paragraph(DISCLAIMER, warn), Spacer(1, 6)]
    if synthetic:
        story.append(Paragraph("<b>DATOS DE DEMOSTRACIÓN FICTICIOS:</b> la organización, el ámbito, la inspección, "
                               "los costes y el presupuesto de este informe son ficticios y solo ilustran el flujo. "
                               "Los indicadores municipales y capas oficiales sí proceden de fuentes reales.", warn))
        story.append(Spacer(1, 6))

    story.append(Paragraph("1. Ámbito y contexto territorial oficial", h2))
    m = ctx.get("municipality") or {}
    rows = [["Indicador", "Valor · estado · fuente (periodo)"],
            ["Ámbito", f"{area['name']} ({STATUS_LABEL['synthetic'] if area.get('record_status') == 'synthetic' else 'registrado por la organización'})"],
            ["Municipio", f"{m.get('name', '—')} (INE {area['municipality_code']})"]]
    for key in ("population", "density", "age_65_plus_share", "altitude_m", "area_km2"):
        if key in m:
            rows.append([m[key]["label"], _ind(m[key])])
    story += [Table(rows, colWidths=[55 * mm, 119 * mm], style=tstyle), Spacer(1, 3),
              Paragraph(m.get("scale_notice", ""), small)]
    ol = ctx.get("official_layers") or {}
    lrows = [["Capa oficial", "Estado", "Reparto de superficie municipal por clase (literal de la fuente)"]]
    for layer in ol.values():
        cls = "; ".join(f"{c['class_label']}: {c['area_share'] * 100:.1f} %" for c in layer.get("classes", [])) or layer.get("reason", "—")
        lrows.append([Paragraph(f"{layer['label']} [{layer['source_id']}]", small), STATUS_LABEL.get(layer["status"], layer["status"]),
                      Paragraph(cls, small)])
    story += [Spacer(1, 4), Table(lrows, colWidths=[55 * mm, 25 * mm, 94 * mm], style=tstyle)]

    if ctx.get("inspections"):
        story.append(Paragraph("2. Inspecciones registradas", h2))
        for ins in ctx["inspections"][:3]:
            story.append(Paragraph(f"{ins['inspected_on']} · {ins['inspector_name']} · revisión técnica: "
                                   f"<b>{'PENDIENTE' if ins['review_status'] == 'pending_technical_review' else 'realizada'}</b>"
                                   f" · {len(ins['evidence'])} evidencias", small))
            irows = [["Elemento", "Respuesta", "Observación"]] + [
                [Paragraph(it["question"] or it["checklist_code"], small), it["answer"], Paragraph(it["observation"] or "", small)]
                for it in ins["items"]]
            story += [Table(irows, colWidths=[80 * mm, 18 * mm, 76 * mm], style=tstyle), Spacer(1, 4)]

    story.append(Paragraph("3. Opciones evaluadas", h2))
    cat = ctx.get("catalog", {})
    orows = [["Medida", "Cant.", "Coste unit.", "Total", "Origen coste", "Prioridad técnica", "Peso cobertura"]]
    for o in sc["options"]:
        orows.append([Paragraph(cat.get(o["measure_code"], {}).get("name", o["measure_code"]), small), f"{o['quantity']:g}",
                      _fmt_eur(o["unit_cost_eur"]), _fmt_eur(o["total_cost_eur"]),
                      {"reference": "referencia", "user_quote": "presupuesto aportado", "scenario": "ESCENARIO"}[o["cost_status"]],
                      str(o["technical_priority"]), f"{o['coverage_weight']:g}"])
    story.append(Table(orows, colWidths=[56 * mm, 12 * mm, 22 * mm, 24 * mm, 26 * mm, 18 * mm, 16 * mm], style=tstyle))

    story.append(Paragraph("4. Comparación de estrategias", h2))
    story.append(Paragraph(f"Presupuesto: <b>{_fmt_eur(sc['budget_eur'])}</b>"
                           f"{' — PRESUPUESTO DE DEMOSTRACIÓN, no es una adjudicación real' if sc['is_demo_budget'] else ''}. "
                           f"Solver: {res.get('solver')} {res.get('solver_version', '')} · estado {res.get('status')} · "
                           f"determinista: {res.get('deterministic')} · huella de entrada {str(res.get('input_hash', ''))[:16]}…", small))
    srows = [["Estrategia", "Actuaciones", "Coste total", "Valor objetivo", "Cobertura de prioridad"]]
    names = {"manual": "Priorización manual (base)", "cheapest_first": "Menor coste primero", "optimized": "Optimizada (CP-SAT)"}
    for st in res.get("strategies", []):
        srows.append([names.get(st["strategy"], st["strategy"]), str(len(st["selected"])), _fmt_eur(st["total_cost_eur"]),
                      f"{st['objective_value']:.2f}", f"{st['priority_coverage_share'] * 100:.1f} %"])
    story += [Table(srows, colWidths=[52 * mm, 22 * mm, 30 * mm, 30 * mm, 40 * mm], style=tstyle), Spacer(1, 3),
              Paragraph(f"<b>Función objetivo:</b> {res.get('objective_definition', '')}", small),
              Paragraph(f"<b>Advertencia:</b> {res.get('disclaimer', '')}", small)]
    if res.get("sensitivity"):
        sens = [["Variante", "Presupuesto", "Coste", "Valor objetivo"]] + [
            [s.get("label", ""), _fmt_eur(s["budget_eur"]), _fmt_eur(s["total_cost_eur"]), f"{s['objective_value']:.2f}"]
            for s in res["sensitivity"]]
        story += [Spacer(1, 4), Paragraph("Análisis de sensibilidad", ss["Heading4"]),
                  Table(sens, colWidths=[60 * mm, 38 * mm, 38 * mm, 38 * mm], style=tstyle)]

    plan = ctx.get("plan")
    if plan:
        story.append(Paragraph("5. Plan de ejecución", h2))
        prow = [["Medida", "Estado", "Responsable", "Vence", "Coste plan.", "Coste real", "Evid."]]
        for a in plan["actions"]:
            prow.append([Paragraph(cat.get(a["measure_code"], {}).get("name", a["measure_code"]), small), a["status"],
                         a["responsible"] or "—", a["due_date"] or "—", _fmt_eur(a["planned_cost_eur"]),
                         _fmt_eur(a["actual_cost_eur"]), str(a["evidence_count"])])
        story.append(Table(prow, colWidths=[52 * mm, 18 * mm, 30 * mm, 20 * mm, 22 * mm, 22 * mm, 10 * mm], style=tstyle))

    story += [PageBreak(), Paragraph("6. Validación profesional", h2),
              Paragraph("<b>PENDIENTE.</b> Las medidas, cantidades y prioridades deben ser revisadas por personal técnico "
                        "competente antes de cualquier ejecución. ESCUDO no aprueba PAIF ni sustituye procedimientos "
                        "administrativos.", body),
              Paragraph("7. Fuentes y procedencia", h2)]
    frows = [["ID", "Fuente", "Licencia", "Extracción", "SHA-256"]]
    for s in ctx.get("sources", []):
        frows.append([s["source_id"], Paragraph(f"{s['title']}<br/><font size=6>{s['catalog_url']}</font>", small), s["license"],
                      (s["last_extracted_at"] or "no ingerida")[:10], (s["sha256"] or "—")[:12]])
    story += [Table(frows, colWidths=[16 * mm, 92 * mm, 20 * mm, 22 * mm, 24 * mm], style=tstyle), Spacer(1, 4),
              Paragraph("Reproducibilidad: python -m escudo_pipelines.fetch → cam_transform → escudo_api.etl_load; "
                        "el resultado del optimizador es determinista (CP-SAT, 1 worker, semilla 0) para la misma huella de entrada.", small)]

    def _footer(canvas, _doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.drawString(18 * mm, 9 * mm, "ESCUDO MADRID · herramienta de apoyo a la planificación · no es documento oficial")
        canvas.drawRightString(192 * mm, 9 * mm, f"pág. {_doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()
