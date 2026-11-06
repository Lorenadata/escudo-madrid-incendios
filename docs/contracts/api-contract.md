# Contrato API v1 — ESCUDO MADRID

Dueño: A0/A6. Fuente de verdad ejecutable: `packages/contracts/openapi.json` (exportado desde FastAPI).
Base URL dev: `http://localhost:8000`. JSON UTF-8. Fechas ISO 8601. Geometrías GeoJSON EPSG:4326.

## Convenciones transversales

**Indicador** (`Indicator`): todo valor mostrado llega envuelto así; la UI pinta un distintivo por `status`.

```json
{
  "indicator_id": "municipality_population_total",
  "label": "Población censada",
  "value": 12345,            // number | string | null
  "unit": "personas",
  "spatial_scope": "municipio",
  "temporal_scope": "2025",
  "status": "official",      // official | derived | scenario | user_reported | unavailable | stale
  "source_id": "CAM-01",
  "method": "Suma de todas las edades y nacionalidades del último año disponible",
  "caveat": "Escala municipal: no representa la población de una urbanización."
}
```

**Errores**: `{"detail": "mensaje"}` con 400/401/403/404/422.
**Auth**: `Authorization: Bearer <jwt>`. Endpoints públicos marcados (P). Privados (🔒) filtran por organización.

## Endpoints

| Método | Ruta | Acceso | Respuesta |
|---|---|---|---|
| GET | `/health` | P | `{status, db, version, sources_ok, sources_total}` |
| GET | `/v1/sources` | P | `Source[]` |
| GET | `/v1/sources/{source_id}` | P | `Source` + `quality_checks[]` |
| GET | `/v1/municipalities?q=&min_density=&max_density=&sort=` | P | `MunicipalitySummary[]` |
| GET | `/v1/municipalities/{ine_code}/profile` | P | `MunicipalityProfile` |
| GET | `/v1/compare?a={ine}&b={ine}` | P | `{a: MunicipalityProfile, b: MunicipalityProfile, same_reference_year: bool}` |
| GET | `/v1/layers` | P | `Layer[]` |
| GET | `/v1/layers/{name}/geojson` | P | `FeatureCollection` (municipios: props `ine_code,name,density,...`) |
| GET | `/v1/weather/context?municipality_code=` | P | `WeatherContext` |
| GET | `/v1/fire-history` | P | `{source_id, scope, series: [{year, fires, area_ha, ...}]}` |
| POST | `/v1/auth/login` | P | `{access_token, token_type, user}` body `{email, password}` |
| GET | `/v1/me` | 🔒 | `User` con `memberships[]` |
| GET | `/v1/areas` | 🔒 | `Area[]` de la organización |
| POST | `/v1/areas` | 🔒 | `Area` body `{name, municipality_code, geometry?: GeoJSON Polygon, description}` |
| GET | `/v1/areas/{id}` | 🔒 | `AreaDetail` (incluye `municipality_profile` y `official_layers` si hay geometría; **nunca población de área**) |
| GET | `/v1/inspections?area_id=` | 🔒 | `Inspection[]` |
| POST | `/v1/inspections` | 🔒 | `Inspection` body `{area_id, inspected_on, inspector_name, items:[{checklist_code, answer, observation}]}` |
| POST | `/v1/inspections/{id}/evidence` | 🔒 | multipart `file` (jpg/png/pdf ≤ 10 MB) → `EvidenceFile` |
| GET | `/v1/measures` | P | `Measure[]` (catálogo) |
| GET | `/v1/scenarios?area_id=` | 🔒 | `Scenario[]` |
| POST | `/v1/scenarios` | 🔒 | `Scenario` body `{area_id, name, budget_eur, is_demo_budget, options:[{measure_code, quantity, unit_cost_eur, technical_priority(1-5), coverage_weight, cost_status}]}` |
| POST | `/v1/scenarios/{id}/solve` | 🔒 | `ScenarioResult` |
| GET | `/v1/scenarios/{id}` | 🔒 | `Scenario` + último `ScenarioResult` |
| POST | `/v1/action-plans` | 🔒 | `ActionPlan` body `{scenario_id}` (convierte opciones seleccionadas en acciones) |
| GET | `/v1/action-plans/{id}` | 🔒 | `ActionPlan` |
| PATCH | `/v1/action-plans/{id}/actions/{action_id}` | 🔒 | `PlanAction` body parcial `{status, responsible, due_date, actual_cost_eur, note}` |
| GET | `/v1/reports/scenario/{scenario_id}.pdf` | 🔒 | PDF |
| GET | `/v1/impact` | 🔒 | KPIs operativos de la organización |
| GET | `/v1/audit?entity=` | 🔒 | `AuditEvent[]` |
| GET | `/v1/demo/guided` | P | Caso guiado público de solo lectura (Flujo C), todo etiquetado `synthetic` salvo los datos oficiales |

## Tipos principales

- `Source`: `{source_id, portal, title, producer, catalog_url, license, spatial_scope, temporal_scope, use_in_product, caveats, last_extracted_at, portal_modified_at, sha256, status: "ok"|"failed"|"not_ingested"}`
- `MunicipalitySummary`: `{ine_code (5 díg., p. ej. "28079"), name, population: Indicator, density: Indicator, altitude_m: Indicator, age_65_plus_share: Indicator}`
- `MunicipalityProfile`: summary + `{area_km2: Indicator(derived), forest_share: Indicator, official_fire: {risk, hazard, vulnerability}: OfficialLayerSummary|unavailable, weather: WeatherContext, sources: string[], scale_notice: string}`
- `OfficialLayerSummary`: `{source_id, status, classes: [{class_label (literal fuente), area_share (0-1, derived)}], dominant_class, version}`
- `WeatherContext`: `{status: "ok"|"stale"|"unavailable", issued_at, valid_from, valid_to, reference_location, variables: Indicator[], fire_danger: Indicator|null, disclaimer: "Índice de peligro meteorológico; no es pronóstico de ignición ni alerta operativa.", last_valid_at}`
- `Area`: `{id, organization_id, name, municipality_code, description, has_geometry, geometry?, record_status ("active"|"synthetic")}`
- `Inspection`: `{id, area_id, inspected_on, inspector_name, review_status ("pending_technical_review"|"reviewed"), items[], evidence[]}`
- `Measure`: `{code, name, description, unit, reference_unit_cost_eur|null, cost_status ("reference"|"user_quote"|"scenario"), cost_source, normative_refs[], prerequisites[], excludes[], requires_professional: bool}`
- `ScenarioResult`: `{solver: "cp-sat", solver_version, status: "OPTIMAL"|"FEASIBLE"|"INFEASIBLE", deterministic: true, budget_eur, is_demo_budget, strategies: [{strategy: "manual"|"cheapest_first"|"optimized", selected: [measure_code], total_cost_eur, objective_value, priority_coverage_share}], sensitivity: [{budget_eur, objective_value, total_cost_eur}], objective_definition, disclaimer}`
- `ActionPlan`: `{id, scenario_id, created_at, actions: PlanAction[]}`; `PlanAction`: `{id, measure_code, status ("pending"|"in_progress"|"done"|"blocked"), responsible, due_date, planned_cost_eur, actual_cost_eur, evidence_count, history[]}`
