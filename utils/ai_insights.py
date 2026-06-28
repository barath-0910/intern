"""
AI Insights Panel — rule-based natural-language observation generator.
(No external LLM call required; deterministic insights from computed audit data,
 phrased like an analyst would write them. Swap in a real LLM call easily if desired.)
"""
import pandas as pd


def generate_insights(
    credit_breaches: pd.DataFrame = None,
    duplicates: pd.DataFrame = None,
    gstin_audit_df: pd.DataFrame = None,
    overdue_df: pd.DataFrame = None,
    suspicious_changes: pd.DataFrame = None,
) -> list:
    insights = []

    if credit_breaches is not None and len(credit_breaches) > 0:
        insights.append(
            f"⚠️ {len(credit_breaches)} customers exceeded their approved credit limits, "
            f"representing a combined exposure increase that requires Credit Control review."
        )

    if duplicates is not None and len(duplicates) > 0:
        gstin_dupes = duplicates[duplicates.get("GSTIN Match", False) == True] if "GSTIN Match" in duplicates.columns else pd.DataFrame()
        if len(gstin_dupes) > 0:
            insights.append(f"🔁 {len(gstin_dupes)} duplicate GSTINs were detected across the customer master, indicating possible duplicate vendor/customer records.")
        insights.append(f"🔁 {len(duplicates)} potential duplicate customer pairs identified via fuzzy name/GSTIN/PAN matching.")

    if gstin_audit_df is not None:
        invalid_count = (gstin_audit_df.get("GSTIN_Status") == "Invalid").sum() if "GSTIN_Status" in gstin_audit_df.columns else 0
        blank_count = (gstin_audit_df.get("GSTIN_Status") == "Blank").sum() if "GSTIN_Status" in gstin_audit_df.columns else 0
        if invalid_count:
            insights.append(f"🧾 {invalid_count} customers have invalid or malformed GSTINs that do not meet statutory format requirements.")
        if blank_count:
            insights.append(f"🧾 {blank_count} customer records are missing GSTIN entirely, posing compliance risk.")

    if overdue_df is not None and len(overdue_df) > 0:
        insights.append(
            f"⏰ {len(overdue_df)} customers are overdue more than 180 days and continue to receive new sales invoices — "
            f"these accounts should be placed on credit hold pending review."
        )

    if suspicious_changes is not None and len(suspicious_changes) > 0:
        susp = suspicious_changes[suspicious_changes.get("Is Suspicious", False) == True] if "Is Suspicious" in suspicious_changes.columns else suspicious_changes
        if len(susp) > 0:
            if "Limit Increase %" in susp.columns:
                total_increase = (susp.get("New Credit Limit", 0) - susp.get("Old Credit Limit", 0)).clip(lower=0).sum()
                insights.append(f"📈 Credit master changes increased aggregate exposure by approximately ₹{total_increase:,.0f}, driven by {len(susp)} flagged change events.")
            top_users = susp["User"].value_counts().head(1)
            if len(top_users) > 0:
                insights.append(f"👤 User '{top_users.index[0]}' was responsible for the highest number of flagged credit master changes ({int(top_users.iloc[0])} events) — recommend segregation-of-duties review.")

    if not insights:
        insights.append("✅ No material exceptions detected across the uploaded datasets based on current thresholds.")

    return insights


def generate_recommendations(risk_summary: pd.DataFrame = None) -> list:
    recs = []
    if risk_summary is not None and "Risk Category" in risk_summary.columns:
        critical = (risk_summary["Risk Category"] == "Critical").sum()
        high = (risk_summary["Risk Category"] == "High").sum()
        if critical:
            recs.append(f"Place {critical} 'Critical' risk customers on immediate credit hold and escalate to the Credit Control Committee.")
        if high:
            recs.append(f"Schedule management review of {high} 'High' risk customer accounts within the next 5 business days.")
    recs.append("Enforce maker-checker approval workflow for any credit limit increase exceeding 50%.")
    recs.append("Mandate GSTIN and KYC document re-verification for all customers flagged with compliance exceptions.")
    recs.append("Implement system-level credit hold to auto-block invoicing for customers overdue beyond 180 days.")
    return recs
