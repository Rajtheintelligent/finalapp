# teacher_dashboard.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
from db import get_batch_performance

# ---------- CONFIG ----------
st.set_page_config(page_title="Teacher Dashboard", layout="wide")

# ---------- Query Params ----------
params = st.query_params
batch = params.get("batch", [""])[0]
subject = params.get("subject", [""])[0]
subtopic = params.get("subtopic", [""])[0]

st.title(f"📊 Live Dashboard — {subject} ({subtopic})")
st.caption(f"Showing results for batch: {batch}")

# ---------- Auto Refresh ----------
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

# ---------- Helpers ----------
def build_pdf(df, subject, subtopic):
    buffer = io.BytesIO()
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet

    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph(f"Performance Report: {subject} - {subtopic}", styles["Title"]))
    elements.append(Spacer(1, 12))

    table_data = [["Student", "Correct", "Incorrect", "Total"]]
    for _, row in df.iterrows():
        table_data.append([row["Student_Name"], row["Correct"], row["Incorrect"], row["Total"]])

    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
        ("ALIGN", (1,1), (-1,-1), "CENTER"),
    ]))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()

# ============================================================
# 📊 LIVE DASHBOARD
# ============================================================
df = get_batch_performance(batch, subject, subtopic)

if df.empty:
    st.info("No live submissions yet.")
else:
    st.subheader("📈 Student Performance")
    df["Total"] = df["Correct"] + df["Incorrect"]
    df = df.sort_values(by="Correct", ascending=False)

    fig_height = max(3, len(df) * 0.6)
    fig, ax = plt.subplots(figsize=(8, fig_height))

    ax.barh(df["Student_Name"], df["Correct"], color="#4CAF50", label="Correct")
    ax.barh(df["Student_Name"], df["Incorrect"],
            left=df["Correct"], color="#E53935", label="Incorrect")

    for i, (c, ic) in enumerate(zip(df["Correct"], df["Incorrect"])):
        if c > 0:
            ax.text(c/2, i, str(c), ha="center", va="center", color="white", fontsize=9, weight="bold")
        if ic > 0:
            ax.text(c + ic/2, i, str(ic), ha="center", va="center", color="white", fontsize=9, weight="bold")

    ax.set_xlabel("Number of Questions")
    ax.set_ylabel("Students")
    ax.set_title(f"{subject} - {subtopic} Performance", weight="bold")
    ax.legend()
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)

    # Downloads
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download CSV", csv_bytes,
                       file_name=f"{batch}_{subtopic}_report.csv",
                       mime="text/csv")

    pdf_bytes = build_pdf(df, subject, subtopic)
    st.download_button("⬇️ Download PDF", pdf_bytes,
                       file_name=f"{batch}_{subtopic}_report.pdf",
                       mime="application/pdf")

# ============================================================
# 🔍 STUDENT DRILL-DOWN (Independent)
# ============================================================
st.header("🔍 Student Drill-Down")

col1, col2, col3 = st.columns([2,2,1])
with col1:
    student_email = st.text_input("Enter Student Email")   # use email (unique)
with col2:
    subject_choice = st.selectbox("Select Subject",
                                  ["Geometry", "Algebra", "Science1", "Science2", "English"])
with col3:
    submit_btn = st.button("Search")

if submit_btn and student_email and subject_choice:
    df_student = get_batch_performance(batch, subject_choice, None)  # ✅ now works after db fix
    df_student = df_student[df_student["Student_Email"] == student_email]

    if df_student.empty:
        st.warning("No records found for this student.")
    else:
        # Aggregate by subtopic
        summary = (
            df_student.groupby("Subtopic")
            .agg({"Correct":"sum","Incorrect":"sum"})
            .reset_index()
        )
        summary["Total"] = summary["Correct"] + summary["Incorrect"]

        fig_height = max(3, len(summary) * 0.6)
        fig, ax = plt.subplots(figsize=(8, fig_height))
        ax.barh(summary["Subtopic"], summary["Correct"], color="#4CAF50", label="Correct")
        ax.barh(summary["Subtopic"], summary["Incorrect"], left=summary["Correct"], color="#E53935", label="Incorrect")

        for i, (c, ic) in enumerate(zip(summary["Correct"], summary["Incorrect"])):
            if c > 0:
                ax.text(c/2, i, str(c), ha="center", va="center", color="white", fontsize=9, weight="bold")
            if ic > 0:
                ax.text(c + ic/2, i, str(ic), ha="center", va="center", color="white", fontsize=9, weight="bold")

        ax.set_xlabel("Number of Questions")
        ax.set_ylabel("Subtopics")
        ax.set_title(f"Performance of {student_email} in {subject_choice}", weight="bold")
        ax.legend()
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)

        # Downloads
        csv_bytes = summary.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", csv_bytes,
                           file_name=f"{student_email}_{subject_choice}_report.csv",
                           mime="text/csv")
