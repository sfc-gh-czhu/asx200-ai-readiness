"""
ASX 200 AI-Readiness — Knowledge Graph Explorer
Streamlit-in-Snowflake application backed by the ASX200_AI knowledge graph.
"""

import streamlit as st
import pandas as pd
import graphviz

from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="ASX 200 AI-Readiness — Knowledge Graph Explorer", layout="wide")

session = get_active_session()


# ---------------------------------------------------------------------------
# Data helpers (cached)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_kg_stats():
    return session.sql("""
        SELECT
            (SELECT COUNT(*) FROM AI_READINESS_DB.ASX200.KG_NODE) AS TOTAL_NODES,
            (SELECT COUNT(*) FROM AI_READINESS_DB.ASX200.KG_EDGE) AS TOTAL_EDGES,
            (SELECT COUNT(DISTINCT NODE_TYPE) FROM AI_READINESS_DB.ASX200.KG_NODE) AS DISTINCT_NODE_TYPES,
            (SELECT COUNT(*) FROM AI_READINESS_DB.ASX200.V_COMPANY) AS DISTINCT_COMPANIES
    """).to_pandas()


@st.cache_data(ttl=600)
def get_node_type_counts():
    return session.sql("""
        SELECT NODE_TYPE, COUNT(*) AS NODE_COUNT
        FROM AI_READINESS_DB.ASX200.KG_NODE
        GROUP BY NODE_TYPE
        ORDER BY NODE_COUNT DESC
    """).to_pandas()


@st.cache_data(ttl=600)
def get_companies():
    return session.sql("""
        SELECT COMPANY_ID, COMPANY_NAME, ASX_TICKER
        FROM AI_READINESS_DB.ASX200.V_COMPANY
        ORDER BY COMPANY_NAME
    """).to_pandas()


@st.cache_data(ttl=600)
def get_company_complete():
    return session.sql("""
        SELECT COMPANY_ID, COMPANY_NAME, ASX_TICKER, GICS_SECTOR, GICS_INDUSTRY,
               MARKET_CAP_AUD, EMPLOYEE_COUNT, AI_POLICY_POSTURE,
               DEVELOPER_DENSITY_TIER, AI_READINESS_SCORE,
               CLEAR_ENTRY_POINT, ENTRY_POINT_FUNCTION
        FROM AI_READINESS_DB.ASX200.V_COMPANY_COMPLETE
    """).to_pandas()


@st.cache_data(ttl=600)
def get_direct_children(node_id: str):
    safe_id = node_id.replace("'", "''")
    return session.sql(f"""
        SELECT * FROM TABLE(AI_READINESS_DB.ASX200.GET_DIRECT_CHILDREN_TOOL('{safe_id}'))
    """).to_pandas()


@st.cache_data(ttl=600)
def get_hiring_signals():
    return session.sql("""
        SELECT h.COMPANY_ID, c.COMPANY_NAME, c.ASX_TICKER,
               h.TOTAL_OPEN_ROLES, h.ENGINEERING_ROLES, h.AI_ML_ROLES,
               h.DEVELOPER_DENSITY_SCORE, h.DEVELOPER_DENSITY_TIER
        FROM AI_READINESS_DB.ASX200.V_HIRING_SIGNAL h
        JOIN AI_READINESS_DB.ASX200.V_COMPANY c ON c.COMPANY_ID = h.COMPANY_ID
        ORDER BY h.AI_ML_ROLES DESC NULLS LAST
    """).to_pandas()


@st.cache_data(ttl=600)
def get_gtm_opportunities():
    return session.sql("""
        SELECT g.OPPORTUNITY_ID, g.COMPANY_ID, c.COMPANY_NAME, c.ASX_TICKER,
               g.PLAY_TYPE, g.PLAY_TYPE_LABEL, g.PRIORITY_TIER,
               g.RATIONALE, g.RECOMMENDED_ENTRY_POINT, g.EST_DEAL_BAND
        FROM AI_READINESS_DB.ASX200.V_GTM_OPPORTUNITY g
        JOIN AI_READINESS_DB.ASX200.V_COMPANY c ON c.COMPANY_ID = g.COMPANY_ID
        ORDER BY g.PRIORITY_TIER, c.COMPANY_NAME
    """).to_pandas()


