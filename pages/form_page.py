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
import hashlib
import random
import re

# --------------------- CONFIG ---------------------
st.set_page_config(page_title="Quiz Form", layout="centered")

# Quick toggles
SHUFFLE_QUESTIONS = True
SHUFFLE_OPTIONS = True
REMEDIAL_DELAY_SECONDS = 20  # change delay here

# --------------------- SMALL HELPERS ---------------------
def pick_query_param(name, default=""):
    v = st.experimental_get_query_params().get(name, [default])
    return v[0] if isinstance(v, list) else v

def safe_str(x):
    return "" if x is None else str(x)

def safe_strip(x):
    return safe_str(x).strip()

def stable_shuffle(items, seed_str):
    seq = list(items)
    h = int(hashlib.md5(seed_str.encode("utf-8")).hexdigest(), 16)
    rnd = random.Random(h)
    rnd.shuffle(seq)
    return seq

def normalize_img_url(value: str) -> str:
    """Try to normalize Google Drive share links and plain file ids to a direct view URL; otherwise return stripped input."""
    v = safe_strip(value)
    if not v:
        return ""
    if "drive.google.com" in v:
        # If it's a "uc?export=view&id=" or "uc?export=download&id=" already fine
        if "uc?export=view" in v or "uc?export=download" in v:
            return v
        # try to extract /d/FILE_ID
        m = re.search(r"/d/([a-zA-Z0-9_-]{10,})", v)
        if m:
            return f"https://drive.google.com/uc?export=view&id={m.group(1)}"
        # try id=...
        m2 = re.search(r"id=([a-zA-Z0-9_-]{10,})", v)
        if m2:
            return f"https://drive.google.com/uc?export=view&id={m2.group(1)}"
    # if looks like a file id alone
    if re.fullmatch(r"[a-zA-Z0-9_-]{10,}", v):
        return f"https://drive.google.com/uc?export=view&id={v}"
    return v

def get_correct_value(row):
    # Accept different correct answer column names
    for name in ("CorrectOption", "Correct_Answer", "CorrectAnswer", "Correct"):
        if name in row and safe_strip(row[name]):
            return safe_strip(row[name])
    return ""

# --------------------- UI: hide menu & sidebar (unless unlock_code present) ---------------------
unlock_code = pick_query_param("unlock_code", "")
if not unlock_code:
    hide_style = """
    <style>
      /* hide top-right menu and header */
      header, footer, .css-1d391kg {visibility: hidden;}
      /* hide sidebar */
      .css-1d391kg {display:none !important;}
    </style>
    """
    st.markdown(hide_style, unsafe_allow_html=True)

# Optional anti-cheat (tab switch) - can be enabled/disabled as needed
ANTI_CHEAT_JS = """
<script>
const UNLOCK= new URLSearchParams(window.location.search).get('unlock_code');
if(!UNLOCK){
  document.addEventListener('contextmenu', e=>e.preventDefault());
  document.addEventListener('selectstart', e=>e.preventDefault());
  document.addEventListener('copy', e=>e.preventDefault());
  function lockit(){ window.alert('You left the tab — quiz locked. Contact teacher.'); }
  document.addEventListener('visibilitychange', function(){ if(document.hidden) lockit(); });
  window.addEventListener('blur', lockit);
}
</script>
"""
st.markdown(ANTI_CHEAT_JS, unsafe_allow_html=True)

# --------------------- Get params ---------------------
subject = pick_query_param("subject", "").strip()
subtopic_id = pick_query_param("subtopic_id", "").strip()

if not subject or not subtopic_id:
    st.error("Missing required URL params: ?subject=...&subtopic_id=...")
    st.stop()

# --------------------- Google Sheets auth & sheet URLs in secrets ---------------------
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
try:
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
except Exception as e:
    st.error("Missing or invalid gcp_service_account in secrets. Please add service account JSON to secrets.")
    st.stop()
client = gspread.authorize(creds)

