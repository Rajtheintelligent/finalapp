import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import requests
from datetime import datetime

# =========================
# Page & Mobile UI Settings
# =========================
st.set_page_config(page_title="Form Page", layout="centered")

MOBILE_CSS = """
<style>
    html, body, [class*="css"] { font-size: 18px !important; }
    .question-card {
        border: 1px solid #e2e2e2;
        border-radius: 12px;
        padding: 14px;
        margin: 12px 0 18px 0;
        background: #fafafa;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    }
    .stRadio label {
        display: block !important;
        padding: 10px 14px !important;
        border-radius: 8px;
        margin-bottom: 8px !important;
        background: #fff;
        border: 1px solid #e6e6e6;
        line-height: 1.25rem;
    }
    .stRadio label:hover { background: #f4f4f4; }
    img { max-width: 100% !important; height: auto !important; }
    /* Gentle focus ring for accessibility */
    .stRadio input:focus + div, .stTextInput input:focus { outline: 2px solid #a3d3ff !important; }
</style>
"""
st.markdown(MOBILE_CSS, unsafe_allow_html=True)

# =========================
# Anti-cheating (JS)
# =========================
ANTI_CHEAT_JS = """
<script>
document.addEventListener('contextmenu', event => event.preventDefault());

// Block some keyboard combos (best-effort; users can still bypass on rooted devices/second screens)
document.addEventListener('keydown', function(e) {
  if ((e.ctrlKey || e.metaKey) && ['c','x','p','s','u'].includes(e.key.toLowerCase())) { e.preventDefault(); }
});

// Track away-from-quiz behavior
let warnCount = 0;
function warnUser() {
  warnCount++;
  alert("⚠ You switched away from the quiz! (" + warnCount + " of 3)");
  if (warnCount >= 3) {
    alert("Quiz auto-submitting due to repeated switching.");
    // Click the first primary button (your Submit button)
    const btn = document.querySelector('button[kind="primary"]');
    if (btn) btn.click();
  }
}
document.addEventListener("visibilitychange", function() { if (document.hidden) warnUser(); });
window.addEventListener("blur", warnUser, { passive: true });
</script>
"""
st.markdown(ANTI_CHEAT_JS, unsafe_allow_html=True)

# =========================
# Helpers
# =========================
def normalize_img_url(value: str) -> str:
    """Accepts Google Drive file IDs or full URLs and returns a direct image URL."""
    value = str(value or "").strip()
    if not value:
        return ""
    if value.startswith("https://drive.google.com/uc?export=download&id="):
        return value
    if len(value) > 20 and "/" not in value:
        return f"https://drive.google.com/uc?export=download&id={value}"
    return value

def safe_int(x, default=1):
    try: return int(x)
    except: return default

def send_telegram(bot_token: str, chat_id: str, text: str):
    """
    Sends a Telegram message. NOTE: chat_id must be a numeric ID and the user must have started the bot.
    If your Register sheet stores @usernames, you should convert them to numeric IDs ahead of time.
    """
    if not bot_token or not chat_id or chat_id.lower().startswith("@"):
        return  # skip if missing/username; avoids API errors
    try:
        requests.get(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            params={"chat_id": chat_id, "text": text},
            timeout=6
        )
    except Exception:
        pass  # Best-effort; don't break the quiz

def render_question_text(qid: str, text: str):
    """
    Renders question text. If it seems to contain LaTeX, we'll allow markdown rendering
    (Streamlit supports inline math in markdown with $...$ and $$...$$), else normal markdown.
    """
    text = str(text or "").strip()
    st.markdown(f"**Q{qid}**:")  # prefix label
    if any(sym in text for sym in ["\\(", "\\)", "$$", "$", "\\frac", "\\times", "\\div", "\\sqrt", "\\sum"]):
        # Let markdown render inline/blocks of LaTeX
        st.markdown(text)
    else:
        st.markdown(text)

# =========================
# URL Params
# =========================
params = st.query_params
subject = params.get("subject", "")
subtopic_id = params.get("subtopic_id", "")

