# form_page.py
import streamlit as st
import pandas as pd
import random
import json
import time
import requests
import uuid

# third-party lib to talk to Google Sheets
import gspread
from gspread.exceptions import APIError

# -------------------------
# CONFIG / UTIL FUNCTIONS
# -------------------------
def _get_gspread_client():
    """
    Expects you to store your service account JSON in Streamlit secrets as
    st.secrets["gcp_service_account"] (the whole JSON parsed to a dict).
    """
    try:
        creds = st.secrets["gcp_service_account"]
    except Exception as e:
        st.error("Missing Google Service Account credentials in Streamlit secrets.")
        st.stop()
    # gspread helper: create client from dict
    try:
        gc = gspread.service_account_from_dict(creds)
    except Exception as e:
        st.error(f"Failed to create gspread client: {e}")
        st.stop()
    return gc

def _open_spreadsheet():
    try:
        spreadsheet_id = st.secrets["google"]["spreadsheet_id"]
    except Exception:
        st.error("Please add your spreadsheet id to st.secrets['google']['spreadsheet_id'].")
        st.stop()
    gc = _get_gspread_client()
    try:
        sh = gc.open_by_key(spreadsheet_id)
    except Exception as e:
        st.error(f"Unable to open spreadsheet. Make sure the service account email has view/edit access. Error: {e}")
        st.stop()
    return sh

def send_telegram_message(text, chat_id):
    token = st.secrets.get("telegram", {}).get("bot_token")
    if not token or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        r = requests.post(url, data=payload, timeout=8)
        return r.status_code == 200
    except Exception:
        return False

def append_row_to_sheet(sh, worksheet_name, row_list):
    try:
        ws = sh.worksheet(worksheet_name)
    except Exception:
        # try create
        ws = sh.add_worksheet(title=worksheet_name, rows="1000", cols="20")
    ws.append_row(row_list)

# -------------------------
# DATA LAYOUT / CONVENTION
# -------------------------
# Expected sheets:
# 1) "questions" sheet (main questions)
#    Columns: SubtopicID, QuestionID, QuestionText, Option_A, Option_B, Option_C, Option_D, CorrectOption (A/B/C/D), ImageURL (can be blank), Marks
# 2) "remedial" sheet
#    Columns: MainQuestionID, RemedialQuestionID, QuestionText, Option_A, Option_B, Option_C, Option_D, CorrectOption, Marks
# 3) "responses" sheet (created by code if missing) - will receive appended rows per submission
# 4) Optional: "roster" sheet (StudentEmail, Parent_TelegramChatID) to map students -> parent chat IDs

