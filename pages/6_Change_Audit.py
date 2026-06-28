import streamlit as st
import pandas as pd
import plotly.express as px
import io

from utils.styling import load_theme, render_sidebar_logo, section_header, inject_favicon
from utils.risk_engine import detect_suspicious_changes

st.set_page_config(page_title="Credit Master Change Audit", page_icon=inject_favicon(), layout="wide")
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True
load_theme(dark=st.session_state.dark_mode)

if not st.session_state.get("authenticated"):
    st.warning("Please sign in from the main page first.")
    st.stop()

with st.sidebar:
    render_sidebar_logo(st.session_state.company_name)

st.markdown("## 📝 Module 5 · Credit Master Change Audit")

change_log = st.session_state.get("change_log")
if change_log is None:
    st.info("Upload **Change Log** in the Excel Import Center to run this audit.")
    st.stop()

flagged = detect_suspicious_changes(change_log)
suspicious = flagged[flagged["Is Suspicious"]]

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Total Changes</div><div class="kpi-value">{len(flagged):,}</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Suspicious Changes</div><div class="kpi-value">{len(suspicious):,}</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Limit Spikes &gt;50%</div><div class="kpi-value">{flagged["Flag: Limit Spike"].sum():,}</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Off-Hours Changes</div><div class="kpi-value">{flagged["Flag: Off Hours"].sum():,}</div></div>', unsafe_allow_html=True)

col1, col2 = st.columns([1.3, 1])
with col1:
    section_header("Audit Timeline", "📅")
    if len(flagged) > 0:
        timeline = flagged.copy()
        timeline["Date"] = timeline["Change Date"].dt.date
        daily = timeline.groupby(["Date", "Is Suspicious"]).size().reset_index(name="Count")
        fig = px.bar(daily, x="Date", y="Count", color="Is Suspicious",
                     color_discrete_map={True: "#ef4444", False: "#3b82f6"})
        fig.update_layout(height=320, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)",
                           plot_bgcolor="rgba(0,0,0,0)", font_color="#9aa7bd")
        st.plotly_chart(fig, use_container_width=True)

with col2:
    section_header("User Leaderboard — Flagged Changes", "👤")
    if len(suspicious) > 0:
        leaderboard = suspicious["User"].value_counts().reset_index()
        leaderboard.columns = ["User", "Flagged Changes"]
        fig2 = px.bar(leaderboard.head(10), x="Flagged Changes", y="User", orientation="h",
                      color="Flagged Changes", color_continuous_scale="Reds")
        fig2.update_layout(height=320, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)", font_color="#9aa7bd")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.success("✅ No suspicious changes by any user.")

section_header("Change Trend — Limit Increase %", "📈")
if len(flagged) > 0:
    fig3 = px.line(flagged.sort_values("Change Date"), x="Change Date", y="Limit Increase %",
                    color="User", markers=True)
    fig3.update_layout(height=320, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)", font_color="#9aa7bd")
    st.plotly_chart(fig3, use_container_width=True)

section_header("Suspicious Change Exceptions", "🚩")
if len(suspicious) > 0:
    show_cols = ["User", "Change Date", "Customer Code", "Old Credit Limit", "New Credit Limit",
                 "Limit Increase %", "Old Credit Days", "New Credit Days", "Days Increase %",
                 "Flag: Limit Spike", "Flag: Days Spike", "Flag: Off Hours", "Flag: Frequent Changes"]
    show_cols = [c for c in show_cols if c in suspicious.columns]
    st.dataframe(suspicious[show_cols].sort_values("Change Date", ascending=False), use_container_width=True, height=400)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        suspicious[show_cols].to_excel(writer, index=False, sheet_name="Suspicious Changes")
    st.download_button("⬇️ Export to Excel", buf.getvalue(), file_name="suspicious_changes.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
else:
    st.success("✅ No suspicious credit master changes detected.")
