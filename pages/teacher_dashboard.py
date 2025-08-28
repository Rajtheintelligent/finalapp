import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io

# ------------------------------
# DB helpers
# ------------------------------
from db import get_batch_performance
# We'll use SessionLocal + ORM models to power the nicer UI controls
try:
    from db import SessionLocal, Student, Response
    HAS_DB_MODELS = True
except Exception:
    HAS_DB_MODELS = False

# Optional quiz helpers (safe if not present)
try:
    from db import get_class_quiz_summary
    HAS_QUIZ = True
except Exception:
    HAS_QUIZ = False

# =============================
# Page config
# =============================
st.set_page_config(page_title="Teacher Dashboard", layout="wide")

# =============================
# Small helpers to fetch distinct values for nicer UI
# =============================

def fetch_distinct_batches():
    """Return a sorted list of distinct class_code values from students table.
    Falls back to an empty list if DB models not importable."""
    if not HAS_DB_MODELS:
        return []
    db = SessionLocal()
    try:
        rows = db.query(Student.class_code).distinct().all()
        vals = sorted({r[0] for r in rows if r[0]})
        return vals
    finally:
        db.close()


def fetch_distinct_subjects():
    if not HAS_DB_MODELS:
        # sensible defaults
        return ["Mathematics", "english", "Science"]
    db = SessionLocal()
    try:
        rows = db.query(Response.subject).distinct().all()
        vals = sorted({(r[0] or "").strip() for r in rows if r[0]})
        # Normalize common casing while keeping DB value
        if not vals:
            return ["Mathematics", "english", "Science"]
        return vals
    finally:
        db.close()


def fetch_subtopics_for(batch_code: str, subject: str) -> list:
    if not HAS_DB_MODELS or not batch_code or not subject:
        return []
    db = SessionLocal()
    try:
        # join Student -> Response to filter by class_code
        rows = (
            db.query(Response.subtopic)
              .join(Student, Student.id == Response.student_id)
              .filter(Student.class_code == batch_code.strip())
              .filter(func_lower(Response.subject) == subject.strip().lower())
              .distinct()
              .all()
        )
        vals = sorted({r[0] for r in rows if r[0]})
        return vals
    finally:
        db.close()

# A tiny helper to avoid importing func from SQLAlchemy if models not available
try:
    from sqlalchemy import func as _sql_func
    def func_lower(col):
        return _sql_func.lower(col)
except Exception:
    def func_lower(col):
        # fallback no-op — when SQL functions not available just return column (may still work)
        return col

# =============================
# Small utilities (kept from your original file)
# =============================
LABEL_MAP = {
    "Geometry": "Mathematics",
    "Algebra": "Mathematics",
    "English": "english",
}

def resolve_subject_value(subject_ui_or_db: str) -> str:
    if not subject_ui_or_db:
        return ""
    return LABEL_MAP.get(subject_ui_or_db, subject_ui_or_db).strip()

def normalize_subtopic_param(s: str) -> str:
    if not s:
        return ""
    return s.replace("_", " ").strip()

# =============================
# Title + user-friendly manual controls (primary change)
# =============================
st.title("📊 Teacher Dashboard — Live (Manual)")
st.write("Use the controls below to view live student performance. You can type values or pick from the suggestions loaded from the DB.")

# Try to preload choices from DB for convenience
batches = fetch_distinct_batches()
subjects = fetch_distinct_subjects()

