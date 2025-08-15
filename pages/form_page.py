st.header("Main Quiz")

user_answers = {}

# --- MAIN QUIZ FORM ---
with st.form("main_quiz"):
    for _, q in main_questions.iterrows():
        
        # --- Image handling ---
        img_url = str(q.get("ImageURL", "") or "").strip()
        if img_url and img_url != "https://drive.google.com/uc?export=view&id=":
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
                img_url = str(q.get("ImageURL", "") or "").strip()
                if img_url and img_url != "https://drive.google.com/uc?export=view&id=":
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
