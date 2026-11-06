"""Registro de indicadores trazables (PRD §4.5) y constructor de objetos `Indicator`."""

from __future__ import annotations

from typing import Any

INDICATORS: dict[str, dict[str, str]] = {
    "municipality_population_total": {
        "label": "Población censada",
        "definition": "Población total censada del municipio (todas las edades, nacionalidades y sexos).",
        "unit": "personas",
        "spatial_scope": "municipio",
        "source_id": "CAM-01",
        "update_frequency": "anual",
        "null_handling": "Valores '-' o vacíos → null (no disponible).",
        "transformation": "cam_transform.build_population: filtro Edad=Total, Nacionalidad=Total, Sexo=Total; último año.",
        "caveat": "Escala municipal: no representa la población de una urbanización o zona.",
        "status": "official",
    },
    "municipality_age_65_plus_share": {
        "label": "Proporción de población ≥ 65 años",
        "definition": "Suma de grupos quinquenales desde 65-69 hasta 100 y más / población total, mismo año.",
        "unit": "proporción",
        "spatial_scope": "municipio",
        "source_id": "CAM-01",
        "update_frequency": "anual",
        "null_handling": "Si la población total es null o 0 → null.",
        "transformation": "cam_transform.build_population: Σ edades ≥65 (Nacionalidad=Total, Sexo=Total) / Total.",
        "caveat": "Perfil municipal; no es el número de personas mayores en una urbanización.",
        "status": "derived",
    },
    "municipality_density": {
        "label": "Densidad de población",
        "definition": "Habitantes por km² publicados por el Instituto de Estadística de la CAM.",
        "unit": "hab/km²",
        "spatial_scope": "municipio",
        "source_id": "CAM-02",
        "update_frequency": "anual",
        "null_handling": "'-' → null.",
        "transformation": "Valor literal del último año disponible.",
        "caveat": "Escala municipal, no parcela.",
        "status": "official",
    },
    "municipality_altitude": {
        "label": "Altitud del municipio",
        "definition": "Altitud publicada para el municipio.",
        "unit": "m",
        "spatial_scope": "municipio",
        "source_id": "CAM-03",
        "update_frequency": "estático",
        "null_handling": "'-' → null.",
        "transformation": "Valor literal (año de referencia publicado).",
        "caveat": "Altitud de referencia administrativa; no sustituye un MDE ni permite derivar pendientes.",
        "status": "official",
    },
    "municipality_area_km2": {
        "label": "Superficie calculada",
        "definition": "Área de la geometría municipal obtenida por disolución de secciones censales, en EPSG:25830.",
        "unit": "km²",
        "spatial_scope": "municipio",
        "source_id": "CAM-08",
        "update_frequency": "según versión del recurso",
        "null_handling": "Sin geometría → null.",
        "transformation": "cam_transform.build_municipal_geometries: unary_union de secciones por CDMUNI; área planar.",
        "caveat": "Límites estadísticos (seccionado 2019), no deslinde jurídico.",
        "status": "derived",
    },
    "official_fire_risk_class": {
        "label": "Riesgo oficial por incendios forestales",
        "definition": "Clase literal publicada en la capa oficial de riesgo (GEO-01). Se muestra el reparto de superficie del municipio por clase.",
        "unit": "clase",
        "spatial_scope": "polígono oficial / reparto municipal",
        "source_id": "GEO-01",
        "update_frequency": "según publicación IDEM",
        "null_handling": "Capa no ingerida → unavailable.",
        "transformation": "Intersección polígonos oficiales × municipio en EPSG:25830 (ver docs/spatial-method.md).",
        "caveat": "Clase oficial sin recalcular; no es una probabilidad anual de incendio.",
        "status": "official",
    },
    "review_priority_index": {
        "label": "Prioridad de revisión ESCUDO",
        "definition": "Cola operativa: acciones vencidas, inspecciones pendientes de revisión técnica y prioridad técnica asignada.",
        "unit": "puntos",
        "spatial_scope": "ámbito de la organización",
        "source_id": "ESCUDO",
        "update_frequency": "en tiempo real",
        "null_handling": "Sin datos de la organización → 0.",
        "transformation": "Ver docs/optimizer-method.md (pesos editables).",
        "caveat": "No es un índice oficial de peligro ni de riesgo de incendio.",
        "status": "derived",
    },
    "budget_allocation_result": {
        "label": "Selección de actuaciones bajo presupuesto",
        "definition": "Actuaciones seleccionadas por CP-SAT maximizando prioridad técnica × cobertura sujeta a presupuesto y restricciones.",
        "unit": "€ / actuaciones",
        "spatial_scope": "ámbito de la organización",
        "source_id": "ESCUDO",
        "update_frequency": "por ejecución",
        "null_handling": "Sin opciones → resultado vacío.",
        "transformation": "services/optimizer (determinista).",
        "caveat": "No es una reducción cuantificada del riesgo real.",
        "status": "scenario",
    },
}


def indicator(indicator_id: str, value: Any, temporal_scope: str | int | None, *, status: str | None = None,
              caveat: str | None = None, label: str | None = None) -> dict[str, Any]:
    d = INDICATORS[indicator_id]
    st = status or d["status"]
    if value is None:
        st = "unavailable"
    return {
        "indicator_id": indicator_id,
        "label": label or d["label"],
        "value": value,
        "unit": d["unit"],
        "spatial_scope": d["spatial_scope"],
        "temporal_scope": str(temporal_scope) if temporal_scope is not None else None,
        "status": st,
        "source_id": d["source_id"],
        "method": d["transformation"],
        "caveat": caveat or d["caveat"],
    }
