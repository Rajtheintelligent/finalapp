import time
import ssl
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from io import BytesIO

import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ──────────────────────────────────────────────────────────────────────────────
# Page config & styling (hide sidebar just for this page)
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Assessment Form", layout="wide")

HIDE_SIDEBAR_CSS = """
<style>
[data-testid="stSidebar"] {display: none;}
[data-testid="stHeader"] { z-index: 2; }
</style>
"""
st.markdown(HIDE_SIDEBAR_CSS, unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def pick_query_param(name: str, default: str = "") -> str:
    """Read a query param safely with the new st.query_params API."""
    params = st.query_params  # returns dict of strings
    v = params.get(name, default)
    return v if v else default

def as_text(val) -> str:
    """Robustly convert any cell value to trimmed string (avoids .strip on ints)."""
    return str(val or "").strip()

def valid_image_url(url: str) -> bool:
    """Accept non-empty, non-placeholder URLs."""
    if not url:
        return False
    if url == "https://drive.google.com/uc?export=view&id=":
        return False
    return True

def render_image_if_any(url: str):
    url = as_text(url)
    if valid_image_url(url):
        # Show image and a tiny 'open image' link
        st.image(url, use_container_width=True)
        st.markdown(f"[Open image in new tab]({url})")

def require_all_answered(answer_map: dict) -> list[str]:
    """Return list of question IDs still unanswered (value is None or empty)."""
    missing = []
    for qid, ans in answer_map.items():
        if ans is None or as_text(ans) == "":
            missing.append(qid)
    return missing

def calc_score(df_subset: pd.DataFrame, answers: dict) -> tuple[int, list[str]]:
    """Return (score, wrong_question_ids). Assumes CorrectOption is the correct answer text."""
    wrong = []
    score = 0
    marks_series = {}
    if "Marks" in df_subset.columns:
        marks_series = df_subset.set_index("QuestionID")["Marks"].to_dict()

    correct_map = df_subset.set_index("QuestionID")["CorrectOption"].to_dict()
    for qid, chosen in answers.items():
        correct_ans = as_text(correct_map.get(qid, ""))
        if as_text(chosen) == correct_ans:
            # add marks if present, else 1
            score += int(marks_series.get(qid, 1))
        else:
            wrong.append(qid)
    return score, wrong

def render_question_review(q_row: pd.Series, selected: str, correct_text: str, section="main"):
    """Read-only review card for a question, showing correct/incorrect."""
    q_text = as_text(q_row.get("QuestionText"))
    img = as_text(q_row.get("ImageURL"))
    opts = [as_text(q_row.get("Option_A")), as_text(q_row.get("Option_B")),
            as_text(q_row.get("Option_C")), as_text(q_row.get("Option_D"))]
    with st.container():
        st.markdown("---")
        if valid_image_url(img):
            render_image_if_any(img)
        st.markdown(f"**Q:** {q_text}")
        for opt in opts:
            if not opt:
                continue
            mark = ""
            if as_text(opt) == as_text(correct_text):
                mark = " ✅ **Correct**"
            if as_text(opt) == as_text(selected) and as_text(selected) != as_text(correct_text):
                mark = " ❌ **Your answer**"
            st.markdown(f"- {opt}{mark}")

def build_html_report(student_info: dict,
                      subject: str,
                      subtopic_id: str,
                      main_df: pd.DataFrame,
                      main_answers: dict,
                      main_score: int,
                      remedial_df: pd.DataFrame,
                      remedial_answers: dict,
                      remedial_score: int) -> str:
    """Create a simple HTML report that can be downloaded or emailed."""
    def rows_html(df, answers):
        html = ""
        correct_map = df.set_index("QuestionID")["CorrectOption"].to_dict() if "QuestionID" in df.columns else {}
        for _, r in df.iterrows():
            qid = as_text(r.get("QuestionID") or r.get("RemedialQuestionID"))
            qtext = as_text(r.get("QuestionText"))
            sel = as_text(answers.get(qid, ""))
            correct = as_text(r.get("CorrectOption"))
            status = "Correct" if sel == correct else "Incorrect"
            img = as_text(r.get("ImageURL"))
            img_html = f'<div><img src="{img}" style="max-width:100%"></div>' if valid_image_url(img) else ""
            html += f"""
            <div style="border:1px solid #ddd;border-radius:8px;padding:12px;margin:10px 0;">
              <div><b>ID:</b> {qid}</div>
              <div><b>Question:</b> {qtext}</div>
              {img_html}
              <div><b>Your Answer:</b> {sel}</div>
              <div><b>Correct Answer:</b> {correct}</div>
              <div><b>Status:</b> <span style="color:{'green' if status=='Correct' else 'red'}">{status}</span></div>
            </div>
            """
        return html

    student_block = "".join([f"<div><b>{k}:</b> {as_text(v)}</div>" for k, v in student_info.items()])
    html = f"""
    <html>
    <head>
      <meta charset="utf-8">
      <title>Assessment Report</title>
      <style>
        body {{ font-family: -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif; padding: 24px; }}
        h1,h2 {{ margin-bottom: 6px; }}
        .score {{ padding: 8px 12px; border-radius: 8px; display: inline-block; }}
      </style>
    </head>
    <body>
      <h1>Assessment Report</h1>
      <div><b>Subject:</b> {as_text(subject)}</div>
      <div><b>Subtopic:</b> {as_text(subtopic_id)}</div>
      <div><b>Timestamp:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
      <hr/>
      <h2>Student</h2>
      {student_block}
      <hr/>
      <h2>Main Quiz</h2>
      <div class="score" style="background:#e7f7ee;border:1px solid #b8e6cb;">Score: {main_score}</div>
      {rows_html(main_df, main_answers)}
      <hr/>
      <h2>Remedial</h2>
      <div class="score" style="background:#e7effa;border:1px solid #c5d7f2;">Score: {remedial_score}</div>
      {rows_html(remedial_df, remedial_answers)}
      <hr/>
      <div>Generated by your assessment portal.</div>
    </body>
    </html>
    """
    return html

def send_report_email(html_report: str, to_emails: list[str]) -> tuple[bool, str]:
    """Email the HTML report using SMTP creds from secrets."""
    try:
        smtp_cfg = st.secrets.get("smtp", {})
        server = smtp_cfg.get("server")
        port = int(smtp_cfg.get("port", "587"))
        username = smtp_cfg.get("username")
        password = smtp_cfg.get("password")
        from_email = smtp_cfg.get("from_email", username)

        if not (server and username and password and from_email and to_emails):
            return False, "SMTP not configured or recipients missing."

        msg = MIMEText(html_report, "html", "utf-8")
        msg["Subject"] = "Your Assessment Report"
        msg["From"] = from_email
        msg["To"] = ", ".join(to_emails)

        context = ssl.create_default_context()
        with smtplib.SMTP(server, port) as s:
            s.starttls(context=context)
            s.login(username, password)
            s.sendmail(from_email, to_emails, msg.as_string())
        return True, "Email sent."
    except Exception as e:
        return False, f"Failed to send email: {e}"

# ──────────────────────────────────────────────────────────────────────────────
# Query params
# ──────────────────────────────────────────────────────────────────────────────
params = st.query_params
subject = pick_query_param("subject", "")
subtopic_id = pick_query_param("subtopic_id", "")

if not subject or not subtopic_id:
    st.error("❌ Missing subject or subtopic_id in URL.")
    st.stop()

# Map incoming subject/bank names to your secrets keys
bank_map = {
    "mathematics": "ssc_maths_geometry",  # default to geometry
    "maths": "ssc_maths_geometry",
    "geometry": "ssc_maths_geometry",
    "algebra": "ssc_maths_algebra",
    "ssc_maths_algebra": "ssc_maths_algebra",
    "ssc_maths_geometry": "ssc_maths_geometry",
    "science": "science_1",  # default
    "science1": "science_1",
    "science_1": "science_1",
    "science2": "science_2",
    "science_2": "science_2",
    "ssc_english": "ssc_english",
}

if subject.lower() in bank_map:
    bank = bank_map[subject.lower()]
else:
    st.error(f"❌ Unknown subject '{subject}'. Please check the URL or mapping.")
    st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# Auth & connections
# ──────────────────────────────────────────────────────────────────────────────
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)