if not subject or not subtopic_id:
    st.error("❌ Missing subject or subtopic_id in URL.")
    st.stop()

subject_key = subject.lower()

# =========================
# Google Sheets Auth
# =========================
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)

# =========================
# Load Register (for validation)
# =========================
# secrets:
# [google]
# register_sheet_url = "https://docs.google.com/spreadsheets/d/REGISTER_ID/edit"
register_sheet_url = st.secrets["google"]["register_sheet_url"]
register_ws = client.open_by_url(register_sheet_url).worksheet("Register")
register_df = pd.DataFrame(register_ws.get_all_records())

# =========================
# Student Validation
# =========================
st.subheader("🔑 Student Verification")
colA, colB = st.columns(2)
with colA:
    tuition_code = st.text_input("Tuition Code", max_chars=12)
with colB:
    student_id = st.text_input("Student ID", max_chars=20)

student_row = None
if tuition_code and student_id:
    match = register_df[
        (register_df["Tuition_Code"].astype(str) == str(tuition_code)) &
        (register_df["Student_ID"].astype(str) == str(student_id))
    ]
    if not match.empty:
        student_row = match.iloc[0]
        st.success(f"✅ Verified: {student_row['Student_Name']} ({student_row['Tuition_Name']})")
    else:
        st.warning("⚠ Not found in Register. You may attempt the quiz, but your attempt will be marked as **Unregistered** and no Telegram will be sent.")

# =========================
# Load Questions (subject sheet)
# =========================
# secrets:
# [google.question_sheet_urls]
# maths   = "https://docs.google.com/spreadsheets/d/QUESTIONS_MATH/edit"
# english = "https://docs.google.com/spreadsheets/d/QUESTIONS_ENG/edit"
questions_url = st.secrets["google"]["question_sheet_urls"][subject_key]
qbook = client.open_by_url(questions_url)

try:
    main_df = pd.DataFrame(qbook.worksheet("Main").get_all_records())
    remedial_df = pd.DataFrame(qbook.worksheet("Remedial").get_all_records())
except gspread.exceptions.WorksheetNotFound as e:
    st.error(f"❌ Worksheet not found: {e}")
    st.stop()

# Filter this subtopic
main_questions = main_df[main_df["SubtopicID"].astype(str) == str(subtopic_id)]
if main_questions.empty:
    st.warning("⚠ No questions found for this subtopic.")
    st.stop()

st.title(f"📄 {subject} — {subtopic_id.replace('_',' ')}")

# =========================
# Response Sheet (subject-specific)
# =========================
# secrets:
# [google.response_sheet_urls]
# maths   = "https://docs.google.com/spreadsheets/d/RESP_MATH/edit"
# english = "https://docs.google.com/spreadsheets/d/RESP_ENG/edit"
responses_url = st.secrets["google"]["response_sheet_urls"][subject_key]
resp_ws = client.open_by_url(responses_url).worksheet("Responses")

# =========================
# MAIN QUIZ
# =========================
user_answers = {}
with st.form("main_quiz"):
    for _, q in main_questions.iterrows():
        qid = str(q.get("QuestionID", "")).strip()
        qtext = str(q.get("QuestionText", "")).strip()

        st.markdown('<div class="question-card">', unsafe_allow_html=True)
        # Question text (with LaTeX support in markdown)
        render_question_text(qid, qtext)

        # Image between question and options
        img_url = normalize_img_url(q.get("ImageURL", ""))
        if img_url:
            st.image(img_url, use_container_width=True)

        # Options
        options = [
            str(q.get("Option_A", "") or "").strip(),
            str(q.get("Option_B", "") or "").strip(),
            str(q.get("Option_C", "") or "").strip(),
            str(q.get("Option_D", "") or "").strip()
        ]
        user_answers[qid] = st.radio(
            label="Select your answer:",
            options=options,
            key=f"main_{qid}"
        )
        st.markdown("</div>", unsafe_allow_html=True)

    submit_main = st.form_submit_button("Submit Quiz")