try:
    question_sheet_url = st.secrets["google"]["question_sheet_url"]
    response_sheet_url = st.secrets["google"]["response_sheet_url"]
    register_sheet_url = st.secrets["google"]["register_sheet_url"]
except Exception as e:
    st.error("Please add google.question_sheet_url, google.response_sheet_url and google.register_sheet_url to secrets.toml.")
    st.stop()

# --------------------- Load Register (student verification) ---------------------
try:
    reg_book = client.open_by_url(register_sheet_url)
    # pick first worksheet by name fallback
    reg_ws = None
    for candidate in ("Register", "register", "Sheet1"):
        try:
            reg_ws = reg_book.worksheet(candidate)
            break
        except Exception:
            continue
    if reg_ws is None:
        reg_ws = reg_book.worksheets()[0]
    register_df = pd.DataFrame(reg_ws.get_all_records())
    # normalize header names
    register_df.columns = register_df.columns.str.strip()
except Exception as e:
    st.error("Unable to load Register sheet or worksheet. Make sure the URL is correct and service account has access.")
    st.stop()

# --------------------- Student Verification UI ---------------------
st.title("🔐 Student Verification")
col1, col2, col3 = st.columns([2,3,1])
with col1:
    tuition_code_in = st.text_input("Tuition Code", max_chars=30)
with col2:
    student_id_in = st.text_input("Student ID", max_chars=50)
with col3:
    verify_btn = st.button("Submit Verification")

verified = False
student_row = None

if verify_btn:
    if not tuition_code_in or not student_id_in:
        st.error("Please enter both Tuition Code and Student ID then click Submit Verification.")
    else:
        mask = (register_df.get("Tuition_Code", register_df.columns[0]).astype(str).str.strip() == tuition_code_in.strip()) & \
               (register_df.get("Student_ID", register_df.columns[1]).astype(str).str.strip() == student_id_in.strip())
        if mask.any():
            student_row = register_df[mask].iloc[0].to_dict()
            st.success(f"✅ Verified: {student_row.get('Student_Name', 'Unknown')}")
            verified = True
            st.session_state["student_row"] = student_row
            st.session_state["tuition_code"] = tuition_code_in.strip()
            st.session_state["student_id"] = student_id_in.strip()
        else:
            st.error("❌ Invalid code or ID. Please try again.")

# If already verified in session, reuse
if "student_row" in st.session_state:
    student_row = st.session_state["student_row"]
    tuition_code_in = st.session_state.get("tuition_code", tuition_code_in)
    student_id_in = st.session_state.get("student_id", student_id_in)
    verified = True

if not verified:
    st.stop()

# --------------------- Load Questions (Main & Remedial) ---------------------
try:
    qb = client.open_by_url(question_sheet_url)
    def open_by_candidates(book, candidates):
        for c in candidates:
            try:
                return book.worksheet(c)
            except Exception:
                continue
        # fallback first
        return book.worksheets()[0]
    main_ws = open_by_candidates(qb, ["Main", "main"])
    remedial_ws = open_by_candidates(qb, ["Remedial", "remedial"])
    main_df = pd.DataFrame(main_ws.get_all_records())
    remedial_df = pd.DataFrame(remedial_ws.get_all_records())
    main_df.columns = main_df.columns.str.strip()
    remedial_df.columns = remedial_df.columns.str.strip()
except Exception as e:
    st.error("Unable to load Main/Remedial worksheets from questions sheet. Check sharing & names.")
    st.stop()

if "SubtopicID" not in main_df.columns:
    st.error("Main sheet must include 'SubtopicID' column.")
    st.stop()

# Filter main questions
main_df["SubtopicID"] = main_df["SubtopicID"].astype(str).str.strip()
main_questions = main_df[main_df["SubtopicID"] == subtopic_id].copy()
if main_questions.empty:
    st.warning("No main questions found for this subtopic.")
    st.stop()