# Fetch URLs from secrets.toml
question_sheets = st.secrets["google"]["question_sheet_urls"]
response_sheets = st.secrets["google"]["response_sheet_urls"]

QUESTION_SHEET_URL = question_sheets.get(bank)
RESPONSE_SHEET_URL = response_sheets.get(bank)

if not QUESTION_SHEET_URL:
    st.error(f"❌ No question sheet URL configured for '{bank}' in secrets.toml.")
    st.stop()

# Connect to the question sheet
sheet = client.open_by_url(QUESTION_SHEET_URL)    

@st.cache_data(ttl=60, show_spinner=False)
def load_worksheets(question_sheet_url: str):
    sheet = client.open_by_url(question_sheet_url)
    main_df = pd.DataFrame(sheet.worksheet("Main").get_all_records())
    remedial_df = pd.DataFrame(sheet.worksheet("Remedial").get_all_records())
    return main_df, remedial_df

@st.cache_data(ttl=60, show_spinner=False)
def load_worksheets(question_sheet_url: str):
    try:
        sheet = client.open_by_url(question_sheet_url)
        main_df = pd.DataFrame(sheet.worksheet("Main").get_all_records())
        remedial_df = pd.DataFrame(sheet.worksheet("Remedial").get_all_records())
        return main_df, remedial_df
    except Exception as e:
        st.error(f"❌ Error loading worksheets: {e}")
        return pd.DataFrame(), pd.DataFrame()

