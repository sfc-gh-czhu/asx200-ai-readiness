# ASX 200 AI-Readiness Knowledge Graph

Seller-focused AI readiness knowledge graph for S&P/ASX 200 companies. Built in two parts:

1. **Part A (this folder)** — Ingestion pipeline: company list, crawl, Cortex extraction → source tables in `AI_READINESS_DB.ASX200`
2. **Part B** — `ontology-stack-builder` skill (KG path, ontology `ASX200_AI`) over those tables

## Snowflake target

- Database: `AI_READINESS_DB`
- Schema: `ASX200`
- Connection: `sfseapac-au_demo70` (Cortex default)

## Cortex Code for Snowflake

Use Cortex Code (not raw `snow sql`) for DDL, validation, and later ontology phases:

```bash
cd /Users/czhu/Documents/GitHub/cortex-code-skills

# 1) Bootstrap DB/schema + deploy DDL (after IP/network policy allows access)
cortex -p "$(cat projects/asx200-ai-readiness/cortex/01_bootstrap_snowflake.md)" \
  -c sfseapac-au_demo70 --output-format stream-json --bypass

# 2) Validate source data before ontology skill
cortex -p "$(cat projects/asx200-ai-readiness/cortex/02_validate_source_tables.md)" \
  -c sfseapac-au_demo70 --output-format stream-json --bypass

# 3) Start ontology-stack-builder (Phase 1 inputs)
cortex -p "$(cat projects/asx200-ai-readiness/cortex/03_ontology_stack_builder_phase1.md)" \
  -c sfseapac-au_demo70
```

### IP / network policy

If you see: `Incoming request with IP ... is not allowed to access Snowflake`, ask your account admin to allowlist your IP on `sfseapac-au_demo70`, or connect via corporate VPN, then re-run the commands above.

## Local pipeline (no Snowflake required)

```bash
cd projects/asx200-ai-readiness
uv sync
uv run python scripts/get_asx200_list.py
uv run python scripts/load_snowflake.py --dry-run   # prints row counts
uv run python scripts/load_snowflake.py            # needs Snowflake access
```

## Project layout

```
sql/           DDL and Cortex extraction SQL
scripts/       Python ingestion
data/          Generated CSV/JSON (gitignored)
cortex/        Headless Cortex prompts
```