# =========================
# Handle MAIN submission
# =========================
if submit_main:
    wrong_questions = []
    total_points = 0
    earned_points = 0

    # Calculate score and prepare per-question logging
    for _, q in main_questions.iterrows():
        qid = str(q.get("QuestionID", "")).strip()
        correct = str(q.get("Correct_Answer", "") or "").strip()
        given = str(user_answers.get(qid, "") or "").strip()
        points = safe_int(q.get("Points", 1), 1)
        total_points += points
        awarded = points if given == correct else 0
        earned_points += awarded
        if awarded == 0:
            wrong_questions.append(q)

        # Append one row per question (MAIN)
        resp_ws.append_row([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),           # Timestamp
            student_id if student_row is not None else "Unregistered",
            student_row["Student_Name"] if student_row is not None else "Unknown",
            tuition_code if student_row is not None else "Unknown",
            subject,
            subtopic_id,
            qid,
            given,
            correct,
            awarded,
            "Main",
            ""   # IP_Address (left blank; capture requires proxy/header setup)
        ])

    # Telegram notifications
    had_incorrect = len(wrong_questions) > 0
    if student_row is not None:
        bot_token = st.secrets["telegram"].get("bot_token", "")
        parent_chat_id = str(student_row.get("Parent_Telegram_ID", "")).strip()
        teacher_chat_id = str(student_row.get("Teacher_Telegram_ID", "")).strip()

        # Parent gets score (only if registered & chat_id usable)
        send_telegram(
            bot_token,
            parent_chat_id,
            f"📊 {student_row['Student_Name']} scored {earned_points}/{total_points} in {subject} → {subtopic_id}."
        )
        # Teacher only if incorrect answers
        if had_incorrect:
            send_telegram(
                bot_token,
                teacher_chat_id,
                f"⚠️ {student_row['Student_Name']} had incorrect answers in {subject} → {subtopic_id}."
            )

    # Show remedial if needed
    if had_incorrect:
        st.warning("⚠️ Some answers were incorrect. Please take the remedial quiz below.")
        with st.form("remedial_quiz"):
            remedial_answers = {}
            for q in wrong_questions:
                qid = str(q.get("QuestionID", "")).strip()
                qtext = str(q.get("QuestionText", "")).strip()

                st.markdown('<div class="question-card">', unsafe_allow_html=True)
                render_question_text(qid, qtext)

                img_url = normalize_img_url(q.get("ImageURL", ""))
                if img_url:
                    st.image(img_url, use_container_width=True)

                opts = [
                    str(q.get("Option_A", "") or "").strip(),
                    str(q.get("Option_B", "") or "").strip(),
                    str(q.get("Option_C", "") or "").strip(),
                    str(q.get("Option_D", "") or "").strip()
                ]
                remedial_answers[qid] = st.radio(
                    label="Select your answer:",
                    options=opts,
                    key=f"remedial_{qid}"
                )
                st.markdown("</div>", unsafe_allow_html=True)

            submit_remedial = st.form_submit_button("Submit Remedial Quiz")

        if submit_remedial:
            # Log remedial attempt per question
            for _, q in pd.DataFrame(wrong_questions).iterrows():
                qid = str(q.get("QuestionID", "")).strip()
                correct = str(q.get("Correct_Answer", "") or "").strip()
                given = str(remedial_answers.get(qid, "") or "").strip()
                points = safe_int(q.get("Points", 1), 1)
                awarded = points if given == correct else 0

                resp_ws.append_row([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    student_id if student_row is not None else "Unregistered",
                    student_row["Student_Name"] if student_row is not None else "Unknown",
                    tuition_code if student_row is not None else "Unknown",
                    subject,
                    subtopic_id,
                    qid,
                    given,
                    correct,
                    awarded,
                    "Remedial",
                    ""
                ])

            st.success("✅ Remedial quiz submitted! Thanks.")
    else:
        st.success("🎉 All answers were correct! No remedial needed.")