controls_left, controls_right = st.columns([3, 2])
with controls_left:
    # =========================
    # 🎛️ Filters Area
    # =========================
    st.markdown("## 🔎 Filters")

    # --- Batch selection ---
    def load_batches(limit=200):
        try:
            from db import SessionLocal, Student
            db = SessionLocal()
            try:
                rows = (
                    db.query(Student.class_code)
                      .distinct()
                      .limit(limit)
                      .all()
                )
                vals = sorted([r[0] for r in rows if r[0]])
                return vals
            finally:
                db.close()
        except Exception:
            # fallback if DB not available
            return ["BatchA", "BatchB", "BatchC"]

    batch_choices = load_batches()
    batch = st.selectbox("📘 Batch", options=batch_choices, index=0)
           
           
    # --- Subject selection ---
    def load_subjects(limit=50):
        try:
            from db import SessionLocal, Response
            db = SessionLocal()
            try:
                rows = (
                    db.query(Response.subject)
                      .distinct()
                      .limit(limit)
                      .all()
                )
                vals = sorted([r[0] for r in rows if r[0]])
                return vals
            finally:
                db.close()
        except Exception:
            return ["Mathematics", "English", "Science"]

    subject_choices = load_subjects()
    subject = st.selectbox("📗 Subject", options=subject_choices, index=0)
          
         
    # --- Subtopic selection (dynamic) ---
    def load_subtopics_for(batch_code: str, subject: str, limit=500):
        if not batch_code or not subject:
            return []
        try:
            from db import SessionLocal, Student, Response
            db = SessionLocal()
            try:
                rows = (
                    db.query(Response.subtopic)
                      .join(Student, Student.id == Response.student_id)
                      .filter(Student.class_code == batch_code.strip())
                      .filter(Response.subject.ilike(subject.strip()))
                      .distinct()
                      .limit(limit)
                      .all()
                )
                vals = sorted([r[0] for r in rows if r[0]])
                return vals
            finally:
                db.close()
        except Exception:
            return []

    if batch and subject:
        subtopic_choices = load_subtopics_for(batch, subject)
    else:
        subtopic_choices = []
           
    if subtopic_choices:
        sub_filter = st.text_input("🔍 Filter subtopics", value="")
        filtered = [s for s in subtopic_choices if sub_filter.lower() in s.lower()] if sub_filter else subtopic_choices
        options = ["All subtopics"] + filtered + ["Other (type manually)"]
        pick = st.selectbox("📙 Subtopic", options=options, index=0)

        if pick == "All subtopics":
            subtopic = ""   # means no filter
        elif pick == "Other (type manually)":
            subtopic = st.text_input("Type subtopic manually").strip()
        else:
            subtopic = pick
    else:
        subtopic = st.text_input("📙 Subtopic (type here if none found)").strip()                                                                                                                                                                                          
                                                                                                  
                                                                                                                                                                                                    
with controls_right:
    st.markdown("**View options**")
    view_options = ["Students", "Subtopics"]
    if HAS_QUIZ:
        view_options.append("Quizzes")
    selected_view = st.selectbox("View", options=view_options, index=0)

# Resolve subject mapping and normalize subtopic
subject = resolve_subject_value(subject_ui)
subtopic = normalize_subtopic_param(subtopic)

# =============================
# Auto-refresh (keeps as original behaviour)
# =============================
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=5000, key="data_refresh")
except Exception:
    import time
    if "last_refresh" not in st.session_state:
        st.session_state["last_refresh"] = time.time()
    if time.time() - st.session_state["last_refresh"] > 30:
        st.session_state["last_refresh"] = time.time()
        st.experimental_rerun()

# =============================
# Validate inputs and fetch data
# =============================
if not batch or not subject:
    st.info("Please enter Batch and Subject above (you can pick from the DB suggestions).")
    st.stop()

# Fetch live data
live_df = get_batch_performance(batch, subject, subtopic or None)

if live_df.empty:
    st.warning("No live submissions found for the given filters yet.")
    st.stop()

# The rest of the dashboard remains functionally equivalent to your original implementation —
# derived datasets, plotting helpers and export buttons are intentionally kept the same so
# teachers retain all previous functionality.

# Derived datasets (per-student and per-subtopic)
student_df = (
    live_df.groupby(["Student_Name", "Student_Email"], as_index=False)
           .agg(Correct=("Correct", "sum"), Incorrect=("Incorrect", "sum"))
)
student_df["Total"] = student_df["Correct"] + student_df["Incorrect"]
student_df["Accuracy%"] = student_df.apply(lambda r: (100*r["Correct"]/r["Total"]) if r["Total"]>0 else np.nan, axis=1)

subtopic_df = (
    live_df.groupby(["Subtopic"], as_index=False)
           .agg(Correct=("Correct", "sum"), Incorrect=("Incorrect", "sum"))
)
subtopic_df["Total"] = subtopic_df["Correct"] + subtopic_df["Incorrect"]
subtopic_df["Accuracy%"] = subtopic_df.apply(lambda r: (100*r["Correct"]/r["Total"]) if r["Total"]>0 else np.nan, axis=1)

