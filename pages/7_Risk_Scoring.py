import streamlit as st
import pandas as pd
import plotly.express as px
import io

from utils.styling import load_theme, render_sidebar_logo, section_header, risk_badge, inject_favicon
from utils.validators import gstin_audit, kyc_completeness
from utils.risk_engine import compute_risk_scores, detect_suspicious_changes, suspicious_change_counts_by_customer

st.set_page_config(page_title="Risk Scoring Engine", page_icon=inject_favicon(), layout="wide")
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True
load_theme(dark=st.session_state.dark_mode)

if not st.session_state.get("authenticated"):
    st.warning("Please sign in from the main page first.")
    st.stop()

with st.sidebar:
    render_sidebar_logo(st.session_state.company_name)

st.markdown("## 🎯 Composite Risk Scoring Engine")
st.caption("Risk Score = Credit Breach (30%) + Overdue Balance (25%) + Invalid GSTIN (15%) + Missing KYC (15%) + Suspicious Changes (15%)")

cm = st.session_state.get("customer_master")
if cm is None:
    st.info("Upload **Customer Master** at minimum to run risk scoring. Aging, GSTIN, KYC, and Change Log data will refine the score further.")
    st.stop()

aging = st.session_state.get("aging")
change_log = st.session_state.get("change_log")

gdf = gstin_audit(cm) if "GSTIN" in cm.columns else None
kdf = kyc_completeness(cm)

gstin_flags = gdf.set_index("Customer Code")["GSTIN_Status"].ne("Valid").astype(int) if gdf is not None else None
kyc_scores = kdf.set_index("Customer Code")["KYC_Score"] if kdf is not None else None

change_counts = None
if change_log is not None:
    flagged = detect_suspicious_changes(change_log)
    change_counts = suspicious_change_counts_by_customer(flagged)

risk_df = compute_risk_scores(
    customers=cm, aging=aging, gstin_flags=gstin_flags,
    kyc_scores=kyc_scores, suspicious_change_counts=change_counts,
)
risk_df = risk_df.merge(cm[["Customer Code", "Customer Name", "Region", "Salesperson"]], on="Customer Code", how="left")

c1, c2, c3, c4 = st.columns(4)
for col, cat, color in zip([c1, c2, c3, c4], ["Low", "Medium", "High", "Critical"],
                            ["#22c55e", "#eab308", "#f97316", "#ef4444"]):
    count = (risk_df["Risk Category"] == cat).sum()
    with col:
        st.markdown(
            f'<div class="kpi-card"><div class="kpi-label">{cat} Risk</div>'
            f'<div class="kpi-value" style="color:{color};">{count:,}</div></div>',
            unsafe_allow_html=True,
        )

col1, col2 = st.columns([1, 1.2])
with col1:
    section_header("Risk Matrix", "🧮")
    fig = px.scatter(risk_df, x="Overdue Score", y="Credit Breach Score", size="Risk Score",
                      color="Risk Category", hover_name="Customer Name",
                      color_discrete_map={"Low": "#22c55e", "Medium": "#eab308", "High": "#f97316", "Critical": "#ef4444"})
    fig.update_layout(height=380, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)",
                       plot_bgcolor="rgba(0,0,0,0)", font_color="#9aa7bd")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    section_header("Risk Distribution", "📊")
    fig2 = px.histogram(risk_df, x="Risk Score", nbins=20, color="Risk Category",
                         color_discrete_map={"Low": "#22c55e", "Medium": "#eab308", "High": "#f97316", "Critical": "#ef4444"})
    fig2.update_layout(height=380, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)", font_color="#9aa7bd")
    st.plotly_chart(fig2, use_container_width=True)

section_header("Customer Risk Register", "📋")
filter_cat = st.multiselect("Filter by Risk Category", ["Low", "Medium", "High", "Critical"],
                             default=["Critical", "High", "Medium", "Low"])
filtered = risk_df[risk_df["Risk Category"].isin(filter_cat)].sort_values("Risk Score", ascending=False)
st.dataframe(filtered, use_container_width=True, height=420)

buf = io.BytesIO()
with pd.ExcelWriter(buf, engine="openpyxl") as writer:
    filtered.to_excel(writer, index=False, sheet_name="Risk Register")
st.download_button("⬇️ Export Risk Register to Excel", buf.getvalue(), file_name="risk_register.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.session_state["_risk_summary_cache"] = risk_df
