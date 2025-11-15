import streamlit as st
import pandas as pd
import hashlib
import os
from io import StringIO

# ------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------
st.set_page_config(page_title="Teacher Admin — Fill Data", layout="wide")

# ------------------------------------------------------------
# HELPERS (cached) — caching file/df loads for snappy UI
# ------------------------------------------------------------
@st.cache_data
def load_csv_to_df(uploaded_file) -> pd.DataFrame:
    if uploaded_file is None:
        return pd.DataFrame()
    try:
        return pd.read_csv(uploaded_file)
    except Exception:
        # try as excel
        return pd.read_excel(uploaded_file)

# ------------------------------------------------------------
# Password helpers (simple salted SHA-256)
# ------------------------------------------------------------
def hash_password(password: str, salt: str = None) -> str:
    if salt is None:
        salt = os.urandom(8).hex()
    digest = hashlib.sha256((salt + password).encode('utf-8')).hexdigest()
    return f"{salt}${digest}"

def verify_password(stored: str, attempt: str) -> bool:
    try:
        salt, stored_hash = stored.split("$", 1)
    except Exception:
        return False
    attempt_hash = hashlib.sha256((salt + attempt).encode('utf-8')).hexdigest()
    return attempt_hash == stored_hash

# ------------------------------------------------------------
# SESSION STATE INIT
# ------------------------------------------------------------
if "subject_teachers" not in st.session_state:
    st.session_state.subject_teachers = []
if "students" not in st.session_state:
    st.session_state.students = []
if "saved_class" not in st.session_state:
    st.session_state.saved_class = {}
if "head_logged_in" not in st.session_state:
    st.session_state.head_logged_in = False

# ------------------------------------------------------------
# helpers to add entries
# ------------------------------------------------------------
def add_subject_teacher(name, email):
    if name:
        st.session_state.subject_teachers.append({"name": name, "email": email})

def add_student(batch, name, email, password):
    if len([s for s in st.session_state.students if s.get('batch') == batch]) >= 40:
        st.warning("Maximum 40 students reached for this batch in the session.")
        return
    if name:
        st.session_state.students.append({"batch": batch, "name": name, "email": email, "password_hash": hash_password(password)})

# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------
st.title("⚙️ Teacher — Quick Admin Data Entry")
st.markdown("A clean page for teachers to add class/head/subject-teacher and student details. Head teacher can log in to view/export lists and change student passwords.")
st.markdown("---")

# ------------------------------------------------------------
# MAIN LAYOUT
# ------------------------------------------------------------
left, right = st.columns([2, 3])

with left:
    st.subheader("👩‍🏫 Class / Teacher Details")
    with st.form("class_teacher_form", clear_on_submit=False):
        cls_name = st.text_input("Class name (e.g. Grade 10 - A)")
        batch = st.text_input("Batch (identifier)")

        st.markdown("**Head Teacher**")
        head_name = st.text_input("Head Teacher name")
        head_email = st.text_input("Head Teacher email")
        head_password = st.text_input("Head Teacher password", type="password")
        change_head_pw = st.checkbox("Allow Head Teacher to change password on first login", value=True)

        st.markdown("**Subject Teachers**")
        col_a, col_b = st.columns(2)
        with col_a:
            subj_name = st.text_input("Subject Teacher name", key="subj_name_input")
        with col_b:
            subj_email = st.text_input("Subject Teacher email", key="subj_email_input")

        add_subj = st.form_submit_button("➕ Add subject teacher")
        save_class = st.form_submit_button("💾 Save class & teachers to session")

    if add_subj:
        if not subj_name or not subj_email:
            st.error("Please provide both name and email for the subject teacher before adding.")
        else:
            add_subject_teacher(subj_name, subj_email)
            st.success(f"Added subject teacher: {subj_name}")

    if save_class:
        # build saved_class in session
        head_pw_hash = hash_password(head_password) if head_password else ""
        st.session_state.saved_class = {
            "class_name": cls_name,
            "batch": batch,
            "head": {"name": head_name, "email": head_email, "password_hash": head_pw_hash},
            "subject_teachers": st.session_state.subject_teachers.copy(),
            "allow_head_pw_change": change_head_pw,
        }
        st.success("Class & teacher details captured in session. Head teacher can now log in on the right panel.")

    # show current subject teachers list
    if st.session_state.subject_teachers:
        st.markdown("**Current subject teachers (session)**")
        for i, t in enumerate(st.session_state.subject_teachers, start=1):
            st.write(f"{i}. {t['name']} — {t['email']}")

    # option to clear subject teachers
    if st.button("🧹 Clear subject teachers list"):
        st.session_state.subject_teachers = []
        st.success("Subject teacher list cleared from session.")

    # bulk import
    st.markdown("----")
    st.markdown("**Bulk import subject teachers**")
    uploaded = st.file_uploader("Upload CSV (columns: name,email)", type=["csv", "xlsx"] , key="upload_subj")
    if uploaded:
        df = load_csv_to_df(uploaded)
        if not df.empty and set([c.lower() for c in df.columns]).issuperset({"name", "email"}):
            for _, row in df.iterrows():
                add_subject_teacher(row['name'], row['email'])
            st.success(f"Imported {len(df)} subject teacher(s) into session list.")
        else:
            st.error("CSV must have columns named 'name' and 'email'.")

