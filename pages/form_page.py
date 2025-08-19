
# pages/form_page.py
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time
import io
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import smtplib
from email.message import EmailMessage
import base64
import random
import hashlib
import requests

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

ss = st.session_state
# ---------- Initialize session_state keys ----------
if "student_info" not in ss:
    ss["student_info"] = {}
if "student_verified" not in ss:
    ss["student_verified"] = False
if "main_user_answers" not in ss:
    ss["main_user_answers"] = {}
if "main_submitted" not in ss:
    ss["main_submitted"] = False
if "main_results" not in ss:
    ss["main_results"] = {}
if "remedial_answers" not in ss:
    ss["remedial_answers"] = {}


# ---------- CONFIG / SETUP ----------
st.set_page_config(page_title="Quiz Form", layout="centered")

# --- Helpful utilities (small, robust) ---
def get_params():
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
    v = str(value or "").strip()
    if not v:
        return ""
    # convert drive file id or share link to direct view if possible
    if "drive.google.com" in v and "id=" not in v:
        # try to extract file id from common formats
        import re
        m = re.search(r"/d/([a-zA-Z0-9_-]+)", v)
        if m:
            fid = m.group(1)
            return f"https://drive.google.com/uc?export=view&id={fid}"
    return v

def stable_shuffle(items, seed_str):
    seq = list(items)
    h = int(hashlib.md5(seed_str.encode("utf-8")).hexdigest(), 16)
    rnd = random.Random(h)
    rnd.shuffle(seq)
    return seq

def get_correct_value(row):
    if "CorrectOption" in row and str(row.get("CorrectOption","")).strip():
        return str(row.get("CorrectOption","")).strip()
    if "Correct_Answer" in row and str(row.get("Correct_Answer","")).strip():
        return str(row.get("Correct_Answer","")).strip()
    # fallback: check single column names
    return str(row.get("CorrectAnswer","")).strip()

def safe_str(v):
    return str(v) if v is not None else ""
# ---------- Check if all main quiz questions are answered ----------
def all_answered_main(q_rows):
    """
    Returns True if every question in q_rows has a non-empty answer in session_state.
    """
    for row in q_rows:
        qid = str(row.QuestionID).strip()
        ans = ss["main_user_answers"].get(qid)
        if not ans:  # catches None or empty string
            return False
    return True

# ---------- PARAMETERS & BANK ----------
param = get_params()
subject = param("subject", "").strip()
subtopic_id = param("subtopic_id", "").strip()
bank = param("bank", subject).strip().lower()   #lowercased for easier mapping

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
    "english": "ssc_english",
    "ssc_english": "ssc_english",
}
if bank.lower() in bank_map:
    bank = bank_map[bank.lower()]
    
if not subject or not subtopic_id:
    st.error("❌ Missing `subject` or `subtopic_id` in URL.")
    st.stop()

# ---------- GOOGLE SHEETS AUTH ----------
scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
try:
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
except Exception as e:
    st.error("Missing/invalid `gcp_service_account` in secrets.")
    st.stop()
client = gspread.authorize(creds)

# ---------- SHEET URLS in secrets ----------
# Put these keys in secrets.toml: google.question_sheet_url and google.response_sheet_url and google.register_sheet_url
try:
    question_sheets = st.secrets["google"]["question_sheet_urls"]
    response_sheets = st.secrets["google"]["response_sheet_urls"]
    register_sheet_url = st.secrets["google"]["register_sheet_url"]

    if bank not in question_sheets:
        st.error(f"No question sheet configured for bank '{bank}'. Check secrets.toml.")
        st.stop()
    if bank not in response_sheets:
        st.error(f"No response sheet configured for bank '{bank}'. Check secrets.toml.")
        st.stop()
    
    question_sheet_url = question_sheets[bank]
    response_sheet_url = response_sheets[bank]
except Exception as e:
    st.error(f"Error loading sheet URLs from secrets: {e}")
    st.stop()

# ---------- LOAD REGISTER for student verification ----------
try:
    reg_book = client.open_by_url(register_sheet_url)
    reg_ws = reg_book.worksheets()[0]
    register_df = pd.DataFrame(reg_ws.get_all_records())
except Exception as e:
    st.error("Unable to load Register sheet. Check URL and sharing with service account.")
    st.stop()

# ---------- STUDENT VERIFICATION UI ----------
st.title(f"📄 {subject} — {subtopic_id.replace('_',' ')}")

