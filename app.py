"""
Customer Master & Credit Control Audit Portal
Main entry point: Login + Executive Dashboard
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from utils.styling import load_theme, kpi_card, section_header, render_sidebar_logo, get_base64_logo, inject_favicon
from utils.data_loader import init_session_state, has_any_data
from utils.validators import gstin_audit, exact_duplicate_codes, find_duplicates_fuzzy, kyc_completeness
from utils.risk_engine import compute_risk_scores, detect_suspicious_changes, suspicious_change_counts_by_customer
from utils.ai_insights import generate_insights

st.set_page_config(
    page_title="Customer Master & Credit Control Audit Portal",
    page_icon=inject_favicon(),
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()
load_theme(dark=st.session_state.dark_mode)


# ---------------------------------------------------------------------------
# LOGIN PAGE
# ---------------------------------------------------------------------------
def render_login():
    logo_b64 = get_base64_logo()
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" width="92" style="margin-bottom:14px;">' if logo_b64 else ""

    st.markdown(
        f"""
        <div class="login-wrapper">
            <div class="login-card">
                {logo_html}
                <h2 style="margin:0 0 4px 0;">Audit Control Portal</h2>
                <div style="color:var(--text-secondary); font-size:0.85rem; margin-bottom:24px;">
                    Customer Master &amp; Credit Risk Management
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        with st.container():
            st.text_input("Username", key="login_user", placeholder="auditor@company.com")
            st.text_input("Password", type="password", key="login_pass", placeholder="••••••••")
            company = st.text_input("Company Name", value="Your Company", key="login_company")
            if st.button("Sign In →", use_container_width=True):
                st.session_state.authenticated = True
                st.session_state.company_name = company or "Your Company"
                st.rerun()
            st.caption("Demo mode — any credentials will sign you in.")


