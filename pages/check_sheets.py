import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="🔍 Check & Fix Sheets", layout="centered")
st.title("🔍 Worksheet Checker + Auto-Fix")

# Load Google credentials
creds_dict = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(
    creds_dict,
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
client = gspread.authorize(creds)

# Load response sheet IDs from secrets.toml
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

            # Ensure Main & Remedial exist
            required = ["Main", "Remedial"]

            for req in required:
                if req not in worksheets:
                    st.warning(f"⚠️ Missing '{req}' worksheet → creating it now...")
                    new_ws = sh.add_worksheet(title=req, rows="100", cols="20")

                    # Copy headers from "Responses" if available
                    if "Responses" in worksheets:
                        responses_ws = sh.worksheet("Responses")
                        headers = responses_ws.row_values(1)
                        if headers:
                            new_ws.insert_row(headers, 1)
                            st.success(f"✅ '{req}' created with headers copied from 'Responses'")
                        else:
                            st.info(f"ℹ️ '{req}' created but 'Responses' has no headers to copy")
                    else:
                        st.info(f"ℹ️ '{req}' created but no 'Responses' sheet found")

        except Exception as e:
            st.error(f"❌ Error: {e}")
