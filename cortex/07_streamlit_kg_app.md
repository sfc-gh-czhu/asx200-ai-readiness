# Streamlit-in-Snowflake: ASX200_AI Knowledge Graph Explorer

Connection: sfseapac-au_demo70. Role ACCOUNTADMIN. Schema: AI_READINESS_DB.ASX200.

**User pre-approves all steps.** Proceed without waiting; use best judgment.

Use the **developing-with-streamlit-in-snowflake** skill for deployment mechanics
(stage, PUT, CREATE STREAMLIT). Deploy a Streamlit-in-Snowflake (SiS) app that
explores the ASX200_AI knowledge graph and AI-readiness signals.

## Goal

Deploy SiS app `AI_READINESS_DB.ASX200.ASX200_AI_EXPLORER` that runs inside
Snowflake (uses `snowflake.snowpark.context.get_active_session()`), backed by the
KG tables, concrete views, and graph UDFs already deployed.

## Hard constraints

- ONLY use packages available in the Snowflake Anaconda channel:
  `streamlit`, `pandas`, and `graphviz` (for network rendering via
  `st.graphviz_chart`). Do NOT use `streamlit-agraph`, `pyvis`, or `networkx`
  drawing backends — they are not in the Snowflake channel.
- Use `get_active_session()`; never open a new connector. Use
  `session.sql(...).to_pandas()` for queries.
- Wrap data reads in `@st.cache_data(ttl=600)` functions.
- Quote/parametrize the selected node id when calling UDFs to avoid SQL injection.

## Known schema (already deployed — verify before use)

Tables:
- `KG_NODE(NODE_ID, NODE_TYPE, NAME, PROPS VARIANT, TS_INGESTED)` — 1,607 rows, 11 node types
- `KG_EDGE(EDGE_ID, SRC_ID, DST_ID, EDGE_TYPE, WEIGHT, PROPS, ...)` — 1,445 rows, 12 edge types

Views:
- `V_COMPANY(NODE_ID, NAME, ASX_TICKER, COMPANY_NAME, GICS_SECTOR, GICS_INDUSTRY, MARKET_CAP_AUD, HQ_CITY, HQ_COUNTRY, EMPLOYEE_COUNT, ...)`
- `V_COMPANY_COMPLETE` — Company joined with AI profile (AI_POLICY_POSTURE, DEVELOPER_DENSITY_TIER, CLEAR_ENTRY_POINT, ENTRY_POINT_FUNCTION, ...)
- `V_POLICY`, `V_BUYER`, `V_GTM_OPPORTUNITY`, `V_HIRING_SIGNAL`,
  `V_GOVERNANCE_STATEMENT`, `V_ANNUAL_REPORT`, `V_ENGINEERING_BLOG`,
  `V_PROCUREMENT_POLICY_DOC`, `V_DOCUMENT`
- `REL_RESOLVED` — edges joined to node names (SRC_NAME, DST_NAME, EDGE_TYPE, ...)

Graph UDFs (table functions):
- `GET_DIRECT_CHILDREN_TOOL(PARENT_NODE_ID STRING) -> (CHILD_ID, CHILD_NAME, CHILD_TYPE, EDGE_TYPE)`
- `EXPAND_DESCENDANTS_TOOL(...)`, `GET_ANCESTORS_TOOL(...)`, `GET_HIERARCHY_PATH_TOOL(...)`

Semantic view: `ASX200_AI_BASE` (for reference; app uses views/UDFs directly).

> Run `DESCRIBE`/`SHOW COLUMNS` to confirm exact column names before generating
> the app code; adjust SQL to actual columns.

## App layout

Page config: wide layout, title "ASX 200 AI-Readiness — Knowledge Graph Explorer".

**Header KG stats** (metrics row): total nodes, total edges, distinct node types,
distinct companies. Plus a small table of node counts by `NODE_TYPE`.

**Sidebar**:
- Company selector: `SELECT NODE_ID, COMPANY_NAME, ASX_TICKER FROM V_COMPANY ORDER BY COMPANY_NAME` (label = `COMPANY_NAME (ASX_TICKER)`).
- Posture filter (multiselect): governed / unknown / permissive.
- Sector filter (multiselect) from `GICS_SECTOR`.

**Tabs**:

1. **Company Graph** — for the selected company:
   - Profile card: posture, developer density tier, clear entry point, entry-point function, sector, market cap (from `V_COMPANY_COMPLETE`).
   - Ego graph: call `GET_DIRECT_CHILDREN_TOOL(<selected NODE_ID>)`; render a
     graphviz digraph with the company as the central node and children colored
     by `CHILD_TYPE`, edges labeled by `EDGE_TYPE`. Use `st.graphviz_chart`.
   - Table of the children below the graph.

2. **Policy Posture** — bar chart of company count by `AI_POLICY_POSTURE`
   (from `V_COMPANY_COMPLETE`), plus filterable table. Answers BQ1.

3. **Developer Density & Hiring** — companies ranked by hiring signals
   (`V_HIRING_SIGNAL` joined to company name): show TOTAL_OPEN_ROLES,
   ENGINEERING_ROLES, AI_ML_ROLES, DEVELOPER_DENSITY_TIER. Answers BQ2.

4. **GTM Opportunities** — `V_GTM_OPPORTUNITY` joined to company name, grouped by
   `PRIORITY_TIER` (P1/P2/...), with PLAY_TYPE, RATIONALE, RECOMMENDED_ENTRY_POINT.
   Answers BQ4.

5. **KG Browser** — node-type picker → list nodes of that type; pick a node →
   show its edges from `REL_RESOLVED` (both directions) and a small graphviz
   neighborhood.

Use `st.dataframe(use_container_width=True)` for tables and `st.bar_chart` for charts.

## Deploy steps

1. Confirm warehouse is available (prefer a STARTED one, e.g. `SNOW_INTELLIGENCE_DEMO_WH` or resume `COMPUTE_WH`).
2. Create a stage if needed: `CREATE STAGE IF NOT EXISTS AI_READINESS_DB.ASX200.STREAMLIT_STAGE`.
3. Write `streamlit_app.py` and an `environment.yml` declaring channel
   `snowflake` and dependencies `streamlit`, `pandas`, `graphviz`.
4. PUT both files to the stage (AUTO_COMPRESS=FALSE, OVERWRITE=TRUE).
5. `CREATE OR REPLACE STREAMLIT AI_READINESS_DB.ASX200.ASX200_AI_EXPLORER
     ROOT_LOCATION='@AI_READINESS_DB.ASX200.STREAMLIT_STAGE'
     MAIN_FILE='streamlit_app.py'
     QUERY_WAREHOUSE='<warehouse>';`
6. Smoke test: run each tab's underlying SQL once to confirm no errors; verify the
   UDF call returns rows for a known company (e.g. CBA).
7. Save the final `streamlit_app.py` and `environment.yml` into the repo at
   `streamlit/` so they are version-controlled.

## Report at end

- Streamlit object name + Snowsight URL (or `SHOW STREAMLITS` row).
- Warehouse used.
- Any columns that differed from the assumed schema and how the SQL was adjusted.
