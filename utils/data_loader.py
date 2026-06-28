"""
Data loading helpers + session state initialization.
"""
import pandas as pd
import streamlit as st
import io


REQUIRED_SCHEMAS = {
    "customer_master": ["Customer Code", "Customer Name", "GSTIN", "PAN", "Credit Limit",
                         "Credit Days", "Region", "Salesperson", "Customer Status", "Created Date"],
    "aging": ["Customer Code", "Outstanding Amount", "0-30 Days", "31-60 Days",
              "61-90 Days", "91-180 Days", "Above 180 Days"],
    "sales": ["Invoice No", "Customer Code", "Invoice Date", "Invoice Amount"],
    "change_log": ["User", "Change Date", "Customer Code", "Old Credit Limit",
                    "New Credit Limit", "Old Credit Days", "New Credit Days"],
}


def init_session_state():
    defaults = {
        "dark_mode": True,
        "authenticated": False,
        "company_name": "Your Company",
        "customer_master": None,
        "aging": None,
        "sales": None,
        "change_log": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def read_uploaded_file(uploaded_file) -> pd.DataFrame:
    """Read xlsx / xls / csv into a DataFrame with basic error handling."""
    name = uploaded_file.name.lower()
    try:
        if name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Failed to read {uploaded_file.name}: {e}")
        return None


def validate_schema(df: pd.DataFrame, dataset_key: str) -> list:
    """Return a list of missing required columns for the given dataset type."""
    required = REQUIRED_SCHEMAS.get(dataset_key, [])
    missing = [c for c in required if c not in df.columns]
    return missing


def get_data_or_none(key: str):
    return st.session_state.get(key)


def has_any_data() -> bool:
    return any(st.session_state.get(k) is not None for k in
               ["customer_master", "aging", "sales", "change_log"])
