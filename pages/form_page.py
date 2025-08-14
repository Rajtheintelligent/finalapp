# form_page.py

import streamlit as st
import pandas as pd
import random
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- PAGE CONFIG ---
st.set_page_config(page_title="Quiz Form", layout="wide")

# --- GOOGLE SHEETS CONNECTION ---
def get_gsheet_data(spreadsheet_id, range_name):
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )
    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    values = result.get("values", [])

    if not values:
        return pd.DataFrame()
    
    df = pd.DataFrame(values[1:], columns=values[0])
    return df

# --- GET QUERY PARAMS ---
query_params = st.experimental_get_query_params()
subject = query_params.get("subject", [""])[0]
subtopic_id = query_params.get("subtopic_id", [""])[0]

if not subject or not subtopic_id:
    st.error("Missing subject or subtopic_id in URL")
    st.stop()

# --- LOAD QUESTIONS ---
spreadsheet_id = st.secrets["google"]["spreadsheet_ids"][subject]
main_df = get_gsheet_data(spreadsheet_id, "MainQuestions")
remedial_df = get_gsheet_data(spreadsheet_id, "RemedialQuestions")

main_questions_to_display = main_df[main_df['SubtopicID'] == subtopic_id]

if main_questions_to_display.empty:
    st.warning("No questions available for this subtopic.")
    st.stop()

st.title(f"📘 {subtopic_id} Quiz")

# --- MAIN QUIZ ---
with st.form("main_quiz_form"):
    st.subheader("Main Quiz")
    user_answers = {}
    for index, q in main_questions_to_display.iterrows():
        st.markdown("---")
        st.markdown(f"**Q{index + 1}: {q['QuestionText']}**")

        if 'ImageURL' in q and pd.notna(q['ImageURL']):
            st.image(q['ImageURL'])

        options = [q[col] for col in ['Option_A', 'Option_B', 'Option_C', 'Option_D'] if col in q and pd.notna(q[col])]
        random.shuffle(options)

        user_answers[q['QuestionID']] = st.radio(
            "Select an answer:",
            options,
            key=f"main_{q['QuestionID']}"
        )

    submitted = st.form_submit_button("Submit Main Quiz")

if submitted:
    score = 0
    incorrect_question_ids = []
    for q_id, user_answer in user_answers.items():
        row = main_questions_to_display[main_questions_to_display['QuestionID'] == q_id]
        if not row.empty and user_answer == row['CorrectOption'].iloc[0]:
            score += 1
        else:
            incorrect_question_ids.append(q_id)

    st.success(f"✅ You scored {score} out of {len(user_answers)} in the main quiz.")

    # --- REMEDIAL QUIZ ---
    if incorrect_question_ids:
        st.warning("You missed some questions. Let's try a few remedial ones.")
        remedial_questions_to_display = remedial_df[remedial_df['MainQuestionID'].isin(incorrect_question_ids)]

        if not remedial_questions_to_display.empty:
            with st.form("remedial_quiz_form"):
                st.subheader("Remedial Quiz")
                remedial_user_answers = {}
                for index, r_q in remedial_questions_to_display.iterrows():
                    st.markdown("---")
                    st.markdown(f"**{r_q['QuestionText']}**")

                    if 'ImageURL' in r_q and pd.notna(r_q['ImageURL']):
                        st.image(r_q['ImageURL'])

                    r_options = [r_q[col] for col in ['Option_A', 'Option_B', 'Option_C', 'Option_D'] if col in r_q and pd.notna(r_q[col])]
                    random.shuffle(r_options)

                    remedial_user_answers[r_q['RemedialQuestionID']] = st.radio(
                        "Select an answer:",
                        r_options,
                        key=f"remedial_{r_q['RemedialQuestionID']}"
                    )

                remedial_submitted = st.form_submit_button("Submit Remedial Answers")

            if remedial_submitted:
                remedial_score = 0
                for r_q_id, r_user_answer in remedial_user_answers.items():
                    r_row = remedial_questions_to_display[remedial_questions_to_display['RemedialQuestionID'] == r_q_id]
                    if not r_row.empty and r_user_answer == r_row['CorrectOption'].iloc[0]:
                        remedial_score += 1

                st.success(f"🎯 You got {remedial_score} out of {len(remedial_user_answers)} remedial questions correct!")
                if remedial_score == len(remedial_user_answers):
                    st.balloons()
        else:
            st.info("No remedial questions available for your incorrect answers.")
    else:
        st.balloons()
        st.success("🎉 Excellent! You got all questions correct.")
