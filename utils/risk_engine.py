"""
Composite Risk Scoring Engine
Risk Score = Credit Breach(30%) + Overdue Balance(25%) + Invalid GSTIN(15%)
            + Missing KYC(15%) + Suspicious Changes(15%)
"""
import pandas as pd
import numpy as np

WEIGHTS = {
    "credit_breach": 0.30,
    "overdue_balance": 0.25,
    "invalid_gstin": 0.15,
    "missing_kyc": 0.15,
    "suspicious_changes": 0.15,
}


def _normalize(series: pd.Series) -> pd.Series:
    s = series.fillna(0).astype(float)
    if s.max() == s.min():
        return pd.Series(np.zeros(len(s)), index=s.index)
    return (s - s.min()) / (s.max() - s.min())


def classify(score: float) -> str:
    if score >= 75:
        return "Critical"
    elif score >= 55:
        return "High"
    elif score >= 30:
        return "Medium"
    return "Low"


def compute_risk_scores(
    customers: pd.DataFrame,
    aging: pd.DataFrame = None,
    gstin_flags: pd.Series = None,
    kyc_scores: pd.Series = None,
    suspicious_change_counts: pd.Series = None,
    code_col: str = "Customer Code",
) -> pd.DataFrame:
    """
    Build a per-customer composite risk score.
    All optional inputs are aligned to `customers` via the customer code column.
    """
    df = customers[[code_col]].drop_duplicates().copy()
    df = df.set_index(code_col)

    # Credit breach component
    if "Credit Limit" in customers.columns and aging is not None and "Outstanding Amount" in aging.columns:
        merged = customers[[code_col, "Credit Limit"]].merge(
            aging[[code_col, "Outstanding Amount"]], on=code_col, how="left"
        ).set_index(code_col)
        breach_amount = (merged["Outstanding Amount"] - merged["Credit Limit"]).clip(lower=0)
        df["credit_breach_raw"] = breach_amount.reindex(df.index).fillna(0)
    else:
        df["credit_breach_raw"] = 0

    # Overdue balance component
    if aging is not None and "Above 180 Days" in aging.columns:
        overdue = aging.set_index(code_col)["Above 180 Days"].reindex(df.index).fillna(0)
        df["overdue_raw"] = overdue
    else:
        df["overdue_raw"] = 0

    # Invalid GSTIN component (binary 0/1)
    if gstin_flags is not None:
        df["gstin_raw"] = gstin_flags.reindex(df.index).fillna(0).astype(int)
    else:
        df["gstin_raw"] = 0

    # Missing KYC component (100 - score, normalized)
    if kyc_scores is not None:
        df["kyc_raw"] = (100 - kyc_scores.reindex(df.index).fillna(0))
    else:
        df["kyc_raw"] = 0

    # Suspicious changes component
    if suspicious_change_counts is not None:
        df["changes_raw"] = suspicious_change_counts.reindex(df.index).fillna(0)
    else:
        df["changes_raw"] = 0

    # Normalize each component to 0-100 then apply weights
    df["Credit Breach Score"] = _normalize(df["credit_breach_raw"]) * 100
    df["Overdue Score"] = _normalize(df["overdue_raw"]) * 100
    df["GSTIN Score"] = _normalize(df["gstin_raw"]) * 100
    df["KYC Score"] = _normalize(df["kyc_raw"]) * 100
    df["Change Score"] = _normalize(df["changes_raw"]) * 100

    df["Risk Score"] = (
        df["Credit Breach Score"] * WEIGHTS["credit_breach"]
        + df["Overdue Score"] * WEIGHTS["overdue_balance"]
        + df["GSTIN Score"] * WEIGHTS["invalid_gstin"]
        + df["KYC Score"] * WEIGHTS["missing_kyc"]
        + df["Change Score"] * WEIGHTS["suspicious_changes"]
    ).round(1)

    df["Risk Category"] = df["Risk Score"].apply(classify)
    df = df.reset_index()
    return df[[code_col, "Credit Breach Score", "Overdue Score", "GSTIN Score",
               "KYC Score", "Change Score", "Risk Score", "Risk Category"]]


def detect_suspicious_changes(change_log: pd.DataFrame) -> pd.DataFrame:
    """
    Flag suspicious entries in the credit master change log:
    - Credit limit increase > 50%
    - Credit days increase > 30%
    - Multiple changes within 30 days for same customer
    - Changes outside business hours (before 9am / after 7pm)
    """
    df = change_log.copy()
    df["Change Date"] = pd.to_datetime(df["Change Date"], errors="coerce")

    df["Limit Increase %"] = np.where(
        df["Old Credit Limit"].fillna(0) > 0,
        (df["New Credit Limit"] - df["Old Credit Limit"]) / df["Old Credit Limit"] * 100,
        0,
    )
    df["Days Increase %"] = np.where(
        df["Old Credit Days"].fillna(0) > 0,
        (df["New Credit Days"] - df["Old Credit Days"]) / df["Old Credit Days"] * 100,
        0,
    )

    df["Flag: Limit Spike"] = df["Limit Increase %"] > 50
    df["Flag: Days Spike"] = df["Days Increase %"] > 30
    df["Flag: Off Hours"] = df["Change Date"].dt.hour.apply(
        lambda h: (h < 9 or h >= 19) if pd.notna(h) else False
    )

    df = df.sort_values(["Customer Code", "Change Date"])
    df["Days Since Last Change"] = df.groupby("Customer Code")["Change Date"].diff().dt.days
    df["Flag: Frequent Changes"] = df["Days Since Last Change"] <= 30

    flag_cols = ["Flag: Limit Spike", "Flag: Days Spike", "Flag: Off Hours", "Flag: Frequent Changes"]
    df["Is Suspicious"] = df[flag_cols].any(axis=1)
    df["Flag Count"] = df[flag_cols].sum(axis=1)

    return df


def suspicious_change_counts_by_customer(flagged_changes: pd.DataFrame) -> pd.Series:
    return flagged_changes.groupby("Customer Code")["Is Suspicious"].sum()
