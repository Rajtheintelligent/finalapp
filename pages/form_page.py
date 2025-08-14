import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Form Page", layout="wide")

# --- Get URL query parameters ---
params = st.query_params
subject = params.get("subject", "")
subtopic_id = params.get("subtopic_id", "")

if not subject or not subtopic_id:
    st.error("Missing subject or subtopic_id in URL.")
    st.stop()

# --- Connect to Google Sheets ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)

spreadsheet_url = st.secrets["google"]["spreadsheet_ids"][subject.lower()]
sheet = client.open_by_url(spreadsheet_url)

# --- Load main & remedial questions ---
main_df = pd.DataFrame(sheet.worksheet("Main").get_all_records())
remedial_questions = remedial_df[remedial_df['MainQuestionID'].isin(main_ids_for_subtopic)]

main_questions = main_df[main_df['SubtopicID'] == subtopic_id]
remedial_questions = remedial_df[remedial_df['SubtopicID'] == subtopic_id]

st.title(f"📄 {subject} - {subtopic_id.replace('_',' ')}")

# --- Main quiz ---
st.header("Main Quiz")
user_answers = {}

with st.form("main_quiz"):
    for _, q in main_questions.iterrows():
        user_answers[q['QuestionID']] = st.radio(
            f"{q['QuestionText']}",
            [q['Option1'], q['Option2'], q['Option3'], q['Option4']],
            key=f"main_{q['QuestionID']}"
        )
    submitted = st.form_submit_button("Submit Answers")

if submitted:
    score = sum(
        1 for qid, ans in user_answers.items()
        if ans == main_questions.loc[main_questions['QuestionID'] == qid, 'CorrectOption'].iloc[0]
    )
    st.success(f"Your main quiz score: {score}/{len(main_questions)}")

    # Determine wrong answers for remedial
    wrong_q_ids = [
        qid for qid, ans in user_answers.items()
        if ans != main_questions.loc[main_questions['QuestionID'] == qid, 'CorrectOption'].iloc[0]
    ]
    if wrong_q_ids:
        st.warning("You got some questions wrong. Please take the remedial quiz below.")

        # --- Remedial quiz ---
        st.header("Remedial Quiz")
        remedial_user_answers = {}
        remedial_questions_to_display = remedial_questions[remedial_questions['MainQuestionID'].isin(wrong_q_ids)]

        with st.form("remedial_quiz"):
            for _, rq in remedial_questions_to_display.iterrows():
                remedial_user_answers[rq['RemedialQuestionID']] = st.radio(
                    f"{rq['QuestionText']}",
                    [rq['Option1'], rq['Option2'], rq['Option3'], rq['Option4']],
                    key=f"remedial_{rq['RemedialQuestionID']}"
                )
            remedial_submitted = st.form_submit_button("Submit Remedial Answers")

        if remedial_submitted:
            remedial_score = sum(
                1 for rqid, ans in remedial_user_answers.items()
                if ans == remedial_questions_to_display.loc[
                    remedial_questions_to_display['RemedialQuestionID'] == rqid, 'CorrectOption'
                ].iloc[0]
            )
            st.success(f"Your remedial quiz score: {remedial_score}/{len(remedial_questions_to_display)}")
    else:
        st.success("🎉 All answers were correct! No remedial needed.")