@st.cache_data(ttl=600)
def get_node_types():
    return session.sql("""
        SELECT DISTINCT NODE_TYPE FROM AI_READINESS_DB.ASX200.KG_NODE ORDER BY NODE_TYPE
    """).to_pandas()


@st.cache_data(ttl=600)
def get_nodes_by_type(node_type: str):
    safe_type = node_type.replace("'", "''")
    return session.sql(f"""
        SELECT NODE_ID, NAME, NODE_TYPE
        FROM AI_READINESS_DB.ASX200.KG_NODE
        WHERE NODE_TYPE = '{safe_type}'
        ORDER BY NAME
    """).to_pandas()


@st.cache_data(ttl=600)
def get_edges_for_node(node_id: str):
    safe_id = node_id.replace("'", "''")
    return session.sql(f"""
        SELECT EDGE_ID, SRC_ID, SRC_NAME, SRC_TYPE, EDGE_TYPE,
               DST_ID, DST_NAME, DST_TYPE, WEIGHT
        FROM AI_READINESS_DB.ASX200.REL_RESOLVED
        WHERE SRC_ID = '{safe_id}' OR DST_ID = '{safe_id}'
        ORDER BY EDGE_TYPE, SRC_NAME, DST_NAME
    """).to_pandas()


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("ASX 200 AI-Readiness — Knowledge Graph Explorer")

stats = get_kg_stats()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Nodes", int(stats["TOTAL_NODES"].iloc[0]))
c2.metric("Total Edges", int(stats["TOTAL_EDGES"].iloc[0]))
c3.metric("Node Types", int(stats["DISTINCT_NODE_TYPES"].iloc[0]))
c4.metric("Companies", int(stats["DISTINCT_COMPANIES"].iloc[0]))

with st.expander("Node counts by type"):
    st.dataframe(get_node_type_counts(), use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------

companies_df = get_companies()
company_complete_df = get_company_complete()

st.sidebar.header("Filters")

# Company selector
company_labels = (companies_df["COMPANY_NAME"] + " (" + companies_df["ASX_TICKER"].fillna("") + ")").tolist()
company_ids = companies_df["COMPANY_ID"].tolist()
selected_idx = st.sidebar.selectbox("Select Company", range(len(company_labels)),
                                    format_func=lambda i: company_labels[i])
selected_company_id = company_ids[selected_idx]

# Posture filter
postures = sorted(company_complete_df["AI_POLICY_POSTURE"].dropna().unique().tolist())
selected_postures = st.sidebar.multiselect("AI Policy Posture", postures, default=postures)

# Sector filter
sectors = sorted(company_complete_df["GICS_SECTOR"].dropna().unique().tolist())
selected_sectors = st.sidebar.multiselect("GICS Sector", sectors, default=sectors)

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Company Graph", "Policy Posture", "Developer Density & Hiring",
    "GTM Opportunities", "KG Browser"
])

# -- Tab 1: Company Graph --------------------------------------------------

