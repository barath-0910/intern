import pandas as pd
from datetime import datetime, timedelta
import os

OUT = os.path.dirname(__file__)

customer_master = pd.DataFrame([
    {"Customer Code": "CUST001", "Customer Name": "Apex Industries Pvt Ltd", "GSTIN": "29ABCDE1234F1Z5", "PAN": "ABCDE1234F",
     "Credit Limit": 500000, "Credit Days": 45, "Region": "South", "Salesperson": "R. Kumar", "Customer Status": "Active", "Created Date": "2021-03-12"},
    {"Customer Code": "CUST002", "Customer Name": "Bright Star Traders", "GSTIN": "27XYZAB5678G1Z9", "PAN": "XYZAB5678G",
     "Credit Limit": 300000, "Credit Days": 30, "Region": "West", "Salesperson": "S. Mehta", "Customer Status": "Active", "Created Date": "2020-11-05"},
    {"Customer Code": "CUST003", "Customer Name": "Bright Star Trader", "GSTIN": "27XYZAB5678G1Z9", "PAN": "XYZAB5679G",
     "Credit Limit": 250000, "Credit Days": 30, "Region": "West", "Salesperson": "S. Mehta", "Customer Status": "Active", "Created Date": "2022-01-15"},
    {"Customer Code": "CUST004", "Customer Name": "Coastal Logistics Co", "GSTIN": "INVALIDGSTIN123", "PAN": "PQRST6789H",
     "Credit Limit": 750000, "Credit Days": 60, "Region": "East", "Salesperson": "A. Sen", "Customer Status": "Active", "Created Date": "2019-07-22"},
    {"Customer Code": "CUST005", "Customer Name": "Delta Manufacturing", "GSTIN": "", "PAN": "LMNOP4321K",
     "Credit Limit": 1000000, "Credit Days": 90, "Region": "North", "Salesperson": "R. Kumar", "Customer Status": "Inactive", "Created Date": "2018-02-10"},
])

aging = pd.DataFrame([
    {"Customer Code": "CUST001", "Outstanding Amount": 620000, "0-30 Days": 200000, "31-60 Days": 150000, "61-90 Days": 100000, "91-180 Days": 100000, "Above 180 Days": 70000},
    {"Customer Code": "CUST002", "Outstanding Amount": 280000, "0-30 Days": 280000, "31-60 Days": 0, "61-90 Days": 0, "91-180 Days": 0, "Above 180 Days": 0},
    {"Customer Code": "CUST003", "Outstanding Amount": 260000, "0-30 Days": 50000, "31-60 Days": 50000, "61-90 Days": 60000, "91-180 Days": 60000, "Above 180 Days": 40000},
    {"Customer Code": "CUST004", "Outstanding Amount": 900000, "0-30 Days": 100000, "31-60 Days": 100000, "61-90 Days": 100000, "91-180 Days": 300000, "Above 180 Days": 300000},
    {"Customer Code": "CUST005", "Outstanding Amount": 1200000, "0-30 Days": 0, "31-60 Days": 0, "61-90 Days": 0, "91-180 Days": 200000, "Above 180 Days": 1000000},
])

base_date = datetime(2026, 5, 1)
sales = pd.DataFrame([
    {"Invoice No": "INV1001", "Customer Code": "CUST001", "Invoice Date": base_date, "Invoice Amount": 120000},
    {"Invoice No": "INV1002", "Customer Code": "CUST004", "Invoice Date": base_date + timedelta(days=3), "Invoice Amount": 95000},
    {"Invoice No": "INV1003", "Customer Code": "CUST005", "Invoice Date": base_date + timedelta(days=10), "Invoice Amount": 250000},
    {"Invoice No": "INV1004", "Customer Code": "CUST002", "Invoice Date": base_date + timedelta(days=12), "Invoice Amount": 60000},
])

change_log = pd.DataFrame([
    {"User": "admin.raj", "Change Date": datetime(2026, 4, 10, 14, 30), "Customer Code": "CUST001", "Old Credit Limit": 300000, "New Credit Limit": 500000, "Old Credit Days": 30, "New Credit Days": 45},
    {"User": "admin.raj", "Change Date": datetime(2026, 4, 22, 22, 15), "Customer Code": "CUST004", "Old Credit Limit": 400000, "New Credit Limit": 750000, "Old Credit Days": 45, "New Credit Days": 60},
    {"User": "ops.simran", "Change Date": datetime(2026, 4, 25, 11, 0), "Customer Code": "CUST005", "Old Credit Limit": 800000, "New Credit Limit": 1000000, "Old Credit Days": 60, "New Credit Days": 90},
    {"User": "admin.raj", "Change Date": datetime(2026, 5, 2, 23, 45), "Customer Code": "CUST004", "Old Credit Limit": 750000, "New Credit Limit": 950000, "Old Credit Days": 60, "New Credit Days": 75},
])

with pd.ExcelWriter(os.path.join(OUT, "Customer_Master_Template.xlsx"), engine="openpyxl") as writer:
    customer_master.to_excel(writer, index=False, sheet_name="Customer Master")

with pd.ExcelWriter(os.path.join(OUT, "AR_Aging_Template.xlsx"), engine="openpyxl") as writer:
    aging.to_excel(writer, index=False, sheet_name="AR Aging")

with pd.ExcelWriter(os.path.join(OUT, "Sales_Transactions_Template.xlsx"), engine="openpyxl") as writer:
    sales.to_excel(writer, index=False, sheet_name="Sales Transactions")

with pd.ExcelWriter(os.path.join(OUT, "Change_Log_Template.xlsx"), engine="openpyxl") as writer:
    change_log.to_excel(writer, index=False, sheet_name="Change Log")

print("Templates generated.")
