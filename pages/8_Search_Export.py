import streamlit as st
import pandas as pd
import io
import os
from datetime import datetime

from utils.styling import load_theme, render_sidebar_logo, section_header, inject_favicon, get_base64_logo
from utils.ai_insights import generate_insights, generate_recommendations
from utils.validators import gstin_audit, find_duplicates_fuzzy

st.set_page_config(page_title="Search & Export Center", page_icon=inject_favicon(), layout="wide")
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True
load_theme(dark=st.session_state.dark_mode)

if not st.session_state.get("authenticated"):
    st.warning("Please sign in from the main page first.")
    st.stop()

with st.sidebar:
    render_sidebar_logo(st.session_state.company_name)

st.markdown("## 🔍 Search & Export Center")

cm = st.session_state.get("customer_master")

# ---------------- Global Search ----------------
section_header("Global Search", "🔎")
if cm is not None:
    query = st.text_input("Search by Customer Code, Name, or GSTIN")
    c1, c2, c3 = st.columns(3)
    with c1:
        region_filter = st.multiselect("Region", sorted(cm["Region"].dropna().unique()) if "Region" in cm.columns else [])
    with c2:
        sp_filter = st.multiselect("Salesperson", sorted(cm["Salesperson"].dropna().unique()) if "Salesperson" in cm.columns else [])
    with c3:
        min_limit, max_limit = (0, int(cm["Credit Limit"].max())) if "Credit Limit" in cm.columns and len(cm) else (0, 0)
        limit_range = st.slider("Credit Limit Range", min_limit, max_limit or 1, (min_limit, max_limit or 1))

    results = cm.copy()
    if query:
        mask = pd.Series(False, index=results.index)
        for col in ["Customer Code", "Customer Name", "GSTIN"]:
            if col in results.columns:
                mask |= results[col].astype(str).str.contains(query, case=False, na=False)
        results = results[mask]
    if region_filter and "Region" in results.columns:
        results = results[results["Region"].isin(region_filter)]
    if sp_filter and "Salesperson" in results.columns:
        results = results[results["Salesperson"].isin(sp_filter)]
    if "Credit Limit" in results.columns:
        results = results[(results["Credit Limit"] >= limit_range[0]) & (results["Credit Limit"] <= limit_range[1])]

    st.dataframe(results, use_container_width=True, height=320)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        results.to_excel(writer, index=False, sheet_name="Search Results")
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("⬇️ Export Results (Excel)", buf.getvalue(), file_name="search_results.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with c2:
        st.download_button("⬇️ Export Results (CSV)", results.to_csv(index=False).encode(), file_name="search_results.csv", mime="text/csv")
else:
    st.info("Upload Customer Master to enable global search.")

st.markdown("---")

# ---------------- Audit Report Generation ----------------
section_header("Audit Report Generator", "📄")
st.write("Generate a management-ready PDF audit report with Executive Summary, Detailed Findings, and Action Points.")

if st.button("📄 Generate PDF Audit Report"):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm as rl_cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        import base64

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("TitleX", parent=styles["Title"], textColor=colors.HexColor("#0f1729"))
        h2_style = ParagraphStyle("H2X", parent=styles["Heading2"], textColor=colors.HexColor("#2563eb"))
        body_style = styles["BodyText"]

        buf_pdf = io.BytesIO()
        doc = SimpleDocTemplate(buf_pdf, pagesize=A4, topMargin=2*rl_cm, bottomMargin=2*rl_cm)
        elements = []

        logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png")
        try:
            elements.append(Image(logo_path, width=2.2*rl_cm, height=2.2*rl_cm))
        except Exception:
            pass

        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f"{st.session_state.company_name} — Credit Control Audit Report", title_style))
        elements.append(Paragraph(f"Generated: {datetime.now().strftime('%d %b %Y, %H:%M')}", body_style))
        elements.append(Spacer(1, 16))

        elements.append(Paragraph("Executive Summary", h2_style))
        summary_text = "This report summarizes key findings from the automated Customer Master & Credit Control audit covering credit limit breaches, duplicate records, GSTIN/KYC compliance, overdue accounts, and credit master change activity."
        elements.append(Paragraph(summary_text, body_style))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("Detailed Findings", h2_style))
        aging = st.session_state.get("aging")
        gdf = gstin_audit(cm) if cm is not None and "GSTIN" in cm.columns else None
        dup_pairs = find_duplicates_fuzzy(cm) if cm is not None and len(cm) < 400 else None

        breach_df = pd.DataFrame()
        if cm is not None and aging is not None and "Credit Limit" in cm.columns and "Outstanding Amount" in aging.columns:
            merged = cm.merge(aging, on="Customer Code", how="inner")
            breach_df = merged[merged["Outstanding Amount"] > merged["Credit Limit"]]

        insights = generate_insights(credit_breaches=breach_df, duplicates=dup_pairs, gstin_audit_df=gdf)
        for ins in insights:
            elements.append(Paragraph(f"• {ins}", body_style))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("Management Action Points", h2_style))
        recs = generate_recommendations(st.session_state.get("_risk_summary_cache"))
        for r in recs:
            elements.append(Paragraph(f"• {r}", body_style))

        doc.build(elements)
        st.success("✅ PDF report generated successfully.")
        st.download_button("⬇️ Download Audit Report (PDF)", buf_pdf.getvalue(),
                            file_name="credit_control_audit_report.pdf", mime="application/pdf")
    except ImportError:
        st.error("`reportlab` is not installed. Run: pip install reportlab")
