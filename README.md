# Customer Master & Credit Control Audit Portal

A premium, enterprise-grade Streamlit application for Internal Audit, Finance, Credit Control, and Risk teams to review customer master data and credit controls — styled like a Big-4 audit analytics solution (SAP / Oracle / Deloitte / PwC aesthetic).

## ✨ Features

- **Glassmorphism UI** with dark/light theme toggle, smooth animations, gradient accents
- **Login page** with your company logo, branded sidebar & header throughout
- **Excel Import Center** — drag-and-drop XLSX/XLS/CSV upload for 4 data sources
- **Executive Dashboard** with animated KPI cards, AI Insights panel, risk distribution & exposure charts
- **Module 1 – Credit Limit Review**: breach detection, severity scoring, override approval exceptions, gauge/heatmap/treemap visuals
- **Module 2 – Duplicate Customer Detection**: exact + fuzzy matching (RapidFuzz), similarity network graph, similarity matrix
- **Module 3 – KYC & GSTIN Validation**: GSTIN format/length/duplicate checks, KYC completeness scoring, donut + scorecard visuals
- **Module 4 – Long Overdue Customer Review**: >180-day overdue customers still receiving sales, heatmap, scatter, top-20 risk table
- **Module 5 – Credit Master Change Audit**: suspicious change detection (limit spikes, day spikes, off-hours, frequent changes), audit timeline, user leaderboard
- **Composite Risk Scoring Engine**: weighted risk score (Credit Breach 30% / Overdue 25% / Invalid GSTIN 15% / Missing KYC 15% / Suspicious Changes 15%), risk matrix & register
- **Search & Export Center**: global search/filters, Excel/CSV export, one-click **PDF audit report** generation (ReportLab) with Executive Summary, Detailed Findings, and Management Action Points

## 📁 Folder Structure

```
audit_portal/
├── app.py                          # Main entry: login + executive dashboard
├── pages/
│   ├── 1_Excel_Import_Center.py
│   ├── 2_Credit_Limit_Review.py
│   ├── 3_Duplicate_Detection.py
│   ├── 4_KYC_GSTIN_Validation.py
│   ├── 5_Overdue_Review.py
│   ├── 6_Change_Audit.py
│   ├── 7_Risk_Scoring.py
│   └── 8_Search_Export.py
├── utils/
│   ├── styling.py                  # Custom CSS / glass cards / KPI components
│   ├── data_loader.py              # File reading + session state
│   ├── validators.py               # GSTIN / PAN / KYC / duplicate logic
│   ├── risk_engine.py              # Composite risk scoring + change-log audit
│   └── ai_insights.py              # Natural-language insights & recommendations
├── assets/
│   └── logo.png                    # Your company logo (auto-loaded into sidebar/login/header/favicon)
├── sample_data/
│   ├── generate_templates.py       # Regenerates the 4 sample Excel templates
│   ├── Customer_Master_Template.xlsx
│   ├── AR_Aging_Template.xlsx
│   ├── Sales_Transactions_Template.xlsx
│   └── Change_Log_Template.xlsx
├── .streamlit/config.toml          # Theme config
├── requirements.txt
└── README.md
```

## 🚀 Getting Started

```bash
# 1. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

The app opens at `http://localhost:8501`. Sign in with any credentials (demo mode — wire up real auth for production).

## 📊 Required Excel Schemas

| Dataset | Required Columns |
|---|---|
| **Customer Master** | Customer Code, Customer Name, GSTIN, PAN, Credit Limit, Credit Days, Region, Salesperson, Customer Status, Created Date |
| **AR Aging** | Customer Code, Outstanding Amount, 0-30 Days, 31-60 Days, 61-90 Days, 91-180 Days, Above 180 Days |
| **Sales Transactions** | Invoice No, Customer Code, Invoice Date, Invoice Amount |
| **Change Log** | User, Change Date, Customer Code, Old Credit Limit, New Credit Limit, Old Credit Days, New Credit Days |

Sample templates matching these schemas are in `sample_data/`. Re-run `python sample_data/generate_templates.py` any time to regenerate them.

## 🎯 Risk Scoring Formula

```
Risk Score = (Credit Breach × 0.30) + (Overdue Balance × 0.25)
           + (Invalid GSTIN × 0.15) + (Missing KYC × 0.15)
           + (Suspicious Changes × 0.15)

Classification:
  0–29   → Low
  30–54  → Medium
  55–74  → High
  75–100 → Critical
```

## 🖌️ Customizing the Logo

Replace `assets/logo.png` with your own logo (square image recommended, PNG with transparent background works best). It's automatically used for:
- Browser favicon
- Login page
- Sidebar branding
- Dashboard header banner

## 🛠️ Tech Stack

Streamlit · Pandas · NumPy · Plotly · OpenPyXL · RapidFuzz · NetworkX · ReportLab · Streamlit-AgGrid

## 📝 Notes

- This is a **demo-mode** app: authentication is not connected to a real identity provider. For production use, integrate `streamlit-authenticator`, SSO, or your internal IAM.
- The AI Insights panel uses deterministic rule-based logic on top of the computed audit results. To use a real LLM (e.g., Claude) for richer narrative insights, plug an API call into `utils/ai_insights.py`.
- All modules gracefully degrade if a dataset hasn't been uploaded yet — the dashboard will prompt you to load the relevant file from the Excel Import Center.
