-- Base de datos de tests separada de la de desarrollo
CREATE DATABASE escudo_test OWNER escudo;
\connect escudo_test
CREATE EXTENSION IF NOT EXISTS postgis;
\connect escudo
CREATE EXTENSION IF NOT EXISTS postgis;
