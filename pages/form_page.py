# form_page.py
# ------------------------------------------------------------
# Features:
# - Student validation against Register sheet (Tuition_Code + Student_ID)
# - Unregistered can submit; marked "Unregistered" and no Telegram sent
# - Subject-specific response sheets (exact columns)
# - Teacher Telegram only if MAIN attempt had incorrect answers
# - Parent Telegram with total score (registered only)
# - Mobile-first UI (MCQ cards), image between question and options
# - LaTeX-friendly questions (markdown w/ $...$/ $$...$$)
# - Anti-cheat (visibility/blur, right-click/keys block, 3 warnings → auto-submit)
# - Questions live in two tabs ("Main"/"Remedial") and are filtered by SubtopicID/MainQuestionID
# ------------------------------------------------------------

import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import requests

# -----------------------------
# Page & Mobile-first Styling
# -----------------------------
st.set_page_config(page_title="Form", layout="centered")

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
    .stTextInput input:focus { outline: 2px solid #a3d3ff !important; }
</style>
"""
st.markdown(MOBILE_CSS, unsafe_allow_html=True)

# -----------------------------
# Anti-cheat (JS)
# -----------------------------
ANTI_CHEAT_JS = """
<script>
document.addEventListener('contextmenu', event => event.preventDefault());
document.addEventListener('keydown', function(e) {
  const k = e.key.toLowerCase();
  if ((e.ctrlKey || e.metaKey) && ['c','x','p','s','u','a'].includes(k)) { e.preventDefault(); }
});
let warnCount = 0;
function warnUser() {
  warnCount++;
  alert("⚠ You switched away from the quiz! (" + warnCount + " of 3)");
  if (warnCount >= 3) {
    alert("Quiz auto-submitting due to repeated switching.");
    const btn = document.querySelector('button[kind="primary"]');
    if (btn) btn.click();
  }
}
document.addEventListener("visibilitychange", function() { if (document.hidden) warnUser(); });
window.addEventListener("blur", warnUser, { passive: true });
</script>
"""
st.markdown(ANTI_CHEAT_JS, unsafe_allow_html=True)

# -----------------------------
# Helpers
# -----------------------------
def get_params():
    """Unified query params for both legacy and new Streamlit APIs."""
    try:
        raw = st.query_params  # new API
    except Exception:
        raw = st.experimental_get_query_params()  # fallback

    def pick(name, default=""):
        v = raw.get(name, default)
        if isinstance(v, list):
            return v[0] if v else default
        return v
    return pick

def normalize_img_url(value: str) -> str:
    """Accepts Google Drive file IDs or full URLs and returns a direct image URL."""
    value = str(value or "").strip()
    if not value:
        return ""
    if value.startswith("https://drive.google.com/uc?export=download&id="):
        return value
    # treat as "just the file id"
    if len(value) > 20 and "/" not in value:
        return f"https://drive.google.com/uc?export=download&id={value}"
    return value

def safe_int(x, default=1):
    try:
        return int(float(str(x).strip()))
    except Exception:
        return default

def open_ws(book, candidates):
    """Open the first worksheet that exists from a list of candidate names."""
    for name in candidates:
        try:
            return book.worksheet(name)
        except Exception:
            continue
    raise gspread.exceptions.WorksheetNotFound(", ".join(candidates))

def send_telegram(bot_token: str, chat_id: str, text: str):
    """
    Sends a Telegram message. Bots can DM only users who have started the bot.
    chat_id should ideally be a numeric ID. If you store @usernames, delivery is not guaranteed.
    """
    try:
        if not bot_token or not chat_id:
            return
        requests.get(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            params={"chat_id": chat_id, "text": text},
            timeout=8
        )
    except Exception:
        # best-effort: ignore failures so quiz flow doesn't break
        pass

def render_question(qid: str, text: str):
    """LaTeX-friendly renderer (markdown supports $...$ and $$...$$)."""
    text = str(text or "").strip()
    st.markdown(f"**Q{qid}**:")
    st.markdown(text)

# -----------------------------
# Read URL parameters
# -----------------------------
param = get_params()
subject      = param("subject", "").strip()       # e.g., "maths", "english", "science"
subtopic_id  = param("subtopic_id", "").strip()   # e.g., "similarity11"
# "bank" chooses which big question/response sheet to use (e.g., "ssc_maths_algebra")
# If omitted, fallback to subject key.
bank         = param("bank", subject.lower()).strip()
# Optional chapter field for logging (falls back to subject if not provided)
chapter      = param("chapter", subject).strip()

if not subject or not subtopic_id:
    st.error("❌ Missing `subject` or `subtopic_id` in URL.")
    st.stop()

# -----------------------------
# Google auth
# -----------------------------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
try:
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
except KeyError:
    st.error("❌ Missing `gcp_service_account` in secrets.toml.")
    st.stop()

client = gspread.authorize(creds)

# -----------------------------
# Secrets: sheet URLs
# -----------------------------
def get_secret_path(path, err_hint):
    # path like ("google","question_sheet_urls", bank)
    try:
        cur = st.secrets
        for p in path:
            cur = cur[p]
        return cur
    except KeyError:
        st.error(err_hint)
        st.stop()

register_sheet_url = get_secret_path(
    ("google", "register_sheet_url"),
    "❌ Missing [google].register_sheet_url in secrets.toml."
)

question_sheet_url = get_secret_path(
    ("google", "question_sheet_urls", bank),
    f"❌ Missing [google.question_sheet_urls].{bank} in secrets.toml."
)

response_sheet_url = get_secret_path(
    ("google", "response_sheet_urls", bank),
    f"❌ Missing [google.response_sheet_urls].{bank} in secrets.toml."
)

# -----------------------------
# Load Register sheet (validation)
# -----------------------------
try:
    reg_book = client.open_by_url(register_sheet_url)
    reg_ws   = open_ws(reg_book, ["Register", "register", "Sheet1"])
    register_df = pd.DataFrame(reg_ws.get_all_records())
except gspread.exceptions.SpreadsheetNotFound:
    st.error("❌ Register sheet URL invalid or not shared with the service account.")
    st.stop()
except gspread.exceptions.WorksheetNotFound:
    st.error("❌ Could not find a 'Register' worksheet (or fallback) in your Register spreadsheet.")
    st.stop()

# Expected columns in Register:
# Tuition_Code, Tuition_Name, Student_ID, Student_Name, Parent_Name, Parent_Telegram_ID,
# Teacher_Name, Teacher_Telegram_ID, Contact_Number_Parent, Contact_Number_Teacher

# -----------------------------
# Student Validation UI
# -----------------------------
st.subheader("🔑 Student Verification")
c1, c2 = st.columns(2)
with c1:
    tuition_code = st.text_input("Tuition Code", max_chars=20)
with c2:
    student_id   = st.text_input("Student ID", max_chars=30)

student_row = None
if tuition_code and student_id:
    mask = (
        register_df["Tuition_Code"].astype(str).str.strip().eq(str(tuition_code).strip()) &
        register_df["Student_ID"].astype(str).str.strip().eq(str(student_id).strip())
    )
    if mask.any():
        student_row = register_df[mask].iloc[0]
        st.success(f"✅ Verified: {student_row['Student_Name']} ({student_row['Tuition_Name']})")
    else:
        st.warning("⚠ Not found in Register. You can attempt the quiz, but your attempt will be marked **Unregistered** and no Telegram will be sent.")

# -----------------------------
# Load Questions (Main & Remedial in SAME book)
# -----------------------------
try:
    q_book = client.open_by_url(question_sheet_url)
    main_ws     = open_ws(q_book, ["Main", "main"])
    remedial_ws = open_ws(q_book, ["Remedial", "remedial"])
    main_df     = pd.DataFrame(main_ws.get_all_records())
    remedial_df = pd.DataFrame(remedial_ws.get_all_records())
except gspread.exceptions.SpreadsheetNotFound:
    st.error("❌ Questions sheet URL invalid or not shared with the service account.")
    st.stop()
except gspread.exceptions.WorksheetNotFound:
    st.error("❌ Could not find 'Main'/'Remedial' worksheets in your Questions spreadsheet.")
    st.stop()

# Filter MAIN by SubtopicID (exact column names per your schema)
if "SubtopicID" not in main_df.columns:
    st.error("❌ 'Main' worksheet must include a 'SubtopicID' column.")
    st.stop()

main_questions = main_df[main_df["SubtopicID"].astype(str).str.strip() == subtopic_id]

if main_questions.empty:
    st.warning("⚠ No MAIN questions found for this subtopic.")
    st.stop()

st.title(f"📄 {subject.title()} — {subtopic_id.replace('_',' ')}")

# -----------------------------
# Open Responses sheet
# -----------------------------
try:
    resp_book = client.open_by_url(response_sheet_url)
    responses_ws = open_ws(resp_book, ["Responses", "responses", "Sheet1"])
except gspread.exceptions.SpreadsheetNotFound:
    st.error("❌ Response sheet URL invalid or not shared with the service account.")
    st.stop()
except gspread.exceptions.WorksheetNotFound:
    st.error("❌ Could not find a 'Responses' worksheet (or fallback) in your Responses spreadsheet.")
    st.stop()

# Expected Responses columns:
# Timestamp, Student_ID, Student_Name, Class_Code, Chapter, Subtopic,
# Question_Number, Student_Answer, Correct_Answer, Points_Awarded,
# Attempt_Type (Main/Remedial), IP_Address

def append_response_row(qnum, given, correct, awarded, attempt_type):
    responses_ws.append_row([
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),                       # Timestamp
        (student_id if student_row is not None else "Unregistered"),        # Student_ID
        (student_row["Student_Name"] if student_row is not None else "Unknown"),
        (tuition_code if student_row is not None else "Unknown"),            # Class_Code (using Tuition_Code)
        chapter,                                                             # Chapter
        subtopic_id,                                                         # Subtopic
        qnum,                                                                # Question_Number
        given,                                                               # Student_Answer
        correct,                                                             # Correct_Answer
        awarded,                                                             # Points_Awarded
        attempt_type,                                                        # Attempt_Type (Main/Remedial)
        ""                                                                   # IP_Address (left blank)
    ])

# -----------------------------
# MAIN QUIZ
# -----------------------------
user_answers = {}
with st.form("main_quiz"):
    for _, q in main_questions.iterrows():
        qid   = str(q.get("QuestionID", "")).strip()
        qtext = str(q.get("QuestionText", "")).strip()

        st.markdown('<div class="question-card">', unsafe_allow_html=True)
        render_question(qid, qtext)

        img_url = normalize_img_url(q.get("ImageURL", ""))
        if img_url:
            st.image(img_url, use_container_width=True)

        options = [
            str(q.get("Option_A", "") or "").strip(),
            str(q.get("Option_B", "") or "").strip(),
            str(q.get("Option_C", "") or "").strip(),
            str(q.get("Option_D", "") or "").strip()
        ]
        user_answers[qid] = st.radio("Select your answer:", options=options, key=f"main_{qid}")
        st.markdown("</div>", unsafe_allow_html=True)

    submit_main = st.form_submit_button("Submit Quiz")

# -----------------------------
# Handle MAIN submission
# -----------------------------
if submit_main:
    wrong_qs = []
    total_points = 0
    earned_points = 0

    for _, q in main_questions.iterrows():
        qid     = str(q.get("QuestionID", "")).strip()
        correct = str(q.get("CorrectOption", "") or "").strip()
        given   = str(user_answers.get(qid, "") or "").strip()
        marks   = safe_int(q.get("Marks", 1), 1)

        total_points += marks
        awarded = marks if given == correct else 0
        earned_points += awarded
        if awarded == 0:
            wrong_qs.append(q)

        # Log MAIN attempt row per question
        append_response_row(qnum=qid, given=given, correct=correct, awarded=awarded, attempt_type="Main")

    # Telegram notifications (registered only)
    if student_row is not None:
        bot_token       = st.secrets.get("telegram", {}).get("bot_token", "")
        parent_chat_id  = str(student_row.get("Parent_Telegram_ID", "")).strip()
        teacher_chat_id = str(student_row.get("Teacher_Telegram_ID", "")).strip()

        # Parent gets total score
        send_telegram(
            bot_token,
            parent_chat_id,
            f"📊 {student_row['Student_Name']} scored {earned_points}/{total_points} in {subject} → {subtopic_id}."
        )

        # Teacher only if incorrect answers in MAIN
        if len(wrong_qs) > 0:
            send_telegram(
                bot_token,
                teacher_chat_id,
                f"⚠️ {student_row['Student_Name']} had incorrect answers in {subject} → {subtopic_id}."
            )

    # If there are wrong answers, show REMEDIAL
    if len(wrong_qs) > 0:
        st.warning("⚠️ Some answers were incorrect. Please take the remedial quiz below.")

        # Build a remedial set filtered by MainQuestionID ∈ wrong set
        wrong_main_ids = [str(q.get("QuestionID", "")).strip() for _, q in pd.DataFrame(wrong_qs).iterrows()]
        rem_set = remedial_df[remedial_df["MainQuestionID"].astype(str).str.strip().isin(wrong_main_ids)].copy()

        if rem_set.empty:
            st.info("ℹ️ No remedial questions found for the incorrect items.")
        else:
            remedial_answers = {}
            with st.form("remedial_quiz"):
                for _, rq in rem_set.iterrows():
                    rqid         = str(rq.get("RemedialQuestionID", "")).strip()
                    r_main_qid   = str(rq.get("MainQuestionID", "")).strip()
                    rq_text      = str(rq.get("QuestionText", "")).strip()

                    st.markdown('<div class="question-card">', unsafe_allow_html=True)
                    render_question(rqid, rq_text)

                    r_img = normalize_img_url(rq.get("ImageURL", ""))
                    if r_img:
                        st.image(r_img, use_container_width=True)

                    r_opts = [
                        str(rq.get("Option_A", "") or "").strip(),
                        str(rq.get("Option_B", "") or "").strip(),
                        str(rq.get("Option_C", "") or "").strip(),
                        str(rq.get("Option_D", "") or "").strip()
                    ]
                    remedial_answers[rqid] = st.radio(
                        "Select your answer:",
                        options=r_opts,
                        key=f"remedial_{rqid}"
                    )
                    st.markdown("</div>", unsafe_allow_html=True)

                submit_remedial = st.form_submit_button("Submit Remedial Quiz")

            if submit_remedial:
                for _, rq in rem_set.iterrows():
                    rqid   = str(rq.get("RemedialQuestionID", "")).strip()
                    correct = str(rq.get("CorrectOption", "") or "").strip()
                    given   = str(remedial_answers.get(rqid, "") or "").strip()
                    marks   = safe_int(rq.get("Marks", 1), 1)
                    awarded = marks if given == correct else 0

                    # Log REMEDIAL attempt row per question
                    # For "Question_Number" we store the remedial question ID here.
                    append_response_row(qnum=rqid, given=given, correct=correct, awarded=awarded, attempt_type="Remedial")

                st.success("✅ Remedial quiz submitted! Thank you.")
    else:
        st.success("🎉 All answers were correct! No remedial needed.")
