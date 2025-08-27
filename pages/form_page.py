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
import threading
import requests
import base64
import random
import hashlib

# DB helpers
from db import save_bulk_responses
from db import mark_and_check_teacher_notified

# PDF / email libs unchanged
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
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

import smtplib
from email.message import EmailMessage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

st.set_page_config(page_title="Quiz Form", layout="centered")
ss = st.session_state

# ---------- Session state defaults ----------
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
if "remedial_page" not in ss:
    ss["remedial_page"] = 0

# ---------- Helpers: caching, image fetch, background worker ----------
@st.cache_data(ttl=600)
def load_sheet_df(sheet_url, worksheet_name):
    """Cached load of a worksheet by name for 10 minutes."""
    book = client.open_by_url(sheet_url)
    # defensive: find worksheet case-insensitively
    for w in book.worksheets():
        if w.title.strip().lower() == worksheet_name.strip().lower():
            return pd.DataFrame(w.get_all_records())
    # fallback
    ws = book.worksheet(worksheet_name)
    return pd.DataFrame(ws.get_all_records())

@st.cache_data(ttl=3600)
def fetch_image_bytes(url):
    """Download image and cache bytes. Returns None on failure."""
    if not url:
        return None
    try:
        r = requests.get(url, timeout=6)
        if r.status_code == 200:
            return r.content
    except Exception:
        return None
    return None

def run_in_background(fn, *args, **kwargs):
    """Fire-and-forget: run fn in separate thread to avoid blocking UI."""
    try:
        t = threading.Thread(target=fn, args=args, kwargs=kwargs, daemon=True)
        t.start()
    except Exception:
        # If threading not allowed, call synchronously (best-effort fallback)
        try:
            fn(*args, **kwargs)
        except Exception:
            pass

