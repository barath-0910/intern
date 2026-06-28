import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import io

from utils.styling import load_theme, render_sidebar_logo, section_header, risk_badge, inject_favicon

st.set_page_config(page_title="Credit Limit Review", page_icon=inject_favicon(), layout="wide")

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True
load_theme(dark=st.session_state.dark_mode)

if not st.session_state.get("authenticated"):
    st.warning("Please sign in from the main page first.")
    st.stop()

with st.sidebar:
    render_sidebar_logo(st.session_state.company_name)

st.markdown("## 💳 Module 1 · Credit Limit Review")

cm = st.session_state.get("customer_master")
aging = st.session_state.get("aging")
sales = st.session_state.get("sales")

if cm is None or aging is None:
    st.info("Upload **Customer Master** and **Accounts Receivable Aging** in the Excel Import Center to run this review.")
    st.stop()

merged = cm.merge(aging, on="Customer Code", how="inner")
merged["Breach Amount"] = merged["Outstanding Amount"] - merged["Credit Limit"]
breach_df = merged[merged["Breach Amount"] > 0].copy()


def severity(row):
    pct = row["Breach Amount"] / row["Credit Limit"] * 100 if row["Credit Limit"] else 0
    if pct > 50:
        return "Critical"
    elif pct > 20:
        return "High"
    elif pct > 5:
        return "Medium"
    return "Low"


if len(breach_df) > 0:
    breach_df["Breach %"] = (breach_df["Breach Amount"] / breach_df["Credit Limit"] * 100).round(1)
    breach_df["Severity"] = breach_df.apply(severity, axis=1)

# Override approval check: customers with sales after breach
override_df = pd.DataFrame()
if sales is not None and len(breach_df) > 0:
    breached_codes = set(breach_df["Customer Code"])
    override_df = sales[sales["Customer Code"].isin(breached_codes)]

section_header("Credit Limit Breach Summary", "🚨")
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Breached Accounts</div><div class="kpi-value">{len(breach_df):,}</div></div>', unsafe_allow_html=True)
with c2:
    total_breach = breach_df["Breach Amount"].sum() if len(breach_df) else 0
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Total Breach Exposure</div><div class="kpi-value">₹{total_breach:,.0f}</div></div>', unsafe_allow_html=True)
with c3:
    crit = (breach_df["Severity"] == "Critical").sum() if len(breach_df) else 0
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Critical Severity</div><div class="kpi-value">{crit:,}</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Sales Despite Breach</div><div class="kpi-value">{len(override_df):,}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])
with col1:
    section_header("Severity Distribution", "📊")
    if len(breach_df) > 0:
        counts = breach_df["Severity"].value_counts().reindex(["Low", "Medium", "High", "Critical"]).fillna(0)
        colors = {"Low": "#22c55e", "Medium": "#eab308", "High": "#f97316", "Critical": "#ef4444"}
        fig = go.Figure(go.Bar(x=counts.index, y=counts.values, marker_color=[colors[c] for c in counts.index]))
        fig.update_layout(height=300, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)",
                           plot_bgcolor="rgba(0,0,0,0)", font_color="#9aa7bd")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.success("No credit limit breaches detected.")

with col2:
    section_header("Credit Exposure Treemap", "🗺️")
    if len(merged) > 0:
        fig = px.treemap(merged, path=["Region", "Customer Name"], values="Outstanding Amount",
                          color="Breach Amount", color_continuous_scale="RdYlGn_r")
        fig.update_layout(height=300, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

section_header("Exception Report — Breached Customers", "📋")
if len(breach_df) > 0:
    show_cols = ["Customer Code", "Customer Name", "Region", "Salesperson", "Credit Limit",
                 "Outstanding Amount", "Breach Amount", "Breach %", "Severity"]
    show_cols = [c for c in show_cols if c in breach_df.columns]

    sev_filter = st.multiselect("Filter by Severity", ["Low", "Medium", "High", "Critical"],
                                 default=["Critical", "High", "Medium", "Low"])
    region_filter = st.multiselect("Filter by Region", sorted(breach_df["Region"].dropna().unique()) if "Region" in breach_df.columns else [])

    filtered = breach_df[breach_df["Severity"].isin(sev_filter)]
    if region_filter:
        filtered = filtered[filtered["Region"].isin(region_filter)]

    st.dataframe(filtered[show_cols].sort_values("Breach Amount", ascending=False),
                 use_container_width=True, height=380)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        filtered[show_cols].to_excel(writer, index=False, sheet_name="Credit Breaches")
    st.download_button("⬇️ Export to Excel", buf.getvalue(), file_name="credit_limit_breaches.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
else:
    st.success("✅ No customers currently exceed their approved credit limits.")

if len(override_df) > 0:
    section_header("Override Approval Exceptions — Sales Despite Breach", "⛔")
    st.dataframe(override_df, use_container_width=True, height=300)

section_header("Risk Gauge — Portfolio Breach Ratio", "🎯")
breach_ratio = (len(breach_df) / len(merged) * 100) if len(merged) else 0
gauge = go.Figure(go.Indicator(
    mode="gauge+number",
    value=breach_ratio,
    number={"suffix": "%"},
    gauge={
        "axis": {"range": [0, 100]},
        "bar": {"color": "#3b82f6"},
        "steps": [
            {"range": [0, 20], "color": "rgba(34,197,94,0.25)"},
            {"range": [20, 50], "color": "rgba(234,179,8,0.25)"},
            {"range": [50, 100], "color": "rgba(239,68,68,0.25)"},
        ],
    },
))
gauge.update_layout(height=280, margin=dict(t=20, b=10, l=20, r=20), paper_bgcolor="rgba(0,0,0,0)", font_color="#9aa7bd")
st.plotly_chart(gauge, use_container_width=True)
