import streamlit as st
import pandas as pd
from io import StringIO

# ------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------
st.set_page_config(page_title="Teacher Admin — Fill Data", layout="wide")

# ------------------------------------------------------------
# HOME NAVIGATION
# ------------------------------------------------------------
st.page_link("Home.py", label="🏠 Home", icon="↩️")

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
# SESSION STATE INIT (dynamic lists)
# ------------------------------------------------------------
if "subject_teachers" not in st.session_state:
    st.session_state.subject_teachers = []  # list of dicts {name,email}
if "students" not in st.session_state:
    st.session_state.students = []  # list of dicts {batch,name,email,password}

# helpers to add entries
def add_subject_teacher(name, email):
    if name:
        st.session_state.subject_teachers.append({"name": name, "email": email})

def add_student(batch, name, email, password):
    if len(st.session_state.students) >= 40:
        st.warning("Maximum 40 students reached for this session.")
        return
    if name:
        st.session_state.students.append({"batch": batch, "name": name, "email": email, "password": password})

# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------
st.title("⚙️ Teacher — Quick Admin Data Entry")
st.markdown("A clean page for teachers to add class/head/subject-teacher and student details. Use the Save buttons to export CSVs for import into your app.")
st.markdown("---")

# ------------------------------------------------------------
# MAIN LAYOUT: two bordered boxes side-by-side on wide screens
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
        save_class = st.form_submit_button("💾 Save class & teachers")

    if add_subj:
        if not subj_name or not subj_email:
            st.error("Please provide both name and email for the subject teacher before adding.")
        else:
            add_subject_teacher(subj_name, subj_email)
            st.success(f"Added subject teacher: {subj_name}")

    if save_class:
        # build dataframe
        teachers_df = pd.DataFrame(st.session_state.subject_teachers)
        head_row = {"role": "Head Teacher", "name": head_name, "email": head_email, "password": head_password, "class": cls_name, "batch": batch}
        st.session_state.saved_class = {
            "class_name": cls_name,
            "batch": batch,
            "head": head_row,
            "subject_teachers": st.session_state.subject_teachers.copy(),
            "allow_head_pw_change": change_head_pw,
        }
        st.success("Class & teacher details captured in session. Use the Download button to export CSV.")

    # show current subject teachers list
    if st.session_state.subject_teachers:
        st.markdown("**Current subject teachers (session)**")
        for i, t in enumerate(st.session_state.subject_teachers, start=1):
            st.write(f"{i}. {t['name']} — {t['email']}")

    # option to clear subject teachers
    if st.button("🧹 Clear subject teachers list"):
        st.session_state.subject_teachers = []
        st.success("Subject teacher list cleared from session.")

    # allow uploading a CSV of subject teachers
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
    st.subheader("👩‍🎓 Students — Batch Entry (max 40 per batch)")

    # quick CSV upload to load students
    st.markdown("**Bulk import students**")
    uploaded_students = st.file_uploader("Upload students CSV (columns: batch, name, email, password)", type=["csv", "xlsx"], key="upload_students")
    if uploaded_students:
        df_students = load_csv_to_df(uploaded_students)
        if not df_students.empty and set([c.lower() for c in df_students.columns]).issuperset({"batch", "name", "email", "password"}):
            added = 0
            for _, r in df_students.iterrows():
                if len(st.session_state.students) < 40:
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
        elif len(st.session_state.students) >= 40:
            st.error("Cannot add more than 40 students for a batch in this session.")
        else:
            add_student(s_batch, s_name, s_email, s_password)
            st.success(f"Added student: {s_name}")

    # display current students
    if st.session_state.students:
        st.markdown(f"**Students in session ({len(st.session_state.students)})**")
        df_show = pd.DataFrame(st.session_state.students)
        st.dataframe(df_show)

    # buttons to export students / teachers / class details
    cols_download = st.columns(3)

    with cols_download[0]:
        if st.button("📥 Download students CSV"):
            if st.session_state.students:
                df_students = pd.DataFrame(st.session_state.students)
                csv = df_students.to_csv(index=False)
                st.download_button("Download students file", data=csv, file_name="students_batch.csv", mime="text/csv")
            else:
                st.info("No students to download.")

    with cols_download[1]:
        if st.button("📥 Download subject teachers CSV"):
            if st.session_state.subject_teachers:
                df_t = pd.DataFrame(st.session_state.subject_teachers)
                csv = df_t.to_csv(index=False)
                st.download_button("Download teachers file", data=csv, file_name="subject_teachers.csv", mime="text/csv")
            else:
                st.info("No subject teachers to download.")

    with cols_download[2]:
        if st.button("📥 Download class metadata"):
            if "saved_class" in st.session_state:
                # flatten saved class dict to csv-like
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
st.caption("Notes: This page stores data in the current Streamlit session. Export CSVs to persist data outside the app. The UI is cached for faster CSV loads.")