# --------------------- Responses sheet open ---------------------
try:
    rb = client.open_by_url(response_sheet_url)
    # pick worksheet by name fallback
    out_ws = None
    for c in ("Responses", "responses", "Sheet1"):
        try:
            out_ws = rb.worksheet(c)
            break
        except Exception:
            continue
    if out_ws is None:
        out_ws = rb.worksheets()[0]
except Exception:
    st.error("Unable to open Responses sheet. Check URL & sharing.")
    st.stop()

def append_response_row(timestamp, student_id_v, student_name_v, tuition_code_v,
                        chapter_v, subtopic_v, qnum, given, correct, awarded, attempt_type):
    # Best-effort append
    try:
        out_ws.append_row([timestamp, student_id_v, student_name_v, tuition_code_v,
                           chapter_v, subtopic_v, qnum, given, correct, awarded, attempt_type])
    except Exception:
        pass

# --------------------- UI header ---------------------
st.title(f"📘 {subject.title()} — {subtopic_id.replace('_',' ')}")

# Stable seed for shuffling
seed_base = f"{student_id_in or 'anon'}::{subtopic_id}"

# --------------------- MAIN QUIZ UI ---------------------
st.header("Main Quiz")
q_rows = list(main_questions.itertuples(index=False))

if SHUFFLE_QUESTIONS:
    q_rows = stable_shuffle(q_rows, seed_base + "::Q")

# session states
if "main_user_answers" not in st.session_state:
    st.session_state.main_user_answers = {}
if "main_submitted" not in st.session_state:
    st.session_state.main_submitted = False
if "main_results" not in st.session_state:
    st.session_state.main_results = {}

def all_answered_main():
    for row in q_rows:
        qid = safe_strip(row._asdict().get("QuestionID",""))
        if not st.session_state.main_user_answers.get(qid):
            return False
    return True

with st.form("main_quiz"):
    for row in q_rows:
        rd = row._asdict()
        qid = safe_strip(rd.get("QuestionID",""))
        qtext = safe_strip(rd.get("QuestionText",""))
        img = normalize_img_url(rd.get("ImageURL",""))
        # options
        opts = [safe_strip(rd.get("Option_A","")), safe_strip(rd.get("Option_B","")),
                safe_strip(rd.get("Option_C","")), safe_strip(rd.get("Option_D",""))]
        opts = [o for o in opts if o]
        disp_opts = stable_shuffle(opts, seed_base + f"::OPT::{qid}") if SHUFFLE_OPTIONS else opts
        st.markdown(f"**{qid} — {qtext}**")
        if img:
            st.image(img, use_container_width=True)
        # populate default from session_state if present
        prev = st.session_state.main_user_answers.get(qid, None)
        try:
            index = disp_opts.index(prev) if prev in disp_opts else 0
        except Exception:
            index = 0
        sel = st.radio("Select your answer:", disp_opts, key=f"main_{qid}", index=index)
        st.session_state.main_user_answers[qid] = sel
        st.markdown("---")
    submit_main = st.form_submit_button("Submit Main Quiz")

# Grade main submission
if submit_main:
    if not all_answered_main():
        st.error("All questions are compulsory. Please answer every question before submitting.")
    else:
        total = 0
        earned = 0
        wrong_rows = []
        for _, q in main_questions.iterrows():
            qid = safe_strip(q.get("QuestionID",""))
            correct = get_correct_value(q)
            given = safe_strip(st.session_state.main_user_answers.get(qid,""))
            marks = int(q.get("Marks") or 1)
            total += marks
            awarded = marks if (given != "" and given == correct) else 0
            earned += awarded
            append_response_row(datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                student_id_in, student_row.get("Student_Name",""), tuition_code_in,
                                subject, subtopic_id, qid, given, correct, awarded, "Main")
            if awarded == 0:
                wrong_rows.append(q)
        st.session_state.main_results = {"total": total, "earned": earned, "wrong": wrong_rows}
        st.session_state.main_submitted = True
        st.success(f"🎯 Main Score: {earned}/{total}")