# ──────────────────────────────────────────────
# Prepare response sheet (for saving student work)
# ──────────────────────────────────────────────        
def get_response_worksheet(response_sheet_url: str):
    try:
        rs = client.open_by_url(response_sheet_url)
        try:
            ws = rs.worksheet("Responses")
        except gspread.exceptions.WorksheetNotFound:
            ws = rs.add_worksheet(title="Responses", rows=1000, cols=30)
            # Add a header row
            ws.append_row([
                "Timestamp", "Subject", "SubtopicID",
                "StudentName", "Class", "RollNo", "StudentEmail", "ParentEmail",
                "MainScore", "RemedialScore", "MainWrongIDs", "RemedialWrongIDs"
            ])
        return ws
    except Exception as e:
        st.warning(f"Could not open response sheet: {e}")
        return None

try:
    main_df, remedial_df = load_worksheets(QUESTION_SHEET_URL)
except gspread.exceptions.WorksheetNotFound as e:
    st.error(f"❌ Worksheet not found: {e}")
    st.stop()

# Only this subtopic
main_questions = main_df[main_df["SubtopicID"] == subtopic_id]
if main_questions.empty:
    st.warning("⚠ No questions found for this subtopic.")
    st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# Session state init
# ──────────────────────────────────────────────────────────────────────────────
ss = st.session_state
ss.setdefault("student_verified", False)
ss.setdefault("student_info", {})
ss.setdefault("main_answers", {})
ss.setdefault("main_submitted", False)
ss.setdefault("remedial_unlocked", False)
ss.setdefault("remedial_countdown_start", None)
ss.setdefault("remedial_answers", {})
ss.setdefault("remedial_submitted", False)
ss.setdefault("main_score", 0)
ss.setdefault("remedial_score", 0)
ss.setdefault("main_wrong_ids", [])
ss.setdefault("remedial_wrong_ids", [])

