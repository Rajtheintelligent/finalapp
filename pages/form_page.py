import streamlit as st
import pandas as pd
import random
from streamlit_gsheets import GSheetsConnection

# --- PAGE CONFIG ---
st.set_page_config(layout="wide")

# --- DATA LOADING FUNCTION ---
# This function connects to Google Sheets and fetches data.
# It's cached to avoid re-downloading data on every interaction.
@st.cache_data(ttl=60) # Cache data for 60 seconds
def load_data(spreadsheet_id, worksheet_name):
    """Loads data from a specific worksheet in a Google Sheet."""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=spreadsheet_id, worksheet=worksheet_name)
        # Filter out empty rows that GSheets sometimes returns
        return df.dropna(how="all")
    except Exception as e:
        st.error(f"Failed to load data from worksheet '{worksheet_name}': {e}")
        return pd.DataFrame()

# --- MAIN LOGIC ---

# 1. GET DETAILS FROM URL
# Get the subject and subtopic ID from the URL query parameters
subject = st.query_params.get("subject")
subtopic_id = st.query_params.get("subtopic_id")

if not subject or not subtopic_id:
    st.error("⚠️ Page loaded incorrectly. Please navigate from the subject page.")
    st.page_link("pages/ICSE_Maths.py", label="Go Back to Subject Selection", icon="👈")
else:
    # 2. LOAD DATA FROM GOOGLE SHEETS
    # Get the correct spreadsheet ID from your secrets
    spreadsheet_id = st.secrets.google.spreadsheet_ids.get(subject)
    if not spreadsheet_id:
        st.error(f"Spreadsheet ID for subject '{subject}' not found in secrets.")
    else:
        # Load main and remedial questions
        main_df = load_data(spreadsheet_id, "main_form")
        remedial_df = load_data(spreadsheet_id, "remedial_form")
        
        # Filter for the specific subtopic
        questions_to_display = main_df[main_df['SubtopicID'] == subtopic_id]

        if questions_to_display.empty:
            st.warning(f"No questions found for Subtopic ID: `{subtopic_id}`")
        else:
            st.title(f"📝 Quiz: {subtopic_id.replace('_', ' ')}")
            st.write("Answer the following questions. Your options will be shuffled.")
            
            # 3. CREATE THE MAIN FORM
            with st.form("main_quiz_form"):
                user_answers = {}
                # Loop through each question for the selected subtopic
                for index, q in questions_to_display.iterrows():
                    st.markdown("---")
                    st.subheader(q['QuestionText'])
                    
                    if pd.notna(q.get('ImageURL')):
                        st.image(q['ImageURL'])

                    # Get options, filter out empty ones, and shuffle them
                    options = [q[col] for col in ['Option_A', 'Option_B', 'Option_C', 'Option_D'] if pd.notna(q[col])]
                    random.shuffle(options)
                    
                    # Create the radio button with shuffled options
                    user_answers[q['QuestionID']] = st.radio(
                        "Select an answer:", 
                        options, 
                        key=f"main_{q['QuestionID']}"
                    )
                
                submitted = st.form_submit_button("Submit My Answers")

            # 4. PROCESS SUBMISSION
            if submitted:
                score = 0
                incorrect_question_ids = []
                
                # Grade the answers
                for q_id, user_answer in user_answers.items():
                    correct_answer = questions_to_display[questions_to_display['QuestionID'] == q_id]['CorrectOption'].iloc[0]
                    if user_answer == correct_answer:
                        score += questions_to_display[questions_to_display['QuestionID'] == q_id]['Marks'].iloc[0]
                    else:
                        incorrect_question_ids.append(q_id)
                
                total_marks = questions_to_display['Marks'].sum()
                st.success(f"**Your Score: {score} / {total_marks}**")
                
                # --- SEND NOTIFICATIONS (Example) ---
                # This is where you would add your Telegram bot logic
                # st.toast(f"Parent notification sent for score: {score}")
                # if incorrect_question_ids:
                #    st.toast("Teacher notification sent for incorrect answers.")

                # 5. GENERATE REMEDIAL FORM (if needed)
                if incorrect_question_ids:
                    st.warning("You had some trouble with the questions below. Let's try a few more to help you understand.")
                    
                    remedial_questions_to_display = remedial_df[remedial_df['MainQuestionID'].isin(incorrect_question_ids)]
                    
                    if not remedial_questions_to_display.empty:
                        with st.form("remedial_quiz_form"):
                            # Create the remedial form
                            for index, r_q in remedial_questions_to_display.iterrows():
                                st.markdown("---")
                                st.subheader(r_q['QuestionText'])
                                if pd.notna(r_q.get('ImageURL')):
                                    st.image(r_q['ImageURL'])
                                
                                r_options = [r_q[col] for col in ['Option_A', 'Option_B', 'Option_C', 'Option_D'] if pd.notna(r_q[col])]
                                random.shuffle(r_options)
                                
                                st.radio("Select an answer:", r_options, key=f"remedial_{r_q['RemedialQuestionID']}")
                            
                            remedial_submitted = st.form_submit_button("Submit Remedial Answers")
                            if remedial_submitted:
                                st.balloons()
                                st.info("Thank you for completing the remedial exercise!")
                    else:
                        st.info("No remedial questions available for the ones you missed.")
                else:
                    st.balloons()
                    st.success("Great job! You got everything correct!")