# --------------------- Show main review (always kept visible after submit) ---------------------
if st.session_state.get("main_submitted", False):
    st.markdown("## Main Review (Your attempt)")
    mr = st.session_state.main_results
    st.success(f"Score: {mr['earned']}/{mr['total']}")
    if mr["wrong"]:
        st.error("These were incorrect (your answer vs correct):")
        rows = []
        for q in mr["wrong"]:
            qid = safe_strip(q.get("QuestionID",""))
            qtext = safe_strip(q.get("QuestionText",""))
            given = safe_strip(st.session_state.main_user_answers.get(qid,""))
            correct = get_correct_value(q)
            rows.append({"QuestionID": qid, "Question": qtext, "Your": given, "Correct": correct})
        st.table(pd.DataFrame(rows))
    else:
        st.success("All main answers correct!")

# --------------------- 20s Delay and remedial readiness ---------------------
if st.session_state.get("main_submitted", False) and st.session_state.main_results.get("wrong"):
    if "remedial_ready" not in st.session_state:
        # show countdown and message (non-blocking UI shows but this loop will wait; it's acceptable for short delays)
        placeholder = st.empty()
        for i in range(REMEDIAL_DELAY_SECONDS, 0, -1):
            placeholder.info(f"Please check your incorrect answers above. Remedial will load in {i} seconds...")
            time.sleep(1)
        placeholder.empty()
        st.session_state.remedial_ready = True

# --------------------- Remedial (below main) ---------------------
if st.session_state.get("remedial_ready", False):
    st.header("Remedial Quiz")
    wrong_qs = st.session_state.main_results.get("wrong", [])
    # map main question IDs to remedial items
    if "MainQuestionID" not in remedial_df.columns:
        st.info("Remedial sheet needs 'MainQuestionID' column to link remedial items.")
    else:
        wrong_ids = [safe_strip(q.get("QuestionID","")) for q in wrong_qs]
        rem_set = remedial_df[remedial_df["MainQuestionID"].astype(str).str.strip().isin(wrong_ids)].copy()
        if rem_set.empty:
            st.info("No remedial questions found for your incorrect answers.")
        else:
            if "remedial_answers" not in st.session_state:
                st.session_state.remedial_answers = {}
            with st.form("remedial_form"):
                for _, r in rem_set.iterrows():
                    rqid = safe_strip(r.get("RemedialQuestionID",""))
                    rtext = safe_strip(r.get("QuestionText",""))
                    rimg = normalize_img_url(r.get("ImageURL",""))
                    rhint = safe_strip(r.get("Hint",""))  # optional hint column
                    opts = [safe_strip(r.get("Option_A","")), safe_strip(r.get("Option_B","")),
                            safe_strip(r.get("Option_C","")), safe_strip(r.get("Option_D",""))]
                    opts = [o for o in opts if o]
                    disp_opts = stable_shuffle(opts, seed_base + f"::ROPT::{rqid}") if SHUFFLE_OPTIONS else opts
                    st.markdown(f"**{rqid} — {rtext}**")
                    if rimg:
                        st.image(rimg, use_container_width=True)
                    if rhint:
                        with st.expander("💡 Hint"):
                            st.write(rhint)
                    prev = st.session_state.remedial_answers.get(rqid, None)
                    try:
                        index = disp_opts.index(prev) if prev in disp_opts else 0
                    except Exception:
                        index = 0
                    sel = st.radio("Select your answer:", disp_opts, key=f"rem_{rqid}", index=index)
                    st.session_state.remedial_answers[rqid] = sel
                    st.markdown("---")
                submit_remedial = st.form_submit_button("Submit Remedial")
            if submit_remedial:
                rem_total = 0
                rem_earned = 0
                for _, r in rem_set.iterrows():
                    rqid = safe_strip(r.get("RemedialQuestionID",""))
                    correct = get_correct_value(r)
                    given = safe_strip(st.session_state.remedial_answers.get(rqid,""))
                    marks = int(r.get("Marks") or 1)
                    awarded = marks if (given != "" and given == correct) else 0
                    rem_total += marks
                    rem_earned += awarded
                    append_response_row(datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        student_id_in, student_row.get("Student_Name",""), tuition_code_in,
                                        subject, subtopic_id, rqid, given, correct, awarded, "Remedial")
                st.success(f"✅ Remedial submitted: {rem_earned}/{rem_total}")
                st.balloons()
                st.session_state.remedial_done = True