with st.expander("👤 Student Verification", expanded=not ss.get("student_verified", False)):
    with st.form("student_verification"):
        c1, c2, c3 = st.columns([1,1,1])
        with c1:
            tuition_code = st.text_input("Tuition Code*", value=ss.get("student_info", {}).get("Tuition_Code", ""))
        with c2:
            student_id = st.text_input("Student ID*", value=ss.get("student_info", {}).get("Student_ID", ""))
        with c3:
            student_password = st.text_input("Password*", type="password")

        verify_submit = st.form_submit_button("Submit Verification")

if verify_submit:
    if not tuition_code.strip() or not student_id.strip() or not student_password.strip():
        st.error("⚠ Please fill in Tuition Code, Student ID and Password.")
    else:
        mask = (
            (register_df["Tuition_Code"].astype(str).str.strip() == tuition_code.strip()) &
            (register_df["Student_ID"].astype(str).str.strip() == student_id.strip()) &
            (register_df["Password"].astype(str).str.strip() == student_password.strip())
        )

        if mask.any():
            student_row = register_df[mask].iloc[0]
            st.success(f"✅ Verified: {student_row['Student_Name']} ({student_row['Tuition_Name']})")
            ss["student_verified"] = True
            ss["student_info"] = {
                "StudentName": student_row.get("Student_Name", ""),
                "Class": student_row.get("Class", ""),
                "RollNo": student_row.get("Roll_No", ""),
                "StudentEmail": student_row.get("Student_Email", ""),
                "ParentEmail": student_row.get("Parent_Email", ""),
                "TeacherEmail": student_row.get("Teacher_Email", ""),
                "HeadTeacherEmail": student_row.get("Head_Teacher_Email", ""),
                "ParentTelegramID": student_row.get("Parent_Telegram_ID", ""),
                "TeacherTelegramID": student_row.get("Teacher_Telegram_ID", ""),
                "Tuition_Code": tuition_code.strip(),
                "Student_ID": student_id.strip(),
                "Password": student_password.strip(),  
            }
        else:
            st.error("❌ Invalid Tuition Code or Student ID. Please try again.")

if not ss.get("student_verified", False):
    st.stop()
    
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

# ---------- LOAD QUESTIONS ----------
try:
    q_book = client.open_by_url(question_sheet_url)
    main_ws = None
    remedial_ws = None
    # try opening named worksheets
    for w in q_book.worksheets():
        nm = w.title.strip().lower()
        if nm == "main":
            main_ws = w
        if nm == "remedial":
            remedial_ws = w
    if main_ws is None:
        main_ws = q_book.worksheet("Main")
    if remedial_ws is None:
        remedial_ws = q_book.worksheet("Remedial")
    main_df = pd.DataFrame(main_ws.get_all_records())
    remedial_df = pd.DataFrame(remedial_ws.get_all_records())
except Exception as e:
    st.error("Unable to load Main/Remedial worksheets. Check names & sharing.")
    st.stop()

# strip column names (defensive)
main_df.columns = main_df.columns.str.strip()
remedial_df.columns = remedial_df.columns.str.strip()

# filter main questions by SubtopicID (strip spaces)
main_df["SubtopicID"] = main_df["SubtopicID"].astype(str).str.strip()
main_questions = main_df[main_df["SubtopicID"] == subtopic_id].copy()
if main_questions.empty:
    st.warning("No questions found for the subtopic.")
    st.stop()

# ---------- RESPONSES sheet ----------
try:
    resp_book = client.open_by_url(response_sheet_url)
    responses_ws = resp_book.worksheets()[0]
except Exception:
    st.error("Unable to open Responses sheet. Check URL & sharing.")
    st.stop()

# helper to append a row
def append_response_row(timestamp, student_id_v, student_name, tuition_code_v,
                        chapter_v, subtopic_v, qnum, given, correct, awarded, attempt_type):
    try:
        responses_ws.append_row([timestamp, student_id_v, student_name, tuition_code_v,
                                 chapter_v, subtopic_v, qnum, given, correct, awarded, attempt_type])
    except Exception:
        pass  # best-effort

# ---------- UI Header ----------
st.title(f"📄 {subject.title()} — {subtopic_id.replace('_',' ')}")

# ---------- SEEDS for stable shuffling ----------
info = ss.get("student_info", {})
seed_base = f"{info.get('Student_ID','anon')}::{subtopic_id}"

