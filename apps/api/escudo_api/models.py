"""Esquema PostGIS de ESCUDO MADRID (PRD §6.3). Dueño único: A0/A6.

Decisión ADR-0002: las tres capas oficiales (riesgo/peligrosidad/vulnerabilidad) comparten
la tabla `official_layer_polygons` con columna `layer`, en lugar de tres tablas idénticas.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from geoalchemy2 import Geometry
from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

JSONType = JSON().with_variant(JSONB(), "postgresql")


def _now() -> datetime:
    return datetime.now(UTC)


def _uuid() -> str:
    return str(uuid.uuid4())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


# ---------------------------------------------------------------- procedencia


class DataSource(Base, TimestampMixin):
    __tablename__ = "data_sources"
    source_id: Mapped[str] = mapped_column(String(16), primary_key=True)
    portal: Mapped[str] = mapped_column(String(16))
    ckan_id: Mapped[str | None] = mapped_column(String(128))
    title: Mapped[str] = mapped_column(Text)
    producer: Mapped[str] = mapped_column(Text)
    catalog_url: Mapped[str] = mapped_column(Text)
    license: Mapped[str] = mapped_column(String(64))
    spatial_scope: Mapped[str] = mapped_column(Text)
    temporal_scope: Mapped[str] = mapped_column(Text)
    use_in_product: Mapped[str] = mapped_column(Text)
    caveats: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="not_ingested")  # ok | failed | not_ingested
    versions: Mapped[list[DatasetVersion]] = relationship(back_populates="source", order_by="DatasetVersion.extracted_at")


class DatasetVersion(Base):
    __tablename__ = "dataset_versions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("data_sources.source_id"))
    resource_url: Mapped[str] = mapped_column(Text)
    file_name: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64))
    bytes: Mapped[int] = mapped_column(Integer)
    portal_modified_at: Mapped[str | None] = mapped_column(String(40))
    extracted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source: Mapped[DataSource] = relationship(back_populates="versions")
    __table_args__ = (UniqueConstraint("source_id", "sha256", name="uq_version_sha"),)


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(16))
    summary: Mapped[dict] = mapped_column(JSONType, default=dict)


class DataQualityCheck(Base):
    __tablename__ = "data_quality_checks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("ingestion_runs.id"))
    source_id: Mapped[str | None] = mapped_column(ForeignKey("data_sources.source_id"))
    check: Mapped[str] = mapped_column(String(64))
    passed: Mapped[bool] = mapped_column(Boolean)
    detail: Mapped[str] = mapped_column(Text)


class IndicatorDefinition(Base):
    """Tabla de trazabilidad por indicador (PRD §4.5)."""

    __tablename__ = "indicator_definitions"
    indicator_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    label: Mapped[str] = mapped_column(Text)
    definition: Mapped[str] = mapped_column(Text)
    unit: Mapped[str] = mapped_column(Text)
    spatial_scope: Mapped[str] = mapped_column(Text)
    source_id: Mapped[str] = mapped_column(String(16))
    update_frequency: Mapped[str] = mapped_column(Text)
    null_handling: Mapped[str] = mapped_column(Text)
    transformation: Mapped[str] = mapped_column(Text)
    caveat: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16))


# ---------------------------------------------------------------- territorio público


class Municipality(Base):
    __tablename__ = "municipalities"
    ine_code: Mapped[str] = mapped_column(String(5), primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    population_total: Mapped[int | None] = mapped_column(Integer)
    population_65_plus: Mapped[int | None] = mapped_column(Integer)
    age_65_plus_share: Mapped[float | None] = mapped_column(Float)
    population_year: Mapped[int | None] = mapped_column(Integer)
    density_hab_km2: Mapped[float | None] = mapped_column(Float)
    density_year: Mapped[int | None] = mapped_column(Integer)
    altitude_m: Mapped[float | None] = mapped_column(Float)
    altitude_year: Mapped[int | None] = mapped_column(Integer)
    area_km2: Mapped[float | None] = mapped_column(Float)
    geom = mapped_column(Geometry("MULTIPOLYGON", srid=4326, spatial_index=True), nullable=True)


class MunicipalSeries(Base):
    __tablename__ = "municipal_series"
    ine_code: Mapped[str] = mapped_column(ForeignKey("municipalities.ine_code"), primary_key=True)
    indicator_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    value: Mapped[float | None] = mapped_column(Float)
    source_id: Mapped[str] = mapped_column(String(16))


class OfficialLayerPolygon(Base):
    __tablename__ = "official_layer_polygons"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    layer: Mapped[str] = mapped_column(String(16), index=True)  # risk | hazard | vulnerability
    source_id: Mapped[str] = mapped_column(String(16))
    class_code: Mapped[str | None] = mapped_column(String(32))
    class_label: Mapped[str] = mapped_column(Text)
    geom = mapped_column(Geometry("MULTIPOLYGON", srid=4326, spatial_index=True))


class OfficialLayerMunicipalShare(Base):
    __tablename__ = "official_layer_municipal_shares"
    ine_code: Mapped[str] = mapped_column(String(5), primary_key=True)
    layer: Mapped[str] = mapped_column(String(16), primary_key=True)
    class_label: Mapped[str] = mapped_column(Text, primary_key=True)
    class_code: Mapped[str | None] = mapped_column(String(32))
    area_ha: Mapped[float] = mapped_column(Float)
    area_share: Mapped[float] = mapped_column(Float)
    source_id: Mapped[str] = mapped_column(String(16))


class SatelliteBurntArea(Base):
    """EFF-01: perímetro de área quemada de EFFIS (MODIS) que interseca la Comunidad de Madrid (atributos literales)."""

    __tablename__ = "satellite_burnt_areas"
    effis_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    source_id: Mapped[str] = mapped_column(String(16))
    fire_date: Mapped[date | None] = mapped_column(Date)
    last_update: Mapped[date | None] = mapped_column(Date)
    year: Mapped[int] = mapped_column(Integer, index=True)
    area_ha_effis: Mapped[float] = mapped_column(Float)
    area_ha_in_region: Mapped[float] = mapped_column(Float)
    commune_literal: Mapped[str | None] = mapped_column(Text)
    province_literal: Mapped[str | None] = mapped_column(Text)
    attributes: Mapped[dict] = mapped_column(JSONType, default=dict)
    geom = mapped_column(Geometry("MULTIPOLYGON", srid=4326, spatial_index=True))


class SatelliteBurntAreaMunicipality(Base):
    """Reparto DERIVADO: superficie de cada perímetro EFFIS dentro de cada municipio (intersección en EPSG:25830)."""

    __tablename__ = "satellite_burnt_area_municipalities"
    effis_id: Mapped[str] = mapped_column(ForeignKey("satellite_burnt_areas.effis_id", ondelete="CASCADE"),
                                          primary_key=True)
    ine_code: Mapped[str] = mapped_column(ForeignKey("municipalities.ine_code"), primary_key=True, index=True)
    area_ha: Mapped[float] = mapped_column(Float)


class RegionalSeries(Base):
    """Series agregadas regionales (CAM-05 incendios, CAM-06 repoblaciones, CAM-07 usos)."""

    __tablename__ = "regional_series"
    source_id: Mapped[str] = mapped_column(String(16), primary_key=True)
    concept: Mapped[str] = mapped_column(String(128), primary_key=True)
    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    value: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(16))


class ProtectedSpace(Base):
    __tablename__ = "protected_spaces"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(Text)
    figure: Mapped[str] = mapped_column(Text)
    name: Mapped[str] = mapped_column(Text)
    area_ha: Mapped[float | None] = mapped_column(Float)
    declared_on: Mapped[str | None] = mapped_column(String(16))
    norm_url: Mapped[str | None] = mapped_column(Text)
    source_id: Mapped[str] = mapped_column(String(16), default="CAM-04")


class WeatherSnapshot(Base):
    __tablename__ = "weather_snapshots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ine_code: Mapped[str] = mapped_column(String(5), index=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    status: Mapped[str] = mapped_column(String(16))
    payload: Mapped[dict] = mapped_column(JSONType)


# ---------------------------------------------------------------- organizaciones (datos privados)


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(32))  # urbanizacion | municipio | otro
    # Solo organizaciones de tipo «municipio»: término municipal sobre el que tienen competencia (Flujo B)
    municipality_code: Mapped[str | None] = mapped_column(String(5), nullable=True)
    record_status: Mapped[str] = mapped_column(String(16), default="active")  # active | synthetic


class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    full_name: Mapped[str] = mapped_column(Text)
    password_hash: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    record_status: Mapped[str] = mapped_column(String(16), default="active")
    memberships: Mapped[list[Membership]] = relationship(back_populates="user", lazy="selectin")


class Membership(Base):
    __tablename__ = "memberships"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"))
    role: Mapped[str] = mapped_column(String(32))  # gestor | tecnico | municipal | analista | admin
    technical_qualification_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    user: Mapped[User] = relationship(back_populates="memberships")
    organization: Mapped[Organization] = relationship(lazy="joined")
    __table_args__ = (UniqueConstraint("user_id", "organization_id"),)


class AreaOfInterest(Base, TimestampMixin):
    __tablename__ = "areas_of_interest"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(Text)
    municipality_code: Mapped[str] = mapped_column(ForeignKey("municipalities.ine_code"))
    description: Mapped[str] = mapped_column(Text, default="")
    geom = mapped_column(Geometry("MULTIPOLYGON", srid=4326), nullable=True)
    # Autorización EXPRESA de la organización propietaria para que el ayuntamiento del término la consulte
    shared_with_municipality: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    record_status: Mapped[str] = mapped_column(String(16), default="active")


class Inspection(Base, TimestampMixin):
    __tablename__ = "inspections"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    area_id: Mapped[str] = mapped_column(ForeignKey("areas_of_interest.id"))
    inspected_on: Mapped[date] = mapped_column(Date)
    inspector_name: Mapped[str] = mapped_column(Text)
    review_status: Mapped[str] = mapped_column(String(32), default="pending_technical_review")
    record_status: Mapped[str] = mapped_column(String(16), default="active")
    items: Mapped[list[InspectionItem]] = relationship(lazy="selectin", cascade="all, delete-orphan")
    evidence: Mapped[list[EvidenceFile]] = relationship(lazy="selectin")


class InspectionItem(Base):
    __tablename__ = "inspection_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inspection_id: Mapped[str] = mapped_column(ForeignKey("inspections.id"))
    checklist_code: Mapped[str] = mapped_column(String(64))
    answer: Mapped[str] = mapped_column(String(16))  # si | no | parcial | na
    observation: Mapped[str] = mapped_column(Text, default="")


class EvidenceFile(Base):
    __tablename__ = "evidence_files"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    inspection_id: Mapped[str | None] = mapped_column(ForeignKey("inspections.id"))
    plan_action_id: Mapped[str | None] = mapped_column(ForeignKey("plan_actions.id"))
    original_name: Mapped[str] = mapped_column(Text)
    content_type: Mapped[str] = mapped_column(String(64))
    bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    storage_key: Mapped[str] = mapped_column(Text)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    record_status: Mapped[str] = mapped_column(String(16), default="active")


class ProfessionalReview(Base):
    __tablename__ = "professional_reviews"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"))
    inspection_id: Mapped[str] = mapped_column(ForeignKey("inspections.id"))
    reviewer_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    verdict: Mapped[str] = mapped_column(String(32))  # util | inviable | redundante | requiere_revision
    note: Mapped[str] = mapped_column(Text, default="")
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class MeasureCatalog(Base):
    __tablename__ = "measures_catalog"
    code: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    unit: Mapped[str] = mapped_column(Text)
    reference_unit_cost_eur: Mapped[float | None] = mapped_column(Numeric(12, 2))
    cost_status: Mapped[str] = mapped_column(String(16))
    cost_source: Mapped[str | None] = mapped_column(Text)
    normative_refs: Mapped[list] = mapped_column(JSONType, default=list)
    prerequisites: Mapped[list] = mapped_column(JSONType, default=list)
    excludes: Mapped[list] = mapped_column(JSONType, default=list)
    requires_professional: Mapped[bool] = mapped_column(Boolean, default=True)
    extra: Mapped[dict] = mapped_column(JSONType, default=dict)


class Scenario(Base, TimestampMixin):
    __tablename__ = "scenarios"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    area_id: Mapped[str] = mapped_column(ForeignKey("areas_of_interest.id"))
    name: Mapped[str] = mapped_column(Text)
    budget_eur: Mapped[float] = mapped_column(Numeric(14, 2))
    is_demo_budget: Mapped[bool] = mapped_column(Boolean, default=True)
    record_status: Mapped[str] = mapped_column(String(16), default="active")
    options: Mapped[list[ScenarioOption]] = relationship(lazy="selectin", cascade="all, delete-orphan",
                                                         order_by="ScenarioOption.position")
    results: Mapped[list[ScenarioResultRow]] = relationship(lazy="selectin", order_by="ScenarioResultRow.solved_at")


class ScenarioOption(Base):
    __tablename__ = "scenario_options"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    scenario_id: Mapped[str] = mapped_column(ForeignKey("scenarios.id"))
    position: Mapped[int] = mapped_column(Integer)
    measure_code: Mapped[str] = mapped_column(ForeignKey("measures_catalog.code"))
    quantity: Mapped[float] = mapped_column(Float)
    unit_cost_eur: Mapped[float] = mapped_column(Numeric(12, 2))
    cost_status: Mapped[str] = mapped_column(String(16))  # reference | user_quote | scenario
    technical_priority: Mapped[int] = mapped_column(Integer)
    coverage_weight: Mapped[float] = mapped_column(Float, default=1.0)
    mandatory: Mapped[bool] = mapped_column(Boolean, default=False)
    manual_rank: Mapped[int | None] = mapped_column(Integer)


class ScenarioResultRow(Base):
    __tablename__ = "scenario_results"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scenario_id: Mapped[str] = mapped_column(ForeignKey("scenarios.id"))
    solved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    input_hash: Mapped[str] = mapped_column(String(64))
    result: Mapped[dict] = mapped_column(JSONType)


class ActionPlan(Base, TimestampMixin):
    __tablename__ = "action_plans"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    scenario_id: Mapped[str] = mapped_column(ForeignKey("scenarios.id"))
    record_status: Mapped[str] = mapped_column(String(16), default="active")
    actions: Mapped[list[PlanAction]] = relationship(lazy="selectin", order_by="PlanAction.position")


class PlanAction(Base, TimestampMixin):
    __tablename__ = "plan_actions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    plan_id: Mapped[str] = mapped_column(ForeignKey("action_plans.id"))
    position: Mapped[int] = mapped_column(Integer)
    measure_code: Mapped[str] = mapped_column(ForeignKey("measures_catalog.code"))
    status: Mapped[str] = mapped_column(String(16), default="pending")
    responsible: Mapped[str | None] = mapped_column(Text)
    due_date: Mapped[date | None] = mapped_column(Date)
    planned_cost_eur: Mapped[float] = mapped_column(Numeric(14, 2))
    actual_cost_eur: Mapped[float | None] = mapped_column(Numeric(14, 2))
    history: Mapped[list] = mapped_column(JSONType, default=list)


class DossierItem(Base):
    """M15: estado declarado por la organización de cada punto del expediente de autoprotección (INFOMA, DOC-02).

    Nunca representa aprobación ni cumplimiento verificado: solo lo que la organización declara tener.
    """

    __tablename__ = "dossier_items"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    area_id: Mapped[str] = mapped_column(ForeignKey("areas_of_interest.id"), index=True)
    item_code: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending|in_progress|available|not_applicable
    note: Mapped[str] = mapped_column(Text, default="")
    updated_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    history: Mapped[list] = mapped_column(JSONType, default=list)
    __table_args__ = (UniqueConstraint("area_id", "item_code", name="uq_dossier_area_item"),)


class Comment(Base):
    """M17: comentario o decisión sobre un ámbito, una inspección o una actuación del plan.

    Inmutable: no se edita ni se borra; una corrección es una entrada nueva (registro auditable con autor y fecha).
    """

    __tablename__ = "comments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    area_id: Mapped[str] = mapped_column(ForeignKey("areas_of_interest.id"), index=True)
    entity_type: Mapped[str] = mapped_column(String(16))  # area | inspection | plan_action
    entity_id: Mapped[str] = mapped_column(String(36), index=True)
    kind: Mapped[str] = mapped_column(String(16), default="comment")  # comment | decision
    body: Mapped[str] = mapped_column(Text)
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    author_name: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    record_status: Mapped[str] = mapped_column(String(16), default="active")


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    organization_id: Mapped[str | None] = mapped_column(String(36), index=True)
    user_id: Mapped[str | None] = mapped_column(String(36))
    action: Mapped[str] = mapped_column(String(64))
    entity: Mapped[str] = mapped_column(String(32))
    entity_id: Mapped[str] = mapped_column(String(64))
    detail: Mapped[dict] = mapped_column(JSONType, default=dict)


class Report(Base):
    __tablename__ = "reports"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[str] = mapped_column(String(36), index=True)
    scenario_id: Mapped[str] = mapped_column(ForeignKey("scenarios.id"))
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    sha256: Mapped[str] = mapped_column(String(64))
    bytes: Mapped[int] = mapped_column(Integer)
