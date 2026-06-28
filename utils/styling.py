"""
Premium Styling Module
Customer Master & Credit Control Audit Portal
Glassmorphism + Enterprise Dark/Light theme
"""
import streamlit as st
import base64
from pathlib import Path

LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "logo.png"


def get_base64_logo() -> str:
    """Return base64-encoded logo for embedding in HTML/CSS."""
    try:
        with open(LOGO_PATH, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return ""


def inject_favicon():
    """Set page favicon to the company logo (called via st.set_page_config in each page)."""
    return str(LOGO_PATH)


def load_theme(dark: bool = True):
    """Inject the full custom CSS theme based on dark/light toggle."""

    if dark:
        bg_grad = "linear-gradient(135deg, #0a0e1a 0%, #0f1729 45%, #131b2e 100%)"
        glass_bg = "rgba(255, 255, 255, 0.045)"
        glass_border = "rgba(255, 255, 255, 0.09)"
        text_primary = "#eef2f9"
        text_secondary = "#9aa7bd"
        card_shadow = "0 8px 32px rgba(0, 0, 0, 0.45)"
        accent = "#3b82f6"
        accent2 = "#06b6d4"
        sidebar_bg = "linear-gradient(180deg, #0b1020 0%, #0e1426 100%)"
        table_bg = "rgba(255,255,255,0.03)"
        input_bg = "rgba(255,255,255,0.06)"
    else:
        bg_grad = "linear-gradient(135deg, #f4f7fc 0%, #eef2f9 45%, #e7ecf5 100%)"
        glass_bg = "rgba(255, 255, 255, 0.65)"
        glass_border = "rgba(15, 23, 42, 0.08)"
        text_primary = "#0f1729"
        text_secondary = "#475569"
        card_shadow = "0 8px 32px rgba(15, 23, 42, 0.10)"
        accent = "#2563eb"
        accent2 = "#0891b2"
        sidebar_bg = "linear-gradient(180deg, #ffffff 0%, #f1f5fb 100%)"
        table_bg = "rgba(15,23,42,0.02)"
        input_bg = "rgba(15,23,42,0.04)"

    st.markdown(
        f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap');

    :root {{
        --accent: {accent};
        --accent2: {accent2};
        --text-primary: {text_primary};
        --text-secondary: {text_secondary};
        --glass-bg: {glass_bg};
        --glass-border: {glass_border};
        --card-shadow: {card_shadow};
        --table-bg: {table_bg};
        --input-bg: {input_bg};
    }}

    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, sans-serif;
    }}

    .stApp {{
        background: {bg_grad};
        color: {text_primary};
    }}

    /* Hide default streamlit chrome */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header[data-testid="stHeader"] {{background: transparent;}}

    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background: {sidebar_bg};
        border-right: 1px solid {glass_border};
    }}
    section[data-testid="stSidebar"] .block-container {{
        padding-top: 1.2rem;
    }}

    /* Headings */
    h1, h2, h3 {{
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: {text_primary} !important;
        letter-spacing: -0.02em;
    }}
    h1 {{ font-weight: 800 !important; }}
    h2, h3 {{ font-weight: 700 !important; }}

    p, span, div, label {{ color: {text_secondary}; }}

    /* ===== Glass card ===== */
    .glass-card {{
        background: {glass_bg};
        backdrop-filter: blur(18px) saturate(160%);
        -webkit-backdrop-filter: blur(18px) saturate(160%);
        border: 1px solid {glass_border};
        border-radius: 18px;
        padding: 22px 24px;
        box-shadow: {card_shadow};
        transition: transform 0.25s ease, box-shadow 0.25s ease;
        animation: fadeInUp 0.5s ease;
    }}
    .glass-card:hover {{
        transform: translateY(-4px);
        box-shadow: 0 14px 40px rgba(59,130,246,0.18);
    }}

    @keyframes fadeInUp {{
        from {{ opacity: 0; transform: translateY(14px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    @keyframes pulseGlow {{
        0%, 100% {{ box-shadow: 0 0 0 0 rgba(59,130,246,0.25); }}
        50% {{ box-shadow: 0 0 0 8px rgba(59,130,246,0); }}
    }}
    @keyframes shimmer {{
        0% {{ background-position: -400px 0; }}
        100% {{ background-position: 400px 0; }}
    }}

    /* ===== KPI metric card ===== */
    .kpi-card {{
        background: {glass_bg};
        backdrop-filter: blur(18px) saturate(160%);
        border: 1px solid {glass_border};
        border-radius: 16px;
        padding: 18px 20px;
        box-shadow: {card_shadow};
        position: relative;
        overflow: hidden;
        animation: fadeInUp 0.6s ease;
    }}
    .kpi-card::before {{
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--accent), var(--accent2));
    }}
    .kpi-label {{
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: {text_secondary};
        margin-bottom: 6px;
    }}
    .kpi-value {{
        font-size: 1.9rem;
        font-weight: 800;
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: {text_primary};
        line-height: 1.1;
    }}
    .kpi-delta-up {{ color: #22c55e; font-size: 0.82rem; font-weight: 600; }}
    .kpi-delta-down {{ color: #ef4444; font-size: 0.82rem; font-weight: 600; }}
    .kpi-icon {{
        font-size: 1.4rem;
        opacity: 0.85;
    }}

    /* Risk badges */
    .badge {{
        display: inline-block;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.02em;
    }}
    .badge-critical {{ background: rgba(239,68,68,0.16); color: #ef4444; border: 1px solid rgba(239,68,68,0.35); }}
    .badge-high {{ background: rgba(249,115,22,0.16); color: #f97316; border: 1px solid rgba(249,115,22,0.35); }}
    .badge-medium {{ background: rgba(234,179,8,0.16); color: #eab308; border: 1px solid rgba(234,179,8,0.35); }}
    .badge-low {{ background: rgba(34,197,94,0.16); color: #22c55e; border: 1px solid rgba(34,197,94,0.35); }}

    /* Section header w/ accent bar */
    .section-header {{
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 1.4rem 0 0.9rem 0;
    }}
    .section-bar {{
        width: 5px;
        height: 26px;
        border-radius: 4px;
        background: linear-gradient(180deg, var(--accent), var(--accent2));
    }}

    /* Buttons */
    .stButton > button {{
        background: linear-gradient(135deg, var(--accent), var(--accent2));
        color: #ffffff !important;
        border: none;
        border-radius: 10px;
        padding: 0.55rem 1.2rem;
        font-weight: 600;
        transition: all 0.2s ease;
        box-shadow: 0 4px 14px rgba(59,130,246,0.3);
    }}
    .stButton > button p {{
        color: #ffffff !important;
    }}
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(59,130,246,0.4);
    }}

    /* Inputs */
    .stTextInput input, .stNumberInput input, .stSelectbox > div > div, .stMultiSelect > div > div {{
        background: var(--input-bg) !important;
        border-radius: 10px !important;
        border: 1px solid {glass_border} !important;
        color: {text_primary} !important;
    }}

    /* DataFrames */
    [data-testid="stDataFrame"] {{
        border-radius: 14px;
        overflow: hidden;
        border: 1px solid {glass_border};
    }}

    /* Tabs (used in Excel Import Center for switching between datasets) */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 6px;
        background: var(--table-bg);
        padding: 6px;
        border-radius: 12px;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 9px;
        font-weight: 600;
        color: #ffffff !important;
    }}
    .stTabs [data-baseweb="tab"] p {{
        color: #ffffff !important;
    }}
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
        color: #ffffff !important;
    }}

    /* Progress / KYC score bar */
    .score-track {{
        width: 100%;
        height: 10px;
        background: {table_bg};
        border-radius: 999px;
        overflow: hidden;
        border: 1px solid {glass_border};
    }}
    .score-fill {{
        height: 100%;
        border-radius: 999px;
        background: linear-gradient(90deg, var(--accent), var(--accent2));
    }}

    /* Sidebar logo container */
    .sidebar-logo-wrap {{
        text-align: center;
        padding: 6px 0 18px 0;
        border-bottom: 1px solid {glass_border};
        margin-bottom: 14px;
    }}
    .sidebar-logo-wrap img {{
        border-radius: 14px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.25);
    }}
    .brand-title {{
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 800;
        font-size: 0.95rem;
        color: {text_primary};
        margin-top: 8px;
        letter-spacing: 0.01em;
    }}
    .brand-subtitle {{
        font-size: 0.72rem;
        color: {text_secondary};
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }}

    /* Login page */
    .login-wrapper {{
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 78vh;
    }}
    .login-card {{
        background: {glass_bg};
        backdrop-filter: blur(22px) saturate(160%);
        border: 1px solid {glass_border};
        border-radius: 22px;
        padding: 46px 44px;
        width: 420px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.35);
        text-align: center;
        animation: fadeInUp 0.6s ease;
    }}

    /* Animated gradient top bar for header */
    .top-banner {{
        background: {glass_bg};
        backdrop-filter: blur(18px);
        border: 1px solid {glass_border};
        border-radius: 18px;
        padding: 18px 26px;
        box-shadow: {card_shadow};
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.2rem;
        animation: fadeInUp 0.5s ease;
    }}

    hr {{ border-color: {glass_border}; }}
    </style>
    """,
        unsafe_allow_html=True,
    )


def kpi_card(label: str, value: str, icon: str = "📊", delta: str = None, delta_positive: bool = True):
    """Render a single animated KPI glass card."""
    delta_html = ""
    if delta:
        cls = "kpi-delta-up" if delta_positive else "kpi-delta-down"
        arrow = "▲" if delta_positive else "▼"
        delta_html = f'<div class="{cls}">{arrow} {delta}</div>'
    st.markdown(
        f"""
        <div class="kpi-card">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div class="kpi-label">{label}</div>
                <div class="kpi-icon">{icon}</div>
            </div>
            <div class="kpi-value">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, icon: str = ""):
    st.markdown(
        f"""
        <div class="section-header">
            <div class="section-bar"></div>
            <h3 style="margin:0;">{icon} {title}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )


def risk_badge(level: str) -> str:
    level = (level or "Low").lower()
    return f'<span class="badge badge-{level}">{level.upper()}</span>'


def render_sidebar_logo(company_name: str = "Your Company"):
    logo_b64 = get_base64_logo()
    if logo_b64:
        st.markdown(
            f"""
            <div class="sidebar-logo-wrap">
                <img src="data:image/png;base64,{logo_b64}" width="86">
                <div class="brand-title">{company_name}</div>
                <div class="brand-subtitle">Credit Risk &amp; Audit Portal</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(f"### {company_name}")