# KPIs
total_q = int(live_df["Correct"].sum() + live_df["Incorrect"].sum())
class_acc = (100 * live_df["Correct"].sum() / total_q) if total_q > 0 else np.nan
num_students = int(student_df.shape[0])

k1, k2, k3, k4 = st.columns([1.2, 1.2, 1.2, 2])
k1.metric("Students Participated", f"{num_students}")
k2.metric("Total Questions (All)", f"{total_q}")
k3.metric("Class Accuracy", f"{class_acc:.0f}%" if not np.isnan(class_acc) else "—")
if subtopic:
    weak_text = subtopic
else:
    if not subtopic_df.empty and subtopic_df["Total"].sum() > 0:
        weak_row = subtopic_df[subtopic_df["Total"] > 0].copy()
        weak_row["acc"] = weak_row["Correct"] / weak_row["Total"]
        weak_name = weak_row.sort_values("acc", ascending=True).iloc[0]["Subtopic"]
        weak_text = str(weak_name)
    else:
        weak_text = "—"
k4.metric("Weakest Subtopic (Class)", weak_text)

st.markdown("---")

# --- Reuse your plotting helpers (minimal changes for clarity) ---

def plot_horizontal_stacked_by_category(df: pd.DataFrame, cat_col: str, title: str):
    d = df.copy()
    d["Total"] = d["Correct"] + d["Incorrect"]
    d["Accuracy"] = d.apply(lambda r: (r["Correct"]/r["Total"]*100) if r["Total"]>0 else np.nan, axis=1)
    d = d.sort_values(by=["Accuracy", "Total"], ascending=[True, False], na_position="last")

    n = max(1, len(d))
    fig_height = max(3.5, n * 0.65)
    fig, ax = plt.subplots(figsize=(10, fig_height))

    y = np.arange(len(d))
    ax.barh(y, d["Correct"], label="Correct")
    ax.barh(y, d["Incorrect"], left=d["Correct"], label="Incorrect")

    for i, (c, ic, tot) in enumerate(zip(d["Correct"], d["Incorrect"], d["Total"])):
        if c > 0: ax.text(c/2, i, str(int(c)), va="center", ha="center", color="white", fontsize=9, weight="bold")
        if ic > 0: ax.text(c + ic/2, i, str(int(ic)), va="center", ha="center", color="white", fontsize=9, weight="bold")
        pct = (100*c/tot) if tot>0 else np.nan
        pct_txt = f"{pct:.0f}%" if not np.isnan(pct) else "—"
        ax.text(tot + max(1, tot*0.02), i, pct_txt, va="center", ha="left", fontsize=9, color="#222")

    ax.set_yticks(y)
    ax.set_yticklabels(d[cat_col].astype(str).tolist())
    ax.invert_yaxis()
    ax.set_xlabel("Number of Questions")
    ax.set_title(title, weight="bold")
    ax.legend(loc="lower right", fontsize=9)
    plt.tight_layout()
    return fig