# ──────────────────────────────────────────────────────────────────────────────
# 1) Student Verification (with its own submit)
# ──────────────────────────────────────────────────────────────────────────────
st.title(f"📄 {subject} — {subtopic_id.replace('_',' ')}")

with st.expander("👤 Student Verification", expanded=not ss["student_verified"]):
    with st.form("student_verification"):
        c1, c2, c3 = st.columns([1,1,1])
        with c1:
            sv_name = st.text_input("Student Name*", value=as_text(ss["student_info"].get("StudentName")))
            sv_class = st.text_input("Class/Section*", value=as_text(ss["student_info"].get("Class")))
        with c2:
            sv_roll = st.text_input("Roll No*", value=as_text(ss["student_info"].get("RollNo")))
            sv_student_email = st.text_input("Student Email*", value=as_text(ss["student_info"].get("StudentEmail")))
        with c3:
            sv_parent_email = st.text_input("Parent Email*", value=as_text(ss["student_info"].get("ParentEmail")))
        verify_submit = st.form_submit_button("Submit Verification")

    if verify_submit:
        required = [sv_name, sv_class, sv_roll, sv_student_email]
        if any(as_text(x) == "" for x in required):
            st.error("Please fill all required fields marked with *.")
        else:
            ss["student_info"] = {
                "StudentName": sv_name,
                "Class": sv_class,
                "RollNo": sv_roll,
                "StudentEmail": sv_student_email,
                "ParentEmail": sv_parent_email,
            }
            ss["student_verified"] = True
            st.success("Verification submitted ✅")

if not ss["student_verified"]:
    st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# 2) MAIN QUIZ (Questions required; stays visible after submit; shows review)
# ──────────────────────────────────────────────────────────────────────────────
st.header("📝 Main Quiz")

if not ss["main_submitted"]:
    # Build the form
    with st.form("main_quiz"):
        main_answers_local = {}
        for _, q in main_questions.iterrows():
            st.markdown("---")
            render_image_if_any(q.get("ImageURL"))
            qid = as_text(q["QuestionID"])
            qtext = as_text(q["QuestionText"])
            options = [as_text(q.get("Option_A")), as_text(q.get("Option_B")),
                       as_text(q.get("Option_C")), as_text(q.get("Option_D"))]
            # Remove empty options
            options = [o for o in options if o]

            # radio with no pre-selection -> required
            ans = st.radio(
                label=qtext,
                options=options,
                index=None,
                key=f"main_{qid}",
                horizontal=False
            )
            main_answers_local[qid] = ans

        submitted = st.form_submit_button("Submit My Answers")
        if submitted:
            # Validate all answered
            missing = require_all_answered(main_answers_local)
            if missing:
                st.error("Please answer all questions before submitting.")
            else:
                ss["main_answers"] = main_answers_local
                # Score & wrong IDs
                score, wrong_ids = calc_score(main_questions, ss["main_answers"])
                ss["main_score"] = score
                ss["main_wrong_ids"] = wrong_ids
                ss["main_submitted"] = True
                st.success(f"Your main quiz score: {score}")
                st.balloons()

# If submitted, show a review of all main questions with correctness
if ss["main_submitted"]:
    st.subheader("Main Quiz Results")
    correct_map = main_questions.set_index("QuestionID")["CorrectOption"].to_dict()
    for _, q in main_questions.iterrows():
        qid = as_text(q["QuestionID"])
        render_question_review(q, ss["main_answers"].get(qid), correct_map.get(qid), section="main")