# ---------- PDF builder (single canonical function) ----------
def build_pdf_bytes(subject, subtopic_id, res, fig, ss_snapshot):
    """Single PDF builder used for both download and emails.
       Keeps fig small (reduced DPI) to speed serialization."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    normal = ParagraphStyle("NormalUnicode", parent=styles["Normal"], fontName="Helvetica", fontSize=10)

    info = ss_snapshot.get("student_info", {})
    elements.append(Paragraph(f"Quiz Report: {subject} — {subtopic_id}", styles["Title"]))
    elements.append(Paragraph(f"Student: {info.get('StudentName','Unknown')} ({info.get('Student_ID','')})", styles["Normal"]))
    elements.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    if fig:
        # save fig with smaller dpi to reduce size/cost
        chart_buf = io.BytesIO()
        fig.savefig(chart_buf, format="PNG", bbox_inches="tight", dpi=80)
        chart_buf.seek(0)
        elements.append(Image(chart_buf, width=360, height=180))
        elements.append(Spacer(1, 16))

    table_data = [[
        Paragraph("Q.No", normal),
        Paragraph("Question", normal),
        Paragraph("Your Answer", normal),
        Paragraph("Correct Answer", normal),
    ]]
    for q in res.get("questions", []):
        table_data.append([
            Paragraph(str(q.get("qid","")), normal),
            Paragraph(str(q.get("question","")), normal),
            Paragraph(str(q.get("student","")), normal),
            Paragraph(str(q.get("correct","")), normal),
        ])
    table = Table(table_data, repeatRows=1, colWidths=[50, 220, 120, 120])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    elements.append(table)

    earned = res.get("earned", 0); total = res.get("total", 0)
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Score: {earned}/{total}", styles["Heading2"]))

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()

# ---------- Email helpers (unchanged semantics) ----------
def send_report_to_student(to_email, pdf_bytes):
    msg = EmailMessage()
    msg["Subject"] = "Your Quiz Report"
    msg["From"] = "noreply@myschool.com"
    msg["To"] = to_email
    msg.set_content("Attached is your quiz performance report.")
    msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename="quiz_report.pdf")
    smtp_cfg = st.secrets.get("smtp", {})
    try:
        with smtplib.SMTP(smtp_cfg.get("server"), int(smtp_cfg.get("port"))) as server:
            server.starttls()
            server.login(smtp_cfg.get("username"), smtp_cfg.get("password"))
            server.send_message(msg)
    except Exception as e:
        # swallow here; caller will show friendly message
        raise

def send_report_to_parent(parent_email, pdf_bytes, student_name):
    from_email = st.secrets["smtp"]["from_email"]
    password = st.secrets["smtp"]["password"]
    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = parent_email
    msg["Subject"] = f"Quiz Report for {student_name}"
    msg.attach(MIMEText("Please find attached the quiz report.", "plain"))
    part = MIMEApplication(pdf_bytes, Name="report.pdf")
    part["Content-Disposition"] = 'attachment; filename="report.pdf"'
    msg.attach(part)
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(from_email, password)
        server.sendmail(from_email, parent_email, msg.as_string())
        server.quit()
    except Exception as e:
        raise

def send_email_simple(to, subject, body):
    smtp_cfg = st.secrets.get("smtp", {})
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_cfg.get("from_email")
    msg["To"] = to
    msg.set_content(body)
    try:
        with smtplib.SMTP(smtp_cfg.get("server"), smtp_cfg.get("port")) as server:
            server.starttls()
            server.login(smtp_cfg.get("username"), smtp_cfg.get("password"))
            server.send_message(msg)
    except Exception:
        raise

# ---------- small utilities (kept) ----------
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
    if not v: return ""
    if "drive.google.com" in v and "id=" not in v:
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
    return str(row.get("CorrectAnswer","")).strip()

def safe_str(v):
    return str(v) if v is not None else ""

def all_answered_main(q_rows):
    for row in q_rows:
        qid = str(row.QuestionID).strip()
        ans = ss["main_user_answers"].get(qid)
        if not ans:
            return False
    return True

# ---------- PARAMS & BANK (unchanged) ----------
param = get_params()
subject = param("subject", "").strip()
subtopic_id = param("subtopic_id", "").strip()
bank = param("bank", subject).strip().lower()

bank_map = {
    "mathematics": ("ssc_maths_geometry", "ssc_maths_geometry_r"),
    "maths": ("ssc_maths_geometry", "ssc_maths_geometry_r"),
    "geometry": ("ssc_maths_geometry", "ssc_maths_geometry_r"),
    "algebra": ("ssc_maths_algebra", "ssc_maths_algebra_r"),
    "ssc_maths_geometry": ("ssc_maths_geometry", "ssc_maths_geometry_r"),
    "ssc_maths_algebra": ("ssc_maths_algebra", "ssc_maths_algebra_r"),
    "science": ("ssc_science_part_1", "ssc_science_part_1_r"),
    "science1": ("ssc_science_part_1", "ssc_science_part_1_r"),
    "science_1": ("ssc_science_part_1", "ssc_science_part_1_r"),
    "science2": ("ssc_science_part_2", "ssc_science_part_2_r"),
    "science_2": ("ssc_science_part_2", "ssc_science_part_2_r"),
    "ssc_science_part_1": ("ssc_science_part_1", "ssc_science_part_1_r"),
    "ssc_science_part_2": ("ssc_science_part_2", "ssc_science_part_2_r"),
    "english": ("ssc_english", "ssc_english_r"),
    "ssc_english": ("ssc_english", "ssc_english_r"),
}

if not subject or not subtopic_id:
    st.error("❌ Missing `subject` or `subtopic_id` in URL.")
    st.stop()

if bank.lower() in bank_map:
    qsheet_key, rsheet_key = bank_map[bank.lower()]
else:
    st.error(f"❌ Unknown subject '{bank}'")
    st.stop()

try:
    qsheet_url = st.secrets["google"]["question_sheet_urls"][qsheet_key]
    rsheet_url = st.secrets["google"]["response_sheet_urls"][rsheet_key]
except KeyError as e:
    st.error(f"❌ Missing sheet key in secrets.toml: {e}")
    st.stop()

# ---------- Google auth & client ----------
scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
try:
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
except Exception:
    st.error("Missing/invalid `gcp_service_account` in secrets.")
    st.stop()
client = gspread.authorize(creds)

# ---------- register sheet (unchanged) ----------
try:
    reg_book = client.open_by_url(st.secrets["google"]["register_sheet_url"])
    reg_ws = reg_book.worksheets()[0]
    register_df = pd.DataFrame(reg_ws.get_all_records())
except Exception:
    st.error("Unable to load Register sheet. Check URL and sharing with service account.")
    st.stop()

# ---------- UI: Verification (unchanged) ----------
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
                "TeacherTelegramID": student_row.get("Teacher_Teleacher_ID", ""),
                "Tuition_Code": tuition_code.strip(),
                "Student_ID": student_id.strip(),
                "Password": student_password.strip(),  
            }
        else:
            st.error("❌ Invalid Tuition Code or Student ID. Please try again.")

if not ss.get("student_verified", False):
    st.stop()

# ---------- ANTI-CHEAT (same) ----------
ANTI_CHEAT_JS = """ ... (unchanged from original) ... """
st.markdown(ANTI_CHEAT_JS, unsafe_allow_html=True)

# ---------- LOAD MAIN QUESTIONS (lazy remedial load: only main now) ----------
try:
    q_book = client.open_by_url(qsheet_url)
    main_ws = None
    for w in q_book.worksheets():
        if w.title.strip().lower() == "main":
            main_ws = w
            break
    if main_ws is None:
        main_ws = q_book.worksheet("Main")
    # load only main now (remedial will be loaded later on-demand)
    main_df = pd.DataFrame(main_ws.get_all_records())
except Exception as e:
    st.error("Unable to load Main worksheet. Check names & sharing.")
    st.stop()

main_df.columns = main_df.columns.str.strip()
main_df["SubtopicID"] = main_df["SubtopicID"].astype(str).str.strip()
main_questions = main_df[main_df["SubtopicID"] == subtopic_id].copy()
if main_questions.empty:
    st.warning("No questions found for the subtopic.")
    st.stop()

# ---------- Responses sheet (unchanged) ----------
try:
    resp_book = client.open_by_url(rsheet_url)
    responses_ws = resp_book.worksheets()[0]
except Exception:
    st.error("Unable to open Responses sheet. Check URL & sharing.")
    st.stop()

def append_response_row(timestamp, student_id_v, student_name, tuition_code_v,
                        chapter_v, subtopic_v, qnum, given, correct, awarded, attempt_type):
    """Append to Google sheet in background for best-effort."""
    def _append():
        try:
            responses_ws.append_row([timestamp, student_id_v, student_name, tuition_code_v,
                                     chapter_v, subtopic_v, qnum, given, correct, awarded, attempt_type])
        except Exception:
            pass
    # fire-and-forget so UI is not blocked
    run_in_background(_append)

# ---------- HEADER & seeds ----------
st.title(f"📄 {subject.title()} — {subtopic_id.replace('_',' ')}")
info = ss.get("student_info", {})
seed_base = f"{info.get('Student_ID','anon')}::{subtopic_id}"

# ---------- MAIN QUIZ UI (mostly unchanged, with image caching) ----------
st.header("Main Quiz (Attempt 1)")
q_rows = list(main_questions.itertuples(index=False))

ss.setdefault("main_user_answers", {})
ss.setdefault("main_submitted", False)
ss.setdefault("main_results", {})

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
                img_bytes = fetch_image_bytes(img)
                if img_bytes:
                    st.image(img_bytes, use_container_width=True)
                else:
                    # fallback: show URL (non-blocking)
                    st.markdown(f"_Image could not be loaded — {img}_")

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
        if not all_answered_main(q_rows):
            st.error("Please answer all questions before submitting (all are compulsory).")
        else:
            total_marks = 0
            earned_marks = 0
            wrong_ids = []
            question_results = []
            bulk_rows = []

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

                bulk_rows.append((
                    ss["student_info"].get("StudentName", ""),
                    ss["student_info"].get("StudentEmail", ""),
                    ss["student_info"].get("Tuition_Code", ""),
                    subject,
                    subtopic_id,
                    qid,
                    given,
                    correct
                ))

            if bulk_rows:
                # Save to DB in background (so UI isn't blocked by DB)
                run_in_background(save_bulk_responses, bulk_rows)

            ss["main_results"] = {
                "total": total_marks,
                "earned": earned_marks,
                "wrong_ids": wrong_ids,
                "questions": question_results
            }
            ss["main_submitted"] = True
            # mark remedial ready immediately (no st.rerun())
            ss["remedial_ready"] = True
            ss["remedial_pending"] = False
            # Immediately rerun so the UI replaces the main form with review (prevents stacked display)
            st.rerun()              #nagaraj note this on line 519

# --- Remove immediate parent email send here (we'll send after the chart/pdf is ready) ---

# ------------------ AFTER SUBMIT (REVIEW MODE) ------------------
if ss.get("main_submitted", False):
    res = ss.get("main_results", {})
    earned = res.get("earned", 0)
    total = res.get("total", 0)

    st.markdown("### Main Quiz Review")
    st.success(f"Score: {earned}/{total}")

    for q in res.get("questions", []):
        qid   = str(q.get("qid", "")).strip()
        qtext = str(q.get("question", "")).strip()
        qimg  = q.get("image", "")
        correct = q.get("correct", "")
        opts = q.get("options", [])

        disp_opts = stable_shuffle(opts, f"MAIN::{qid}")

        st.markdown(f"**{qid}**<br>{qtext}", unsafe_allow_html=True)
        if qimg:
            img_bytes = fetch_image_bytes(qimg)
            if img_bytes:
                st.image(img_bytes, use_container_width=True)
            else:
                st.markdown("_Image could not be loaded_")

        student_ans = q.get("student", "")

        for opt in disp_opts:
            if opt == student_ans:
                if opt == correct:
                    st.markdown(
                        f"<div style='background-color: rgba(0,255,0,0.15); padding:4px; border-radius:5px; display:flex; justify-content:space-between;'><span>{opt}</span><span>✅ Correct</span></div>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"<div style='background-color: rgba(255,0,0,0.15); padding:4px; border-radius:5px; display:flex; justify-content:space-between;'><span>{opt}</span><span>❌ Incorrect</span></div>",
                        unsafe_allow_html=True
                    )
            elif opt == correct:
                st.markdown(f"<div style='display:flex; justify-content:space-between;'><span>{opt}</span><span>✅ Correct</span></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div>{opt}</div>", unsafe_allow_html=True)

        st.markdown("---")

    st.success(f"Final Score: {earned}/{total}")

    # --- Summary / Graph (reuse and keep lightweight) ---
    questions = res.get("questions", [])
    wrong_ids = res.get("wrong_ids", [])
    total_q = len(questions)
    incorrect_q = len(wrong_ids)
    correct_q = total_q - incorrect_q if total_q > 0 else 0

    base   = st.get_option("theme.base") or "light"
    primary = st.get_option("theme.primaryColor") or "#4CAF50"
    text    = st.get_option("theme.textColor") or ("#31333F" if base == "light" else "#FAFAFA")
    bg      = st.get_option("theme.backgroundColor") or ("#FFFFFF" if base == "light" else "#0E1117")
    sbg     = st.get_option("theme.secondaryBackgroundColor") or ("#F5F5F5" if base == "light" else "#262730")
    error   = "#E53935" if base == "light" else "#FF6B6B"

    fig, ax = plt.subplots(figsize=(5.5, 3.2), constrained_layout=True)
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(sbg)

    labels = ["Correct", "Incorrect"]
    values = [correct_q, incorrect_q]
    bars = ax.bar(labels, values, edgecolor=text, linewidth=0.6)

    # tint bars with theme colors
    bars[0].set_color(primary)
    bars[1].set_color(error)

    ymax = max(values + [1])
    ax.set_ylim(0, ymax + 1)
    ax.yaxis.set_major_locator(MaxNLocator(nbins=6, integer=True))
    ax.grid(axis="y", linestyle="--", linewidth=0.7, alpha=0.3)

    ax.set_title("Main Performance", color=text, fontsize=14, weight="bold", pad=10)
    ax.set_ylabel("Number of Questions", color=text, fontsize=11)
    ax.tick_params(axis="x", colors=text, labelsize=11)
    ax.tick_params(axis="y", colors=text, labelsize=10)

    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color(text)
        ax.spines[spine].set_alpha(0.25)

    for r in bars:
        h = r.get_height()
        ax.annotate(f"{int(h)}", xy=(r.get_x() + r.get_width() / 2, h), xytext=(0, 5),
                    textcoords="offset points", ha="center", va="bottom",
                    color=text, fontsize=11, weight="bold")

    st.pyplot(fig)
        # Streamlit returns True only on click; this block is rarely triggered in some versions,
    
    # Provide explicit download and email builders (build on demand)
    if st.button("Build & Download PDF Report"):
        # build pdf (blocking but user triggered)
        pdf_bytes = build_pdf_bytes(subject, subtopic_id, res, fig, ss)
        st.download_button(
            "Download ready PDF",
            data=pdf_bytes,
            file_name=f"report_{ss['student_info'].get('Student_ID','')}_{subtopic_id}.pdf",
            mime="application/pdf",
            key=f"download_main_{subject}_{subtopic_id}_ready"
        )
        # also send to parent using background thread so UI doesn't freeze
        parent_email = ss["student_info"].get("ParentEmail", "")
        student_name = ss["student_info"].get("StudentName", "Student")
        if parent_email:
            try:
                run_in_background(send_report_to_parent, parent_email, pdf_bytes, student_name)
                st.success(f"Parent report queued to send to {parent_email}")
            except Exception as e:
                st.warning(f"Could not queue parent email: {e}")
                                
    # Student email (explicit)
    if st.button("📧 Send Copy to My Email", key=f"email_main_{subject}_{subtopic_id}"):
        student_email = ss.get("student_info", {}).get("StudentEmail", "")
        if not student_email:
            st.error("No student email found in register.")
        else:
            # build pdf and send in background
            pdf_bytes = build_pdf_bytes(subject, subtopic_id, res, fig, ss)
            try:
                run_in_background(send_report_to_student, student_email, pdf_bytes)
                st.success("📧 Report queued to be sent to your email.")
            except Exception as e:
                st.error(f"Could not queue sending email: {e}")

# ------------------ REMEDIAL (lazy, cached, paginated) ------------------
# Only render remedial UI once remedial_ready is True
if ss.get("remedial_ready", False):
    st.header("Remedial Quiz")

    # Load remedial DF on demand (cached)
    with st.spinner("Loading remedial questions..."):
        try:
            remedial_df = load_sheet_df(qsheet_url, "Remedial")
            remedial_df.columns = remedial_df.columns.str.strip()
        except Exception:
            st.error("Remedial sheet could not be loaded. Check the sheet name & sharing.")
            remedial_df = pd.DataFrame()

    wrong_ids = ss["main_results"].get("wrong_ids", [])
    if remedial_df.empty:
        st.info("No remedial questions available.")
    elif "MainQuestionID" not in remedial_df.columns:
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

            # --- Pagination config (adjust per_page to taste) ---
            per_page = 5
            total_questions = len(rem_set)
            total_pages = (total_questions + per_page - 1) // per_page
            page = ss.get("remedial_page", 0)
            page = max(0, min(page, max(0, total_pages - 1)))
            start = page * per_page
            end = start + per_page
            page_slice = rem_set.iloc[start:end]

            st.write(f"Showing remedial questions {start + 1}–{min(end, total_questions)} of {total_questions}")

            if not ss["remedial_submitted"]:
                with st.form("remedial_form"):
                    # iterate with iterrows so we can derive a stable id from the dataframe index
                    for offset, (idx_row, r) in enumerate(page_slice.iterrows(), start=1):
                        # stable remedial question id:
                        # prefer RemedialQuestionID, else MainQuestionID, else generate R<seq>
                        rqid = str(r.get("RemedialQuestionID", "") or "").strip()
                        if not rqid:
                            rqid = str(r.get("MainQuestionID", "") or "").strip()
                        if not rqid:
                            rqid = f"R{start + offset}"
                               
                        rtext = str(r.get("QuestionText", "")).strip()
                        rimg  = normalize_img_url(r.get("ImageURL", ""))
                        rhint = str(r.get("Hint", "")).strip()
                                 
                        opts = [
                            str(r.get("Option_A", "") or "").strip(),
                            str(r.get("Option_B", "") or "").strip(),
                            str(r.get("Option_C", "") or "").strip(),
                            str(r.get("Option_D", "") or "").strip()
                        ]
                        opts = [o for o in opts if o]
                        disp_opts = stable_shuffle(opts, seed_base + f"::ROPT::{rqid}")
                                
                        st.markdown(f"**{rqid}**<br>{rtext}", unsafe_allow_html=True)
                        if rimg:
                            img_bytes = fetch_image_bytes(rimg)
                            if img_bytes:
                                st.image(img_bytes, use_container_width=True)
                            else:
                                st.markdown("_Image could not be loaded_")
                                         
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

                # pagination controls for non-submitted
            if total_pages > 1 and not ss.get("remedial_submitted", False):
                c1, c2, c3 = st.columns([1, 1, 1])
                if c1.button("◀ Prev", disabled=page <= 0):
                    ss["remedial_page"] = max(0, page - 1)
                    st.experimental_rerun()
                # center cell left intentionally blank to keep layout balanced
                if c3.button("Next ▶", disabled=page >= total_pages - 1):
                    ss["remedial_page"] = min(total_pages - 1, page + 1)
                    st.experimental_rerun()

                if submit_remedial:
                    # NOTE: only grade the full rem_set (not just page slice)
                    missing_any = False
                    for idx_row, r in rem_set.iterrows():
                        # stable id: RemedialQuestionID -> MainQuestionID -> generated R<seq_based_on_df_index>
                        rqid = str(r.get("RemedialQuestionID", "") or "").strip()
                        if not rqid:
                            rqid = str(r.get("MainQuestionID", "") or "").strip()
                        if not rqid:
                            rqid = f"R{idx_row}"  
                            
                        if not ss["remedial_answers"].get(rqid):
                            missing_any = True
                            break
                                  
                if missing_any:
                    st.error("⚠ Please answer all remedial questions before submitting.")
                else:
                    # proceed to grade — use the same rqid logic below when reading answers/awarding marks
                    rem_total, rem_earned = 0, 0
                    for idx_row, r in rem_set.iterrows():
                        rqid = str(r.get("RemedialQuestionID", "") or "").strip()
                        if not rqid:
                            rqid = str(r.get("MainQuestionID", "") or "").strip()
                        if not rqid:
                            rqid = f"R{idx_row}"
                        correct = get_correct_value(r)
                        given   = str(ss["remedial_answers"].get(rqid, "")).strip()
                        marks   = int(r.get("Marks") or 1)
                        awarded = marks if (given and given == correct) else 0
                        rem_total  += marks
                        rem_earned += awarded
                                 
                        # Save each remedial response in background
                        run_in_background(
                            append_response_row,
                            datetime.now().isoformat(),
                            ss["student_info"].get("Student_ID", ""),
                            ss["student_info"].get("StudentName", ""),
                            ss["student_info"].get("Tuition_Code", ""),
                            subject, subtopic_id, rqid, given, correct, awarded, "Remedial"
                        )
                                  
                    ss["remedial_results"] = {"total": rem_total, "earned": rem_earned}
                    ss["remedial_submitted"] = True
                    st.success("Remedial submitted — well done!")
                    st.balloons()
                        # no st.rerun() required; UI below will show review

            else:
                # REVIEW of remedial (after submission)
                res = ss.get("remedial_results", {"total": 0, "earned": 0})
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

                    st.markdown(f"**{rqid}**<br>{rtext}", unsafe_allow_html=True)
                    if rimg:
                        img_bytes = fetch_image_bytes(rimg)
                        if img_bytes:
                            st.image(img_bytes, use_container_width=True)
                        else:
                            st.markdown("_Image could not be loaded_")
                    student_ans = ss["remedial_answers"].get(rqid, "")
                    for opt in disp_opts:
                        if opt == student_ans:
                            if opt == correct:
                                st.markdown(f"<div style='background-color: rgba(0,255,0,0.15); padding:4px; border-radius:5px; display:flex; justify-content:space-between;'><span>{opt}</span><span>✅ Correct</span></div>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"<div style='background-color: rgba(255,0,0,0.15); padding:4px; border-radius:5px; display:flex; justify-content:space-between;'><span>{opt}</span><span>❌ Incorrect</span></div>", unsafe_allow_html=True)
                        elif opt == correct:
                            st.markdown(f"<div style='display:flex; justify-content:space-between;'><span>{opt}</span><span>✅ Correct</span></div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div>{opt}</div>", unsafe_allow_html=True)
                    st.markdown("---")

                # Remedial chart
                correct_q = res["earned"]
                incorrect_q = res["total"] - res["earned"]
                labels = ["Correct", "Incorrect"]
                values = [correct_q, incorrect_q]

                base    = st.get_option("theme.base") or "light"
                primary = st.get_option("theme.primaryColor") or "#4CAF50"
                text    = st.get_option("theme.textColor") or ("#31333F" if base == "light" else "#FAFAFA")
                bg      = st.get_option("theme.backgroundColor") or ("#FFFFFF" if base == "light" else "#0E1117")
                sbg     = st.get_option("theme.secondaryBackgroundColor") or ("#F5F5F5" if base == "light" else "#262730")
                error   = "#E53935" if base == "light" else "#FF6B6B"

                fig, ax = plt.subplots(figsize=(4,4))
                fig.patch.set_facecolor(bg)
                ax.set_facecolor(sbg)
                wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.0f%%', colors=[primary, error], startangle=90, wedgeprops={"linewidth":1, "edgecolor":bg}, textprops={"color": text, "fontsize":11})
                ax.set_title("Remedial Performance", color=text, fontsize=14, weight="bold", pad=10)
                for autotext in autotexts:
                    autotext.set_color("white")
                    autotext.set_weight("bold")
                st.pyplot(fig)
