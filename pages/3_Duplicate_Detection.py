import streamlit as st
import pandas as pd
import plotly.express as px
import io

from utils.styling import load_theme, render_sidebar_logo, section_header, inject_favicon
from utils.validators import exact_duplicate_codes, find_duplicates_fuzzy

st.set_page_config(page_title="Duplicate Detection", page_icon=inject_favicon(), layout="wide")
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True
load_theme(dark=st.session_state.dark_mode)

if not st.session_state.get("authenticated"):
    st.warning("Please sign in from the main page first.")
    st.stop()

with st.sidebar:
    render_sidebar_logo(st.session_state.company_name)

st.markdown("## 🔁 Module 2 · Duplicate Customer Detection")

cm = st.session_state.get("customer_master")
if cm is None:
    st.info("Upload **Customer Master** in the Excel Import Center to run duplicate detection.")
    st.stop()

exact_dups = exact_duplicate_codes(cm)

threshold = st.slider("Fuzzy match similarity threshold (%)", 70, 99, 85)
with st.spinner("Running fuzzy match across customer records..."):
    fuzzy_dups = find_duplicates_fuzzy(cm, threshold=threshold)

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Exact Duplicate Codes</div><div class="kpi-value">{len(exact_dups):,}</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Potential Duplicate Pairs</div><div class="kpi-value">{len(fuzzy_dups):,}</div></div>', unsafe_allow_html=True)
with c3:
    crit = (fuzzy_dups["Risk Level"] == "Critical").sum() if len(fuzzy_dups) else 0
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Critical Risk Pairs</div><div class="kpi-value">{crit:,}</div></div>', unsafe_allow_html=True)

section_header("Exact Duplicate Customer Codes", "🆔")
if len(exact_dups) > 0:
    st.dataframe(exact_dups, use_container_width=True, height=240)
else:
    st.success("✅ No exact duplicate customer codes found.")

section_header("Fuzzy Duplicate Matches", "🔍")
if len(fuzzy_dups) > 0:
    risk_filter = st.multiselect("Filter by Risk Level", ["Critical", "High", "Medium", "Low"],
                                  default=["Critical", "High", "Medium", "Low"])
    filtered = fuzzy_dups[fuzzy_dups["Risk Level"].isin(risk_filter)].sort_values("Similarity %", ascending=False)
    st.dataframe(filtered, use_container_width=True, height=380)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        filtered.to_excel(writer, index=False, sheet_name="Duplicate Matches")
    st.download_button("⬇️ Export to Excel", buf.getvalue(), file_name="duplicate_customers.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    section_header("Similarity Network", "🕸️")
    try:
        import networkx as nx
        import plotly.graph_objects as go

        G = nx.Graph()
        for _, row in filtered.iterrows():
            G.add_edge(row["Customer Code A"], row["Customer Code B"], weight=row["Similarity %"])
        pos = nx.spring_layout(G, seed=42)

        edge_x, edge_y = [], []
        for e in G.edges():
            x0, y0 = pos[e[0]]; x1, y1 = pos[e[1]]
            edge_x += [x0, x1, None]; edge_y += [y0, y1, None]
        node_x = [pos[n][0] for n in G.nodes()]
        node_y = [pos[n][1] for n in G.nodes()]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode="lines", line=dict(width=1, color="rgba(59,130,246,0.4)"), hoverinfo="none"))
        fig.add_trace(go.Scatter(x=node_x, y=node_y, mode="markers+text", text=list(G.nodes()),
                                  textposition="top center", marker=dict(size=14, color="#3b82f6")))
        fig.update_layout(height=420, showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           xaxis=dict(visible=False), yaxis=dict(visible=False), margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        st.caption("Install `networkx` to view the similarity network graph.")

    section_header("Similarity Matrix (Top Pairs)", "📐")
    top = filtered.head(15)
    if len(top) > 0:
        pivot = top.pivot_table(index="Customer Name A", columns="Customer Name B", values="Similarity %", aggfunc="mean")
        fig2 = px.imshow(pivot, color_continuous_scale="Blues", aspect="auto")
        fig2.update_layout(height=350, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2, use_container_width=True)
else:
    st.success("✅ No potential duplicates found at this similarity threshold.")