with right:
    st.subheader("👩‍🎓 Students — Batch Entry & Head Teacher Panel")

    # Bulk upload students
    st.markdown("**Bulk import students**")
    uploaded_students = st.file_uploader("Upload students CSV (columns: batch, name, email, password)", type=["csv", "xlsx"], key="upload_students")
    if uploaded_students:
        df_students = load_csv_to_df(uploaded_students)
        if not df_students.empty and set([c.lower() for c in df_students.columns]).issuperset({"batch", "name", "email", "password"}):
            added = 0
            for _, r in df_students.iterrows():
                if len([s for s in st.session_state.students if s.get('batch') == r['batch']]) < 40:
                    add_student(r['batch'], r['name'], r['email'], r['password'])
                    added += 1
            st.success(f"Added {added} student(s) from CSV (session). Total now: {len(st.session_state.students)}")
        else:
            st.error("CSV must have columns: batch, name, email, password")

    st.markdown("**Add student (manual)**")
    with st.form("student_form", clear_on_submit=True):
        s_batch = st.text_input("Batch")
        s_name = st.text_input("Student name")
        s_email = st.text_input("Student email")
        s_password = st.text_input("Student password", type="password")
        add_student_btn = st.form_submit_button("➕ Add student")

    if add_student_btn:
        if not (s_batch and s_name and s_email and s_password):
            st.error("All student fields are required.")
        elif len([s for s in st.session_state.students if s.get('batch') == s_batch]) >= 40:
            st.error("Cannot add more than 40 students for a batch in this session.")
        else:
            add_student(s_batch, s_name, s_email, s_password)
            st.success(f"Added student: {s_name}")

    # display current students
    if st.session_state.students:
        st.markdown(f"**Students in session ({len(st.session_state.students)})**")
        df_show = pd.DataFrame(st.session_state.students)
        st.dataframe(df_show)

    # Head Teacher login panel
    st.markdown("---")
    st.subheader("🔐 Head Teacher — Login to manage batch")
    if not st.session_state.saved_class:
        st.info("No class saved in session. Save class & teachers on the left first.")
    else:
        with st.form("head_login_form"):
            ht_email = st.text_input("Head teacher email", value=st.session_state.saved_class.get('head', {}).get('email', ''))
            ht_password = st.text_input("Head teacher password", type="password")
            login_btn = st.form_submit_button("🔓 Login as head teacher")
        if login_btn:
            stored = st.session_state.saved_class.get('head', {}).get('password_hash', '')
            if stored and verify_password(stored, ht_password) and ht_email == st.session_state.saved_class.get('head', {}).get('email'):
                st.session_state.head_logged_in = True
                st.success("Head teacher logged in — you can now view/download lists and reset student passwords for the class/batch.")
            else:
                st.error("Invalid credentials. Make sure class is saved and credentials match the saved head teacher.")

    # Head-only tools
    if st.session_state.head_logged_in:
        st.markdown("---")
        st.subheader("Head teacher tools — view / export / reset student passwords")

        # select batches to view (collect unique batches)
        batches = sorted(list({s['batch'] for s in st.session_state.students}))
        if not batches:
            st.info("No students added yet. Add students to session to use head tools.")
        else:
            selected_batch = st.selectbox("Select batch to manage:", ["All"] + batches)

            # filter students and teachers by batch
            if selected_batch == "All":
                students_filtered = st.session_state.students
                teachers_filtered = st.session_state.subject_teachers
            else:
                students_filtered = [s for s in st.session_state.students if s['batch'] == selected_batch]
                teachers_filtered = st.session_state.subject_teachers

            # show counts
            st.write(f"Students: {len(students_filtered)} | Subject teachers: {len(teachers_filtered)}")

            # download buttons
            col1, col2 = st.columns(2)
            if students_filtered:
                csv_students = pd.DataFrame(students_filtered).to_csv(index=False)
                col1.download_button(label="📥 Download students (CSV)", data=csv_students, file_name=f"students_{selected_batch}.csv", mime="text/csv")
            else:
                col1.info("No students to download for selected batch.")

            if teachers_filtered:
                csv_teachers = pd.DataFrame(teachers_filtered).to_csv(index=False)
                col2.download_button(label="📥 Download teachers (CSV)", data=csv_teachers, file_name=f"teachers_{selected_batch}.csv", mime="text/csv")
            else:
                col2.info("No teachers to download for selected batch.")

            st.markdown("---")
            st.subheader("Reset a student's password")
            if students_filtered:
                student_names = [f"{s['name']} <{s['email']}>" for s in students_filtered]
                sel = st.selectbox("Choose student to reset password:", student_names)
                idx = student_names.index(sel)
                chosen_student = students_filtered[idx]

                with st.form("reset_pw_form"):
                    new_pw = st.text_input("New password for student", type="password")
                    confirm_pw = st.text_input("Confirm new password", type="password")
                    reset_btn = st.form_submit_button("🔁 Reset password")

                if reset_btn:
                    if not new_pw:
                        st.error("Enter a new password.")
                    elif new_pw != confirm_pw:
                        st.error("Passwords do not match.")
                    else:
                        # update in session list
                        for s in st.session_state.students:
                            if s['email'] == chosen_student['email'] and s['batch'] == chosen_student['batch']:
                                s['password_hash'] = hash_password(new_pw)
                                st.success(f"Password updated for {s['name']}")
                                break
            else:
                st.info("No students to reset password for.")

            st.markdown("---")
            st.subheader("View full lists (in-app)")
            st.markdown("**Students**")
            st.dataframe(pd.DataFrame(students_filtered))
            st.markdown("**Subject teachers**")
            st.dataframe(pd.DataFrame(teachers_filtered))

    # logout button
    if st.session_state.head_logged_in:
        if st.button("🔒 Logout head teacher"):
            st.session_state.head_logged_in = False
            st.success("Head teacher logged out.")

    # buttons to export students / teachers / class details from session (non-head)
    st.markdown("---")
    cols_download = st.columns(3)

    with cols_download[0]:
        if st.button("📥 Download students CSV (all)"):
            if st.session_state.students:
                df_students = pd.DataFrame(st.session_state.students)
                csv = df_students.to_csv(index=False)
                st.download_button("Download students file", data=csv, file_name="students_all.csv", mime="text/csv")
            else:
                st.info("No students to download.")

    with cols_download[1]:
        if st.button("📥 Download subject teachers CSV (all)"):
            if st.session_state.subject_teachers:
                df_t = pd.DataFrame(st.session_state.subject_teachers)
                csv = df_t.to_csv(index=False)
                st.download_button("Download teachers file", data=csv, file_name="subject_teachers_all.csv", mime="text/csv")
            else:
                st.info("No subject teachers to download.")

    with cols_download[2]:
        if st.button("📥 Download class metadata"):
            if st.session_state.saved_class:
                sc = st.session_state.saved_class
                head = sc.get('head', {})
                subj = sc.get('subject_teachers', [])
                out = {"class_name": sc.get('class_name'), "batch": sc.get('batch'), "head_name": head.get('name'), "head_email": head.get('email'), "allow_head_pw_change": sc.get('allow_head_pw_change')}
                df_out = pd.DataFrame([out])
                csv = df_out.to_csv(index=False)
                st.download_button("Download class file", data=csv, file_name="class_metadata.csv", mime="text/csv")
            else:
                st.info("No class metadata saved. Use 'Save class & teachers' on the left.")

    # clear students
    if st.button("🧹 Clear students list"):
        st.session_state.students = []
        st.success("Students cleared from session.")

st.markdown("---")
st.caption("Notes: This page stores data in the current Streamlit session. Head teacher login is validated against the saved class head credentials in session. When you integrate with MySQL later, you can replace session storage with DB reads/writes and keep the head-only password-reset logic unchanged.")
