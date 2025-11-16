# streamlit_upload.py
import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error
import bcrypt
from io import StringIO

st.set_page_config(page_title="CSV → Aiven MySQL uploader")

st.title("Upload teacher / students CSV")

# === CONFIG: put these in Streamlit secrets (recommended) ===
# Example st.secrets format (see below)
HOST = st.secrets["mysql"]["host"]
PORT = int(st.secrets["mysql"].get("port", 15211))
USER = st.secrets["mysql"]["user"]
PASSWORD = st.secrets["mysql"]["password"]
SSL_CA = st.secrets["mysql"]["ssl_ca_path"]  # path to downloaded aiven-ca.pem on the machine

# expected columns in CSV:
EXPECTED_COLS = [
    "ClassesName", "Grade", "HeadTeacher", "HeadTeacherEmail",
    "HeadTeacherPassword", "Batch",
    "StudentName", "StudentEmail", "StudentPassword", "LogoUrl"
]

st.markdown("**CSV columns expected:** " + ", ".join(EXPECTED_COLS))

uploaded_file = st.file_uploader("Choose CSV file", type=["csv"])

def get_db_connection():
    return mysql.connector.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
        ssl_ca=SSL_CA,
        ssl_verify_cert=True,
        autocommit=False
    )

def hash_password(plain: str) -> str:
    if plain is None:
        plain = ""
    hashed = bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")

def upsert_head_teacher(cursor, name, email, password_plain):
    # check if exists
    cursor.execute("SELECT id FROM head_teachers WHERE email = %s", (email,))
    r = cursor.fetchone()
    if r:
        return r[0]
    pw_hash = hash_password(password_plain)
    cursor.execute(
        "INSERT INTO head_teachers (name, email, password_hash) VALUES (%s,%s,%s)",
        (name, email, pw_hash)
    )
    return cursor.lastrowid

def get_or_create_class(cursor, class_name, grade, head_teacher_id, logo_url, batch):
    # try find existing by name + head_teacher
    cursor.execute(
        "SELECT id FROM classes WHERE class_name = %s AND head_teacher_id = %s",
        (class_name, head_teacher_id)
    )
    r = cursor.fetchone()
    if r:
        return r[0]
    cursor.execute(
        "INSERT INTO classes (class_name, grade, head_teacher_id, logo_url, batch) VALUES (%s,%s,%s,%s,%s)",
        (class_name, grade, head_teacher_id, logo_url, batch)
    )
    return cursor.lastrowid

def upsert_student(cursor, class_id, student_name, student_email, student_password_plain):
    # unique key (student_email, class_id)
    cursor.execute("SELECT id FROM students WHERE student_email = %s AND class_id = %s", (student_email, class_id))
    r = cursor.fetchone()
    if r:
        # update name/password if needed
        pw_hash = hash_password(student_password_plain)
        cursor.execute(
            "UPDATE students SET student_name=%s, student_password_hash=%s WHERE id=%s",
            (student_name, pw_hash, r[0])
        )
        return r[0]
    pw_hash = hash_password(student_password_plain)
    cursor.execute(
        "INSERT INTO students (class_id, student_name, student_email, student_password_hash) VALUES (%s,%s,%s,%s)",
        (class_id, student_name, student_email, pw_hash)
    )
    return cursor.lastrowid

if uploaded_file is not None:
    # read csv to dataframe
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Could not read CSV: {e}")
        st.stop()

    st.write(f"CSV loaded: {len(df)} rows")
    missing = [c for c in EXPECTED_COLS if c not in df.columns]
    if missing:
        st.warning(f"CSV missing columns: {missing}. You can still try, but mapping may be needed.")

    if st.button("Import CSV to Aiven MySQL"):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            processed = 0
            errors = []
            for i, row in df.iterrows():
                try:
                    class_name = row.get("ClassesName") or row.get("ClassName") or row.get("Class") or "Unknown"
                    grade = row.get("Grade")
                    head_name = row.get("HeadTeacher")
                    head_email = row.get("HeadTeacherEmail")
                    head_password = row.get("HeadTeacherPassword")
                    batch = row.get("Batch")
                    student_name = row.get("StudentName")
                    student_email = row.get("StudentEmail")
                    student_password = row.get("StudentPassword")
                    logo_url = row.get("LogoUrl")

                    # basic validation
                    if pd.isna(head_email) or pd.isna(student_email):
                        raise ValueError("Missing head or student email")

                    # upsert head teacher
                    head_id = upsert_head_teacher(cursor, head_name, head_email, head_password)

                    # get/create class
                    class_id = get_or_create_class(cursor, class_name, grade, head_id, logo_url, batch)

                    # upsert student
                    upsert_student(cursor, class_id, student_name, student_email, student_password)

                    processed += 1
                except Exception as e:
                    errors.append({"row": int(i)+1, "error": str(e)})
                    # continue with other rows

            conn.commit()
            st.success(f"Import finished. Processed: {processed}. Errors: {len(errors)}")
            if errors:
                st.json(errors)
        except Error as e:
            st.error(f"MySQL error: {e}")
        finally:
            if conn:
                conn.close()
