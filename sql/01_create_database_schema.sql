-- ASX 200 AI-Readiness: database and schema
-- Run via Cortex Code: projects/asx200-ai-readiness/cortex/01_bootstrap_snowflake.md

CREATE DATABASE IF NOT EXISTS AI_READINESS_DB
  COMMENT = 'ASX 200 AI-readiness knowledge graph — seller GTM targeting';

CREATE SCHEMA IF NOT EXISTS AI_READINESS_DB.ASX200
  COMMENT = 'Source tables + ontology artifacts for ASX200_AI';

USE DATABASE AI_READINESS_DB;
USE SCHEMA ASX200;
