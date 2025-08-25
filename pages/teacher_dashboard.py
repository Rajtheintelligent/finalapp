import streamlit as st
import pandas as pd
from sqlalchemy import func
from database import SessionLocal, Student, Response
from utils import get_batch_performance   # your function from earlier

st.set_page_config(page_title="📊 Teacher Dashboard", layout="wide")

st.title("📊 Teacher Dashboard")

# --- Fetch distinct filter values from DB ---
def get_filter_options():
    db = SessionLocal()
    try:
        batches = [r[0] for r in db.query(Student.class_code).distinct().all()]
        subjects = [r[0] for r in db.query(Response.subject).distinct().all()]
        subtopics = [r[0] for r in db.query(Response.subtopic).distinct().all()]
        return batches, subjects, subtopics
    finally:
        db.close()

batches, subjects, subtopics = get_filter_options()

# --- Sidebar filters ---
st.sidebar.header("🔎 Filters")
batch_code = st.sidebar.selectbox("Batch", batches)
subject = st.sidebar.selectbox("Subject", subjects)
subtopic = st.sidebar.selectbox("Subtopic (optional)", [""] + subtopics)

# --- Show filter summary ---
st.markdown(
    f"**Batch:** {batch_code} | **Subject:** {subject} | **Subtopic:** {subtopic or 'All'}"
)

# --- Live Dashboard ---
st.subheader("📈 Live Dashboard")

perf = get_batch_performance(batch_code, subject, subtopic or None)

if perf.empty:
    st.warning("No live submissions found for the given filters yet.")
else:
    st.dataframe(perf)
    # Optional: Plot performance chart
    chart = (
        perf.groupby("Student_Name")[["Correct","Incorrect"]]
        .sum()
        .plot(kind="bar", stacked=True, figsize=(8,4))
    )
    st.pyplot(chart.figure)

# 🚫 Removed Student Drill-Down section
