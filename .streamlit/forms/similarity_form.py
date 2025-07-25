import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Setup Google Sheets API
@st.cache_resource
def get_gsheet_data():
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]

    creds = ServiceAccountCredentials.from_json_keyfile_name("gsheet_key.json", scope)
    client = gspread.authorize(creds)

    sheet = client.open("Similarity_MCQ").sheet1
    data = sheet.get_all_records()
    return pd.DataFrame(data)

def main():
    st.title("Similarity - Basic Concepts (MCQ Form)")
    df = get_gsheet_data()

    user_answers = {}

    with st.form("similarity_form"):
        for idx, row in df.iterrows():
            question = row['Question']
            options = [f"A. {row['Option A']}", f"B. {row['Option B']}",
                       f"C. {row['Option C']}", f"D. {row['Option D']}"]
            user_choice = st.radio(question, options, key=f"q{idx}")
            user_answers[question] = user_choice[0]  # Extract A/B/C/D

        submitted = st.form_submit_button("Submit")

    if submitted:
        score = 0
        total = len(df)
        for idx, row in df.iterrows():
            correct = row['Answer']
            if user_answers[row['Question']] == correct:
                score += 1

        st.success(f"Your Score: {score} / {total}")

if __name__ == "__main__":
    main()

