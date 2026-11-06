"""Registro de fuentes de datos de ESCUDO MADRID.

Única fuente de verdad sobre procedencia. Cada entrada se materializa en la tabla
`data_sources` y en `DATA_CATALOG.md`. Las URL de recursos se resuelven siempre a
través de la API CKAN del Portal (package_show) para no depender de enlaces rotos.

`portal`:
  - "CAM"   → Portal de Datos Abiertos de la Comunidad de Madrid (requisito de admisión DATAMAD)
  - "IDEM"  → Infraestructura de Datos Espaciales de la CAM / datos.gob.es (complementario)
  - "AEMET" → AEMET OpenData (complementario)
"""

from __future__ import annotations

from dataclasses import dataclass, field

CKAN_BASE = "https://datos.comunidad.madrid/api/3/action"


@dataclass(frozen=True)
class SourceSpec:
    source_id: str
    portal: str
    ckan_id: str | None
    title: str
    producer: str
    catalog_url: str
    license: str
    spatial_scope: str
    temporal_scope: str
    use_in_product: str
    caveats: str
    resource_format: str = "CSV"
    resource_name_hint: str | None = None
    tags: tuple[str, ...] = field(default_factory=tuple)


CAM_SOURCES: tuple[SourceSpec, ...] = (
    SourceSpec(
        source_id="CAM-01",
        portal="CAM",
        ckan_id="poblacion_censada_por_edad_nacionalidad_y_sexo",
        title="Población censada por edad, nacionalidad y sexo. Censo anual. Municipios",
        producer="Instituto de Estadística de la Comunidad de Madrid",
        catalog_url="https://datos.comunidad.madrid/dataset/poblacion_censada_por_edad_nacionalidad_y_sexo",
        license="CC-BY 4.0",
        spatial_scope="municipio",
        temporal_scope="serie anual",
        use_in_product="Ficha demográfica municipal: población total y proporción ≥65 años (perfil municipal)",
        caveats="Escala municipal. Nunca se reparte entre urbanizaciones ni se usa como población expuesta.",
    ),
    SourceSpec(
        source_id="CAM-02",
        portal="CAM",
        ckan_id="1930748",
        title="Densidad de población. Municipios",
        producer="Instituto de Estadística de la Comunidad de Madrid",
        catalog_url="https://datos.comunidad.madrid/dataset/1930748",
        license="CC-BY 4.0",
        spatial_scope="municipio",
        temporal_scope="serie anual",
        use_in_product="Comparador y filtro regional por densidad (hab/km²)",
        caveats="Escala municipal, no parcela.",
    ),
    SourceSpec(
        source_id="CAM-03",
        portal="CAM",
        ckan_id="101002",
        title="Altitud. Municipios",
        producer="Instituto de Estadística de la Comunidad de Madrid",
        catalog_url="https://datos.comunidad.madrid/dataset/101002",
        license="CC-BY 4.0",
        spatial_scope="municipio",
        temporal_scope="estático",
        use_in_product="Contexto de altitud del núcleo municipal",
        caveats="No sustituye un MDE; no permite calcular pendientes.",
    ),
    SourceSpec(
        source_id="CAM-04",
        portal="CAM",
        ckan_id="espacios_protegidos",
        title="Espacios protegidos",
        producer="Comunidad de Madrid",
        catalog_url="https://datos.comunidad.madrid/dataset/espacios_protegidos",
        license="CC-BY 4.0",
        spatial_scope="listado (sin geometría verificada)",
        temporal_scope="estático",
        use_in_product="Catálogo de espacios de interés ambiental",
        caveats="Recurso tabular: sin geometría no se hace cruce espacial.",
    ),
    SourceSpec(
        source_id="CAM-05",
        portal="CAM",
        ckan_id="101019",
        title="Incendios y superficie afectada",
        producer="Instituto de Estadística de la Comunidad de Madrid",
        catalog_url="https://datos.comunidad.madrid/dataset/101019",
        license="CC-BY 4.0",
        spatial_scope="según fichero (verificar)",
        temporal_scope="serie anual",
        use_in_product="Serie histórica contextual de incendios y superficie afectada",
        caveats="No atribuir granularidad municipal si el fichero es agregado.",
    ),
    SourceSpec(
        source_id="CAM-06",
        portal="CAM",
        ckan_id="repoblaciones_forestales",
        title="Repoblaciones forestales",
        producer="Comunidad de Madrid",
        catalog_url="https://datos.comunidad.madrid/dataset/repoblaciones_forestales",
        license="CC-BY 4.0",
        spatial_scope="según fichero (verificar)",
        temporal_scope="serie anual",
        use_in_product="Contexto histórico de restauración forestal",
        caveats="Puede ser serie agregada regional.",
    ),
    SourceSpec(
        source_id="CAM-07",
        portal="CAM",
        ckan_id="1101001",
        title="Distribución de la superficie por usos",
        producer="Instituto de Estadística de la Comunidad de Madrid",
        catalog_url="https://datos.comunidad.madrid/dataset/1101001",
        license="CC-BY 4.0",
        spatial_scope="según fichero (verificar)",
        temporal_scope="serie anual",
        use_in_product="Proporción de superficie forestal (arbolada, arbustiva y matorral) por ámbito",
        caveats="Uso del suelo estadístico, no cartografía de combustibles.",
    ),
    SourceSpec(
        source_id="CAM-08",
        portal="CAM",
        ckan_id="secciones_censales",
        title="Secciones censales (geometría SHP)",
        producer="Instituto de Estadística de la Comunidad de Madrid",
        catalog_url="https://datos.comunidad.madrid/dataset/secciones_censales",
        license="CC-BY 4.0",
        spatial_scope="sección censal → disuelta a municipio",
        temporal_scope="estático (versión del recurso)",
        use_in_product="Geometría de los 179 municipios (disolución de secciones por código INE)",
        caveats="Límites estadísticos; no son deslinde jurídico.",
        resource_format="SHP",
    ),
)

ALL_SOURCES: dict[str, SourceSpec] = {s.source_id: s for s in CAM_SOURCES}
