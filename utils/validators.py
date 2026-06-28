"""
Validation utilities: GSTIN format checks, KYC completeness, duplicate detection.
"""
import re
import pandas as pd

GSTIN_REGEX = re.compile(r"^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")
PAN_REGEX = re.compile(r"^[A-Z]{5}\d{4}[A-Z]{1}$")

REQUIRED_KYC_DOCS = ["PAN", "GST Certificate", "Trade License", "Address Proof"]


def validate_gstin(gstin: str) -> dict:
    """Validate a single GSTIN. Returns dict with status flags."""
    result = {"is_blank": False, "is_valid_length": False, "is_valid_format": False}
    if pd.isna(gstin) or str(gstin).strip() == "":
        result["is_blank"] = True
        return result
    gstin = str(gstin).strip().upper()
    result["is_valid_length"] = len(gstin) == 15
    result["is_valid_format"] = bool(GSTIN_REGEX.match(gstin))
    return result


def validate_pan(pan: str) -> bool:
    if pd.isna(pan) or str(pan).strip() == "":
        return False
    return bool(PAN_REGEX.match(str(pan).strip().upper()))


def gstin_audit(df: pd.DataFrame, gstin_col: str = "GSTIN") -> pd.DataFrame:
    """Run GSTIN validation across the customer master dataframe."""
    out = df.copy()
    flags = out[gstin_col].apply(validate_gstin)
    out["GSTIN_Blank"] = flags.apply(lambda x: x["is_blank"])
    out["GSTIN_Invalid_Length"] = flags.apply(lambda x: not x["is_blank"] and not x["is_valid_length"])
    out["GSTIN_Invalid_Format"] = flags.apply(lambda x: not x["is_blank"] and not x["is_valid_format"])
    out["GSTIN_Status"] = "Valid"
    out.loc[out["GSTIN_Blank"], "GSTIN_Status"] = "Blank"
    out.loc[out["GSTIN_Invalid_Length"] | out["GSTIN_Invalid_Format"], "GSTIN_Status"] = "Invalid"

    dup_mask = out[gstin_col].duplicated(keep=False) & out[gstin_col].notna() & (out[gstin_col].astype(str).str.strip() != "")
    out["GSTIN_Duplicate"] = dup_mask
    out.loc[dup_mask, "GSTIN_Status"] = "Duplicate"
    return out


def kyc_completeness(df: pd.DataFrame, doc_columns: dict = None) -> pd.DataFrame:
    """
    Compute KYC completeness score per customer.
    doc_columns: mapping of required doc -> dataframe column name holding boolean/Y-N flag.
    If doc columns are not present in the uploaded file, this function safely defaults to
    treating PAN presence as the only available signal.
    """
    out = df.copy()
    available_docs = []
    if doc_columns is None:
        doc_columns = {}

    for doc in REQUIRED_KYC_DOCS:
        col = doc_columns.get(doc)
        if col and col in out.columns:
            available_docs.append(col)

    if not available_docs and "PAN" in out.columns:
        out["KYC_Score"] = out["PAN"].apply(lambda x: 100 if validate_pan(x) else 0)
        out["KYC_Missing_Docs"] = out["PAN"].apply(lambda x: "" if validate_pan(x) else "PAN")
        return out

    if available_docs:
        def score_row(row):
            present = sum(1 for c in available_docs if str(row.get(c, "")).strip().upper() in ("Y", "YES", "TRUE", "1"))
            return round(100 * present / len(available_docs), 1)

        def missing_row(row):
            missing = [c for c in available_docs if str(row.get(c, "")).strip().upper() not in ("Y", "YES", "TRUE", "1")]
            return ", ".join(missing)

        out["KYC_Score"] = out.apply(score_row, axis=1)
        out["KYC_Missing_Docs"] = out.apply(missing_row, axis=1)
    else:
        out["KYC_Score"] = 0
        out["KYC_Missing_Docs"] = "No KYC columns found"

    return out


def find_duplicates_fuzzy(df: pd.DataFrame, name_col="Customer Name", gstin_col="GSTIN",
                           pan_col="PAN", threshold: int = 85) -> pd.DataFrame:
    """Fuzzy duplicate detection using rapidfuzz. Falls back gracefully if not installed."""
    try:
        from rapidfuzz import fuzz
    except ImportError:
        from difflib import SequenceMatcher

        class _Fallback:
            @staticmethod
            def ratio(a, b):
                return SequenceMatcher(None, a, b).ratio() * 100

        fuzz = _Fallback()

    records = df.to_dict("records")
    pairs = []
    n = len(records)
    for i in range(n):
        for j in range(i + 1, n):
            a, b = records[i], records[j]
            name_a, name_b = str(a.get(name_col, "")), str(b.get(name_col, ""))
            if not name_a or not name_b:
                continue
            sim = fuzz.ratio(name_a.lower(), name_b.lower())
            gstin_match = str(a.get(gstin_col, "")) == str(b.get(gstin_col, "")) and str(a.get(gstin_col, "")).strip() != ""
            pan_match = str(a.get(pan_col, "")) == str(b.get(pan_col, "")) and str(a.get(pan_col, "")).strip() != ""

            if sim >= threshold or gstin_match or pan_match:
                risk = "Critical" if (gstin_match and sim >= 90) else "High" if sim >= 90 else "Medium" if sim >= threshold else "Low"
                pairs.append({
                    "Customer Code A": a.get("Customer Code"),
                    "Customer Name A": name_a,
                    "Customer Code B": b.get("Customer Code"),
                    "Customer Name B": name_b,
                    "Similarity %": round(sim, 1),
                    "GSTIN Match": gstin_match,
                    "PAN Match": pan_match,
                    "Risk Level": risk,
                })
    return pd.DataFrame(pairs)


def exact_duplicate_codes(df: pd.DataFrame, code_col="Customer Code") -> pd.DataFrame:
    dup = df[df.duplicated(subset=[code_col], keep=False)].sort_values(code_col)
    return dup