# ──────────────────────────────────────────────────────────────────────────────
# 3) REMEDIAL COUNTDOWN (20s) and REMEDIAL QUIZ
# ──────────────────────────────────────────────────────────────────────────────
if ss["main_submitted"] and ss["main_wrong_ids"]:
    if not ss["remedial_unlocked"]:
        # Start or update countdown
        if ss["remedial_countdown_start"] is None:
            ss["remedial_countdown_start"] = time.time()

        remaining = 20 - int(time.time() - ss["remedial_countdown_start"])
        if remaining > 0:
            st.info(
                f"🔍 Please review your incorrect responses above.\n\n"
                f"⏳ Remedial quiz will unlock in **{remaining} seconds**."
            )
            time.sleep(1)
            st.rerun()
        else:
            ss["remedial_unlocked"] = True

    if ss["remedial_unlocked"]:
        st.header("🧩 Remedial Quiz")
        # Pick remedial questions based on wrong main QuestionIDs
        remedial_to_show = remedial_df[remedial_df["MainQuestionID"].isin(ss["main_wrong_ids"])].copy()

        if remedial_to_show.empty:
            st.info("No remedial questions mapped for your incorrect answers. Great effort!")
        else:
            if not ss["remedial_submitted"]:
                with st.form("remedial_quiz"):
                    remedial_answers_local = {}
                    for _, rq in remedial_to_show.iterrows():
                        st.markdown("---")
                        render_image_if_any(rq.get("ImageURL"))
                        rqid = as_text(rq["RemedialQuestionID"])
                        qtext = as_text(rq["QuestionText"])
                        options = [as_text(rq.get("Option_A")), as_text(rq.get("Option_B")),
                                   as_text(rq.get("Option_C")), as_text(rq.get("Option_D"))]
                        options = [o for o in options if o]

                        ans = st.radio(
                            label=qtext,
                            options=options,
                            index=None,
                            key=f"remedial_{rqid}",
                            horizontal=False
                        )
                        remedial_answers_local[rqid] = ans

                        # 💡 Hint box if available
                        hint_text = as_text(rq.get("Hint"))
                        if hint_text:
                            with st.expander("💡 Hint"):
                                st.write(hint_text)

                    remedial_submit = st.form_submit_button("Submit Remedial Answers")
                    if remedial_submit:
                        missing_r = require_all_answered(remedial_answers_local)
                        if missing_r:
                            st.error("Please answer all remedial questions before submitting.")
                        else:
                            ss["remedial_answers"] = remedial_answers_local
                            # Score remedial — note key is RemedialQuestionID, so map by that
                            # Build a df keyed by RemedialQuestionID to reuse calc_score style
                            tmp = remedial_to_show.rename(columns={"RemedialQuestionID": "QuestionID"})
                            rscore, rwrong = calc_score(tmp, ss["remedial_answers"])
                            ss["remedial_score"] = rscore
                            ss["remedial_wrong_ids"] = rwrong
                            ss["remedial_submitted"] = True
                            st.success("Thank you! Your remedial answers were submitted. 🎉")
            # Always show remedial review once submitted
            if ss["remedial_submitted"]:
                st.subheader("Remedial Results")
                correct_map_r = remedial_to_show.set_index("RemedialQuestionID")["CorrectOption"].to_dict()
                for _, rq in remedial_to_show.iterrows():
                    rqid = as_text(rq["RemedialQuestionID"])
                    # Use same renderer (convert to QuestionID-like shape)
                    render_question_review(
                        rq.rename({"RemedialQuestionID": "QuestionID"}),
                        ss["remedial_answers"].get(rqid),
                        correct_map_r.get(rqid),
                        section="remedial"
                    )

