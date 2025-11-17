import streamlit as st
import io
import pandas as pd
import traceback
from io import StringIO
#from utils import parse_file_bytes, get_mysql_conn_cached, cached_simple_query


# ------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------
st.set_page_config(page_title="Admin — CSV Data Entry", layout="wide")

# ------------------------------------------------------------
# HOME NAVIGATION
# ------------------------------------------------------------
st.page_link("Home.py", label="🏠 Home", icon="↩️")


# ------------------------------------------------------------
# CACHE HELPERS
# ------------------------------------------------------------
@st.cache_data
def make_template_df():
    # create template with header and one example row
    cols = [
        "ClassesName",
        "Grade",
        "HeadTeacher",
        "HeadTeacherEmail",
        "HeadTeacherPassword",
        "Batch",
        "StudentName",
        "StudentEmail",
        "StudentPassword",
    ]
    example = {
        "ClassesName": "Grade 10 - A",
        "Grade": "10",
        "HeadTeacher": "Ms. Anita Rao",
        "HeadTeacherEmail": "anita@example.com",
        "HeadTeacherPassword": "ExamplePass123",
        "Batch": "Batch-A",
        "StudentName": "Ravi Kumar",
        "StudentEmail": "ravi.kumar@example.com",
        "StudentPassword": "StuPass123",
    }
    df = pd.DataFrame([example], columns=cols)
    return df

@st.cache_data
def parse_uploaded_csv(uploaded) -> pd.DataFrame:
    # returns dataframe or raises
    if uploaded is None:
        return pd.DataFrame()
    try:
        df = pd.read_csv(uploaded)
    except Exception:
        df = pd.read_excel(uploaded)
    return df

# ------------------------------------------------------------
# SESSION STATE INIT
# ------------------------------------------------------------
if "uploaded_df" not in st.session_state:
    st.session_state.uploaded_df = pd.DataFrame()

# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------
st.title("📥 Admin — CSV-based Data Entry")
st.markdown(
    "This page provides a simple, formal CSV workflow so teachers can prepare student lists offline and upload them in one batch."
)
st.markdown("---")

# ------------------------------------------------------------
# Additional imports and DB helpers for MySQL import
# ------------------------------------------------------------
# these imports are minimal and local to the file to avoid interfering if not used
try:
    import mysql.connector
    import bcrypt
    from mysql.connector import Error
    MYSQL_LIBS_AVAILABLE = True
except Exception:
    MYSQL_LIBS_AVAILABLE = False

def get_db_conn():
    """
    Create and return a mysql.connector connection using st.secrets.
    st.secrets should contain:
    [mysql]
    host = "..."
    port = "15211"
    user = "avnadmin"
    password = "AVNS_..."
    ssl_ca_path = "aiven-ca.pem"   # path on the running host
    """
    if not MYSQL_LIBS_AVAILABLE:
        raise RuntimeError("mysql-connector-python and bcrypt must be installed. Add them to requirements.txt")
    cfg = st.secrets.get("mysql", {})
    host = cfg.get("host")
    port = int(cfg.get("port", 15211))
    user = cfg.get("user")
    password = cfg.get("password")
    ssl_ca = cfg.get("ssl_ca_path")  # local path to aiven-ca.pem
    if not (host and user and password):
        raise RuntimeError("Missing DB credentials in st.secrets['mysql']. Provide host,user,password (and ssl_ca_path).")
    return mysql.connector.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        ssl_ca=ssl_ca,
        ssl_verify_cert=True,
        autocommit=False
    )

def hash_pw(plain):
    if plain is None:
        plain = ""
    try:
        return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    except Exception:
        # fallback - don't fail hard, but highly recommend bcrypt to be installed
        return plain

def upsert_head_teacher(cursor, name, email, password_plain):
    cursor.execute("SELECT id FROM head_teachers WHERE email = %s", (email,))
    r = cursor.fetchone()
    if r:
        return r[0]
    pw = hash_pw(password_plain)
    cursor.execute("INSERT INTO head_teachers (name, email, password_hash) VALUES (%s,%s,%s)",
                   (name, email, pw))
    return cursor.lastrowid

