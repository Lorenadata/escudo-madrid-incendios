// Tipos del contrato API v1 (docs/contracts/api-contract.md).
// Si existe packages/contracts/openapi.json, este archivo debe mantenerse alineado.

export type IndicatorStatus =
  | "official"
  | "derived"
  | "scenario"
  | "user_reported"
  | "unavailable"
  | "stale";

export interface Indicator {
  indicator_id: string;
  label: string;
  value: number | string | null;
  unit?: string | null;
  spatial_scope?: string | null;
  temporal_scope?: string | null;
  status: IndicatorStatus;
  source_id?: string | null;
  method?: string | null;
  caveat?: string | null;
}

export interface Health {
  status: string;
  db: string;
  version: string;
  sources_ok: number;
  sources_total: number;
}

export interface QualityCheck {
  check_id?: string;
  name?: string;
  passed?: boolean;
  status?: string;
  detail?: string | null;
  checked_at?: string | null;
}

export interface Source {
  source_id: string;
  portal: string;
  title: string;
  producer: string;
  catalog_url: string;
  license: string;
  spatial_scope: string;
  temporal_scope: string;
  use_in_product: string;
  caveats: string;
  last_extracted_at: string | null;
  portal_modified_at: string | null;
  sha256: string | null;
  status: "ok" | "failed" | "not_ingested" | string;
  quality_checks?: QualityCheck[];
}

export interface MunicipalitySummary {
  ine_code: string;
  name: string;
  population: Indicator;
  density: Indicator;
  altitude_m: Indicator;
  age_65_plus_share: Indicator;
  forest_share?: Indicator;
}

export interface OfficialLayerClass {
  class_label: string;
  area_share: number | null;
}

export interface OfficialLayerSummary {
  source_id: string;
  label?: string;
  reason?: string;
  status: IndicatorStatus | string;
  classes: OfficialLayerClass[];
  dominant_class: string | null;
  version?: string | null;
}

export interface WeatherContext {
  status: "ok" | "stale" | "unavailable";
  issued_at: string | null;
  valid_from: string | null;
  valid_to: string | null;
  reference_location: string | { ine_code?: string; name?: string; type?: string; aemet_url?: string } | null;
  source_id?: string;
  provider?: string;
  source_url?: string;
  attribution?: string;
  message?: string | null;
  variables: Indicator[];
  fire_danger: Indicator | null;
  disclaimer: string;
  last_valid_at: string | null;
}

export interface MunicipalityProfile extends MunicipalitySummary {
  area_km2: Indicator;
  forest_share: Indicator;
  official_fire: {
    risk: OfficialLayerSummary | null;
    hazard: OfficialLayerSummary | null;
    vulnerability: OfficialLayerSummary | null;
  } | null;
  weather: WeatherContext | null;
  sources: string[];
  scale_notice: string;
}

export interface CompareResponse {
  a: MunicipalityProfile;
  b: MunicipalityProfile;
  same_reference_year: boolean;
}

export interface LayerLegendItem {
  label: string;
  color: string;
}

export interface OfficialClassMeta {
  class_code: number | string;
  class_label: string;
  color_suggestion?: string | null;
  transparent_in_official_style?: boolean;
  present_in_raster?: boolean;
  regional_area_ha?: number | null;
}

export interface MunicipalSeries {
  ine_code: string;
  status: string;
  series: Record<string, Array<{ year: number; value: number | null; source_id: string }>>;
}

export interface Layer {
  name: string;
  title?: string;
  label?: string;
  features?: number;
  classes?: OfficialClassMeta[];
  license?: string | null;
  version?: string | null;
  kind?: string;
  source_id?: string | null;
  status?: IndicatorStatus | string;
  available: boolean;
  legend?: LayerLegendItem[];
  class_property?: string | null;
  description?: string | null;
}

export interface GeoFeature {
  type: "Feature";
  id?: string | number;
  geometry: GeoJSON.Geometry;
  properties: Record<string, unknown>;
}

export interface FeatureCollection {
  type: "FeatureCollection";
  features: GeoFeature[];
}

export interface FireHistory {
  source_id: string;
  status?: string;
  caveat?: string;
  scope: string;
  series: Array<{ year: number; fires?: number | null; area_ha?: number | null; [k: string]: unknown }>;
}

export interface Membership {
  organization_id: number | string;
  organization_name?: string;
  organization_kind?: string;
  municipality_code?: string | null;
  role: string;
}