# -------------------------
# FORM / REMEDIAL LOGIC
# -------------------------
def run(subtopic_id=None):
    """
    Entry point for rendering the form for a given subtopic.
    If subtopic_id is None, the function will try to read from query params,
    else it will let user pick from available subtopics in the questions sheet.
    """
    st.set_page_config(page_title="Assessment form", layout="wide")
    st.header("📝 Assessment Form")

    # load sheets
    sh = _open_spreadsheet()

    # load main questions sheet
    try:
        q_ws = sh.worksheet("questions")
        q_records = q_ws.get_all_records()
        q_df = pd.DataFrame(q_records)
    except Exception:
        q_df = pd.DataFrame(columns=["SubtopicID","QuestionID","QuestionText","Option_A","Option_B","Option_C","Option_D","CorrectOption","ImageURL","Marks"])

    # load remedial sheet (may be empty)
    try:
        r_ws = sh.worksheet("remedial")
        r_records = r_ws.get_all_records()
        r_df = pd.DataFrame(r_records)
    except Exception:
        r_df = pd.DataFrame(columns=["MainQuestionID","RemedialQuestionID","QuestionText","Option_A","Option_B","Option_C","Option_D","CorrectOption","Marks"])

    # allow subtopic param override (from query param or caller)
    if subtopic_id is None:
        params = st.experimental_get_query_params()
        subtopic_id = params.get("topic", [None])[0]

    if not subtopic_id:
        # show available subtopics to choose from (teacher preview or debugging)
        st.info("No subtopic provided in URL. Pick a subtopic to preview the form.")
        subtopics = sorted(q_df["SubtopicID"].dropna().unique().tolist())
        if not subtopics:
            st.warning("No subtopics found in the 'questions' sheet. Please add questions first.")
            st.stop()
        subtopic_id = st.selectbox("Choose subtopic", subtopics)

    st.subheader(f"Subtopic: {subtopic_id}")

    # filter questions for the chosen subtopic
    q_sub = q_df[q_df["SubtopicID"] == subtopic_id].copy()
    if q_sub.empty:
        st.warning(f"No questions found for SubtopicID = '{subtopic_id}'.")
        st.stop()

    # --- Student / teacher metadata collection (top of form) ---
    with st.form("student_info", clear_on_submit=False):
        col1, col2, col3 = st.columns([2,3,2])
        with col1:
            student_name = st.text_input("Student name", "")
            student_email = st.text_input("Student email", "")
        with col2:
            class_code = st.text_input("Class code (e.g. 1102)", "")
            roll_no = st.text_input("Roll no / Adm no (optional)", "")
        with col3:
            # optional toggle: teacher mode shows copy link & open in new tab options
            is_teacher = st.checkbox("I am a teacher (show share link)", value=False)
        submitted = st.form_submit_button("Start / Resume Test")

    if not submitted:
        st.info("Fill student details and click **Start / Resume Test** to load the paper.")
        # show shareable link for teacher if requested
        if is_teacher:
            show_teacher_share_link(subtopic_id)
        st.stop()

    # If teacher asked to share link, show copyable link
    if is_teacher:
        show_teacher_share_link(subtopic_id)

    # Build a session id (helps group main + remedial attempts)
    session_id = str(uuid.uuid4())[:8]
    st.write(f"Session id: `{session_id}` (keeps this attempt together)")

    # --- Present Main Form Questions ---
    st.markdown("### Main Form")
    answers = {}   # qid -> selected option text
    correct_map = {}  # qid -> correct option text

    form_key = f"main_form_{session_id}"
    with st.form(form_key):
        for idx, row in q_sub.iterrows():
            qid = str(row.get("QuestionID", f"q{idx}"))
            qtext = row.get("QuestionText", "")
            opts = [
                row.get("Option_A", ""),
                row.get("Option_B", ""),
                row.get("Option_C", ""),
                row.get("Option_D", ""),
            ]
            # shuffle options for each question
            shuffled = opts.copy()
            random.shuffle(shuffled)
            # store correct option text for later checking
            correct_label = str(row.get("CorrectOption", "A")).strip().upper()
            label_to_text = {"A": row.get("Option_A", ""), "B": row.get("Option_B", ""), "C": row.get("Option_C", ""), "D": row.get("Option_D", "")}
            correct_text = label_to_text.get(correct_label, "")
            correct_map[qid] = correct_text

            # show question and radio
            if row.get("ImageURL"):
                st.image(row.get("ImageURL"), width=300)
            selected = st.radio(label=f"{qtext}  (QID: {qid})", options=shuffled, key=f"{form_key}_{qid}")
            answers[qid] = selected

        submit_main = st.form_submit_button("Submit Main Form")

    if not submit_main:
        st.info("Click **Submit Main Form** when student finishes.")
        st.stop()

    # --- Evaluate main form ---
    total = len(answers)
    correct = 0
    incorrect_qids = []
    answers_summary = []

    for qid, selected_text in answers.items():
        correct_text = correct_map.get(qid, "")
        is_correct = (selected_text == correct_text)
        if is_correct:
            correct += 1
        else:
            incorrect_qids.append(qid)
        answers_summary.append({
            "QuestionID": qid,
            "Selected": selected_text,
            "Correct": correct_text,
            "IsCorrect": int(is_correct)
        })

    score_percent = round(correct / total * 100, 2)

    st.success(f"Main attempt submitted — Score: **{correct}/{total}** ({score_percent}%).")

    # --- Persist main attempt to 'responses' sheet ---
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        responses_ws = sh.worksheet("responses")
    except Exception:
        # create worksheet
        responses_ws = sh.add_worksheet(title="responses", rows="2000", cols="30")
        # write header (first row)
        responses_ws.append_row(["Timestamp","SessionID","StudentName","StudentEmail","ClassCode","RollNo","SubtopicID","AttemptType","AnswersJSON","CorrectCount","TotalQ","ScorePct","IP","Extra"])
    # append row (one row per attempt storing answers as JSON)
    row_to_append = [
        timestamp,
        session_id,
        student_name,
        student_email,
        class_code,
        roll_no,
        subtopic_id,
        "main",
        json.dumps(answers_summary, ensure_ascii=False),
        correct,
        total,
        score_percent,
        "client-ip-not-recorded",  # see note below about IP
        ""  # extra
    ]
    responses_ws.append_row(row_to_append)

    # --- Notify teacher if incorrect answers found ---
    teacher_chat = st.secrets.get("telegram", {}).get("teacher_chat_id")
    if incorrect_qids and teacher_chat:
        # build message summarizing incorrect answers
        msg_lines = [
            f"❗ Student {student_name} ({student_email}) attempted '{subtopic_id}'",
            f"Score: {correct}/{total} ({score_percent}%)",
            "Incorrect QIDs: " + ", ".join(incorrect_qids),
            f"Session: {session_id}",
            f"Time: {timestamp}"
        ]
        send_telegram_message("\n".join(msg_lines), teacher_chat)

    # --- If there are incorrect questions, offer remedial form for only those QIDs ---
    if incorrect_qids:
        st.markdown("---")
        st.warning("Student has incorrect answers — launching remedial questions below.")
        remedial_for_wrong = r_df[r_df["MainQuestionID"].astype(str).isin(incorrect_qids)].copy()
        if remedial_for_wrong.empty:
            st.info("No remedial questions defined for these incorrect questions. You can add remedial rows into the 'remedial' sheet (MainQuestionID -> RemedialQuestionID mapping).")
        else:
            remedial_answers = {}

            remedial_form_key = f"remedial_form_{session_id}"
            with st.form(remedial_form_key):
                st.markdown("### Remedial Form (only for incorrect questions)")
                for idx, r in remedial_for_wrong.iterrows():
                    rid = r.get("RemedialQuestionID", f"r{idx}")
                    rtext = r.get("QuestionText", "")
                    
                     # Show image if available
                    if r.get("ImageURL"):
                        st.image(r.get("ImageURL"), width=300)
                        
                    ropts = [r.get("Option_A",""), r.get("Option_B",""), r.get("Option_C",""), r.get("Option_D","")]
                    shuffled_r = ropts.copy()
                    random.shuffle(shuffled_r)
                    selected_r = st.radio(label=f"{rtext}  (RemID: {rid})", options=shuffled_r, key=f"{remedial_form_key}_{rid}")
                    remedial_answers[rid] = {
                        "Selected": selected_r,
                        "Correct": r.get("Option_" + str(r.get("CorrectOption","A")).upper(), "")
                    }
                submit_remedial = st.form_submit_button("Submit Remedial")
            if submit_remedial:
                # evaluate remedial
                remedial_correct = 0
                remedial_total = len(remedial_answers)
                remedial_summary = []
                for rid, info in remedial_answers.items():
                    is_corr = (info["Selected"] == info["Correct"])
                    remedial_summary.append({"RemedialID": rid, "Selected": info["Selected"], "Correct": info["Correct"], "IsCorrect": int(is_corr)})
                    if is_corr:
                        remedial_correct += 1
                remedial_pct = round(remedial_correct / remedial_total * 100, 2) if remedial_total>0 else 0
                st.success(f"Remedial submitted — Score: {remedial_correct}/{remedial_total} ({remedial_pct}%)")

                # persist remedial attempt
                row_to_append = [
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                    session_id,
                    student_name,
                    student_email,
                    class_code,
                    roll_no,
                    subtopic_id,
                    "remedial",
                    json.dumps(remedial_summary, ensure_ascii=False),
                    remedial_correct,
                    remedial_total,
                    remedial_pct,
                    "client-ip-not-recorded",
                    ""
                ]
                responses_ws.append_row(row_to_append)

                # notify teacher about remedial result (optional)
                if teacher_chat:
                    msg = f"Remedial result for {student_name} ({student_email})\nSubtopic: {subtopic_id}\nRemedial: {remedial_correct}/{remedial_total} ({remedial_pct}%)\nSession: {session_id}"
                    send_telegram_message(msg, teacher_chat)

    # --- Notify parent(s) of final score (optional) ---
    # This example: looks up roster sheet for Parent Telegram chat id using student_email
    try:
        roster_ws = sh.worksheet("roster")
        roster = roster_ws.get_all_records()
        roster_df = pd.DataFrame(roster)
    except Exception:
        roster_df = pd.DataFrame(columns=["StudentEmail", "ParentChatID"])

    parent_chat_id = None
    if not roster_df.empty and student_email:
        found = roster_df[roster_df["StudentEmail"].astype(str).str.strip().str.lower() == str(student_email).strip().lower()]
        if not found.empty:
            # if multiple parents available, you might loop and notify each
            parent_chat_id = found.iloc[0].get("ParentChatID")

    # send parent notification (score after main & remedial combined approach — keep simple here)
    if parent_chat_id:
        msg = f"📊 {student_name} scored {correct}/{total} ({score_percent}%) in {subtopic_id}.\nClass: {class_code}\nSession: {session_id}"
        send_telegram_message(msg, parent_chat_id)

    st.balloons()
    st.info("Form complete. Responses saved to Google Sheets.")
    st.stop()

