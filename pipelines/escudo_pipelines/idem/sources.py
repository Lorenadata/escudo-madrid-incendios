"""Fuentes IDEM (Infraestructura de Datos Espaciales de la Comunidad de Madrid).

Capas del Catálogo de Riesgos Potenciales de Protección Civil (CRP-CAM), publicadas
en datos.gob.es (publicador A13002908) con descarga directa en el servidor IDEM.
Verificado el 06/11/2026: la descarga es un ZIP con un GeoTIFF uint8 de 5 m (+ .tfw),
no un SHP; licencia CC BY 4.0 Comunidad de Madrid (metadatos ISO 19139 del catálogo
GeoNetwork del IDEM), CRS EPSG:25830, escala de referencia 1:5.000. Las etiquetas de
clase proceden literalmente de la leyenda oficial del WMS (GetLegendGraphic).

Son fuentes COMPLEMENTARIAS: no sustituyen el requisito de uso del Portal CKAN de la CAM.
"""

from __future__ import annotations

from dataclasses import dataclass

from escudo_pipelines.sources import SourceSpec

IDEM_DOWNLOAD_BASE = "https://idem.comunidad.madrid/recursos_cat_geo/Catalogo/recursos/ZonasRiesgo/PCivil"
IDEM_METADATA_XML = "https://idem.comunidad.madrid/catalogocartografia/srv/api/records/{record_id}/formatters/xml"
IDEM_WMS = "https://idem.comunidad.madrid/geoidem/ZonasRiesgo/wms"
METHODOLOGY_PDF =f"{IDEM_DOWNLOAD_BASE}/CRP-CAM_MEMORIA_METODOLOGICA_NOV.2025.pdf"

_COMMON_CAVEAT = (
    "Capa oficial del Catálogo de Riesgos Potenciales de Protección Civil. Se muestran las clases "
    "literales de la fuente, sin recalcular. Escala de referencia 1:5.000; no es una evaluación de parcela "
    "ni de vivienda."
)


@dataclass(frozen=True)
class IdemLayer:
    spec: SourceSpec
    layer: str            # nombre de contrato: risk | hazard | vulnerability
    zip_name: str         # fichero en IDEM_DOWNLOAD_BASE
    metadata_record: str  # identificador GeoNetwork

    @property
    def download_url(self) -> str:
        return f"{IDEM_DOWNLOAD_BASE}/{self.zip_name}"

    @property
    def metadata_url(self) -> str:
        return IDEM_METADATA_XML.format(record_id=self.metadata_record)

    @property
    def wms_layer(self) -> str:
        return self.zip_name.removesuffix(".zip")

    @property
    def legend_url(self) -> str:
        """Leyenda oficial (GeoServer GetLegendGraphic JSON): etiquetas y colores literales."""
        return (f"{IDEM_WMS}?service=WMS&version=1.3.0&request=GetLegendGraphic"
                f"&format=application/json&layer={self.wms_layer}")

    @property
    def tif_name(self) -> str:
        return f"{self.wms_layer}.tif"


def _spec(source_id: str, slug: str, title: str, use: str) -> SourceSpec:
    return SourceSpec(
        source_id=source_id,
        portal="IDEM",
        ckan_id=None,
        title=title,
        producer="Comunidad de Madrid — Protección Civil (Catálogo de Riesgos Potenciales, IDEM)",
        catalog_url=f"https://datos.gob.es/es/catalogo/a13002908-{slug}-por-incendios-forestales",
        license="CC BY 4.0 Comunidad de Madrid",
        spatial_scope="polígonos regionales (escala 1:5.000)",
        temporal_scope="versión del catálogo (ver manifest/layers_meta)",
        use_in_product=use,
        caveats=_COMMON_CAVEAT,
        resource_format="GeoTIFF (ZIP)",
        tags=("incendios", "proteccion-civil", "inspire-zonas-riesgo"),
    )


IDEM_LAYERS: tuple[IdemLayer, ...] = (
    IdemLayer(
        spec=_spec("GEO-01", "riesgo", "Riesgo por incendios forestales",
                   "Capa de riesgo oficial y reparto de clases por municipio"),
        layer="risk", zip_name="riesgo_3_1.zip", metadata_record="spacm_riesgoiiff",
    ),
    IdemLayer(
        spec=_spec("GEO-02", "peligrosidad", "Peligrosidad por incendios forestales",
                   "Capa de peligrosidad oficial (distinta del riesgo)"),
        layer="hazard", zip_name="peligrosid_3_1.zip", metadata_record="spacm_peligroiiff",
    ),
    IdemLayer(
        spec=_spec("GEO-03", "vulnerabilidad", "Vulnerabilidad por incendios forestales",
                   "Capa de vulnerabilidad oficial (distinta de la peligrosidad)"),
        layer="vulnerability", zip_name="vulnera_3_1.zip", metadata_record="spacm_vulneraiiff",
    ),
)

IDEM_SOURCES: tuple[SourceSpec, ...] = tuple(layer.spec for layer in IDEM_LAYERS)
IDEM_BY_SOURCE: dict[str, IdemLayer] = {layer.spec.source_id: layer for layer in IDEM_LAYERS}
IDEM_BY_LAYER: dict[str, IdemLayer] = {layer.layer: layer for layer in IDEM_LAYERS}