# ---------- MAIN QUIZ FORM ----------
st.header("Main Quiz (Attempt 1)")
q_rows = list(main_questions.itertuples(index=False))
# stable shuffle
q_rows = stable_shuffle(q_rows, seed_base + "::Q") if True else q_rows

# init containers for answers (persist across reruns)
if "main_user_answers" not in st.session_state:
    st.session_state.main_user_answers = {}

if "main_submitted" not in st.session_state:
    st.session_state.main_submitted = False
if "main_results" not in st.session_state:
    st.session_state.main_results = {}

def all_answered_main(q_rows):
    for row in q_rows:
        rowd = row._asdict()
        qid = str(rowd.get("QuestionID","")).strip()
        if not st.session_state.main_user_answers.get(qid):
            return False
    return True

with st.form("main_quiz"):
    for row in q_rows:
        rowd = row._asdict()
        qid = str(rowd.get("QuestionID","")).strip()
        qtext = str(rowd.get("QuestionText","")).strip()
        img = normalize_img_url(rowd.get("ImageURL",""))
        # options
        opts = [str(rowd.get("Option_A","") or "").strip(),
                str(rowd.get("Option_B","") or "").strip(),
                str(rowd.get("Option_C","") or "").strip(),
                str(rowd.get("Option_D","") or "").strip()]
        opts = [o for o in opts if o]
        disp_opts = stable_shuffle(opts, seed_base + f"::OPT::{qid}") if True else opts

        st.markdown(f"**{qid}**")
        st.write(qtext)
        if img:
            st.image(img, use_container_width=True)
        # restore previous selection if exists (index used is last chosen index)
        prev = st.session_state.main_user_answers.get(qid, None)
        sel = st.radio("Select your answer:", options=disp_opts, key=f"main_{qid}", index=None if prev is None else disp_opts.index(prev))
        st.session_state.main_user_answers[qid] = sel
        st.markdown("---")
    submit_main = st.form_submit_button("Submit Main Quiz")

# Validate & grade main submission
if submit_main:
    if not all_answered_main(q_rows):
        st.error("Please answer all questions before submitting (all questions are compulsory).")
    else:
        # grade
        total = 0
        earned = 0
        wrong_rows = []
        for _, q in main_questions.iterrows():
            qid = str(q.get("QuestionID","")).strip()
            correct = get_correct_value(q)
            given = str(st.session_state.main_user_answers.get(qid,"")).strip()
            marks = int(q.get("Marks") or 1)
            total += marks
            awarded = marks if (given != "" and given == correct) else 0
            earned += awarded
            append_response_row(
                datetime.now().isoformat(),
                ss["student_info"].get("Student_ID", ""),
                ss["student_info"].get("StudentName", ""),
                ss["student_info"].get("Tuition_Code", ""),
                subject, subtopic_id, qid, given, correct, awarded, "Main"
            )

            if awarded == 0:
                wrong_rows.append(q)
        st.session_state.main_results = {"total": total, "earned": earned, "wrong": wrong_rows}
        st.session_state.main_submitted = True
        st.success(f"🎯 Main Score: {earned}/{total}")

# ---------- SHOW MAIN RESULTS (keeps visible) ----------
if st.session_state.main_submitted:
    res = st.session_state.main_results
    st.markdown("### Main Quiz Review")
    st.success(f"Score: {res['earned']}/{res['total']}")
    if res["wrong"]:
        st.error("You answered these questions incorrectly. Review below:")
        # table of mistakes
        table = []
        for q in res["wrong"]:
            qid = str(q.get("QuestionID","")).strip()
            qtext = str(q.get("QuestionText","")).strip()
            correct = get_correct_value(q)
            given = str(st.session_state.main_user_answers.get(qid,"")).strip()
            table.append({"QuestionID": qid, "Question": qtext, "Your": given, "Correct": correct})
        st.table(pd.DataFrame(table))
    else:
        st.success("All main answers correct!")

# ---------- 20s DELAY & REMEDIAL DISPLAY ----------
if st.session_state.get("main_submitted", False) and st.session_state.get("main_results", {}).get("wrong"):
    # show message and countdown once
    if "remedial_ready" not in st.session_state:
        placeholder = st.empty()
        for i in range(20, 0, -1):
            placeholder.info(f"Please review your incorrect answers above. Remedial will load in {i} seconds...")
            time.sleep(1)
        placeholder.empty()
        st.session_state.remedial_ready = True

