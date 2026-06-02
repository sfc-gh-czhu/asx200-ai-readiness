# Extract signals (pilot) and validate seller tables

Connection: sfseapac-au_demo70. Schema: AI_READINESS_DB.ASX200.

## Steps

1. Confirm RAW_DOCUMENT has rows with FETCH_STATUS='ok' for pilot tickers:
   CBA.AX, BHP.AX, CSL.AX, XRO.AX, TLS.AX, WOW.AX, MQG.AX, WTC.AX, QAN.AX, COH.AX

2. Execute SQL from repo file `sql/03_extract_signals.sql` in order (may take several minutes due to AI_COMPLETE per document).

3. If AI_PARSE_JSON or model errors, note the error and try `snowflake-arctic` or account-default Cortex model.

4. Report for pilot companies only:
   - RAW_DOCUMENT count by FETCH_STATUS and DIMENSION
   - POLICY posture distribution
   - HIRING_SIGNAL developer_density_tier distribution
   - BUYER count where IS_ENTRY_POINT = TRUE
   - GTM_OPPORTUNITY count by PRIORITY_TIER
   - COMPANY_AI_PROFILE rows for pilot COMPANY_IDs

5. Flag any pilot company missing all of POLICY, HIRING_SIGNAL, GTM_OPPORTUNITY.

Do not start ontology-stack-builder until extraction summary is printed.
