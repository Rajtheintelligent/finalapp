import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- Helper: Normalize Image URLs ---
def normalize_img_url(value):
    value = str(value or "").strip()
    if not value:
        return ""
    # Already a full Drive direct link
    if value.startswith("https://drive.google.com/uc?export=download&id="):
        return value
    # Just a file ID (no slashes, long enough to be a Drive ID)
    if len(value) > 20 and "/" not in value:
        return f"https://drive.google.com/uc?export=download&id={value}"
    return value

# --- Page config ---
st.set_page_config(page_title="Form Page", layout="wide")

# --- Get URL query parameters ---
params = st.query_params
subject = params.get("subject", "")
subtopic_id = params.get("subtopic_id", "")

if not subject or not subtopic_id:
    st.error("❌ Missing subject or subtopic_id in URL.")
    st.stop()

# --- Connect to Google Sheets ---
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=scope
)
client = gspread.authorize(creds)

spreadsheet_url = st.secrets["google"]["spreadsheet_ids"][subject.lower()]
sheet = client.open_by_url(spreadsheet_url)

# --- Load data from both sheets ---
try:
    main_df = pd.DataFrame(sheet.worksheet("Main").get_all_records())
    remedial_df = pd.DataFrame(sheet.worksheet("Remedial").get_all_records())
except gspread.exceptions.WorksheetNotFound as e:
    st.error(f"❌ Worksheet not found: {e}")
    st.stop()

# --- Filter main questions for this subtopic ---
main_questions = main_df[main_df["SubtopicID"] == subtopic_id]

if main_questions.empty:
    st.warning("⚠ No questions found for this subtopic.")
    st.stop()

st.title(f"📄 {subject} - {subtopic_id.replace('_',' ')}")

# --- MAIN QUIZ FORM ---
user_answers = {}

with st.form("main_quiz"):
    for _, q in main_questions.iterrows():
        
        # --- Image handling ---
        img_url = normalize_img_url(q.get("ImageURL", ""))
        if img_url:
            st.write("Image debug link:", img_url)  # Debugging line
            st.image(img_url, use_container_width=True)

        # --- Options ---
        options = [
            str(q.get("Option_A", "") or "").strip(),
            str(q.get("Option_B", "") or "").strip(),
            str(q.get("Option_C", "") or "").strip(),
            str(q.get("Option_D", "") or "").strip()
        ]

        # --- Question ---
        user_answers[q["QuestionID"]] = st.radio(
            label=f"{q['QuestionText']}",
            options=options,
            key=f"main_{q['QuestionID']}"
        )

    submit_main = st.form_submit_button("Submit Quiz")

# --- After Main Quiz Submission ---
if submit_main:
    st.success("✅ Main quiz submitted!")
    
    # --- Find incorrect answers ---
    wrong_questions = []
    for _, q in main_questions.iterrows():
        correct = str(q.get("Correct_Answer", "") or "").strip()
        given = user_answers.get(q["QuestionID"], "").strip()
        if given != correct:
            wrong_questions.append(q)

    # --- Show remedial quiz if needed ---
    if wrong_questions:
        st.warning("⚠️ You got some answers wrong. Let's try the remedial quiz!")

        with st.form("remedial_quiz"):
            remedial_answers = {}
            for q in wrong_questions:
                
                # --- Image handling ---
                img_url = normalize_img_url(q.get("ImageURL", ""))
                if img_url:
                    st.write("Image debug link:", img_url)  # Debugging line
                    st.image(img_url, use_container_width=True)

                options = [
                    str(q.get("Option_A", "") or "").strip(),
                    str(q.get("Option_B", "") or "").strip(),
                    str(q.get("Option_C", "") or "").strip(),
                    str(q.get("Option_D", "") or "").strip()
                ]

                remedial_answers[q["QuestionID"]] = st.radio(
                    label=f"{q['QuestionText']}",
                    options=options,
                    key=f"remedial_{q['QuestionID']}"
                )

            submit_remedial = st.form_submit_button("Submit Remedial Quiz")

        if submit_remedial:
            st.success("✅ Remedial quiz submitted!")
            # Here you can add Google Sheets logging or Telegram notifications
    else:
        st.success("🎉 All answers were correct! No remedial needed.")