# --------------------- Final combined summary, chart, PDF, Email ---------------------
if st.session_state.get("main_submitted", False):
    st.markdown("## Final Summary & Download")
    main_res = st.session_state.main_results
    st.write(f"Main: {main_res['earned']}/{main_res['total']}")
    if st.session_state.get("remedial_done", False):
        st.write("Remedial: submitted")
    # Chart
    fig, ax = plt.subplots(figsize=(4,2))
    correct_count = main_res['earned']
    wrong_count = main_res['total'] - main_res['earned']
    ax.bar(['Correct','Incorrect'], [correct_count, wrong_count], color=['#2ca02c', '#d62728'])
    ax.set_title("Main Performance")
    st.pyplot(fig)

    # Build PDF report (simple)
    def build_pdf():
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        width, height = A4
        c.setFont("Helvetica-Bold", 16)
        c.drawString(40, height - 50, f"Quiz Report — {subject} / {subtopic_id}")
        c.setFont("Helvetica", 12)
        c.drawString(40, height - 80, f"Student: {student_row.get('Student_Name','Unknown')} ({student_id_in})")
        c.drawString(40, height - 100, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        # embed chart image
        imgbuf = io.BytesIO()
        fig.savefig(imgbuf, format='PNG', bbox_inches='tight')
        imgbuf.seek(0)
        c.drawImage(ImageReader(imgbuf), 40, height - 350, width=400, preserveAspectRatio=True, mask='auto')
        y = height - 380
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "Main Answers:")
        y -= 18
        for _, q in main_questions.iterrows():
            qid = safe_strip(q.get("QuestionID",""))
            qtext = safe_strip(q.get("QuestionText",""))
            given = safe_strip(st.session_state.main_user_answers.get(qid,""))
            correct = get_correct_value(q)
            c.setFont("Helvetica", 10)
            line = f"{qid}: Your: {given}  |  Correct: {correct}"
            c.drawString(45, y, line[:90])
            y -= 12
            if y < 80:
                c.showPage()
                y = height - 50
        c.showPage()
        c.save()
        buf.seek(0)
        return buf.read()

    pdf_bytes = build_pdf()
    st.download_button("📄 Download PDF Report", data=pdf_bytes, file_name=f"report_{student_id_in}_{subtopic_id}.pdf", mime="application/pdf")

    # Email option (requires smtp secrets)
    smtp_cfg = st.secrets.get("smtp", {})
    if smtp_cfg:
        if st.button("📧 Email Report to Student & Parent"):
            try:
                msg = EmailMessage()
                msg["Subject"] = f"Quiz Report: {subject} - {subtopic_id}"
                msg["From"] = smtp_cfg.get("from_email")
                to_addrs = []
                stud_email = student_row.get("Student_Email","")
                parent_email = student_row.get("Parent_Email","")
                if stud_email: to_addrs.append(stud_email)
                if parent_email: to_addrs.append(parent_email)
                if not to_addrs:
                    st.error("No student or parent email found in register.")
                else:
                    msg["To"] = ", ".join(to_addrs)
                    msg.set_content("Please find attached your quiz report.")
                    msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename="report.pdf")
                    server = smtplib.SMTP(smtp_cfg.get("server"), int(smtp_cfg.get("port",587)))
                    server.starttls()
                    server.login(smtp_cfg.get("username"), smtp_cfg.get("password"))
                    server.send_message(msg)
                    server.quit()
                    st.success("Email sent successfully!")
            except Exception as e:
                st.error(f"Failed to send email: {e}")

# --------------------- End ---------------------
