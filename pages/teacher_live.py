# pages/teacher_live.py
import streamlit as st
import pandas as pd
from urllib.parse import unquote
import matplotlib.pyplot as plt

st.set_page_config(page_title="Live Teacher Dashboard", layout="wide")
st.title("📊 Live Dashboard (teacher view)")

# Read query params
qp = st.query_params
batch = qp.get("batch", [None])[0]
subject = qp.get("subject", [None])[0]
subtopic = qp.get("subtopic", [None])[0]  # optional

# Friendly messaging if someone opens the page without params
if not batch or not subject:
    st.error(
        "This page expects `batch` and `subject` query params. Example:\n\n"
        "`https://<your-app>/?page=teacher_live&batch=1100&subject=english&subtopic=tenses`"
    )
    st.stop()

st.markdown(f"**Batch:** `{batch}` • **Subject:** `{subject}` • **Subtopic:** `{subtopic or 'All'}`")

# Try to use your project's helper first (if present). If not, fall back to generic SQL.
perf_df = None
try:
    # If you already have a helper like `get_batch_performance(batch, subject, subtopic)` in your codebase:
    from db import get_batch_performance  # adjust if your module is different
    perf_df = get_batch_performance(batch, subject, subtopic or None)
except Exception:
    # Fallback: try direct query using DB creds in st.secrets
    try:
        # IMPORTANT: Put Postgres credentials in Streamlit secrets as "postgres" dict
        # Example st.secrets:
        # postgres = {
        #   "host": "....",
        #   "port": "5432",
        #   "dbname": "postgres",
        #   "user": "username",
        #   "password": "pwd"
        # }
        import psycopg2
        from psycopg2.extras import RealDictCursor

        if "postgres" not in st.secrets and "DATABASE_URL" not in st.secrets:
            raise RuntimeError("No DB credentials found in st.secrets (key 'postgres' or 'DATABASE_URL').")

        if "postgres" in st.secrets:
            p = st.secrets["postgres"]
            conn = psycopg2.connect(
                host=p["host"], port=p.get("port", 5432), dbname=p["dbname"], user=p["user"], password=p["password"]
            )
        else:
            # If you set a single DATABASE_URL in secrets: use it
            conn = psycopg2.connect(st.secrets["DATABASE_URL"])

        sql = """
        SELECT s.name as student_name,
               r.question_no,
               r.student_answer,
               r.correct_answer
        FROM responses r
        JOIN students s ON s.id = r.student_id
        WHERE s.class_code = %s AND r.subject = %s
        """
        params = [batch, subject]
        if subtopic:
            sql += " AND r.subtopic = %s"
            params.append(subtopic)

        df = pd.read_sql(sql, conn, params=params)
        conn.close()

        if df.empty:
            perf_df = pd.DataFrame()
        else:
            # compute per-student correct/incorrect counts (simple text equality check)
            def is_correct(row):
                try:
                    a = str(row["student_answer"]).strip().lower()
                    b = str(row["correct_answer"]).strip().lower()
                    return a == b
                except Exception:
                    return False

            df["is_correct"] = df.apply(is_correct, axis=1)
            agg = df.groupby("student_name")["is_correct"].agg(['sum', 'count']).reset_index()
            agg["Correct"] = agg["sum"].astype(int)
            agg["Incorrect"] = (agg["count"] - agg["sum"]).astype(int)
            perf_df = agg[["student_name", "Correct", "Incorrect"]]
    except Exception as e:
        st.error(f"Could not fetch performance data: {e}")
        perf_df = pd.DataFrame()

# If no data show friendly message
if perf_df is None or perf_df.empty:
    st.warning("No live submissions found for these filters yet.")
else:
    st.subheader("Per-student performance (live)")
    st.dataframe(perf_df.rename(columns={"student_name": "Student"}), use_container_width=True)

    # stacked bar plot: one bar per student (matplotlib — no explicit color set)
    plot_df = perf_df.set_index("student_name")
    fig, ax = plt.subplots(figsize=(10, max(4, len(plot_df) * 0.35)))
    plot_df[["Correct", "Incorrect"]].plot(kind="bar", stacked=True, ax=ax)
    ax.set_ylabel("Questions")
    ax.set_xlabel("")
    ax.set_title(f"Correct vs Incorrect — Batch {batch} — {subject} {('- ' + subtopic) if subtopic else ''}")
    plt.xticks(rotation=30, ha="right")
    st.pyplot(fig)

# Optional: small raw link for teacher to copy
st.markdown("---")
st.markdown("If you need the deep link again (copy/paste):")
safe_link = st.query_params
base = st.get_option("server.baseUrl") if st.get_option("server.baseUrl", None) else ""
# show the actual URL teacher used (not always possible to compute programmatically), so print expected pattern:
st.code(f"https://<your-app>/?page=teacher_live&batch={batch}&subject={subject}&subtopic={subtopic or ''}")
