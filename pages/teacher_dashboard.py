# teacher_dashboard.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io

# ------------------------------
# DB helpers
# ------------------------------
from db import get_batch_performance

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
# Subject aliases (same idea as your Drilldown)
# UI label -> DB value
# =============================
LABEL_MAP = {
    "Geometry": "Mathematics",
    "Algebra": "Mathematics",
    "English": "english",
    # Add more as needed
}

def resolve_subject_value(subject_ui_or_db: str) -> str:
    # If URL passes a UI label, map to DB value; else return as-is
    if not subject_ui_or_db:
        return ""
    return LABEL_MAP.get(subject_ui_or_db, subject_ui_or_db).strip()

def normalize_subtopic_param(s: str) -> str:
    # Handle links like ...&subtopic=Quadratic_1 -> "Quadratic 1"
    if not s:
        return ""
    return s.replace("_", " ").strip()

# =============================
# Query params (URL)
# Example: ?batch=1102&subject=Algebra&subtopic=Quadratic_1
# =============================
params = st.query_params
batch_raw = params.get("batch", [""])[0].strip()
subject_raw = params.get("subject", [""])[0].strip()
subtopic_raw = params.get("subtopic", [""])[0].strip()

batch = batch_raw
subject = resolve_subject_value(subject_raw)
subtopic = normalize_subtopic_param(subtopic_raw)

# =============================
# Title + context
# =============================
st.title("📊 Teacher Dashboard — Live")
st.caption(f"Batch: {batch or '—'} | Subject (URL): {subject_raw or '—'} → Using in DB: {subject or '—'} | Subtopic: {subtopic or 'All'}")

# =============================
# Auto-refresh (every 5s)
# =============================
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=5000, key="data_refresh")
except Exception:
    import time
    if "last_refresh" not in st.session_state:
        st.session_state["last_refresh"] = time.time()
    if time.time() - st.session_state["last_refresh"] > 5:
        st.session_state["last_refresh"] = time.time()
        st.experimental_rerun()

# =============================
# Chart helpers
# =============================
def plot_horizontal_stacked_by_category(df: pd.DataFrame, cat_col: str, title: str):
    """Stacked H bars (Correct/Incorrect) by a categorical column, sorted by accuracy."""
    d = df.copy()
    d["Total"] = d["Correct"] + d["Incorrect"]
    d["Accuracy"] = d.apply(lambda r: (r["Correct"]/r["Total"]*100) if r["Total"]>0 else np.nan, axis=1)
    d = d.sort_values(by=["Accuracy", "Total"], ascending=[True, False], na_position="last")

    n = max(1, len(d))
    fig_height = max(3.5, n * 0.65)
    fig, ax = plt.subplots(figsize=(10, fig_height))

    y = np.arange(len(d))
    correct_color = "#2E7D32"
    incorrect_color = "#C62828"

    ax.barh(y, d["Correct"], label="Correct", color=correct_color)
    ax.barh(y, d["Incorrect"], left=d["Correct"], label="Incorrect", color=incorrect_color)

    # Inline labels
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
    """Stacked V bars (Correct/Incorrect) by a categorical column."""
    d = df.copy()
    d["Total"] = d["Correct"] + d["Incorrect"]
    # Sort by total desc
    d = d.sort_values(by="Total", ascending=False)

    n = max(1, len(d))
    fig_width = max(10, n * 0.6)  # wider for many bars (mobile scrolls horizontally)
    fig, ax = plt.subplots(figsize=(fig_width, 6.5))

    x = np.arange(len(d))
    correct_color = "#2E7D32"
    incorrect_color = "#C62828"

    ax.bar(x, d["Correct"], label="Correct", color=correct_color)
    ax.bar(x, d["Incorrect"], bottom=d["Correct"], label="Incorrect", color=incorrect_color)

    # Labels on bars
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
# PDF helper (optional dependency)
# =============================
def build_pdf(df: pd.DataFrame, title: str) -> bytes | None:
    try:
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
    except Exception:
        return None

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph(title, styles["Title"]))
    elements.append(Spacer(1, 12))

    table_data = [["Student", "Correct", "Incorrect", "Total", "Accuracy%"]]
    for _, r in df.iterrows():
        total = int(r["Correct"] + r["Incorrect"])
        acc = (100 * r["Correct"] / total) if total > 0 else float("nan")
        acc_txt = f"{acc:.0f}%" if not np.isnan(acc) else "—"
        table_data.append([r["Student_Name"], int(r["Correct"]), int(r["Incorrect"]), total, acc_txt])

    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
        ("ALIGN", (1,1), (-1,-1), "CENTER"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
    ]))

    elements.append(table)
    doc.build(elements)
    buf.seek(0)
    return buf.read()

