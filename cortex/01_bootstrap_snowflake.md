# Bootstrap AI_READINESS_DB.ASX200

Connection: sfseapac-au_demo70. Role: ACCOUNTADMIN if needed. Warehouse: COMPUTE_WH.

## Steps

1. Run connectivity check:
   ```sql
   SELECT CURRENT_ACCOUNT(), CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE();
   ```

2. Execute SQL files in order from the repo (read and run each file with sql_execute):
   - `projects/asx200-ai-readiness/sql/01_create_database_schema.sql`
   - `projects/asx200-ai-readiness/sql/02_create_source_tables.sql`

3. Verify:
   ```sql
   SHOW TABLES IN SCHEMA AI_READINESS_DB.ASX200;
   ```

4. Report: tables created, row counts (all zero expected), and confirm ready for COMPANY load.

Do not start ontology-stack-builder in this session.
