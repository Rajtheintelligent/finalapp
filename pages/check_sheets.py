import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="🔍 Check Sheets", layout="centered")
st.title("🔍 Worksheet Checker")

# Load Google credentials
creds_dict = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(
    creds_dict,
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
client = gspread.authorize(creds)

# Load response sheet URLs from secrets.toml
response_sheets = st.secrets["google"].get("response_sheet_urls", {})

if not response_sheets:
    st.error("❌ No response_sheet_urls found in your secrets.toml")
else:
    for subject, sheet_id in response_sheets.items():
        st.write(f"### 📘 {subject}")
        try:
            sh = client.open_by_key(sheet_id)
            worksheets = [ws.title for ws in sh.worksheets()]
            st.success(f"✅ Worksheets found: {worksheets}")
            
            # Check for Main & Remedial specifically
            if "Main" not in worksheets:
                st.warning("⚠️ Missing 'Main' worksheet")
            if "Remedial" not in worksheets:
                st.warning("⚠️ Missing 'Remedial' worksheet")
        except Exception as e:
            st.error(f"❌ Error: {e}")