# =============================
# Header controls (teacher-facing)
# =============================
left, right = st.columns([3, 2])

with left:
    st.subheader("📈 Live Dashboard")
    st.write("This page auto-refreshes every 5 seconds. Use URL params or the controls below.")

with right:
    view_options = ["Students", "Subtopics"]
    if HAS_QUIZ:
        view_options.append("Quizzes")
    selected_view = st.selectbox("View", options=view_options, index=0, help="Choose aggregation view")

# Let teachers adjust in-page even if URL given
ui_col1, ui_col2, ui_col3 = st.columns([2, 2, 2])
with ui_col1:
    batch = st.text_input("Batch (Tuition Code)", value=batch)
with ui_col2:
    subject_ui = st.text_input("Subject (UI/DB value)", value=subject_raw or subject)
    subject = resolve_subject_value(subject_ui)
with ui_col3:
    subtopic_ui = st.text_input("Subtopic (optional)", value=subtopic)
    subtopic = normalize_subtopic_param(subtopic_ui)

# =============================
# Data fetch
# =============================
if not (batch and subject):
    st.info("Add URL params (?batch=YOUR_CODE&subject=SUBJECT[&subtopic=SUBTOPIC]) or fill the inputs above.")
    st.stop()

live_df = get_batch_performance(batch, subject, subtopic or None)

if live_df.empty:
    st.warning("No live submissions found for the given filters yet.")
    st.stop()

# =============================
# Derived datasets
# =============================
# (1) Per-student aggregation
student_df = (
    live_df.groupby(["Student_Name", "Student_Email"], as_index=False)
           .agg(Correct=("Correct", "sum"), Incorrect=("Incorrect", "sum"))
)
student_df["Total"] = student_df["Correct"] + student_df["Incorrect"]
student_df["Accuracy%"] = student_df.apply(lambda r: (100*r["Correct"]/r["Total"]) if r["Total"]>0 else np.nan, axis=1)

# (2) Per-subtopic aggregation (only meaningful if not filtering to one subtopic)
subtopic_df = (
    live_df.groupby(["Subtopic"], as_index=False)
           .agg(Correct=("Correct", "sum"), Incorrect=("Incorrect", "sum"))
)
subtopic_df["Total"] = subtopic_df["Correct"] + subtopic_df["Incorrect"]
subtopic_df["Accuracy%"] = subtopic_df.apply(lambda r: (100*r["Correct"]/r["Total"]) if r["Total"]>0 else np.nan, axis=1)

# =============================
# KPIs
# =============================
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
    # weakest subtopic by accuracy (min)
    if not subtopic_df.empty and subtopic_df["Total"].sum() > 0:
        weak_row = subtopic_df[subtopic_df["Total"] > 0].copy()
        weak_row["acc"] = weak_row["Correct"] / weak_row["Total"]
        weak_name = weak_row.sort_values("acc", ascending=True).iloc[0]["Subtopic"]
        weak_text = str(weak_name)
    else:
        weak_text = "—"
k4.metric("Weakest Subtopic (Class)", weak_text)

st.markdown("---")

