-- Gerado por split_schema_dump.py — NÃO editar manualmente; regenere a partir do dump.
-- Fase: 01_extensions_schemas.sql
-- Execução: ver README.md e run_rebuild.sh

--
-- Name: timescaledb; Type: EXTENSION; Schema: -; Owner: -
--


CREATE EXTENSION IF NOT EXISTS timescaledb WITH SCHEMA public;


--
-- Name: analytics_analytics; Type: SCHEMA; Schema: -; Owner: admin
--


CREATE SCHEMA analytics_analytics;


ALTER SCHEMA analytics_analytics OWNER TO admin;

--
-- Name: pg_cron; Type: EXTENSION; Schema: -; Owner: -
--


CREATE EXTENSION IF NOT EXISTS pg_cron WITH SCHEMA pg_catalog;


--
-- Name: topology; Type: SCHEMA; Schema: -; Owner: admin
--


CREATE SCHEMA topology;


ALTER SCHEMA topology OWNER TO admin;

--
-- Name: address_standardizer; Type: EXTENSION; Schema: -; Owner: -
--


CREATE EXTENSION IF NOT EXISTS address_standardizer WITH SCHEMA public;


--
-- Name: citext; Type: EXTENSION; Schema: -; Owner: -
--


CREATE EXTENSION IF NOT EXISTS citext WITH SCHEMA public;


--
-- Name: fuzzystrmatch; Type: EXTENSION; Schema: -; Owner: -
--


CREATE EXTENSION IF NOT EXISTS fuzzystrmatch WITH SCHEMA public;


--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--


CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: postgis; Type: EXTENSION; Schema: -; Owner: -
--


CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;


--
-- Name: postgis_topology; Type: EXTENSION; Schema: -; Owner: -
--


CREATE EXTENSION IF NOT EXISTS postgis_topology WITH SCHEMA topology;