# Helper to show share link and copy button (teacher convenience)
def show_teacher_share_link(subtopic_id):
    # compute your deployed app root. If you don't know, ask the hosting page owner / check Streamlit Cloud URL.
    deployed_base = st.secrets.get("app", {}).get("base_url", "")
    if not deployed_base:
        # fallback: try to derive from current page
        url = st.experimental_get_query_params().get("url", [""])[0]
        deployed_base = ""
    # If you know your base URL, store in secrets: st.secrets["app"]["base_url"] = "https://your-app.streamlit.app"
    if deployed_base:
        link = f"{deployed_base}/?show_form=1&topic={subtopic_id}"
    else:
        # default: use relative link (teacher can copy the current URL and add params)
        current = st.experimental_get_query_params()
        link = f"(Add ?show_form=1&topic={subtopic_id} to your app URL)"
    st.markdown("#### Teacher share link (copy & paste to Google Classroom)")
    st.text_input("Form link", value=link, key=f"copylink_{subtopic_id}")
    # small raw HTML copy button (works inside the app)
    copy_html = f"""
    <div>
      <input id="link_{subtopic_id}" value="{link}" style="width:80%"/>
      <button onclick="navigator.clipboard.writeText(document.getElementById('link_{subtopic_id}').value)">Copy</button>
    </div>
    """
    st.components.v1.html(copy_html, height=60)