def get_or_create_class(cursor, class_name, grade, head_id, logo_url, batch):
    cursor.execute("SELECT id FROM classes WHERE class_name = %s AND head_teacher_id = %s",
                   (class_name, head_id))
    r = cursor.fetchone()
    if r:
        return r[0]
    cursor.execute("INSERT INTO classes (class_name, grade, head_teacher_id, logo_url, batch) VALUES (%s,%s,%s,%s,%s)",
                   (class_name, grade, head_id, logo_url, batch))
    return cursor.lastrowid

def upsert_student(cursor, class_id, name, email, pw_plain):
    cursor.execute("SELECT id FROM students WHERE student_email = %s AND class_id = %s", (email, class_id))
    r = cursor.fetchone()
    pw_hash = hash_pw(pw_plain)
    if r:
        cursor.execute("UPDATE students SET student_name=%s, student_password_hash=%s WHERE id=%s",
                       (name, pw_hash, r[0]))
        return r[0]
    cursor.execute("INSERT INTO students (class_id, student_name, student_email, student_password_hash) VALUES (%s,%s,%s,%s)",
                   (class_id, name, email, pw_hash))
    return cursor.lastrowid

# ------------------------------------------------------------
# Left: Template download + upload area
# ------------------------------------------------------------
left, right = st.columns([2, 2])

with left:
    st.subheader("1) Download CSV template")
    st.write(
        "Click the button below to download a CSV template. The first row is an example for reference. Only use the columns shown in the template."
    )

    template_df = make_template_df()
    csv_bytes = template_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ Download CSV template",
        data=csv_bytes,
        file_name="students_template.csv",
        mime="text/csv",
    )

    st.markdown("---")
    st.subheader("2) Upload completed CSV")
    st.write("Select the completed CSV file using the button below. The file will be validated before import.")

    uploaded_file = st.file_uploader("Upload CSV (required columns: ClassesName, Grade, HeadTeacher, HeadTeacherEmail, HeadTeacherPassword, Batch, StudentName, StudentEmail, StudentPassword)", type=["csv", "xlsx"], accept_multiple_files=False)

    if uploaded_file:
        try:
            # use cached parser - pass file bytes + filename so cache keys are correct
            file_bytes = uploaded_file.read()
            df = parse_file_bytes(file_bytes, uploaded_file.name)
            required_cols = [
                "ClassesName",
                "Grade",
                "HeadTeacher",
                "HeadTeacherEmail",
                "HeadTeacherPassword",
                "Batch",
                "StudentName",
                "StudentEmail",
                "StudentPassword",
            ]
            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                st.error(f"Uploaded file is missing required columns: {missing}")
            else:
                # limit check: max 40 students per batch
                counts = df.groupby('Batch').size().to_dict()
                violating = {b: n for b, n in counts.items() if n > 40}
                if violating:
                    st.error(f"Batch size limit exceeded for: {violating}. Each batch can have up to 40 students.")
                else:
                    st.success("File validated successfully.")
                    st.session_state.uploaded_df = df
                    st.dataframe(df)
                    st.markdown("**Summary by batch:**")
                    st.table(pd.DataFrame(list(counts.items()), columns=['Batch','Count']))

                    # final import button (writes to DB)
                    if st.button("✅ Import to system (DB)"):
                        if st.session_state.uploaded_df is None or st.session_state.uploaded_df.empty:
                            st.error("No data to import. Upload and validate first.")
                        else:
                            df2 = st.session_state.uploaded_df.copy()
                            conn = None
                            try:
                                cfg = st.secrets.get("mysql", {})
                                conn = get_mysql_conn_cached(
                                    host=cfg["host"],
                                    port=int(cfg.get("port", 15211)),
                                    user=cfg["user"],
                                    password=cfg["password"],
                                    ssl_ca_path=cfg.get("ssl_ca_path")
                                )
                                cur = conn.cursor()
                                processed = 0
                                errors = []
                                for i, row in df2.iterrows():
                                    try:
                                        class_name = row.get("ClassesName") or "Unknown"
                                        grade = row.get("Grade")
                                        head_name = row.get("HeadTeacher")
                                        head_email = row.get("HeadTeacherEmail")
                                        head_pass = row.get("HeadTeacherPassword")
                                        batch = row.get("Batch")
                                        student_name = row.get("StudentName")
                                        student_email = row.get("StudentEmail")
                                        student_pass = row.get("StudentPassword")
                                        logo_url = row.get("LogoUrl", None)

                                        if pd.isna(head_email) or pd.isna(student_email):
                                            raise ValueError("Missing head or student email")

                                        head_id = upsert_head_teacher(cur, head_name, head_email, head_pass)
                                        class_id = get_or_create_class(cur, class_name, grade, head_id, logo_url, batch)
                                        upsert_student(cur, class_id, student_name, student_email, student_pass)

                                        processed += 1
                                    except Exception as e:
                                        errors.append({"row": int(i)+1, "error": str(e)})
                                        # continue with next rows

                                conn.commit()
                                st.success(f"DB import finished. Rows processed: {processed}. Errors: {len(errors)}")
                                if errors:
                                    st.json(errors)
                                # optionally set imported_df for download utilities
                                st.session_state.imported_df = df2.copy()
                            except Error as e:
                                if conn:
                                    conn.rollback()
                                st.error(f"MySQL error: {e}")
                            except Exception as e:
                                st.error(f"Unexpected error: {e}")
                            finally:
                                if conn:
                                    conn.close()

                    # optional: keep session-only import fallback (commented)
                    # if st.button("✅ Import to system (session only)"):
                    #     st.session_state.imported_df = df.copy()
                    #     st.success(f"Imported {len(df)} rows into session storage. (Replace with DB write in production)")
        except Exception as e:
            st.exception(e)

