# Ontology Stack Builder — Phase 1 inputs (ASX 200 AI Readiness)

Use the **ontology-stack-builder** skill. Follow SKILL.md gates; stop after Phase 1 gate for user confirmation.

## Inputs

- **Database.Schema**: AI_READINESS_DB.ASX200
- **Ontology name**: ASX200_AI
- **Path**: Yes — KG path (KG_NODE/KG_EDGE)
- **Source tables**:
  COMPANY, RAW_DOCUMENT, AI_GOVERNANCE_STATEMENT, ANNUAL_REPORT, HIRING_SIGNAL,
  ENGINEERING_BLOG, PROCUREMENT_POLICY_DOC, POLICY, BUYER, GTM_OPPORTUNITY, COMPANY_AI_PROFILE

## Business questions (seller / GTM)

1. Which ASX 200 companies have permissive vs governed AI policy posture?
2. Which companies have the highest developer density and most AI/ML hiring?
3. For company {name}, what is the clear entry point and which buyer should I contact for AI conversations?
4. What are top GTM opportunities by priority tier and what evidence supports each?
5. Which financial-sector companies are governed but have high developer density?
6. Which companies published a new AI governance statement in the last 12 months?
7. Which buyers are flagged as entry points for AI governance enablement plays?

## Ontology design intent

- **Company** hub connects to **Policy**, **Buyer**, **GTMOpportunity**
- Evidence: GovernanceStatement, AnnualReport, HiringSignal, EngineeringBlog, ProcurementPolicyDoc
- Seller signals: permissive vs governed (Policy), developer density (HiringSignal), clear entry point (Buyer + GTMOpportunity)

## Phase 4 options (note for later)

- Graph traversal UDFs: Yes
- Inference engine: optional

Collect inputs, discover existing semantic views, present Phase 1 summary, then STOP at the Phase 1 gate.
