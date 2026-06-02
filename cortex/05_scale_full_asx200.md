# Scale ASX 200: extract signals for all crawled documents

Connection: sfseapac-au_demo70. Use role ACCOUNTADMIN if needed.

## Context

- Pilot (10 tickers) already extracted into seller tables.
- RAW_DOCUMENT may now include ~190 additional companies from scale crawl.
- SQL file: `sql/03_extract_signals.sql` (uses mistral-large2, incremental via NOT EXISTS on STG_DOC_EXTRACT).

## Steps

1. Report RAW_DOCUMENT totals: COUNT(*), COUNT(DISTINCT COMPANY_ID), FETCH_STATUS breakdown.

2. Run `sql/03_extract_signals.sql` incrementally (only new DOC_IDs not in STG_DOC_EXTRACT).

3. Re-run downstream INSERT sections from that file for new extractions only (or full file if idempotent INSERTs with NOT EXISTS).

4. Re-run COMPANY_AI_PROFILE MERGE.

5. Report final counts for: RAW_DOCUMENT, POLICY, BUYER, GTM_OPPORTUNITY, HIRING_SIGNAL, COMPANY_AI_PROFILE.

6. POSTURE distribution across all companies with POLICY rows.

Do not start ontology-stack-builder in this session.