# ------------------------------------------------------------
# Right: Actions and utilities
# ------------------------------------------------------------
with right:
    st.subheader("Utilities")
    st.write("After uploading and validating the CSV you may import or use the utilities below.")

    # Download last imported data
    if 'imported_df' in st.session_state and not st.session_state.imported_df.empty:
        st.download_button(
            label="📥 Download last imported (CSV)",
            data=st.session_state.imported_df.to_csv(index=False),
            file_name="last_imported_students.csv",
            mime="text/csv",
        )
    else:
        st.info("No data imported yet. Upload a CSV and use 'Import to system' first.")

    st.markdown("---")
    st.write("**Student password change**")
    st.write("(Placeholder) — click to open password-change workflow for a batch. Implementation details to follow.")
    if st.button("🔁 Student password change"):
        st.info("Student password-change workflow will be implemented here. You can upload a CSV with updated passwords or select individual students once connected to the DB.")

    st.markdown("---")
    st.write("**Get batch details**")
    st.write("(Placeholder) — download batch-wise student and teacher lists. When connected to DB this will query the requested batch(es).")
    if st.button("📂 Get batch details"):
        if 'imported_df' in st.session_state and not st.session_state.imported_df.empty:
            # produce zipped csv per batch or a single file
            df = st.session_state.imported_df
            st.success("Batch details prepared below.")
            # show a table of counts
            st.table(df.groupby('Batch').size().rename('Count').reset_index())
            # provide per-batch CSV downloads
            batches = sorted(df['Batch'].unique())
            for b in batches:
                sub = df[df['Batch'] == b]
                st.download_button(label=f"Download {b} (CSV)", data=sub.to_csv(index=False), file_name=f"batch_{b}.csv", mime="text/csv")
        else:
            st.info("No imported data in session. Upload & import a CSV first.")

st.markdown("---")
st.caption("Notes: This page uses a simple CSV workflow to keep load on the server minimal. Currently imports store data in the Streamlit session; replace the import action with a DB write when you are ready to integrate MySQL.")