# ---------------------------------------------------------------------------
# SIDEBAR (shown once authenticated)
# ---------------------------------------------------------------------------
def render_sidebar():
    with st.sidebar:
        render_sidebar_logo(st.session_state.company_name)

        st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode, key="dark_mode_toggle",
                  on_change=lambda: st.session_state.update(dark_mode=st.session_state.dark_mode_toggle))

        st.markdown("---")
        st.caption("NAVIGATION")
        st.page_link("app.py", label="Executive Dashboard", icon="🏠")
        st.page_link("pages/1_Excel_Import_Center.py", label="Excel Import Center", icon="📥")
        st.page_link("pages/2_Credit_Limit_Review.py", label="Credit Limit Review", icon="💳")
        st.page_link("pages/3_Duplicate_Detection.py", label="Duplicate Detection", icon="🔁")
        st.page_link("pages/4_KYC_GSTIN_Validation.py", label="KYC & GSTIN Validation", icon="🧾")
        st.page_link("pages/5_Overdue_Review.py", label="Overdue Customer Review", icon="⏰")
        st.page_link("pages/6_Change_Audit.py", label="Credit Master Change Audit", icon="📝")
        st.page_link("pages/7_Risk_Scoring.py", label="Risk Scoring Engine", icon="🎯")
        st.page_link("pages/8_Search_Export.py", label="Search & Export Center", icon="🔍")

        st.markdown("---")
        if st.button("Sign Out", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()


# ---------------------------------------------------------------------------
# EXECUTIVE DASHBOARD
# ---------------------------------------------------------------------------
def render_dashboard():
    logo_b64 = get_base64_logo()
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" width="46" style="border-radius:10px;">' if logo_b64 else ""

    st.markdown(
        f"""
        <div class="top-banner">
            <div style="display:flex; align-items:center; gap:14px;">
                {logo_html}
                <div>
                    <h2 style="margin:0;">Executive Dashboard</h2>
                    <div style="color:var(--text-secondary); font-size:0.85rem;">
                        {st.session_state.company_name} · Internal Audit &amp; Credit Control
                    </div>
                </div>
            </div>
            <div style="text-align:right; color:var(--text-secondary); font-size:0.8rem;">
                Last refreshed<br><b style="color:var(--text-primary);">just now</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cm = st.session_state.customer_master
    aging = st.session_state.aging
    sales = st.session_state.sales
    change_log = st.session_state.change_log

    if not has_any_data():
        st.markdown(
            """
            <div class="glass-card" style="text-align:center; padding:50px;">
                <h3>📥 No data loaded yet</h3>
                <p>Head to the <b>Excel Import Center</b> to upload your Customer Master,
                Accounts Receivable Aging, Sales Transactions, and Change Log files
                to populate this dashboard.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Go to Excel Import Center →"):
            st.switch_page("pages/1_Excel_Import_Center.py")
        return

    # ---- Run lightweight computations for KPIs ----
    total_customers = len(cm) if cm is not None else 0
    active_customers = (cm["Customer Status"].astype(str).str.lower() == "active").sum() if cm is not None and "Customer Status" in cm.columns else 0
    total_exposure = aging["Outstanding Amount"].sum() if aging is not None and "Outstanding Amount" in aging.columns else 0
    avg_credit_limit = cm["Credit Limit"].mean() if cm is not None and "Credit Limit" in cm.columns else 0

    breach_df = pd.DataFrame()
    if cm is not None and aging is not None and "Credit Limit" in cm.columns and "Outstanding Amount" in aging.columns:
        merged = cm.merge(aging, on="Customer Code", how="inner")
        breach_df = merged[merged["Outstanding Amount"] > merged["Credit Limit"]]

    gstin_df = gstin_audit(cm) if cm is not None and "GSTIN" in cm.columns else None
    invalid_gstins = (gstin_df["GSTIN_Status"] == "Invalid").sum() if gstin_df is not None else 0
    dup_codes = exact_duplicate_codes(cm) if cm is not None else pd.DataFrame()

    kyc_df = kyc_completeness(cm) if cm is not None else None
    missing_kyc = (kyc_df["KYC_Score"] < 100).sum() if kyc_df is not None else 0

    overdue_df = pd.DataFrame()
    if aging is not None and sales is not None and "Above 180 Days" in aging.columns:
        overdue_candidates = aging[aging["Above 180 Days"] > 0]
        if "Invoice Date" in sales.columns:
            recent_codes = set(sales["Customer Code"].unique())
            overdue_df = overdue_candidates[overdue_candidates["Customer Code"].isin(recent_codes)]

    suspicious_df = pd.DataFrame()
    unauthorized_changes = 0
    if change_log is not None and all(c in change_log.columns for c in ["Old Credit Limit", "New Credit Limit", "Old Credit Days", "New Credit Days", "Change Date"]):
        suspicious_df = detect_suspicious_changes(change_log)
        unauthorized_changes = suspicious_df["Is Suspicious"].sum()

    # high risk customers via risk engine (rough pass)
    high_risk_count = 0
    risk_summary = None
    if cm is not None:
        gstin_flag_series = gstin_df.set_index("Customer Code")["GSTIN_Status"].ne("Valid").astype(int) if gstin_df is not None else None
        kyc_score_series = kyc_df.set_index("Customer Code")["KYC_Score"] if kyc_df is not None else None
        change_counts = suspicious_change_counts_by_customer(suspicious_df) if len(suspicious_df) > 0 else None
        risk_summary = compute_risk_scores(
            customers=cm, aging=aging, gstin_flags=gstin_flag_series,
            kyc_scores=kyc_score_series, suspicious_change_counts=change_counts,
        )
        high_risk_count = risk_summary["Risk Category"].isin(["High", "Critical"]).sum()

    # ---- Credit KPI Row ----
    section_header("Credit KPIs", "💳")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: kpi_card("Total Customers", f"{total_customers:,}", "👥")
    with c2: kpi_card("Active Customers", f"{active_customers:,}", "✅")
    with c3: kpi_card("Total Credit Exposure", f"₹{total_exposure:,.0f}", "💰")
    with c4: kpi_card("Avg Credit Limit", f"₹{avg_credit_limit:,.0f}", "📊")
    with c5: kpi_card("Exceeding Limit", f"{len(breach_df):,}", "🚨", delta="needs review" if len(breach_df) else None, delta_positive=False)
    with c6: kpi_card("High-Risk Customers", f"{high_risk_count:,}", "⚠️", delta_positive=False)

    # ---- Audit KPI Row ----
    section_header("Audit KPIs", "🧾")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: kpi_card("Duplicate Codes", f"{len(dup_codes):,}", "🔁")
    with c2: kpi_card("Invalid GSTINs", f"{invalid_gstins:,}", "🆔")
    with c3: kpi_card("Missing KYC", f"{missing_kyc:,}", "📂")
    with c4: kpi_card("Unauthorized Changes", f"{int(unauthorized_changes):,}", "🔓")
    with c5: kpi_card("Overdue Customers", f"{len(overdue_df):,}", "⏰")

    st.markdown("<br>", unsafe_allow_html=True)

    # ---- Charts row ----
    col1, col2 = st.columns([1.3, 1])
    with col1:
        section_header("Risk Distribution", "🎯")
        if risk_summary is not None and len(risk_summary) > 0:
            counts = risk_summary["Risk Category"].value_counts().reindex(["Low", "Medium", "High", "Critical"]).fillna(0)
            colors = {"Low": "#22c55e", "Medium": "#eab308", "High": "#f97316", "Critical": "#ef4444"}
            fig = go.Figure(go.Bar(
                x=counts.index, y=counts.values,
                marker_color=[colors[c] for c in counts.index],
                text=counts.values, textposition="outside",
            ))
            fig.update_layout(
                height=320, margin=dict(t=10, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#9aa7bd" if st.session_state.dark_mode else "#475569",
                xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)"),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Upload data to compute risk distribution.")

    with col2:
        section_header("Credit Exposure Mix", "🥧")
        if cm is not None and "Region" in cm.columns and aging is not None:
            merged = cm.merge(aging, on="Customer Code", how="inner")
            region_exposure = merged.groupby("Region")["Outstanding Amount"].sum().reset_index()
            fig = px.pie(region_exposure, names="Region", values="Outstanding Amount", hole=0.55,
                         color_discrete_sequence=px.colors.sequential.Blues_r)
            fig.update_layout(
                height=320, margin=dict(t=10, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#9aa7bd" if st.session_state.dark_mode else "#475569",
                showlegend=True,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Upload Customer Master + Aging data for exposure mix.")

    # ---- AI Insights Panel ----
    section_header("AI Insights Panel", "🤖")
    insights = generate_insights(
        credit_breaches=breach_df,
        duplicates=find_duplicates_fuzzy(cm) if cm is not None and len(cm) < 400 else None,
        gstin_audit_df=gstin_df,
        overdue_df=overdue_df,
        suspicious_changes=suspicious_df if len(suspicious_df) > 0 else None,
    )
    insight_html = "".join(f"<li style='margin-bottom:8px;'>{i}</li>" for i in insights)
    st.markdown(
        f"""
        <div class="glass-card">
            <ul style="padding-left:18px; margin:0;">{insight_html}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# ROUTER
# ---------------------------------------------------------------------------
if not st.session_state.authenticated:
    render_login()
else:
    render_sidebar()
    render_dashboard()
