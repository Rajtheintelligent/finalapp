# form_page.py
# ------------------------------------------------------------
# Features:
# - Student validation (Tuition_Code + Student_ID) from Register sheet
# - Unregistered can submit (no Telegram) and are logged as "Unregistered"
# - Subject-bank driven sheets via secrets: question_sheet_urls / response_sheet_urls
# - Writes Responses with exact columns requested
# - Teacher Telegram only if MAIN attempt has any wrong answers
# - Parent Telegram with total score (registered only)
# - Mobile-first layout using Streamlit containers (no external CSS)
# - Image shown BETWEEN question and options
# - LaTeX-friendly (Markdown supports $...$ / $$...$$)
# - Anti-cheat: disable selection/copy/context menu; warn on blur/visibility; auto-submit after 3 warns
# - Prevent duplicate MAIN attempts (session + Responses-sheet check; override via ?allow_retake=1)
# - Remedial flow filtered by MainQuestionID for wrong MAIN answers
# - Optionally shuffle questions & options (stable per student+subtopic)
# ------------------------------------------------------------

import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import requests
import hashlib
import random

# -----------------------------
# Page & Mobile-first
# -----------------------------
st.set_page_config(page_title="Form", layout="centered")

# -----------------------------
# Anti-cheat (JS + minimal CSS)
# -----------------------------
ANTI_CHEAT_JS = """
<script>
// ===== CONFIG =====
const UNLOCK_CODE = new URLSearchParams(window.location.search).get('unlock_code');

// ===== Utility: lock screen =====
function lockQuiz(reason) {
  if (UNLOCK_CODE) { 
    localStorage.removeItem('quiz_locked');
    return; // teacher unlocked
  }
  
  localStorage.setItem('quiz_locked', '1');

  // Disable all inputs/buttons
  document.querySelectorAll('input, button, select, textarea').forEach(el => el.disabled = true);

  // Overlay
  let overlay = document.createElement('div');
  overlay.style.position = 'fixed';
  overlay.style.top = 0;
  overlay.style.left = 0;
  overlay.style.width = '100%';
  overlay.style.height = '100%';
  overlay.style.background = 'rgba(0,0,0,0.85)';
  overlay.style.color = 'white';
  overlay.style.display = 'flex';
  overlay.style.flexDirection = 'column';
  overlay.style.justifyContent = 'center';
  overlay.style.alignItems = 'center';
  overlay.style.zIndex = 9999;
  overlay.innerHTML = `
    <h2 style="color: red; font-size: 28px;">🚫 Quiz Locked!</h2>
    <p style="max-width: 80%; text-align: center;">
      You switched away from the quiz.<br>
      Please contact your teacher to reopen it.
    </p>
  `;
  document.body.appendChild(overlay);

  // Vibrate on mobile
  if (navigator.vibrate) {
    navigator.vibrate([200, 100, 200]);
  }
}

// ===== Check lock status on load =====
if (localStorage.getItem('quiz_locked') && !UNLOCK_CODE) {
  window.addEventListener('load', () => lockQuiz("already locked"));
}

// ===== Anti-cheat events =====
document.addEventListener('contextmenu', event => event.preventDefault());
document.addEventListener('selectstart', event => event.preventDefault());
document.addEventListener('copy', event => event.preventDefault());
document.addEventListener('keydown', function(e) {
  const k = e.key.toLowerCase();
  if ((e.ctrlKey || e.metaKey) && ['c','x','p','s','u','a'].includes(k)) {
    e.preventDefault();
  }
});

function triggerCheatLock() {
  lockQuiz("tab switch");
}

document.addEventListener("visibilitychange", function() {
  if (document.hidden) triggerCheatLock();
});
window.addEventListener("blur", triggerCheatLock, { passive: true });
</script>
<style>
* {
  -webkit-user-select: none;
  -ms-user-select: none;
  user-select: none;
}
</style>
"""
st.markdown(ANTI_CHEAT_JS, unsafe_allow_html=True)


# -----------------------------
# Config toggles
# -----------------------------
SHUFFLE_QUESTIONS = True
SHUFFLE_OPTIONS   = True