# =============================
# View: Students / Subtopics / Quizzes
# =============================
if selected_view == "Students":
    # Search + sort controls
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

    # Chart: horizontal stacked per student
    title = f"{subject}" + (f" — {subtopic}" if subtopic else "") + " (Per Student)"
    fig = plot_horizontal_stacked_by_category(
        filtered.rename(columns={"Student_Name": "Category"}),
        "Category",
        title=title
    )
    st.pyplot(fig, use_container_width=True)

    # Table + downloads
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
        pdf_bytes = build_pdf(filtered, title=f"Performance Report — {subject}{(' — '+subtopic) if subtopic else ''}")
        if pdf_bytes:
            st.download_button(
                "⬇️ Download PDF (Students)",
                data=pdf_bytes,
                file_name=f"{batch}_{subject}{('_'+subtopic) if subtopic else ''}_students.pdf",
                mime="application/pdf"
            )
        else:
            st.caption("Install `reportlab` to enable PDF export: `pip install reportlab`")

elif selected_view == "Subtopics":
    if subtopic:  # already filtered to one subtopic → show quick note + student view fallback
        st.info("You selected a specific subtopic via URL/inputs. Showing classwide **student** view is more meaningful here.")
        # Reuse student chart for this subtopic
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
        # Classwide per-subtopic (vertical bars)
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

        # Downloads
        col_a, col_b = st.columns(2)
        with col_a:
            st.download_button(
                "⬇️ Download CSV (Subtopics)",
                data=subtopic_df.to_csv(index=False).encode("utf-8"),
                file_name=f"{batch}_{subject}_subtopics.csv",
                mime="text/csv"
            )
        with col_b:
            # Simple PDF for subtopics (reuse student table builder by renaming)
            pdf_df = subtopic_df.rename(columns={"Subtopic":"Student_Name"}).copy()
            pdf_bytes = build_pdf(pdf_df, title=f"Subtopic Report — {subject}")
            if pdf_bytes:
                st.download_button(
                    "⬇️ Download PDF (Subtopics)",
                    data=pdf_bytes,
                    file_name=f"{batch}_{subject}_subtopics.pdf",
                    mime="application/pdf"
                )
            else:
                st.caption("Install `reportlab` to enable PDF export: `pip install reportlab`")

elif selected_view == "Quizzes" and HAS_QUIZ:
    st.subheader("Classwide Quiz Breakdown")
    quiz_df = get_class_quiz_summary(batch, subject)
    if quiz_df.empty:
        st.info("No quiz_id data available yet. Ensure you’re saving quiz_id in responses.")
    else:
        # Clean & plot (vertical stacked bars)
        quiz_plot_df = quiz_df.rename(columns={"Quiz_ID": "Category", "Class_Correct":"Correct", "Class_Incorrect":"Incorrect"}).copy()
        quiz_plot_df["Total"] = quiz_plot_df["Correct"] + quiz_plot_df["Incorrect"]

        fig = plot_vertical_stacked_by_category(
            quiz_plot_df,
            "Category",
            title=f"{subject} — Per Quiz (Class)"
        )
        st.pyplot(fig, use_container_width=True)

        # Table
        show_cols = ["Quiz_ID","Class_Correct","Class_Incorrect","Class_Total","Class_AccuracyPct"]
        st.dataframe(quiz_df[show_cols], use_container_width=True)

        # Downloads
        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                "⬇️ Download CSV (Quizzes)",
                data=quiz_df.to_csv(index=False).encode("utf-8"),
                file_name=f"{batch}_{subject}_quizzes.csv",
                mime="text/csv"
            )
        with c2:
            # PDF via rename trick
            pdf_df = quiz_df.rename(columns={
                "Quiz_ID":"Student_Name",
                "Class_Correct":"Correct",
                "Class_Incorrect":"Incorrect"
            })[["Student_Name","Correct","Incorrect"]].copy()
            pdf_bytes = build_pdf(pdf_df, title=f"Quiz Report — {subject}")
            if pdf_bytes:
                st.download_button(
                    "⬇️ Download PDF (Quizzes)",
                    data=pdf_bytes,
                    file_name=f"{batch}_{subject}_quizzes.pdf",
                    mime="application/pdf"
                )
            else:
                st.caption("Install `reportlab` to enable PDF export: `pip install reportlab`")