# ---------- REMEDIAL (shows below main, main stays visible) ----------
if st.session_state.get("remedial_ready", False):
    st.header("Remedial Quiz")
    wrong_qs = st.session_state.main_results.get("wrong", [])
    # build remedial set by MainQuestionID mapping
    if "MainQuestionID" not in remedial_df.columns:
        st.info("Remedial sheet missing 'MainQuestionID' column. Add it to map remedial items to main questions.")
    else:
        wrong_ids = [str(q.get("QuestionID","")).strip() for q in wrong_qs]
        rem_set = remedial_df[remedial_df["MainQuestionID"].astype(str).str.strip().isin(wrong_ids)].copy()
        if rem_set.empty:
            st.info("No remedial questions found for these misses.")
        else:
            # prepare session state for remedial answers
            if "remedial_answers" not in st.session_state:
                st.session_state.remedial_answers = {}
            with st.form("remedial_form"):
                for _, r in rem_set.iterrows():
                    rqid = str(r.get("RemedialQuestionID","")).strip()
                    rtext = str(r.get("QuestionText","")).strip()
                    rimg = normalize_img_url(r.get("ImageURL",""))
                    rhint = str(r.get("Hint","")).strip()  # hint column in Remedial sheet (optional)
                    opts = [str(r.get("Option_A","") or "").strip(),
                            str(r.get("Option_B","") or "").strip(),
                            str(r.get("Option_C","") or "").strip(),
                            str(r.get("Option_D","") or "").strip()]
                    opts = [o for o in opts if o]
                    disp_opts = stable_shuffle(opts, seed_base + f"::ROPT::{rqid}") if True else opts
                    st.markdown(f"**{rqid}**")     # remedial question ID
                    st.write(rtext)                # remedial question text
                    if rimg:
                        st.image(rimg, use_container_width=True)
                    # hint UI (bulb)
                    if rhint:
                        with st.expander("💡 Hint"):
                            st.write(rhint)
                    prev = st.session_state.remedial_answers.get(rqid, None)
                    sel = st.radio("Select your answer:", options=disp_opts, key=f"rem_{rqid}", index=0 if prev is None else disp_opts.index(prev))
                    st.session_state.remedial_answers[rqid] = sel
                    st.markdown("---")
                submit_remedial = st.form_submit_button("Submit Remedial")

            if submit_remedial:
                # grade remedial
                rem_total = 0
                rem_earned = 0
                for _, r in rem_set.iterrows():
                    rqid = str(r.get("RemedialQuestionID","")).strip()
                    correct = get_correct_value(r)
                    given = str(st.session_state.remedial_answers.get(rqid,"")).strip()
                    marks = int(r.get("Marks") or 1)
                    awarded = marks if (given != "" and given == correct) else 0
                    append_response_row(
                        datetime.now().isoformat(),
                        ss["student_info"].get("Student_ID", ""),
                        ss["student_info"].get("StudentName", ""),
                        ss["student_info"].get("Tuition_Code", ""),
                        subject, subtopic_id, qid, given, correct, awarded, "Remedial"
                    )
                    rem_total += marks
                    rem_earned += awarded
                st.success(f"✅ Remedial submitted: {rem_earned}/{rem_total}")
                st.balloons()
                st.session_state.remedial_done = True