with tab1:
    company_row = company_complete_df[company_complete_df["COMPANY_ID"] == selected_company_id]
    if not company_row.empty:
        row = company_row.iloc[0]
        st.subheader(f"{row['COMPANY_NAME']} ({row['ASX_TICKER']})")

        pc1, pc2, pc3 = st.columns(3)
        pc1.markdown(f"**Sector:** {row['GICS_SECTOR']}")
        pc1.markdown(f"**Industry:** {row['GICS_INDUSTRY']}")
        pc2.markdown(f"**AI Policy Posture:** {row['AI_POLICY_POSTURE']}")
        pc2.markdown(f"**Developer Density Tier:** {row['DEVELOPER_DENSITY_TIER']}")
        pc3.markdown(f"**Clear Entry Point:** {row['CLEAR_ENTRY_POINT']}")
        pc3.markdown(f"**Entry Point Function:** {row['ENTRY_POINT_FUNCTION']}")

        mcap = row['MARKET_CAP_AUD']
        emp = row['EMPLOYEE_COUNT']
        score = row['AI_READINESS_SCORE']
        m1, m2, m3 = st.columns(3)
        m1.metric("Market Cap (AUD)", f"${mcap:,.0f}" if pd.notna(mcap) else "N/A")
        m2.metric("Employees", f"{int(emp):,}" if pd.notna(emp) else "N/A")
        m3.metric("AI Readiness Score", f"{score}" if pd.notna(score) else "N/A")
    else:
        st.info("Select a company from the sidebar.")

    st.subheader("Ego Graph (Direct Children)")
    children_df = get_direct_children(selected_company_id)

    if not children_df.empty:
        # Color map for node types
        type_colors = {
            "COMPANY": "#29B5E8",
            "HIRING_SIGNAL": "#FF6B6B",
            "GTM_OPPORTUNITY": "#4ECDC4",
            "POLICY": "#45B7D1",
            "BUYER": "#96CEB4",
            "GOVERNANCE_STATEMENT": "#FFEAA7",
            "ANNUAL_REPORT": "#DDA0DD",
            "ENGINEERING_BLOG": "#98D8C8",
            "PROCUREMENT_POLICY_DOC": "#F7DC6F",
            "DOCUMENT": "#BB8FCE",
        }

        dot = graphviz.Digraph(comment="Ego Graph")
        dot.attr(rankdir="LR", bgcolor="transparent")
        dot.attr("node", style="filled", fontsize="10")

        # Central node
        company_name = companies_df[companies_df["COMPANY_ID"] == selected_company_id]["COMPANY_NAME"].iloc[0]
        dot.node(selected_company_id, company_name, fillcolor="#29B5E8", fontcolor="white", shape="box")

        # Children
        for _, child in children_df.iterrows():
            color = type_colors.get(child["CHILD_TYPE"], "#CCCCCC")
            label = str(child["CHILD_NAME"])[:30] if pd.notna(child["CHILD_NAME"]) else child["CHILD_ID"][:15]
            dot.node(child["CHILD_ID"], label, fillcolor=color)
            dot.edge(selected_company_id, child["CHILD_ID"], label=child["EDGE_TYPE"], fontsize="8")

        st.graphviz_chart(dot, use_container_width=True)
        st.dataframe(children_df, use_container_width=True, hide_index=True)
    else:
        st.info("No direct children found for this company node.")

# -- Tab 2: Policy Posture -------------------------------------------------

with tab2:
    st.subheader("AI Policy Posture Distribution")

    filtered_posture = company_complete_df[
        (company_complete_df["AI_POLICY_POSTURE"].isin(selected_postures)) &
        (company_complete_df["GICS_SECTOR"].isin(selected_sectors))
    ]

    posture_counts = filtered_posture.groupby("AI_POLICY_POSTURE").size().reset_index(name="COUNT")
    if not posture_counts.empty:
        st.bar_chart(posture_counts.set_index("AI_POLICY_POSTURE")["COUNT"])
    else:
        st.info("No data for selected filters.")

    st.subheader("Companies by Posture")
    display_cols = ["COMPANY_NAME", "ASX_TICKER", "GICS_SECTOR", "AI_POLICY_POSTURE",
                    "DEVELOPER_DENSITY_TIER", "AI_READINESS_SCORE"]
    st.dataframe(
        filtered_posture[display_cols].sort_values("AI_POLICY_POSTURE"),
        use_container_width=True, hide_index=True
    )

# -- Tab 3: Developer Density & Hiring -------------------------------------

with tab3:
    st.subheader("Developer Density & Hiring Signals")

    hiring_df = get_hiring_signals()
    # Filter by selected sectors/postures via company_complete
    valid_ids = company_complete_df[
        (company_complete_df["AI_POLICY_POSTURE"].isin(selected_postures)) &
        (company_complete_df["GICS_SECTOR"].isin(selected_sectors))
    ]["COMPANY_ID"]
    hiring_filtered = hiring_df[hiring_df["COMPANY_ID"].isin(valid_ids)]

    if not hiring_filtered.empty:
        st.dataframe(
            hiring_filtered[["COMPANY_NAME", "ASX_TICKER", "TOTAL_OPEN_ROLES",
                             "ENGINEERING_ROLES", "AI_ML_ROLES",
                             "DEVELOPER_DENSITY_SCORE", "DEVELOPER_DENSITY_TIER"]],
            use_container_width=True, hide_index=True
        )
    else:
        st.info("No hiring signal data for the selected filters.")

# -- Tab 4: GTM Opportunities ----------------------------------------------

