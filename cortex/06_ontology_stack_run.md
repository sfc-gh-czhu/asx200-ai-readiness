# Ontology Stack Builder — ASX200_AI (full run)

Work from repo: asx200-ai-readiness. Connection: sfseapac-au_demo70.

**User pre-approves all phase gates.** Proceed through phases without waiting; use best judgment at each gate.

Invoke the **ontology-stack-builder** skill per SKILL.md.

## Inputs

- Database.Schema: AI_READINESS_DB.ASX200
- Ontology name: ASX200_AI
- Path: **KG path** (KG_NODE/KG_EDGE)
- Source tables: COMPANY, RAW_DOCUMENT, AI_GOVERNANCE_STATEMENT, ANNUAL_REPORT, HIRING_SIGNAL, ENGINEERING_BLOG, PROCUREMENT_POLICY_DOC, POLICY, BUYER, GTM_OPPORTUNITY, COMPANY_AI_PROFILE
- Graph traversal UDFs: Yes
- Inference engine: No

## Business questions

1. Which ASX 200 companies have permissive vs governed AI policy posture?
2. Which companies have the highest developer density and most AI/ML hiring?
3. For company {name}, what is the clear entry point and which buyer for AI conversations?
4. Top GTM opportunities by priority tier with evidence?
5. Financial-sector companies governed but high developer density?
6. Companies with new AI governance statements in last 12 months?
7. Buyers flagged as entry points for AI governance enablement?

## Ontology intent

- Company hub → Policy, Buyer, GTMOpportunity
- Evidence: GovernanceStatement, AnnualReport, HiringSignal, EngineeringBlog, ProcurementPolicyDoc
- Signals: permissive/governed, developer density tier, clear entry point

## Execute

Run Phases 1–7 as far as automation allows. Deploy SQL in Phase 4 after review. Create semantic views (Phases 4.5–5) and Cortex Agent ASX200_AI (Phase 6). Validate (Phase 7).

Summarize deployed objects at end.