def plot_vertical_stacked_by_category(df: pd.DataFrame, cat_col: str, title: str):
    d = df.copy()
    d["Total"] = d["Correct"] + d["Incorrect"]
    d = d.sort_values(by="Total", ascending=False)

    n = max(1, len(d))
    fig_width = max(10, n * 0.6)
    fig, ax = plt.subplots(figsize=(fig_width, 6.5))

    x = np.arange(len(d))
    ax.bar(x, d["Correct"], label="Correct")
    ax.bar(x, d["Incorrect"], bottom=d["Correct"], label="Incorrect")

    for i, (c, ic, tot) in enumerate(zip(d["Correct"], d["Incorrect"], d["Total"])):
        if c > 0: ax.text(i, c/2, str(int(c)), ha="center", va="center", color="white", fontsize=9, weight="bold")
        if ic > 0: ax.text(i, c + ic/2, str(int(ic)), ha="center", va="center", color="white", fontsize=9, weight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(d[cat_col].astype(str).tolist(), rotation=45, ha="right")
    ax.set_ylabel("Number of Questions")
    ax.set_title(title, weight="bold")
    ax.legend(loc="upper right", fontsize=9)
    plt.tight_layout()
    return fig

# =============================
# Views (Students / Subtopics / Quizzes)
# =============================
if selected_view == "Students":
    filt_col1, filt_col2, filt_col3 = st.columns([2, 1.3, 1.3])
    with filt_col1:
        query = st.text_input("Search student (name/email)", value="")
    with filt_col2:
        sort_by = st.selectbox("Sort by", ["Accuracy%", "Correct", "Total", "Incorrect"], index=0)
    with filt_col3:
        ascending = st.checkbox("Ascending", value=False)

    filtered = student_df.copy()
    if query:
        q = query.lower()
        filtered = filtered[filtered["Student_Name"].str.lower().str.contains(q) |
                            filtered["Student_Email"].str.lower().str.contains(q)]

    filtered = filtered.sort_values(by=sort_by, ascending=ascending, na_position="last")

    title = f"{subject}" + (f" — {subtopic}" if subtopic else "") + " (Per Student)"
    fig = plot_horizontal_stacked_by_category(
        filtered.rename(columns={"Student_Name": "Category"}),
        "Category",
        title=title
    )
    st.pyplot(fig, use_container_width=True)

    st.subheader("Student Summary")
    st.dataframe(filtered[["Student_Name","Student_Email","Correct","Incorrect","Total","Accuracy%"]],
                 use_container_width=True)

    dl_col1, dl_col2 = st.columns(2)
    with dl_col1:
        st.download_button(
            "⬇️ Download CSV (Students)",
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name=f"{batch}_{subject}{('_'+subtopic) if subtopic else ''}_students.csv",
            mime="text/csv"
        )
    with dl_col2:
        st.caption("PDF export available if reportlab is installed on the server.")

elif selected_view == "Subtopics":
    if subtopic:
        st.info("You selected a specific subtopic. Showing classwide student view for this subtopic.")
        title = f"{subject} — {subtopic} (Per Student)"
        fig = plot_horizontal_stacked_by_category(
            student_df.rename(columns={"Student_Name": "Category"}),
            "Category",
            title=title
        )
        st.pyplot(fig, use_container_width=True)
        st.dataframe(student_df[["Student_Name","Student_Email","Correct","Incorrect","Total","Accuracy%"]],
                     use_container_width=True)
    else:
        st.subheader("Classwide Subtopic Breakdown")
        if subtopic_df.empty:
            st.info("No subtopic data yet.")
        else:
            fig = plot_vertical_stacked_by_category(
                subtopic_df.rename(columns={"Subtopic": "Category"}),
                "Category",
                title=f"{subject} — Subtopic Performance (Class)"
            )
            st.pyplot(fig, use_container_width=True)
            st.dataframe(subtopic_df[["Subtopic","Correct","Incorrect","Total","Accuracy%"]],
                         use_container_width=True)

        col_a, col_b = st.columns(2)
        with col_a:
            st.download_button(
                "⬇️ Download CSV (Subtopics)",
                data=subtopic_df.to_csv(index=False).encode("utf-8"),
                file_name=f"{batch}_{subject}_subtopics.csv",
                mime="text/csv"
            )
        with col_b:
            st.caption("PDF export available if reportlab is installed on the server.")

elif selected_view == "Quizzes" and HAS_QUIZ:
    st.subheader("Classwide Quiz Breakdown")
    quiz_df = get_class_quiz_summary(batch, subject)
    if quiz_df.empty:
        st.info("No quiz_id data available yet. Ensure you’re saving quiz_id in responses.")
    else:
        quiz_plot_df = quiz_df.rename(columns={"Quiz_ID": "Category", "Class_Correct":"Correct", "Class_Incorrect":"Incorrect"}).copy()
        quiz_plot_df["Total"] = quiz_plot_df["Correct"] + quiz_plot_df["Incorrect"]

        fig = plot_vertical_stacked_by_category(
            quiz_plot_df,
            "Category",
            title=f"{subject} — Per Quiz (Class)"
        )
        st.pyplot(fig, use_container_width=True)
        show_cols = ["Quiz_ID","Class_Correct","Class_Incorrect","Class_Total","Class_AccuracyPct"]
        st.dataframe(quiz_df[show_cols], use_container_width=True)

# End of file