with tab4:
    st.subheader("GTM Opportunities")

    gtm_df = get_gtm_opportunities()
    valid_ids_gtm = company_complete_df[
        (company_complete_df["AI_POLICY_POSTURE"].isin(selected_postures)) &
        (company_complete_df["GICS_SECTOR"].isin(selected_sectors))
    ]["COMPANY_ID"]
    gtm_filtered = gtm_df[gtm_df["COMPANY_ID"].isin(valid_ids_gtm)]

    if not gtm_filtered.empty:
        # Summary by priority tier
        tier_counts = gtm_filtered.groupby("PRIORITY_TIER").size().reset_index(name="COUNT")
        st.bar_chart(tier_counts.set_index("PRIORITY_TIER")["COUNT"])

        # Filter by priority tier
        tiers = sorted(gtm_filtered["PRIORITY_TIER"].dropna().unique().tolist())
        selected_tier = st.selectbox("Filter by Priority Tier", ["All"] + tiers)

        display_gtm = gtm_filtered if selected_tier == "All" else gtm_filtered[gtm_filtered["PRIORITY_TIER"] == selected_tier]
        st.dataframe(
            display_gtm[["COMPANY_NAME", "ASX_TICKER", "PRIORITY_TIER", "PLAY_TYPE",
                         "PLAY_TYPE_LABEL", "RATIONALE", "RECOMMENDED_ENTRY_POINT", "EST_DEAL_BAND"]],
            use_container_width=True, hide_index=True
        )
    else:
        st.info("No GTM opportunity data for the selected filters.")

# -- Tab 5: KG Browser -----------------------------------------------------

with tab5:
    st.subheader("Knowledge Graph Browser")

    node_types_df = get_node_types()
    type_list = node_types_df["NODE_TYPE"].tolist()
    selected_type = st.selectbox("Select Node Type", type_list)

    nodes_df = get_nodes_by_type(selected_type)
    st.write(f"**{len(nodes_df)} nodes** of type `{selected_type}`")

    if not nodes_df.empty:
        node_labels = nodes_df["NAME"].fillna(nodes_df["NODE_ID"]).tolist()
        node_ids = nodes_df["NODE_ID"].tolist()
        selected_node_idx = st.selectbox("Select Node", range(len(node_labels)),
                                         format_func=lambda i: node_labels[i])
        selected_node_id = node_ids[selected_node_idx]

        st.subheader(f"Edges for: {node_labels[selected_node_idx]}")
        edges_df = get_edges_for_node(selected_node_id)

        if not edges_df.empty:
            st.dataframe(edges_df[["SRC_NAME", "SRC_TYPE", "EDGE_TYPE", "DST_NAME", "DST_TYPE", "WEIGHT"]],
                         use_container_width=True, hide_index=True)

            # Mini neighborhood graph
            dot2 = graphviz.Digraph(comment="Neighborhood")
            dot2.attr(rankdir="LR", bgcolor="transparent")
            dot2.attr("node", style="filled", fontsize="9")
            dot2.node(selected_node_id, node_labels[selected_node_idx],
                      fillcolor="#29B5E8", fontcolor="white", shape="box")

            seen_nodes = set()
            for _, edge in edges_df.iterrows():
                if edge["SRC_ID"] == selected_node_id:
                    other_id = edge["DST_ID"]
                    other_name = str(edge["DST_NAME"])[:25] if pd.notna(edge["DST_NAME"]) else other_id[:12]
                    if other_id not in seen_nodes:
                        dot2.node(other_id, other_name, fillcolor="#4ECDC4")
                        seen_nodes.add(other_id)
                    dot2.edge(selected_node_id, other_id, label=edge["EDGE_TYPE"], fontsize="7")
                else:
                    other_id = edge["SRC_ID"]
                    other_name = str(edge["SRC_NAME"])[:25] if pd.notna(edge["SRC_NAME"]) else other_id[:12]
                    if other_id not in seen_nodes:
                        dot2.node(other_id, other_name, fillcolor="#FF6B6B")
                        seen_nodes.add(other_id)
                    dot2.edge(other_id, selected_node_id, label=edge["EDGE_TYPE"], fontsize="7")

            st.graphviz_chart(dot2, use_container_width=True)
        else:
            st.info("No edges found for this node.")
