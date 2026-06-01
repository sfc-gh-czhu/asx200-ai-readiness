# ASX 200 AI-Readiness Knowledge Graph

Seller-focused AI readiness knowledge graph for S&P/ASX 200 companies.

**Repo:** [sfc-gh-czhu/asx200-ai-readiness](https://github.com/sfc-gh-czhu/asx200-ai-readiness)

## Architecture

1. **Part A (this repo)** — Ingestion: company list, URL enrichment, crawl → `RAW_DOCUMENT`, Cortex extraction → source tables in `AI_READINESS_DB.ASX200`
2. **Part B** — [ontology-stack-builder](https://github.com/Snowflake-Labs/cortex-code-skills/tree/main/skills/ontology-stack-builder) skill (KG path, ontology `ASX200_AI`) over those tables. Interactive 7-phase workflow via Cortex Code.

## Snowflake target

| Setting | Value |
|---------|--------|
| Database | `AI_READINESS_DB` |
| Schema | `ASX200` |
| Connection | `sfseapac-au_demo70` |

## Quick start (local)

```bash
cd asx200-ai-readiness
uv sync
uv run python scripts/get_asx200_list.py
uv run python scripts/enrich_company_urls.py --pilot
uv run python scripts/crawl_documents.py --pilot
uv run python scripts/load_raw_to_snowflake.py --jsonl data/raw_documents.jsonl
```

## Cortex Code (Snowflake)

Run from **this repo root**:

```bash
cd asx200-ai-readiness

# Validate source tables
cortex -p "$(cat cortex/02_validate_source_tables.md)" \
  -c sfseapac-au_demo70 --output-format stream-json --bypass

# Bootstrap (first-time only)
cortex -p "$(cat cortex/01_bootstrap_snowflake.md)" \
  -c sfseapac-au_demo70 --output-format stream-json --bypass

# Pilot extraction + validation
cortex -p "$(cat cortex/04_extract_and_validate_pilot.md)" \
  -c sfseapac-au_demo70 --output-format stream-json --bypass

# Ontology stack builder — Phase 1 (interactive; follow skill gates)
cortex -p "$(cat cortex/03_ontology_stack_builder_phase1.md)" \
  -c sfseapac-au_demo70
```

Requires Cortex Code with `ontology-stack-builder` skill available (bundled or installed from Snowflake-Labs).

### Network policy

If Snowflake rejects your IP, use VPN or ask admin to allowlist, then retry.

## Project layout

```
sql/           DDL and Cortex extraction SQL
scripts/       Python ingestion (list, enrich, crawl, load)
data/          company.csv + generated crawl outputs (gitignored where noted)
cortex/        Headless Cortex prompts
```

## Pilot companies (10)

CBA, BHP, CSL, XRO, TLS, WOW, MQG, WTC, QAN, COH — see `scripts/pilot_tickers.py`.
