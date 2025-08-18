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

# ---------- PARAMETERS & BANK ----------
param = get_params()
subject = param("subject", "").strip()
subtopic_id = param("subtopic_id", "").strip()
bank = param("bank", subject).strip()

if not subject or not subtopic_id:
    st.error("Missing `subject` or `subtopic_id` in URL.")
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
    question_sheet_url = st.secrets["google"]["question_sheet_url"]
    response_sheet_url = st.secrets["google"]["response_sheet_url"]
    register_sheet_url = st.secrets["google"]["register_sheet_url"]
except Exception:
    st.error("Please add google.question_sheet_url, google.response_sheet_url, google.register_sheet_url to secrets.toml.")
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
        c1, c2 = st.columns([1,1])
        with c1:
            tuition_code = st.text_input("Tuition Code*", value=ss.get("student_info", {}).get("Tuition_Code", ""))
        with c2:
            student_id = st.text_input("Student ID*", value=ss.get("student_info", {}).get("Student_ID", ""))
        verify_submit = st.form_submit_button("Submit Verification")

    if verify_submit:
        if not tuition_code.strip() or not student_id.strip():
            st.error("⚠ Please fill in both Tuition Code and Student ID.")
        else:
            # lookup in register sheet
            mask = (
                (register_df["Tuition_Code"].astype(str).str.strip() == tuition_code.strip()) &
                (register_df["Student_ID"].astype(str).str.strip() == student_id.strip())
            )

            if mask.any():
                student_row = register_df[mask].iloc[0]
                st.success(f"✅ Verified: {student_row['Student_Name']} ({student_row['Tuition_Name']})")
                ss["student_verified"] = True
                ss["student_info"] = {
                    "StudentName": student_row.get["Student_Name", ""],
                    "Class": student_row.get("Class", ""),
                    "RollNo": student_row.get("Roll_No", ""),
                    "StudentEmail": student_row.get("Student_Email", ""),
                    "ParentEmail": student_row.get("Parent_Email", ""),
                    "Tuition_Code": tuition_code.strip(),
                    "Student_ID": student_id.strip(),
                }
            else:
                st.error("❌ Invalid Tuition Code or Student ID. Please try again.")

if not ss.get("student_verified", False):
    st.stop()


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
seed_base = f"{student_id or 'anon'}::{subtopic_id}"

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

        st.markdown(f"**{qid} — {qtext}**")
        if img:
            st.image(img, use_container_width=True)
        # restore previous selection if exists (index used is last chosen index)
        prev = st.session_state.main_user_answers.get(qid, None)
        sel = st.radio("Select your answer:", options=disp_opts, key=f"main_{qid}", index=0 if prev is None else disp_opts.index(prev))
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
            append_response_row(datetime.now().isoformat(), student_id, student_row.get("Student_Name",""), tuition_code,
                                subject, subtopic_id, qid, given, correct, awarded, "Main")
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
                    st.markdown(f"**{rqid} — {rtext}**")
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
                    append_response_row(datetime.now().isoformat(), student_id, student_row.get("Student_Name",""), tuition_code,
                                        subject, subtopic_id, rqid, given, correct, awarded, "Remedial")
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
    ax.bar(['Correct','Incorrect'], [correct_count, wrong_count])
    ax.set_title("Main Performance")
    st.pyplot(fig)

    # Build PDF bytes (reportlab + embed plt as image)
    def build_pdf_bytes():
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        c.setFont("Helvetica-Bold", 16)
        c.drawString(40, height - 50, f"Quiz Report: {subject} - {subtopic_id}")
        c.setFont("Helvetica", 12)
        c.drawString(40, height - 80, f"Student: {student_row.get('Student_Name','Unknown')} ({student_id})")
        c.drawString(40, height - 100, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        # embed chart
        imgbuf = io.BytesIO()
        fig.savefig(imgbuf, format="PNG", bbox_inches='tight')
        imgbuf.seek(0)
        c.drawImage(ImageReader(imgbuf), 40, height - 350, width=400, preserveAspectRatio=True, mask='auto')
        y = height - 380
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "Main Results:")
        y -= 20
        for _, q in main_questions.iterrows():
            qid = str(q.get("QuestionID","")).strip()
            qtext = str(q.get("QuestionText","")).strip()
            given = st.session_state.main_user_answers.get(qid,"")
            correct = get_correct_value(q)
            c.setFont("Helvetica", 10)
            c.drawString(45, y, f"{qid}: Your: {given}  |  Correct: {correct}")
            y -= 14
            if y < 80:
                c.showPage()
                y = height - 50
        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer.read()

    pdf_bytes = build_pdf_bytes()
    st.download_button("📄 Download PDF Report", data=pdf_bytes, file_name=f"report_{student_id}_{subtopic_id}.pdf", mime="application/pdf")

    # EMAIL option (optional): requires SMTP in secrets
    if st.button("📧 Email Report to Parent & Student"):
        try:
            smtp_cfg = st.secrets.get("smtp", {})
            if not smtp_cfg:
                st.error("SMTP config not found in secrets.toml.")
            else:
                msg = EmailMessage()
                msg["Subject"] = f"Quiz Report: {subject} - {subtopic_id}"
                msg["From"] = smtp_cfg.get("from_email")
                to_addrs = []
                student_email = student_row.get("Student_Email","")
                parent_email = student_row.get("Parent_Email","")
                if student_email: to_addrs.append(student_email)
                if parent_email: to_addrs.append(parent_email)
                if not to_addrs:
                    st.error("No student/parent email found in register.")
                else:
                    msg["To"] = ", ".join(to_addrs)
                    msg.set_content("Please find attached the quiz report.")
                    msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename=f"report_{student_id}.pdf")
                    server = smtplib.SMTP(smtp_cfg.get("server"), int(smtp_cfg.get("port",587)))
                    server.starttls()
                    server.login(smtp_cfg.get("username"), smtp_cfg.get("password"))
                    server.send_message(msg)
                    server.quit()
                    st.success("Email sent successfully!")
        except Exception as e:
            st.error(f"Failed to send email: {e}")
