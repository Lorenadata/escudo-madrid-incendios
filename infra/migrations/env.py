"""Entorno Alembic: usa DATABASE_URL de escudo_api.config y los modelos como metadata."""
from alembic import context
from sqlalchemy import engine_from_config, pool, text

from escudo_api import models  # noqa: F401  (registra tablas)
from escudo_api.config import settings
from escudo_api.db import Base

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)
target_metadata = Base.metadata


def include_object(obj, name, type_, reflected, compare_to):
    # tablas internas de PostGIS/tiger
    return not (type_ == "table" and reflected and compare_to is None)


def run_migrations_online() -> None:
    connectable = engine_from_config(config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.",
                                     poolclass=pool.NullPool)
    with connectable.connect() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS unaccent"))
        connection.commit()
        context.configure(connection=connection, target_metadata=target_metadata, include_object=include_object)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