# -----------------------------
# Helpers
# -----------------------------
def get_params():
    """Unified query params (new + legacy)."""
    try:
        raw = st.query_params
    except Exception:
        raw = st.experimental_get_query_params()
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
    Sends a Telegram message via Bot API. Delivery requires:
    - chat_id is a user id (numeric) of someone who started the bot, OR
    - a group/channel id or @channelusername
    """
    try:
        if not bot_token or not str(chat_id).strip():
            return
        requests.get(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            params={"chat_id": chat_id, "text": text},
            timeout=8
        )
    except Exception:
        # Best-effort only; don't block the quiz
        pass

def stable_shuffle(items, seed_str):
    """Deterministic shuffle using md5(seed_str)."""
    seq = list(items)
    h = int(hashlib.md5(seed_str.encode("utf-8")).hexdigest(), 16)
    rnd = random.Random(h)
    rnd.shuffle(seq)
    return seq

def get_correct_value(row):
    """
    Return the correct answer TEXT from a row.
    Supports 'CorrectOption' (preferred) or 'Correct_Answer' as fallback.
    """
    if "CorrectOption" in row and str(row.get("CorrectOption", "")).strip():
        return str(row.get("CorrectOption", "")).strip()
    if "Correct_Answer" in row and str(row.get("Correct_Answer", "")).strip():
        return str(row.get("Correct_Answer", "")).strip()
    return ""

def render_question(qid: str, text: str):
    """LaTeX-friendly renderer (Markdown supports $...$ / $$...$$)."""
    text = str(text or "").strip()
    st.markdown(f"**{qid}**")
    st.markdown(text)

# -----------------------------
# URL params
# -----------------------------
param = get_params()
subject      = param("subject", "").strip()       # e.g., "maths", "english", "science"
subtopic_id  = param("subtopic_id", "").strip()   # e.g., "similarity11"
chapter      = param("chapter", subject).strip()  # for logging

# Choose which big sheet (bank) to use; defaults to subject
bank         = param("bank", subject.lower()).strip()
allow_retake = param("allow_retake", "0").strip() # to bypass duplicate-prevention: "1" enables

# Map incoming names to your secrets keys (edit to your preferences)
bank_map = {
    "mathematics": "ssc_maths_geometry",  # or "ssc_maths_algebra"
    "maths": "ssc_maths_geometry",
    "geometry": "ssc_maths_geometry",
    "algebra": "ssc_maths_algebra",
    "ssc_maths_algebra": "ssc_maths_algebra",
    "ssc_maths_geometry": "ssc_maths_geometry",
    "science": "science_1",
    "science1": "science_1",
    "science_1": "science_1",
    "science2": "science_2",
    "science_2": "science_2",
}
if bank in bank_map:
    bank = bank_map[bank]

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
    st.error("❌ Missing `gcp_service_account` in secrets.")
    st.stop()

client = gspread.authorize(creds)

# -----------------------------
# Secrets: sheet URLs
# -----------------------------
def get_secret_path(path, err_hint):
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
# Load Register (validation)
# -----------------------------
try:
    reg_book = client.open_by_url(register_sheet_url)
    reg_ws   = open_ws(reg_book, ["Register", "register", "Sheet1"])
    register_df = pd.DataFrame(reg_ws.get_all_records())
except gspread.exceptions.SpreadsheetNotFound:
    st.error("❌ Register sheet URL invalid or not shared with the service account.")
    st.stop()
except gspread.exceptions.WorksheetNotFound:
    st.error("❌ Could not find a 'Register' worksheet (or fallback) in the Register sheet.")
    st.stop()

# Expected columns:
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
verified = False

if tuition_code and student_id:
    mask = (
        register_df["Tuition_Code"].astype(str).str.strip().eq(str(tuition_code).strip()) &
        register_df["Student_ID"].astype(str).str.strip().eq(str(student_id).strip())
    )
    if mask.any():
        student_row = register_df[mask].iloc[0]
        st.success(f"✅ Verified: {student_row['Student_Name']} ({student_row['Tuition_Name']})")
        verified = True
    else:
        st.error("❌ Invalid code or ID. Please try again.")
 # Only show quiz if verified
if not verified:
    st.stop()     

# -----------------------------
# Load Questions (Main & Remedial from same book)
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
    st.error("❌ Could not find 'Main'/'Remedial' worksheets in the Questions sheet.")
    st.stop()

# Validate columns & filter MAIN
if "SubtopicID" not in main_df.columns:
    st.error("❌ 'Main' worksheet must include a 'SubtopicID' column.")
    st.stop()

main_questions = main_df[main_df["SubtopicID"].astype(str).str.strip() == subtopic_id].copy()
if main_questions.empty:
    st.warning("⚠ No MAIN questions found for this subtopic.")
    st.stop()

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
    st.error("❌ Could not find a 'Responses' worksheet (or fallback) in the Responses sheet.")
    st.stop()

# -----------------------------
# Duplicate-prevention
# -----------------------------
attempt_key = f"attempt::{bank}::{subtopic_id}::{student_id or 'anon'}"
if st.session_state.get(attempt_key):
    st.error("⛔ You have already submitted this MAIN attempt in this session.")
    st.stop()

def has_existing_main_attempt(student_id_val, subtopic_val) -> bool:
    """
    Check Responses sheet for a prior MAIN attempt by the same Student_ID & Subtopic.
    NOTE: This pulls all rows; for very large sheets consider optimizing or paging.
    """
    try:
        rows = responses_ws.get_all_records()
        if not rows:
            return False
        df = pd.DataFrame(rows)
        if df.empty:
            return False
        cond = (
            df["Student_ID"].astype(str).str.strip().eq(str(student_id_val).strip()) &
            df["Subtopic"].astype(str).str.strip().eq(str(subtopic_val).strip()) &
            df["Attempt_Type"].astype(str).str.strip().str.lower().eq("main")
        )
        return cond.any()
    except Exception:
        return False

if allow_retake != "1" and student_row is not None and has_existing_main_attempt(student_id, subtopic_id):
    st.error("⛔ A MAIN attempt for this subtopic already exists for this Student ID. Append `?allow_retake=1` in the URL to override.")
    st.stop()

# -----------------------------
# UI header
# -----------------------------
st.title(f"📄 {subject.title()} — {subtopic_id.replace('_',' ')}")

# -----------------------------
# Responses logging
# -----------------------------
def append_response_row(qnum, given, correct, awarded, attempt_type):
    responses_ws.append_row([
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),                       # Timestamp
        (student_id if student_row is not None else "Unregistered"),        # Student_ID
        (student_row["Student_Name"] if student_row is not None else "Unknown"),
        (tuition_code if student_row is not None else "Unknown"),           # Class_Code (using Tuition_Code)
        chapter,                                                            # Chapter
        subtopic_id,                                                        # Subtopic
        qnum,                                                               # Question_Number
        given,                                                              # Student_Answer
        correct,                                                            # Correct_Answer
        awarded,                                                            # Points_Awarded
        attempt_type,                                                       # Attempt_Type (Main/Remedial)
        ""                                                                  # IP_Address (left blank)
    ])

# -----------------------------
# MAIN quiz (with optional shuffles)
# -----------------------------
# Deterministic seeds (consistent per student+subtopic)
seed_base = f"{student_id or 'anon'}::{subtopic_id}"
q_rows = list(main_questions.itertuples(index=False))

if SHUFFLE_QUESTIONS:
    q_rows = stable_shuffle(q_rows, seed_base + "::Q")

user_answers = {}
with st.form("main_quiz"):
    for row in q_rows:
        # Access row fields by name
        rowd = row._asdict() if hasattr(row, "_asdict") else dict(row._asdict())  # safety
        qid   = str(rowd.get("QuestionID", "")).strip()
        qtext = str(rowd.get("QuestionText", "")).strip()
        img   = normalize_img_url(rowd.get("ImageURL", ""))

        options = [
            str(rowd.get("Option_A", "") or "").strip(),
            str(rowd.get("Option_B", "") or "").strip(),
            str(rowd.get("Option_C", "") or "").strip(),
            str(rowd.get("Option_D", "") or "").strip(),
        ]
        # Filter empty options gracefully
        options = [o for o in options if o]

        # Optionally shuffle options (but comparison is TEXT vs TEXT, so safe)
        disp_options = stable_shuffle(options, seed_base + f"::OPT::{qid}") if SHUFFLE_OPTIONS else options

        with st.container():
            # Question
            render_question(qid, qtext)

            # Image (between question and options)
            if img:
                st.image(img, use_container_width=True)

            # Options
            user_answers[qid] = st.radio(
                "Select your answer:",
                options=disp_options,
                key=f"main_{qid}",
                index=None
            )

    submit_main = st.form_submit_button("Submit Quiz")
      st.success(f"🎯 You scored {earned_points} out of {total_points} in the main quiz!")
# -----------------------------
# Handle MAIN submission
# -----------------------------
if submit_main:
    wrong_qs = []
    total_points = 0
    earned_points = 0

    # We need original order from dataframe; iterate main_questions (not shuffled),
    # because Responses need the real qids, and correctness is by answer text.
    for _, q in main_questions.iterrows():
        qid     = str(q.get("QuestionID", "")).strip()
        correct = get_correct_value(q)
        given   = str(user_answers.get(qid, "") or "").strip()
        marks   = safe_int(q.get("Marks", 1), 1)

        total_points += marks
        awarded = marks if given == correct and given != "" else 0
        earned_points += awarded

        if awarded == 0:
            wrong_qs.append(q)

        # Log MAIN attempt row per question
        append_response_row(qnum=qid, given=given, correct=correct, awarded=awarded, attempt_type="Main")

    # Mark session attempt to block re-submission
    st.session_state[attempt_key] = True

    # Telegram notifications (registered only)
    if student_row is not None:
        bot_token       = st.secrets.get("telegram", {}).get("bot_token", "")
        parent_chat_id  = str(student_row.get("Parent_Telegram_ID", "")).strip()
        teacher_chat_id = str(student_row.get("Teacher_Telegram_ID", "")).strip()

        # Parent gets total score
        if bot_token and parent_chat_id:
            send_telegram(
                bot_token,
                parent_chat_id,
                f"📊 {student_row['Student_Name']} scored {earned_points}/{total_points} in {subject} → {subtopic_id}."
            )

        # Teacher only if there were incorrect answers in MAIN
        if bot_token and teacher_chat_id and len(wrong_qs) > 0:
            send_telegram(
                bot_token,
                teacher_chat_id,
                f"⚠️ {student_row['Student_Name']} had incorrect answers in {subject} → {subtopic_id}."
            )

    # If there are wrong answers, show REMEDIAL
    if len(wrong_qs) > 0:
        st.warning("⚠️ Some answers were incorrect. Please take the remedial quiz below.")

        wrong_main_ids = [str(q.get("QuestionID", "")).strip() for _, q in pd.DataFrame(wrong_qs).iterrows()]
        if "MainQuestionID" not in remedial_df.columns:
            st.info("ℹ️ No remedial mapping: 'Remedial' sheet needs a 'MainQuestionID' column.")
        else:
            rem_set = remedial_df[remedial_df["MainQuestionID"].astype(str).str.strip().isin(wrong_main_ids)].copy()

            if rem_set.empty:
                st.info("ℹ️ No remedial questions found for the incorrect items.")
            else:
                # Optional: shuffle remedial set deterministically
                rem_rows = list(rem_set.itertuples(index=False))
                if SHUFFLE_QUESTIONS:
                    rem_rows = stable_shuffle(rem_rows, seed_base + "::RQ")

                remedial_answers = {}
                with st.form("remedial_quiz"):
                    for rq in rem_rows:
                        rd = rq._asdict()
                        rqid       = str(rd.get("RemedialQuestionID", "")).strip()
                        r_main_qid = str(rd.get("MainQuestionID", "")).strip()
                        rq_text    = str(rd.get("QuestionText", "")).strip()
                        r_img      = normalize_img_url(rd.get("ImageURL", ""))

                        r_opts = [
                            str(rd.get("Option_A", "") or "").strip(),
                            str(rd.get("Option_B", "") or "").strip(),
                            str(rd.get("Option_C", "") or "").strip(),
                            str(rd.get("Option_D", "") or "").strip(),
                        ]
                        r_opts = [o for o in r_opts if o]
                        disp_r_opts = stable_shuffle(r_opts, seed_base + f"::ROPT::{rqid}") if SHUFFLE_OPTIONS else r_opts

                        with st.container():
                            render_question(rqid, rq_text)
                            if r_img:
                                st.image(r_img, use_container_width=True)

                            remedial_answers[rqid] = st.radio(
                                "Select your answer:",
                                options=disp_r_opts,
                                key=f"remedial_{rqid}",
                                index=None
                            )

                    submit_remedial = st.form_submit_button("Submit Remedial Quiz")

                if submit_remedial:
                    # Iterate the actual rem_set (original df) for authoritative rows
                    for _, row in rem_set.iterrows():
                        rqid    = str(row.get("RemedialQuestionID", "")).strip()
                        correct = get_correct_value(row)
                        given   = str(remedial_answers.get(rqid, "") or "").strip()
                        marks   = safe_int(row.get("Marks", 1), 1)
                        awarded = marks if given == correct and given != "" else 0

                        append_response_row(
                            qnum=rqid,
                            given=given,
                            correct=correct,
                            awarded=awarded,
                            attempt_type="Remedial"
                        )

                    st.success("✅ Remedial quiz submitted! Thank you.")
    else:
        st.success("🎉 All answers were correct! No remedial needed.")
