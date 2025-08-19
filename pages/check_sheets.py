import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

# Load secrets
creds_dict = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(
    creds_dict,
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)

client = gspread.authorize(creds)

# Grab all response sheet IDs
sheet_ids = st.secrets["google"]["response_sheet_urls"]

print("🔍 Checking worksheets for each response sheet...\n")
for subject, sheet_id in sheet_ids.items():
    try:
        sh = client.open_by_key(sheet_id)
        worksheets = [ws.title for ws in sh.worksheets()]
        print(f"✅ {subject}: {worksheets}")
    except Exception as e:
        print(f"❌ {subject}: {e}")
