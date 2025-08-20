# pages/form_page.py
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time
import io
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

# --- ReportLab (PDF generation) ---
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- Email ---
import smtplib
from email.message import EmailMessage

# --- Other utilities ---
import base64
import random
import hashlib
import requests


# ---------- CONFIG / SETUP ----------
st.set_page_config(page_title="Quiz Form", layout="centered")

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
  
def build_pdf_bytes(score, total, wrong_table):
    """
    Build a simple PDF report and return it as bytes.
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 50, "Quiz Report")

    c.setFont("Helvetica", 12)
    c.drawString(100, height - 100, f"Score: {score}/{total}")

    if wrong_table:
        c.drawString(100, height - 130, "Incorrect Answers:")
        y = height - 150
        for row in wrong_table:
            qid = row.get("QuestionID", "")
            qtext = row.get("QuestionText", "")[:60]  # trim
            corr = row.get("Correct", "")
            given = row.get("Your", "")
            c.drawString(100, y, f"{qid}: {qtext} | Your: {given} | Correct: {corr}")
            y -= 20

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()
def send_report_to_student(to_email, pdf_bytes):
    """
    Send quiz report to student via email.
    """
    msg = EmailMessage()
    msg["Subject"] = "Your Quiz Report"
    msg["From"] = "noreply@myschool.com"
    msg["To"] = to_email
    msg.set_content("Attached is your quiz performance report.")

    msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename="quiz_report.pdf")

    # Uses st.secrets["smtp"] values
    smtp_cfg = st.secrets.get("smtp", {})
    with smtplib.SMTP_SSL(smtp_cfg.get("server"), smtp_cfg.get("port")) as server:
        server.login(smtp_cfg.get("user"), smtp_cfg.get("password"))
        server.send_message(msg)



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
# ---------- BANK MAPPING ----------

# Maps incoming subject/bank name (from URL param) to the sheet keys in secrets.toml
bank_map = {
    # Maths
    "mathematics": ("ssc_maths_geometry", "ssc_maths_geometry_r"),
    "maths": ("ssc_maths_geometry", "ssc_maths_geometry_r"),
    "geometry": ("ssc_maths_geometry", "ssc_maths_geometry_r"),
    "algebra": ("ssc_maths_algebra", "ssc_maths_algebra_r"),
    "ssc_maths_geometry": ("ssc_maths_geometry", "ssc_maths_geometry_r"),
    "ssc_maths_algebra": ("ssc_maths_algebra", "ssc_maths_algebra_r"),

    # Science
    "science": ("ssc_science_part_1", "ssc_science_part_1_r"),  # default maps to part 1
    "science1": ("ssc_science_part_1", "ssc_science_part_1_r"),
    "science_1": ("ssc_science_part_1", "ssc_science_part_1_r"),
    "science2": ("ssc_science_part_2", "ssc_science_part_2_r"),
    "science_2": ("ssc_science_part_2", "ssc_science_part_2_r"),
    "ssc_science_part_1": ("ssc_science_part_1", "ssc_science_part_1_r"),
    "ssc_science_part_2": ("ssc_science_part_2", "ssc_science_part_2_r"),

    # English
    "english": ("ssc_english", "ssc_english_r"),
    "ssc_english": ("ssc_english", "ssc_english_r"),
}

# ✅ Get subject + subtopic from query params
if not subject or not subtopic_id:
    st.error("❌ Missing `subject` or `subtopic_id` in URL.")
    st.stop()

# ✅ Resolve the subject → sheet keys
if bank.lower() in bank_map:
    qsheet_key, rsheet_key = bank_map[bank.lower()]
else:
    st.error(f"❌ Unknown subject '{bank}'")
    st.stop()

# ✅ Pull actual Google Sheet URLs from secrets.toml
try:
    qsheet_url = st.secrets["google"]["question_sheet_urls"][qsheet_key]
    rsheet_url = st.secrets["google"]["response_sheet_urls"][rsheet_key]
except KeyError as e:
    st.error(f"❌ Missing sheet key in secrets.toml: {e}")
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

    if qsheet_key not in question_sheets:
        st.error(f"No question sheet configured for key '{qsheet_key}'. Check secrets.toml.")
        st.stop()
    if rsheet_key not in response_sheets:
        st.error(f"No response sheet configured for key '{rsheet_key}'. Check secrets.toml.")
        st.stop()
    
    question_sheet_url = question_sheets[qsheet_key]
    response_sheet_url = response_sheets[rsheet_key]
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
st.markdown(ANTI_CHEAT_JS, unsafe_allow_html=True)

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
q_rows = stable_shuffle(q_rows, seed_base + "::Q")

ss.setdefault("main_user_answers", {})
ss.setdefault("main_submitted", False)
ss.setdefault("main_results", {})

def _all_answered(qrows):
    for r in qrows:
        qid = str(r.QuestionID).strip()
        if not ss["main_user_answers"].get(qid):
            return False
    return True

# ------------------ BEFORE SUBMIT ------------------
if not ss["main_submitted"]:
    with st.form("main_quiz"):
        for i, row in enumerate(q_rows, start=1):
            rowd  = row._asdict()
            qid   = str(rowd.get("QuestionID","")).strip()
            qtext = str(rowd.get("QuestionText","")).strip()
            img   = normalize_img_url(rowd.get("ImageURL",""))

            opts = [str(rowd.get("Option_A","") or "").strip(),
                    str(rowd.get("Option_B","") or "").strip(),
                    str(rowd.get("Option_C","") or "").strip(),
                    str(rowd.get("Option_D","") or "").strip()]
            opts = [o for o in opts if o]
            disp_opts = stable_shuffle(opts, seed_base + f"::OPT::{qid}")

            st.markdown(f"**{qid}**<br>{qtext}", unsafe_allow_html=True)
            if img:
                st.image(img, use_container_width=True)

            prev = ss["main_user_answers"].get(qid, None)
            sel = st.radio(
                "Select your answer:",
                options=disp_opts,
                key=f"main_{qid}",
                index=disp_opts.index(prev) if prev in disp_opts else None
            )
            ss["main_user_answers"][qid] = sel
            st.markdown("---")

        submit_main = st.form_submit_button("Submit Main Quiz")

    if submit_main:
        if not _all_answered(q_rows):
            st.error("Please answer all questions before submitting (all are compulsory).")
        else:
            # grade + store results
            total_marks = 0
            earned_marks = 0
            wrong_ids = []
            question_results = []

            for _, q in main_questions.iterrows():
                qid     = str(q.get("QuestionID","")).strip()
                qtext   = str(q.get("QuestionText","")).strip()
                img     = normalize_img_url(q.get("ImageURL",""))
                correct = get_correct_value(q)
                given   = str(ss["main_user_answers"].get(qid,"")).strip()
                marks   = int(q.get("Marks") or 1)

                total_marks += marks
                awarded = marks if (given and given == correct) else 0
                earned_marks += awarded
                if awarded == 0:
                    wrong_ids.append(qid)

                question_results.append({
                    "qid": qid,
                    "question": qtext,
                    "image": img,
                    "options": [o for o in [q.get("Option_A"), q.get("Option_B"),
                                            q.get("Option_C"), q.get("Option_D")] if o],
                    "correct": correct,
                    "student": given
                })

                append_response_row(
                    datetime.now().isoformat(),
                    ss["student_info"].get("Student_ID", ""),
                    ss["student_info"].get("StudentName", ""),
                    ss["student_info"].get("Tuition_Code", ""),
                    subject, subtopic_id, qid, given, correct, awarded, "Main"
                )

            ss["main_results"] = {
                "total": total_marks,
                "earned": earned_marks,
                "wrong_ids": wrong_ids,
                "questions": question_results
            }
            ss["main_submitted"] = True
            st.rerun()

# ------------------ AFTER SUBMIT (REVIEW MODE) ------------------
else:
    res = ss["main_results"]
    earned = res["earned"]
    total = res["total"]

    st.markdown("### ✅ Main Quiz Review")

    for q in res["questions"]:
        st.markdown(f"**{q['qid']}**. {q['question']}")
        if q["image"]:
            st.image(q["image"], use_container_width=True)

        for opt in q["options"]:
            if opt == q["correct"]:
                st.markdown(
                    f"<div style='background-color: rgba(0,255,0,0.2); padding:4px; border-radius:4px;'>{opt} ✅ Correct</div>",
                    unsafe_allow_html=True
                )
            elif opt == q["student"]:
                st.markdown(f"**{opt} (your choice)**")
            else:
                st.write(opt)

        st.write("---")

    st.success(f"Score: {earned}/{total}")

    # ---------- FINAL COMBINED SUMMARY / GRAPH / PDF EXPORT / EMAIL ----------
    from matplotlib.ticker import MaxNLocator

    # --- Data ---
    total_q = len(res["questions"])
    incorrect_q = len(res["wrong_ids"])
    correct_q = total_q - incorrect_q

    # --- Theme-aware colors ---
    base   = st.get_option("theme.base") or "light"
    primary = st.get_option("theme.primaryColor") or "#4CAF50"
    text    = st.get_option("theme.textColor") or ("#31333F" if base == "light" else "#FAFAFA")
    bg      = st.get_option("theme.backgroundColor") or ("#FFFFFF" if base == "light" else "#0E1117")
    sbg     = st.get_option("theme.secondaryBackgroundColor") or ("#F5F5F5" if base == "light" else "#262730")
    error   = "#E53935" if base == "light" else "#FF6B6B"

    # --- Figure ---
    fig, ax = plt.subplots(figsize=(6, 3.6), constrained_layout=True)
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(sbg)

    labels = ["Correct", "Incorrect"]
    values = [correct_q, incorrect_q]
    bars = ax.bar(labels, values, color=[primary, error], edgecolor=text, linewidth=0.6)

    # --- Y-axis scaling ---
    ymax = max(values + [1])
    ax.set_ylim(0, ymax + 1)
    ax.yaxis.set_major_locator(MaxNLocator(nbins=6, integer=True))
    ax.grid(axis="y", linestyle="--", linewidth=0.7, alpha=0.3)

    # --- Labels & Title ---
    ax.set_title("Main Performance", color=text, fontsize=14, weight="bold", pad=10)
    ax.set_ylabel("Number of Questions", color=text, fontsize=11)

    ax.tick_params(axis="x", colors=text, labelsize=11)
    ax.tick_params(axis="y", colors=text, labelsize=10)

    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color(text)
        ax.spines[spine].set_alpha(0.25)

    # --- Value labels ---
    for r in bars:
        h = r.get_height()
        ax.annotate(
            f"{int(h)}",
            xy=(r.get_x() + r.get_width() / 2, h),
            xytext=(0, 5),
            textcoords="offset points",
            ha="center",
            va="bottom",
            color=text,
            fontsize=11,
            weight="bold"
        )

    st.pyplot(fig)

    # --- Build PDF function ---
    def build_pdf_bytes(subject, subtopic_id, res, fig, ss):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # Override default Normal style with Unicode font
        normal_style = ParagraphStyle("NormalUnicode", parent=styles["Normal"], fontName="DejaVuSans", fontSize=10)

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
        elements.append(Image(imgbuf, width=400, height=200))
        elements.append(Spacer(1, 20))

        # Table data
        table_data = [
            [
                Paragraph("Q.No", normal_style),
                Paragraph("Question", normal_style),
                Paragraph("Your Answer", normal_style),
                Paragraph("Correct Answer", normal_style),
            ]
        ]
        for q in res["questions"]:
            table_data.append([
                Paragraph(q["qid"], normal_style),
                Paragraph(q["question"], normal_style),
                Paragraph(q["student"], normal_style),
                Paragraph(q["correct"], normal_style)
            ])
            
        table = Table(table_data, colWidths=[50, 220, 120, 120])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('TEXTCOLOR',(0,0),(-1,0),colors.black),
            ('ALIGN',(0,0),(-1,-1),'LEFT'),
            ('FONTNAME', (0,0), (-1,-1), 'DejaVuSans'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ]))
        elements.append(table)

        # Build document
        elements.append(table)
        doc.build(elements)
        buffer.seek(0)
        return buffer.read()

    # --- Download button ---
    pdf_bytes = build_pdf_bytes(subject, subtopic_id, res, fig, ss)
    st.download_button(
        "📄 Download PDF Report",
        data=pdf_bytes,
        file_name=f"report_{ss['student_info'].get('Student_ID','')}_{subtopic_id}.pdf",
        mime="application/pdf",
        key=f"download_main_{subject}_{subtopic_id}"
    )

    # --- Email button ---
    if st.button("📧 Send Copy to My Email", key=f"email_main_{subject}_{subtopic_id}"):
        student_email = ss.get("student_info", {}).get("StudentEmail", "")
        if not student_email:
            st.error("No student email found in register.")
        else:
            send_report_to_student(student_email, pdf_bytes)
            st.success("📧 Report sent to your email.")
# ---------- REMEDIAL (shows below main, main stays visible) ----------
if ss.get("main_submitted", False) and ss.get("main_results", {}).get("wrong_ids"):
    # Countdown before remedial
    if "remedial_ready" not in ss:
        placeholder = st.empty()
        for i in range(20, 0, -1):
            placeholder.info(f"Please review your incorrect answers above. Remedial will load in {i} seconds...")
            time.sleep(1)
        placeholder.empty()
        ss["remedial_ready"] = True

if ss.get("remedial_ready", False):
    st.header("Remedial Quiz")

    wrong_ids = ss["main_results"].get("wrong_ids", [])
    if "MainQuestionID" not in remedial_df.columns:
        st.info("Remedial sheet missing 'MainQuestionID' column.")
    else:
        rem_set = remedial_df[
            remedial_df["MainQuestionID"].astype(str).str.strip().isin(wrong_ids)
        ].copy()

        if rem_set.empty:
            st.info("No remedial questions found for these misses.")
        else:
            ss.setdefault("remedial_answers", {})
            ss.setdefault("remedial_submitted", False)

            if not ss["remedial_submitted"]:
                # ---------- INPUT MODE ----------
                with st.form("remedial_form"):
                    for j, r in enumerate(rem_set.itertuples(index=False), start=1):
                        rqid  = str(getattr(r, "RemedialQuestionID", "")).strip()
                        rtext = str(getattr(r, "QuestionText", "")).strip()
                        rimg  = normalize_img_url(getattr(r, "ImageURL", ""))
                        rhint = str(getattr(r, "Hint", "")).strip()

                        opts = [
                            str(getattr(r, "Option_A", "") or "").strip(),
                            str(getattr(r, "Option_B", "") or "").strip(),
                            str(getattr(r, "Option_C", "") or "").strip(),
                            str(getattr(r, "Option_D", "") or "").strip()
                        ]
                        opts = [o for o in opts if o]
                        disp_opts = stable_shuffle(opts, seed_base + f"::ROPT::{rqid}")

                        st.markdown(f"**{rqid}**<br>{rtext}", unsafe_allow_html=True)
                        if rimg:
                            st.image(rimg, use_container_width=True)
                        if rhint:
                            with st.expander("💡 Hint"):
                                st.write(rhint)

                        prev = ss["remedial_answers"].get(rqid, None)
                        sel = st.radio(
                            "Select your answer:",
                            options=disp_opts,
                            key=f"rem_{rqid}",
                            index=disp_opts.index(prev) if prev in disp_opts else None
                        )
                        ss["remedial_answers"][rqid] = sel
                        st.markdown("---")

                    submit_remedial = st.form_submit_button("Submit Remedial")

                if submit_remedial:
                    if not _all_remedial_answered(rem_set):
                        st.error("⚠ Please answer all remedial questions before submitting.")
                    else:
                        # ---------- GRADE ----------
                        rem_total, rem_earned = 0, 0
                        for _, r in rem_set.iterrows():
                            rqid    = str(r.get("RemedialQuestionID", "")).strip()
                            correct = get_correct_value(r)
                            given   = str(ss["remedial_answers"].get(rqid, "")).strip()
                            marks   = int(r.get("Marks") or 1)
                            awarded = marks if (given and given == correct) else 0
                            rem_total  += marks
                            rem_earned += awarded

                            # Save to Responses sheet
                            append_response_row(
                                datetime.now().isoformat(),
                                ss["student_info"].get("Student_ID", ""),
                                ss["student_info"].get("StudentName", ""),
                                ss["student_info"].get("Tuition_Code", ""),
                                subject, subtopic_id, rqid, given, correct, awarded, "Remedial"
                            )

                        ss["remedial_results"] = {"total": rem_total, "earned": rem_earned}
                        st.markdown("### Remedial Quiz Review")
                        st.success(f"Your Remedial Score: {rem_earned} / {rem_total}")
                        ss["remedial_submitted"] = True
                        st.balloons()
                        st.rerun()

            else:
                # ---------- REVIEW MODE ----------
                res = ss["remedial_results"]
                st.markdown("### Remedial Quiz Review")
                st.success(f"Score: {res['earned']}/{res['total']}")

                for _, r in rem_set.iterrows():
                    rqid    = str(r.get("RemedialQuestionID", "")).strip()
                    rtext   = str(r.get("QuestionText", "")).strip()
                    rimg    = normalize_img_url(r.get("ImageURL", ""))
                    correct = get_correct_value(r)

                    opts = [
                        str(r.get("Option_A", "") or "").strip(),
                        str(r.get("Option_B", "") or "").strip(),
                        str(r.get("Option_C", "") or "").strip(),
                        str(r.get("Option_D", "") or "").strip()
                    ]
                    opts = [o for o in opts if o]
                    disp_opts = stable_shuffle(opts, seed_base + f"::ROPT::{rqid}")

                    st.markdown(f"**{rqid}.** {rtext}")
                    if rimg:
                        st.image(rimg, use_container_width=True)

                    for opt in disp_opts:
                        style = "background-color: rgba(0,255,0,0.2); border-radius: 5px;" if opt == correct else ""
                        st.markdown(f"<div style='{style}; padding:4px;'>{opt}</div>", unsafe_allow_html=True)

                st.markdown("---")

                # --- Pie Chart after Review ---
                correct_q = res["earned"]
                incorrect_q = res["total"] - res["earned"]

                labels = ["Correct", "Incorrect"]
                values = [correct_q, incorrect_q]

                # --- Theme-aware colors (reuse from main) ---
                base    = st.get_option("theme.base") or "light"
                primary = st.get_option("theme.primaryColor") or "#4CAF50"
                text    = st.get_option("theme.textColor") or ("#31333F" if base == "light" else "#FAFAFA")
                bg      = st.get_option("theme.backgroundColor") or ("#FFFFFF" if base == "light" else "#0E1117")
                sbg     = st.get_option("theme.secondaryBackgroundColor") or ("#F5F5F5" if base == "light" else "#262730")
                error   = "#E53935" if base == "light" else "#FF6B6B"

                # --- Figure ---
                fig, ax = plt.subplots(figsize=(4,4))
                fig.patch.set_facecolor(bg)
                ax.set_facecolor(sbg)

                wedges, texts, autotexts = ax.pie(
                    values, labels=labels, autopct='%1.0f%%',
                    colors=[primary, error], startangle=90,
                    wedgeprops={"linewidth":1, "edgecolor":bg},
                    textprops={"color": text, "fontsize":11}
                )

                ax.set_title("Remedial Performance", color=text, fontsize=14, weight="bold", pad=10)

                for autotext in autotexts:
                    autotext.set_color("white")
                    autotext.set_weight("bold")

                st.pyplot(fig)




