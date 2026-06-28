import streamlit as st
import pandas as pd
import plotly.express as px
import io

from utils.styling import load_theme, render_sidebar_logo, section_header, inject_favicon

st.set_page_config(page_title="Overdue Customer Review", page_icon=inject_favicon(), layout="wide")
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True
load_theme(dark=st.session_state.dark_mode)

if not st.session_state.get("authenticated"):
    st.warning("Please sign in from the main page first.")
    st.stop()

with st.sidebar:
    render_sidebar_logo(st.session_state.company_name)

st.markdown("## ⏰ Module 4 · Long Overdue Customer Review")

cm = st.session_state.get("customer_master")
aging = st.session_state.get("aging")
sales = st.session_state.get("sales")

if cm is None or aging is None or sales is None:
    st.info("Upload **Customer Master**, **Aging**, and **Sales Transactions** to run this review.")
    st.stop()

overdue_candidates = aging[aging["Above 180 Days"] > 0].copy()
recent_codes = set(sales["Customer Code"].unique())
overdue_candidates["Still Receiving Sales"] = overdue_candidates["Customer Code"].isin(recent_codes)

risky = overdue_candidates[overdue_candidates["Still Receiving Sales"]].merge(
    cm[["Customer Code", "Customer Name", "Region", "Salesperson"]], on="Customer Code", how="left"
)

recent_sales_by_cust = sales.groupby("Customer Code")["Invoice Amount"].sum().rename("Recent Sales Amount")
risky = risky.merge(recent_sales_by_cust, on="Customer Code", how="left")

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">High-Risk Overdue Customers</div><div class="kpi-value">{len(risky):,}</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Outstanding (&gt;180d)</div><div class="kpi-value">₹{risky["Above 180 Days"].sum():,.0f}</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Recent Sales to These Accounts</div><div class="kpi-value">₹{risky["Recent Sales Amount"].sum():,.0f}</div></div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])
with col1:
    section_header("Risk Heatmap — Region vs Aging", "🔥")
    if "Region" in risky.columns and len(risky) > 0:
        pivot = risky.pivot_table(index="Region", values="Above 180 Days", aggfunc="sum").reset_index()
        fig = px.bar(pivot, x="Region", y="Above 180 Days", color="Above 180 Days", color_continuous_scale="Reds")
        fig.update_layout(height=320, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)",
                           plot_bgcolor="rgba(0,0,0,0)", font_color="#9aa7bd")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No overdue + still-selling accounts found.")

with col2:
    section_header("Outstanding vs Recent Sales", "📍")
    if len(risky) > 0:
        fig2 = px.scatter(risky, x="Above 180 Days", y="Recent Sales Amount", size="Above 180 Days",
                           color="Region" if "Region" in risky.columns else None,
                           hover_name="Customer Name")
        fig2.update_layout(height=320, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)", font_color="#9aa7bd")
        st.plotly_chart(fig2, use_container_width=True)

section_header("Top 20 Riskiest Overdue Customers", "🏆")
if len(risky) > 0:
    top20 = risky.sort_values("Above 180 Days", ascending=False).head(20)
    show_cols = ["Customer Code", "Customer Name", "Region", "Salesperson", "Outstanding Amount",
                 "Above 180 Days", "Recent Sales Amount"]
    show_cols = [c for c in show_cols if c in top20.columns]
    st.dataframe(top20[show_cols], use_container_width=True, height=420)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        top20[show_cols].to_excel(writer, index=False, sheet_name="Overdue Risk")
    st.download_button("⬇️ Export to Excel", buf.getvalue(), file_name="overdue_high_risk.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
else:
    st.success("✅ No customers overdue beyond 180 days are still receiving sales.")