# ---------- FINAL COMBINED SUMMARY / GRAPH / PDF EXPORT / EMAIL ----------
if st.session_state.get("main_submitted", False):
    st.markdown("## Final Summary & Download")
    main_res = st.session_state.main_results
    st.write(f"Main: {main_res['earned']}/{main_res['total']}")
    if st.session_state.get("remedial_done", False):
        st.write("Remedial: submitted")
    # simple graph: main correct vs wrong
    fig, ax = plt.subplots(figsize=(4,2))
    correct_count = main_res['earned']
    wrong_count = main_res['total'] - main_res['earned']
    ax.bar(['Correct','Incorrect'], [correct_count, wrong_count], color=['blue','red'])
    ax.set_title("Main Performance")
    ax.set_ylim(0, max(correct_count, wrong_count) + 1)
    ax.set_yticks(range(0, max(correct_count, wrong_count) + 2))
    ax.set_ylabel("Number of Questions")
    st.pyplot(fig)

    # Build PDF bytes (reportlab + embed plt as image)
    def build_pdf_bytes():
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        ...
        doc.build(elements)
        buffer.seek(0)
        return buffer.read()
        # Title
        elements.append(Paragraph(f"Quiz Report: {subject} - {subtopic_id}", styles["Title"]))
        info = ss.get("student_info", {})
        elements.append(Paragraph(f"Student: {info.get('StudentName','Unknown')} ({info.get('Student_ID','')})", styles["Normal"]))
        elements.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]))
        elements.append(Spacer(1, 12))
 
        # Insert chart
        imgbuf = io.BytesIO()
        fig.savefig(imgbuf, format="PNG", bbox_inches='tight')
        imgbuf.seek(0)
        from reportlab.platypus import Image
        elements.append(Image(imgbuf, width=400, height=200))
        elements.append(Spacer(1, 20))

        # Build table data (Question | Your Answer | Correct Answer)
        table_data = [["Q.No", "Question", "Your Answer", "Correct Answer"]]
        for _, q in main_questions.iterrows():
            qid = str(q.get("QuestionID","")).strip()
            qtext = str(q.get("QuestionText","")).strip()
            given = st.session_state.main_user_answers.get(qid,"")
            correct = get_correct_value(q)
            table_data.append([qid, qtext, given, correct])

        # Create table
        table = Table(table_data, colWidths=[40, 220, 100, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('TEXTCOLOR',(0,0),(-1,0),colors.black),
            ('ALIGN',(0,0),(-1,-1),'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 11),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ]))

        elements.append(table)
        doc.build(elements)
        buffer.seek(0)
        return buffer.read()

    pdf_bytes = build_pdf_bytes()
    info = ss.get("student_info", {})

    try:
        smtp_cfg = st.secrets.get("smtp", {})
        if not smtp_cfg:
            st.error("SMTP config not found in secrets.toml.")
        else:
            # ---------------------------
            # Auto-send to Parent + Teachers
            # ---------------------------
            msg = EmailMessage()
            msg["Subject"] = f"Quiz Report: {subject} - {subtopic_id}"
            msg["From"] = smtp_cfg.get("from_email")

            # Collect recipients
            student_email = info.get("StudentEmail", "")
            parent_email = info.get("ParentEmail", "")
            subject_teacher = info.get(f"{subject.title()}_Teacher", "")
            head_teacher = info.get("Head_Teacher", "")

            to_auto = []
            if parent_email: to_auto.append(parent_email)
            if subject_teacher: to_auto.append(subject_teacher)
            if head_teacher: to_auto.append(head_teacher)

            if not to_auto:
                st.error("No parent/teacher email found for this student in Register.")
            else:
                msg["To"] = ", ".join(to_auto)
                msg.set_content("Please find attached the quiz report.")
                msg.add_attachment(
                    pdf_bytes,
                    maintype="application",
                    subtype="pdf",
                    filename=f"report_{info.get('Student_ID','')}.pdf"
                )

                server = smtplib.SMTP(smtp_cfg.get("server"), int(smtp_cfg.get("port",587)))
                server.starttls()
                server.login(smtp_cfg.get("username"), smtp_cfg.get("password"))
                server.send_message(msg)
                server.quit()
                st.success("✅ Report sent automatically to Parent + Teacher(s).")

        # ---------------------------
        # Optional: Student self-copy
        # ---------------------------
        # --- PDF Download Section ---
        st.markdown("### 📄 Download Your Report")
        pdf_bytes = build_pdf_bytes()
        info = ss.get("student_info", {})
        st.download_button(
            label="⬇️ Download PDF Report",
            data=pdf_bytes,
            file_name=f"{info.get('StudentName','student')}_report.pdf",
            mime="application/pdf"
        )
        
         # -------------------- Email Copy Section --------------------   
        with st.expander("📧 Send Copy to My Email"):
            if not student_email:
                st.error("No student email found in register.")
            else:
                try:
                    msg2 = EmailMessage()
                    msg2["Subject"] = f"Your Quiz Report: {subject} - {subtopic_id}"
                    msg2["From"] = smtp_cfg.get("from_email")
                    msg2["To"] = student_email
                    msg2.set_content("Here is your personal copy of the quiz report.")
                    msg2.add_attachment(
                        pdf_bytes,
                        maintype="application",
                        subtype="pdf",
                        filename=f"report_{info.get('Student_ID','')}.pdf"
                    )
                    server = smtplib.SMTP(smtp_cfg.get("server"), int(smtp_cfg.get("port",587)))
                    server.starttls()
                    server.login(smtp_cfg.get("username"), smtp_cfg.get("password"))
                    server.send_message(msg2)
                    server.quit()
                    st.success("📧 Report sent to your email.")
                except Exception as e:
                    st.error(f"Failed to send student copy: {e}")

    except Exception as e:
        st.error(f"Failed to send email: {e}")
