import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

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

# --- Main Quiz ---
st.header("Main Quiz")
user_answers = {}

with st.form("main_quiz"):
    for _, q in main_questions.iterrows():
        # Get and clean the ImageURL
        img_url = str(q.get("ImageURL", "")).strip()
        
        # Only display if it's not empty and not the placeholder link
        if img_url and img_url != "https://drive.google.com/uc?export=view&id=":
            st.image(img_url, use_container_width=True)

        # Display question options
        options = [
            q.get("Option_A", "").strip(),
            q.get("Option_B", "").strip(),
            q.get("Option_C", "").strip(),
            q.get("Option_D", "").strip()
        ]
        user_answers[q["QuestionID"]] = st.radio(
            f"{q['QuestionText']}",
            options,
            key=f"main_{q['QuestionID']}"
        )
    submitted = st.form_submit_button("Submit Answers")

if submitted:
    score = sum(
        1
        for qid, ans in user_answers.items()
        if ans == main_questions.loc[
            main_questions["QuestionID"] == qid, "CorrectOption"
        ].iloc[0]
    )
    st.success(f"✅ Your main quiz score: {score}/{len(main_questions)}")

    # Find wrong answers
    wrong_q_ids = [
        qid
        for qid, ans in user_answers.items()
        if ans != main_questions.loc[
            main_questions["QuestionID"] == qid, "CorrectOption"
        ].iloc[0]
    ]

    if wrong_q_ids:
        st.warning("⚠ Some answers were incorrect. Please take the remedial quiz below.")

        # --- Remedial Quiz ---
        st.header("Remedial Quiz")
        remedial_user_answers = {}
        remedial_questions_to_display = remedial_df[
            remedial_df["MainQuestionID"].isin(wrong_q_ids)
        ]

        if remedial_questions_to_display.empty:
            st.info("ℹ No remedial questions found for your wrong answers.")
        else:
            with st.form("remedial_quiz"):
                for _, rq in remedial_questions_to_display.iterrows():
                    # Get and clean the ImageURL
                    img_url = str(rq.get("ImageURL", "")).strip()

                    # Display if valid
                    if img_url and img_url != "https://drive.google.com/uc?export=view&id=":
                        st.image(img_url, use_container_width=True)
                    
                    options = [
                        rq.get("Option_A", "").strip(),
                        rq.get("Option_B", "").strip(),
                        rq.get("Option_C", "").strip(),
                        rq.get("Option_D", "").strip()
                    ]
                    remedial_user_answers[rq["RemedialQuestionID"]] = st.radio(
                        f"{rq['QuestionText']}",
                        options,
                        key=f"remedial_{rq['RemedialQuestionID']}"
                    )
                remedial_submitted = st.form_submit_button("Submit Remedial Answers")

            if remedial_submitted:
                remedial_score = sum(
                    1
                    for rqid, ans in remedial_user_answers.items()
                    if ans == remedial_questions_to_display.loc[
                        remedial_questions_to_display["RemedialQuestionID"] == rqid,
                        "CorrectOption"
                    ].iloc[0]
                )
                st.success(
                    f"✅ Your remedial quiz score: {remedial_score}/{len(remedial_questions_to_display)}"
                )
    else:
        st.success("🎉 All answers correct! No remedial needed.")