# ──────────────────────────────────────────────────────────────────────────────
# 4) PERFORMANCE SUMMARY (charts) + DOWNLOAD + EMAIL + VERSIONED SAVE
# ──────────────────────────────────────────────────────────────────────────────
if ss["main_submitted"]:
    st.markdown("---")
    st.header("📊 Performance Summary")

    # Totals
    total_main = int(main_questions["Marks"].sum()) if "Marks" in main_questions.columns else len(main_questions)
    total_remedial = 0
    if ss["remedial_unlocked"]:
        # the actual questions shown
        remedial_to_show = remedial_df[remedial_df["MainQuestionID"].isin(ss["main_wrong_ids"])]
        total_remedial = int(remedial_to_show["Marks"].sum()) if "Marks" in remedial_to_show.columns else len(remedial_to_show)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Main Score", ss["main_score"], help="Total marks or count of correct answers")
    with c2:
        st.metric("Main Incorrect", len(ss["main_wrong_ids"]))
    with c3:
        if ss["remedial_unlocked"]:
            st.metric("Remedial Score", ss["remedial_score"])

    # Simple chart: Correct vs Incorrect (main; remedial if available)
    main_correct = total_main - len(ss["main_wrong_ids"]) if "Marks" not in main_questions.columns else ss["main_score"]
    main_points = pd.DataFrame(
        {"Category": ["Main Correct", "Main Incorrect"],
         "Count": [main_correct, len(ss["main_wrong_ids"])]}
    ).set_index("Category")
    st.bar_chart(main_points)

    if ss["remedial_unlocked"]:
        remedial_to_show = remedial_df[remedial_df["MainQuestionID"].isin(ss["main_wrong_ids"])]
        rem_total = len(remedial_to_show) if "Marks" not in remedial_to_show.columns else int(remedial_to_show["Marks"].sum())
        rem_incorrect = rem_total - ss["remedial_score"]
        remedial_points = pd.DataFrame(
            {"Category": ["Remedial Correct", "Remedial Incorrect"],
             "Count": [ss["remedial_score"], rem_incorrect]}
        ).set_index("Category")
        st.bar_chart(remedial_points)

    # Build HTML report (always available after main submit)
    remedial_to_show = remedial_df[remedial_df["MainQuestionID"].isin(ss["main_wrong_ids"])] if ss["main_wrong_ids"] else remedial_df.iloc[0:0]
    html_report = build_html_report(
        student_info=ss["student_info"],
        subject=subject,
        subtopic_id=subtopic_id,
        main_df=main_questions,
        main_answers=ss["main_answers"],
        main_score=ss["main_score"],
        remedial_df=remedial_to_show.rename(columns={"RemedialQuestionID": "QuestionID"}),
        remedial_answers=ss["remedial_answers"],
        remedial_score=ss["remedial_score"],
    )

    # Download button (HTML -> user can Print to PDF)
    st.download_button(
        "⬇️ Download Report (HTML)",
        data=html_report.encode("utf-8"),
        file_name=f"report_{subject}_{subtopic_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
        mime="text/html",
    )

    # Email the report
    with st.expander("✉️ Email this report"):
        to_student = as_text(ss["student_info"].get("StudentEmail"))
        to_parent = as_text(ss["student_info"].get("ParentEmail"))
        default_recipients = ", ".join([x for x in [to_student, to_parent] if x])
        emails_input = st.text_input("Recipient Emails (comma separated)", value=default_recipients)
        if st.button("Send Email"):
            recipients = [as_text(x) for x in emails_input.split(",") if as_text(x)]
            ok, msg = send_report_email(html_report, recipients)
            if ok:
                st.success(msg)
            else:
                st.error(msg)

    # Versioned save (progress tracking)
    ws = get_response_worksheet(RESPONSE_SHEET_URL)
    if ws is not None:
        try:
            ws.append_row([
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                subject, subtopic_id,
                ss["student_info"].get("StudentName"),
                ss["student_info"].get("Class"),
                ss["student_info"].get("RollNo"),
                ss["student_info"].get("StudentEmail"),
                ss["student_info"].get("ParentEmail"),
                ss["main_score"],
                ss["remedial_score"],
                ",".join(ss["main_wrong_ids"]),
                ",".join(ss["remedial_wrong_ids"]),
            ])
        except Exception as e:
            st.warning(f"Could not log response to sheet: {e}")
