
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
from db import get_batch_performance, get_student_summary

# =============================
# Page config
# =============================
st.set_page_config(page_title="Teacher Dashboard", layout="wide")

# =============================
# Query params (URL)
# Use: ?batch=1102&subject=Algebra&subtopic=Quadratic_1
# =============================
params = st.query_params
batch = params.get("batch", [""])[0].strip()
subject = params.get("subject", [""])[0].strip()
subtopic = params.get("subtopic", [""])[0].strip()

st.title("📊 Teacher Dashboard")
st.caption(f"Batch: {batch or '—'} | Subject: {subject or '—'} | Subtopic: {subtopic or '—'}")

# =============================
# Auto-refresh (5s)
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
# Helpers
# =============================
def build_pdf(df, subject, subtopic):
    buffer = io.BytesIO()
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet

    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    title = f"Performance Report: {subject}"
    if subtopic:
        title += f" — {subtopic}"
    elements.append(Paragraph(title, styles["Title"]))
    elements.append(Spacer(1, 12))

    # Build table
    table_data = [["Student", "Correct", "Incorrect", "Total"]]
    for _, row in df.iterrows():
        table_data.append([row["Student_Name"], int(row["Correct"]), int(row["Incorrect"]), int(row["Total"])])

    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
        ("ALIGN", (1,1), (-1,-1), "CENTER"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
    ]))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()

def stacked_bar(df, y_field, title):
    df = df.copy()
    df["Total"] = df["Correct"] + df["Incorrect"]
    df = df.sort_values(by="Correct", ascending=False)

    fig_height = max(3, len(df) * 0.6)
    fig, ax = plt.subplots(figsize=(8, fig_height))

    ax.barh(df[y_field], df["Correct"], label="Correct")
    ax.barh(df[y_field], df["Incorrect"], left=df["Correct"], label="Incorrect")

    for i, (c, ic) in enumerate(zip(df["Correct"], df["Incorrect"])):
        if c > 0:
            ax.text(c/2, i, str(int(c)), ha="center", va="center", color="white", fontsize=9, weight="bold")
        if ic > 0:
            ax.text(c + ic/2, i, str(int(ic)), ha="center", va="center", color="white", fontsize=9, weight="bold")

    ax.set_xlabel("Number of Questions")
    ax.set_ylabel(y_field.replace("_"," "))
    ax.set_title(title, weight="bold")
    ax.legend()
    plt.tight_layout()
    return fig

# =============================
# Section 1: LIVE DASHBOARD
# =============================
st.header("📈 Live Dashboard")
if not (batch and subject):
    st.info("Add URL params ?batch=YOUR_CODE&subject=SUBJECT&subtopic=SUBTOPIC to see live data.")
else:
    live_df = get_batch_performance(batch, subject, subtopic if subtopic else None)

    if live_df.empty:
        st.warning("No live submissions found for the given filters yet.")
    else:
        live_df = live_df.copy()
        live_df["Total"] = live_df["Correct"] + live_df["Incorrect"]

        # Chart
        fig = stacked_bar(live_df, "Student_Name", f"{subject}{' — ' + subtopic if subtopic else ''} Performance")
        st.pyplot(fig, use_container_width=True)

        # Downloads
        csv_bytes = live_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", csv_bytes,
                           file_name=f"{batch}_{subject}{('_'+subtopic) if subtopic else ''}_report.csv",
                           mime="text/csv")

        pdf_bytes = build_pdf(live_df, subject, subtopic)
        st.download_button("⬇️ Download PDF", pdf_bytes,
                           file_name=f"{batch}_{subject}{('_'+subtopic) if subtopic else ''}_report.pdf",
                           mime="application/pdf")

# =============================
# Section 2: STUDENT DRILL-DOWN (Independent)
# =============================
st.header("🔍 Student Drill-Down")

col1, col2, col3 = st.columns([2,2,1])
with col1:
    dd_batch = st.text_input("Batch Code", value=batch)
with col2:
    dd_subject = st.selectbox(
        "Subject",
        options=["Mathematics","english"],  # match your DB exactly
        index=(["Mathematics","english"].index(subject) if subject in ["Mathematics","english"] else 0)
    )
with col3:
    dd_email = st.text_input("Student Email", placeholder="student@example.com")

go = st.button("Show Student Summary")

if go:
    if not (dd_batch and dd_subject and dd_email):
        st.error("Please fill Batch, Subject and Student Email.")
    else:
        summary = get_student_summary(dd_batch, dd_subject, dd_email)
        if summary.empty:
            st.warning("No records found for this student/subject in the selected batch.")
        else:
            # Chart
            fig = stacked_bar(summary, "Subtopic", f"{dd_email} — {dd_subject} (by Subtopic)")
            st.pyplot(fig, use_container_width=True)

            # Table
            st.dataframe(summary, use_container_width=True)

            # Downloads
            csv_bytes = summary.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download Student CSV", csv_bytes,
                               file_name=f"{dd_email}_{dd_subject}_summary.csv",
                               mime="text/csv")