export interface User {
  id: number | string;
  email: string;
  full_name?: string | null;
  memberships: Membership[];
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Area {
  id: number | string;
  organization_id: number | string;
  name: string;
  municipality_code: string;
  description: string | null;
  has_geometry: boolean;
  geometry?: GeoJSON.Geometry | null;
  record_status: "active" | "synthetic" | string;
  shared_with_municipality?: boolean;
}

export interface AreaDetail extends Area {
  municipality_profile?: MunicipalityProfile | null;
  population_notice?: string;
  official_layers_scope?: string;
  official_layers_area?: Record<string, unknown> | null;
  official_layers?: Record<string, OfficialLayerSummary | null> | null;
}

export interface InspectionItem {
  id?: number | string;
  checklist_code: string;
  question?: string;
  answer: string;
  observation?: string | null;
}

export interface EvidenceFile {
  id: number | string;
  filename?: string;
  original_name?: string;
  bytes?: number;
  sha256?: string;
  content_type?: string;
  size_bytes?: number;
  uploaded_at?: string;
  record_status?: string;
}

export interface Inspection {
  id: number | string;
  area_id: number | string;
  inspected_on: string;
  inspector_name: string;
  review_status: "pending_technical_review" | "reviewed" | string;
  items: InspectionItem[];
  evidence: EvidenceFile[];
  record_status?: string;
}

export interface Measure {
  code: string;
  name: string;
  description: string;
  unit: string;
  reference_unit_cost_eur: number | null;
  cost_status: "reference" | "user_quote" | "scenario" | string;
  cost_source: string | null;
  normative_refs: string[];
  prerequisites: string[];
  excludes: string[];
  requires_professional: boolean;
}

export interface ScenarioOption {
  id?: number | string;
  option_id?: string;
  total_cost_eur?: number;
  mandatory?: boolean;
  manual_rank?: number | null;
  measure_code: string;
  quantity: number;
  unit_cost_eur: number;
  technical_priority: number;
  coverage_weight: number;
  cost_status: string;
}

export interface StrategyResult {
  strategy: "manual" | "cheapest_first" | "optimized" | string;
  feasible?: boolean;
  selected: string[];
  selected_option_ids?: string[];
  total_cost_eur: number;
  objective_value: number;
  priority_coverage_share: number;
}

export interface SensitivityPoint {
  label?: string;
  cost_multiplier?: number;
  status?: string;
  selected_option_ids?: string[];
  budget_eur: number;
  objective_value: number;
  total_cost_eur: number;
}

export interface ScenarioResult {
  solver: string;
  solver_version: string;
  status: "OPTIMAL" | "FEASIBLE" | "INFEASIBLE" | string;
  deterministic: boolean;
  budget_eur: number;
  is_demo_budget: boolean;
  strategies: StrategyResult[];
  sensitivity: SensitivityPoint[];
  objective_definition: string;
  disclaimer: string;
  message?: string | null;
  input_hash?: string;
}

export interface Scenario {
  id: number | string;
  area_id: number | string;
  name: string;
  budget_eur: number;
  is_demo_budget: boolean;
  options: ScenarioOption[];
  result?: ScenarioResult | null;
  latest_result?: ScenarioResult | null;
  record_status?: string;
}

export interface PlanAction {
  id: number | string;
  measure_code: string;
  status: "pending" | "in_progress" | "done" | "blocked" | string;
  responsible: string | null;
  due_date: string | null;
  planned_cost_eur: number | null;
  actual_cost_eur: number | null;
  evidence_count: number;
  history: Array<Record<string, unknown>>;
}

export interface ActionPlan {
  id: number | string;
  scenario_id: number | string;
  created_at: string;
  record_status?: string;
  actions: PlanAction[];
}

export interface ChecklistQuestion {
  code: string;
  question: string;
}

export interface AuditEvent {
  id?: number | string;
  user_id?: string | null;
  entity: string;
  entity_id?: string | number;
  action: string;
  actor?: string | null;
  at: string;
  detail?: Record<string, unknown> | null;
}

export interface ImpactKpi {
  kpi_id?: string;
  label: string;
  value: number | string | null;
  unit?: string | null;
  status?: IndicatorStatus | string;
  method?: string | null;
}

export interface ImpactResponse {
  kpis: Indicator[];
  notice?: string;
}

export interface GuidedDemo {
  notice: string;
  organization: { name: string; record_status: string };
  area: AreaDetail;
  inspections: Inspection[];
  measures: Measure[];
  scenario: Scenario;
  plan: ActionPlan | null;
  report_url: string;
}
