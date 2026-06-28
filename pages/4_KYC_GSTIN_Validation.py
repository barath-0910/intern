import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io

from utils.styling import load_theme, render_sidebar_logo, section_header, inject_favicon
from utils.validators import gstin_audit, kyc_completeness

st.set_page_config(page_title="KYC & GSTIN Validation", page_icon=inject_favicon(), layout="wide")
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True
load_theme(dark=st.session_state.dark_mode)

if not st.session_state.get("authenticated"):
    st.warning("Please sign in from the main page first.")
    st.stop()

with st.sidebar:
    render_sidebar_logo(st.session_state.company_name)

st.markdown("## 🧾 Module 3 · KYC & GSTIN Validation")

cm = st.session_state.get("customer_master")
if cm is None:
    st.info("Upload **Customer Master** in the Excel Import Center to run validation.")
    st.stop()

gdf = gstin_audit(cm)
kdf = kyc_completeness(cm)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Invalid GSTIN</div><div class="kpi-value">{(gdf["GSTIN_Status"]=="Invalid").sum():,}</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Duplicate GSTIN</div><div class="kpi-value">{gdf["GSTIN_Duplicate"].sum():,}</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Blank GSTIN</div><div class="kpi-value">{(gdf["GSTIN_Status"]=="Blank").sum():,}</div></div>', unsafe_allow_html=True)
with c4:
    avg_kyc = kdf["KYC_Score"].mean() if "KYC_Score" in kdf.columns else 0
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Avg KYC Completeness</div><div class="kpi-value">{avg_kyc:.0f}%</div></div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])
with col1:
    section_header("GSTIN Compliance Donut", "🍩")
    counts = gdf["GSTIN_Status"].value_counts()
    fig = go.Figure(go.Pie(labels=counts.index, values=counts.values, hole=0.6,
                            marker_colors=["#22c55e", "#ef4444", "#eab308", "#f97316"]))
    fig.update_layout(height=320, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)", font_color="#9aa7bd")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    section_header("KYC Compliance Scorecard", "📋")
    bands = pd.cut(kdf["KYC_Score"], bins=[-1, 25, 50, 75, 100], labels=["Critical (0-25%)", "Poor (26-50%)", "Fair (51-75%)", "Good (76-100%)"])
    band_counts = bands.value_counts().reindex(["Critical (0-25%)", "Poor (26-50%)", "Fair (51-75%)", "Good (76-100%)"]).fillna(0)
    fig2 = go.Figure(go.Bar(x=band_counts.index, y=band_counts.values,
                             marker_color=["#ef4444", "#f97316", "#eab308", "#22c55e"]))
    fig2.update_layout(height=320, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)", font_color="#9aa7bd")
    st.plotly_chart(fig2, use_container_width=True)

section_header("GSTIN Exception Report", "🚩")
gstin_cols = ["Customer Code", "Customer Name", "GSTIN", "GSTIN_Status", "GSTIN_Duplicate"]
gstin_cols = [c for c in gstin_cols if c in gdf.columns]
exceptions = gdf[gdf["GSTIN_Status"] != "Valid"][gstin_cols]
if len(exceptions) > 0:
    st.dataframe(exceptions, use_container_width=True, height=320)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        exceptions.to_excel(writer, index=False, sheet_name="GSTIN Exceptions")
    st.download_button("⬇️ Export GSTIN Exceptions", buf.getvalue(), file_name="gstin_exceptions.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
else:
    st.success("✅ All GSTIN records are valid and unique.")

section_header("KYC Completeness by Customer", "📂")
kyc_cols = ["Customer Code", "Customer Name", "KYC_Score", "KYC_Missing_Docs"]
kyc_cols = [c for c in kyc_cols if c in kdf.columns]
low_kyc = kdf[kdf["KYC_Score"] < 100][kyc_cols].sort_values("KYC_Score")
if len(low_kyc) > 0:
    for _, row in low_kyc.head(8).iterrows():
        score = row["KYC_Score"]
        st.markdown(
            f"""
            <div class="glass-card" style="margin-bottom:10px; padding:14px 18px;">
                <div style="display:flex; justify-content:space-between;">
                    <b>{row.get('Customer Name','')} ({row.get('Customer Code','')})</b>
                    <span>{score:.0f}%</span>
                </div>
                <div class="score-track" style="margin-top:6px;"><div class="score-fill" style="width:{score}%;"></div></div>
                <div style="font-size:0.78rem; margin-top:4px;">Missing: {row.get('KYC_Missing_Docs','')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.dataframe(low_kyc, use_container_width=True, height=280)
else:
    st.success("✅ All customers have complete KYC documentation.")
