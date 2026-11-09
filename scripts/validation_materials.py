"""Materiales del experimento de utilidad (ROADMAP 3.1, PRD §5.5) a partir de los casos FICTICIOS del seed.

    python scripts/validation_materials.py                 # genera docs/validation/materiales/
    python scripts/validation_materials.py score A FAJA-30,PAIF-RED,...   # puntúa la selección de un participante

Las hojas de participante contienen exactamente la misma información que ve quien usa ESCUDO (hallazgos,
actuaciones, cantidades, costes, prioridad técnica, presupuesto, prerrequisitos e incompatibilidades), para que
la única diferencia entre condiciones sea la herramienta. La clave del evaluador usa el mismo optimizador CP-SAT
determinista que la aplicación y la misma función objetivo (prioridad técnica × cobertura): no es reducción de riesgo.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "fixtures" / "synthetic" / "demo_seed.json"
CATALOG = ROOT / "data" / "reference" / "measures_catalog.json"
OUT = ROOT / "docs" / "validation" / "materiales"
CASES = {"A": "val_a", "B": "val_b"}
ANSWERS = {"si": "Sí", "no": "No", "parcial": "Parcial"}
CHECKLIST_LABELS = {
    "franja_perimetral": "Franja perimetral de protección",
    "vegetacion_viviendas": "Vegetación en contacto con viviendas",
    "restos_vegetales": "Acopio de restos vegetales",
    "hidrantes": "Hidrantes y puntos de agua",
    "accesos": "Accesos y viales (gálibo)",
    "plan_autoproteccion": "Plan de autoprotección",
    "informacion_vecinal": "Información a la población",
}


def _eur(v: float) -> str:
    return f"{v:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def load_case(letter: str) -> tuple[dict, dict, dict, dict]:
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    key = CASES[letter]
    area = next(a for a in seed["areas"] if a["key"] == key)
    insp = next(i for i in seed["inspections"] if i["area"] == key)
    scen = next(s for s in seed["scenarios"] if s["area"] == key)
    catalog = {m["code"]: m for m in json.loads(CATALOG.read_text(encoding="utf-8"))["measures"]}
    return area, insp, scen, catalog


def solve_case(scen: dict, catalog: dict) -> dict:
    sys.path.insert(0, str(ROOT / "services" / "optimizer"))
    from escudo_optimizer import OptionInput, SolveRequest, solve

    codes = {o["measure_code"] for o in scen["options"]}
    opts = [OptionInput(option_id=o["measure_code"], measure_code=o["measure_code"], quantity=o["quantity"],
                        unit_cost_eur=o["unit_cost_eur"], technical_priority=o["technical_priority"],
                        coverage_weight=o["coverage_weight"], manual_rank=o.get("manual_rank"),
                        requires=[c for c in catalog[o["measure_code"]].get("prerequisites") or [] if c in codes],
                        excludes=[c for c in catalog[o["measure_code"]].get("excludes") or [] if c in codes])
            for o in scen["options"]]
    return solve(SolveRequest(budget_eur=scen["budget_eur"], options=opts, is_demo_budget=True)).model_dump()


def score(letter: str, selected: list[str]) -> dict:
    """Puntúa una selección con la MISMA función objetivo que el optimizador (prioridad × peso de cobertura)."""
    _, _, scen, catalog = load_case(letter)
    by = {o["measure_code"]: o for o in scen["options"]}
    unknown = [c for c in selected if c not in by]
    sel = [c for c in selected if c in by]
    cost = sum(by[c]["quantity"] * by[c]["unit_cost_eur"] for c in sel)
    total_w = sum(o["technical_priority"] * o["coverage_weight"] for o in scen["options"])
    got = sum(by[c]["technical_priority"] * by[c]["coverage_weight"] for c in sel)
    violations = []
    for c in sel:
        m = catalog[c]
        violations += [f"{c} requiere {p}" for p in (m.get("prerequisites") or []) if p in by and p not in sel]
        violations += [f"{c} incompatible con {x}" for x in (m.get("excludes") or []) if x in sel]
    return {"case": letter, "selected": sel, "unknown_codes": unknown, "total_cost_eur": round(cost, 2),
            "within_budget": cost <= scen["budget_eur"] + 1e-6, "priority_coverage_share": round(got / total_w, 4),
            "constraint_violations": sorted(set(violations))}


def participant_sheet(letter: str) -> str:
    area, insp, scen, catalog = load_case(letter)
    lines = [
        f"# Caso {letter} — hoja del participante (DATOS FICTICIOS)",
        "",
        f"**Ámbito:** {area['name']}. Municipio de referencia (real): INE {area['municipality_code']}. "
        "La urbanización, la inspección, las cantidades, los costes y el presupuesto son **inventados** para esta prueba.",
        "",
        f"**Presupuesto disponible:** {_eur(scen['budget_eur'])} (ficticio).",
        "",
        "## 1. Resultado de la inspección (ficticia)",
        "",
        "| Elemento revisado | Cumple | Observación |",
        "|---|---|---|",
    ]
    for it in insp["items"]:
        lines.append(f"| {CHECKLIST_LABELS.get(it['checklist_code'], it['checklist_code'])} | "
                     f"{ANSWERS.get(it['answer'], it['answer'])} | {it['observation']} |")
    lines += ["", "## 2. Actuaciones posibles", "",
              "Prioridad técnica: 1 (baja) a 5 (alta), asignada por el técnico del caso (ficticio).", "",
              "| Código | Actuación | Cantidad | Coste unitario | Coste total | Prioridad técnica | Requiere | Incompatible con |",
              "|---|---|---:|---:|---:|---:|---|---|"]
    codes = {o["measure_code"] for o in scen["options"]}
    for o in scen["options"]:
        m = catalog[o["measure_code"]]
        req = ", ".join(c for c in m.get("prerequisites") or [] if c in codes) or "—"
        exc = ", ".join(c for c in m.get("excludes") or [] if c in codes) or "—"
        lines.append(f"| {o['measure_code']} | {m['name']} | {o['quantity']:g} {m['unit']} | {_eur(o['unit_cost_eur'])} | "
                     f"{_eur(o['quantity'] * o['unit_cost_eur'])} | {o['technical_priority']} | {req} | {exc} |")
    total = sum(o["quantity"] * o["unit_cost_eur"] for o in scen["options"])
    lines += ["", f"Coste de todas las actuaciones: {_eur(total)} — supera el presupuesto.", "",
              "## 3. Tarea", "",
              "Prepara un **plan de actuaciones preventivas** para el próximo año que:",
              "1. no supere el presupuesto;",
              "2. atienda las prioridades técnicas de la inspección y respete prerrequisitos e incompatibilidades;",
              "3. asigne a cada actuación un **responsable** y una **fecha límite**;",
              "4. indique en qué **fuentes** te apoyas (datos del municipio, cartografía oficial, plan anual…);",
              "5. deje constancia de cómo se documentará su ejecución.",
              "",
              "Puedes usar las herramientas que uses habitualmente (hoja de cálculo, papel, buscador). "
              "Cuando termines, avisa a la persona que conduce la sesión.",
              "",
              "## 4. Plantilla de respuesta", "",
              "| Código | Responsable | Fecha límite | Cómo se documentará | Justificación |",
              "|---|---|---|---|---|",
              "| | | | | |", "", "Fuentes consultadas:", "",
              "> Ejercicio de planificación con datos ficticios. No es un PAIF ni una prescripción técnica."]
    return "\n".join(lines) + "\n"


def evaluator_key() -> str:
    lines = ["# Clave del evaluador — NO entregar a participantes", "",
             "Calculada con el optimizador CP-SAT de ESCUDO (determinista, 1 worker, semilla 0) y la función objetivo "
             "acordada: Σ prioridad técnica × peso de cobertura de las actuaciones seleccionadas / total posible. "
             "Es una función objetivo de planificación, **no** una reducción de riesgo.", ""]
    for letter in CASES:
        area, _, scen, catalog = load_case(letter)
        res = solve_case(scen, catalog)
        lines += [f"## {area['name']}", "",
                  "| Estrategia | Actuaciones | Coste | Cobertura de prioridad |", "|---|---|---:|---:|"]
        for s in res["strategies"]:
            lines.append(f"| {s['strategy']} | {', '.join(s['selected'])} | {_eur(s['total_cost_eur'])} | "
                         f"{s['priority_coverage_share']:.1%} |")
        lines += ["", "**Elementos obligatorios para contar omisiones** (1 punto cada uno que falte):",
                  "- coste dentro de presupuesto;",
                  "- ninguna incompatibilidad violada y prerrequisitos incluidos;",
                  "- todas las actuaciones de prioridad 5 incluidas o su exclusión justificada;",
                  "- cada actuación con responsable;",
                  "- cada actuación con fecha límite;",
                  "- al menos una fuente oficial citada;",
                  "- previsión de evidencia de ejecución.", ""]
    lines += ["Puntuar una selección: `python scripts/validation_materials.py score A CÓDIGO1,CÓDIGO2,…`", ""]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    if argv[:1] == ["score"]:
        print(json.dumps(score(argv[1].upper(), [c.strip() for c in argv[2].split(",") if c.strip()]),
                         ensure_ascii=False, indent=2))
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    for letter in CASES:
        (OUT / f"caso-{letter}-participante.md").write_text(participant_sheet(letter), encoding="utf-8")
    (OUT / "clave-evaluador.md").write_text(evaluator_key(), encoding="utf-8")
    print(f"Materiales en {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
