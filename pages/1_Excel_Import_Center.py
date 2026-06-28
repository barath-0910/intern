import streamlit as st
from utils.styling import load_theme, render_sidebar_logo, section_header, inject_favicon
from utils.data_loader import init_session_state, read_uploaded_file, validate_schema

st.set_page_config(page_title="Excel Import Center", page_icon=inject_favicon(), layout="wide")
init_session_state()
load_theme(dark=st.session_state.dark_mode)

if not st.session_state.authenticated:
    st.warning("Please sign in from the main page first.")
    st.stop()

with st.sidebar:
    render_sidebar_logo(st.session_state.company_name)

st.markdown("## 📥 Excel Import Center")
st.caption("Upload your audit datasets. Supported formats: **XLSX, XLS, CSV**")

datasets = [
    {"key": "customer_master", "label": "Customer Master", "icon": "👥",
     "desc": "Customer Code, Customer Name, GSTIN, PAN, Credit Limit, Credit Days, Region, Salesperson, Customer Status, Created Date"},
    {"key": "aging", "label": "Accounts Receivable Aging", "icon": "📊",
     "desc": "Customer Code, Outstanding Amount, 0-30 Days, 31-60 Days, 61-90 Days, 91-180 Days, Above 180 Days"},
    {"key": "sales", "label": "Sales Transactions", "icon": "🧾",
     "desc": "Invoice No, Customer Code, Invoice Date, Invoice Amount"},
    {"key": "change_log", "label": "Credit Master Change Log", "icon": "📝",
     "desc": "User, Change Date, Customer Code, Old Credit Limit, New Credit Limit, Old Credit Days, New Credit Days"},
]

tabs = st.tabs([f"{d['icon']} {d['label']}" for d in datasets])

for tab, d in zip(tabs, datasets):
    with tab:
        st.markdown(
            f"""
            <div class="glass-card" style="margin-bottom:16px;">
                <b>{d['label']}</b><br>
                <span style="font-size:0.85rem;">Required columns: {d['desc']}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        file = st.file_uploader(
            f"Drag and drop {d['label']} file here",
            type=["xlsx", "xls", "csv"],
            key=f"upload_{d['key']}",
        )
        if file is not None:
            df = read_uploaded_file(file)
            if df is not None:
                missing = validate_schema(df, d["key"])
                if missing:
                    st.warning(f"⚠️ Missing expected columns: {', '.join(missing)} — data loaded anyway, some checks may be limited.")
                st.session_state[d["key"]] = df
                st.success(f"✅ Loaded {len(df):,} rows into {d['label']}")
                st.dataframe(df.head(20), use_container_width=True, height=300)

        existing = st.session_state.get(d["key"])
        if existing is not None and file is None:
            st.info(f"Currently loaded: {len(existing):,} rows from a previous upload.")
            st.dataframe(existing.head(20), use_container_width=True, height=280)

st.markdown("---")
section_header("Need Sample Templates?", "📋")
st.write("Download ready-to-use Excel templates matching the required schema from the **Sample Templates** folder included with this portal (`sample_data/`).")
