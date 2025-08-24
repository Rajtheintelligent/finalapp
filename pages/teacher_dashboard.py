import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io

from db import get_batch_performance  # ✅ import your DB query

# ---------- CONFIG ----------
st.set_page_config(page_title="Teacher Dashboard", layout="wide")

# ---------- Query Params ----------
params = st.query_params
batch = params.get("batch", [""])[0]
subject = params.get("subject", [""])[0]
subtopic_id = params.get("subtopic_id", [""])[0]

st.title(f"📊 Live Dashboard — {subject} ({subtopic_id})")
st.caption(f"Showing results for batch: {batch}")

# ---------- Autorefresh ----------
# prefer the package when available, otherwise fall back to a tiny timer-based rerun
try:
    # correct import name uses underscore, not dash
    from streamlit_autorefresh import st_autorefresh
    # call it (interval is milliseconds)
    st_autorefresh(interval=5000, key="data_refresh")
except Exception:
    # fallback if the package isn't installed or import fails
    import time
    # create/initialize last_refresh timestamp
    if "last_refresh" not in st.session_state:
        st.session_state["last_refresh"] = time.time()
    # small interval in seconds
    _interval_seconds = 5
    if time.time() - st.session_state["last_refresh"] > _interval_seconds:
        st.session_state["last_refresh"] = time.time()
        # this causes Streamlit to rerun — works as a simple auto-refresh fallback
        st.experimental_rerun()


# ---------- Load Responses ----------
DEMO_MODE = False   # 🔄 toggle True for testing without DB

def load_responses_demo(batch, subject, subtopic_id):
    """Demo placeholder data"""
    data = [
        {"Student_Name": "Vinayak Ambat", "Correct": 6, "Incorrect": 2},
        {"Student_Name": "Rahul Patil", "Correct": 4, "Incorrect": 4},
        {"Student_Name": "Sneha Kulkarni", "Correct": 7, "Incorrect": 1},
    ]
    return pd.DataFrame(data)

if DEMO_MODE:
    df = load_responses_demo(batch, subject, subtopic_id)
else:
    df = get_batch_performance(batch, subject, subtopic_id)
st.write("DEBUG df.columns:", df.columns.tolist())
st.write("DEBUG query params:",
         batch, subject, subtopic_id)

st.write("DEBUG loaded submissions (head):")
st.dataframe(df.head())   # df = dataframe you load for responses

# Check what unique values exist in the sheet
st.write("DEBUG unique batches:", df["Tuition_Code"].unique().tolist())
st.write("DEBUG unique subjects:", df["Subject"].unique().tolist())
st.write("DEBUG unique subtopics:", df["Subtopic_ID"].unique().tolist())

if df.empty:
    st.info("No submissions yet.")
    st.stop()

# ---------- Visualization ----------
st.subheader("📈 Student Performance")

# Sort by correct answers
df["Total"] = df["Correct"] + df["Incorrect"]
df = df.sort_values(by="Correct", ascending=False)

# Mobile-friendly: adjust fig height based on number of students
fig_height = max(3, len(df) * 0.6)
fig, ax = plt.subplots(figsize=(8, fig_height))

bars_correct = ax.barh(df["Student_Name"], df["Correct"], color="#4CAF50", label="Correct")
bars_incorrect = ax.barh(df["Student_Name"], df["Incorrect"],
                         left=df["Correct"], color="#E53935", label="Incorrect")

# Add labels inside bars
for i, (c, ic) in enumerate(zip(df["Correct"], df["Incorrect"])):
    if c > 0:
        ax.text(c / 2, i, str(c), va="center", ha="center", color="white", fontsize=9, weight="bold")
    if ic > 0:
        ax.text(c + ic / 2, i, str(ic), va="center", ha="center", color="white", fontsize=9, weight="bold")

ax.set_xlabel("Number of Questions", fontsize=11)
ax.set_ylabel("Students", fontsize=11)
ax.set_title(f"{subject} - {subtopic_id} Performance", fontsize=14, weight="bold", pad=12)

# Style tweaks for mobile view
ax.tick_params(axis="y", labelsize=10)
ax.tick_params(axis="x", labelsize=9)
ax.legend(loc="upper right", fontsize=9)
plt.tight_layout()

st.pyplot(fig, use_container_width=True)

# ---------- Download CSV ----------
csv_bytes = df.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download CSV", csv_bytes,
                   file_name=f"{batch}_{subtopic_id}_report.csv",
                   mime="text/csv")

# ---------- Download PDF ----------
def build_pdf(df):
    buffer = io.BytesIO()
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet

    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph(f"Performance Report: {subject} - {subtopic_id}", styles["Title"]))
    elements.append(Spacer(1, 12))

    # Build table
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

pdf_bytes = build_pdf(df)
st.download_button("⬇️ Download PDF", pdf_bytes,
                   file_name=f"{batch}_{subtopic_id}_report.pdf",
                   mime="application/pdf")
# ============================================================
# 🔍 Student Drill-Down Section
# ============================================================

st.subheader("🔍 Student Drill-Down")

col1, col2, col3 = st.columns([2,2,1])
with col1:
    student_id_input = st.text_input("Enter Student ID")
with col2:
    subject_choice = st.selectbox("Select Subject", 
                                  ["Geometry", "Algebra", "Science1", "Science2", "English"])
with col3:
    submit_btn = st.button("Enter")

if submit_btn and student_id_input and subject_choice:
    try:
        # Query all subtopics for this student/subject
        df_student = get_batch_performance(batch, subject_choice, None)
        df_student = df_student[df_student["Student_ID"] == student_id_input]

        if df_student.empty:
            st.warning("No records found for this student.")
        else:
            # Build summary: one row per subtopic
            summary = (
                df_student.groupby("Subtopic_ID")
                .agg({"Correct":"sum","Incorrect":"sum"})
                .reset_index()
            )
            summary["Total"] = summary["Correct"] + summary["Incorrect"]

            # 📊 Horizontal stacked bar chart
            fig_height = max(3, len(summary) * 0.6)
            fig, ax = plt.subplots(figsize=(8, fig_height))

            bars_c = ax.barh(summary["Subtopic_ID"], summary["Correct"], 
                             color="#4CAF50", label="Correct")
            bars_i = ax.barh(summary["Subtopic_ID"], summary["Incorrect"], 
                             left=summary["Correct"], color="#E53935", label="Incorrect")

            for i, (c, ic) in enumerate(zip(summary["Correct"], summary["Incorrect"])):
                if c > 0:
                    ax.text(c/2, i, str(c), ha="center", va="center", color="white", fontsize=9, weight="bold")
                if ic > 0:
                    ax.text(c+c/2, i, str(ic), ha="center", va="center", color="white", fontsize=9, weight="bold")

            ax.set_xlabel("Number of Questions")
            ax.set_ylabel("Subtopics")
            ax.set_title(f"Performance of {student_id_input} in {subject_choice}", weight="bold")
            ax.legend()
            plt.tight_layout()

            st.pyplot(fig, use_container_width=True)

            # ----------------- Downloads -----------------
            st.subheader("⬇️ Download Reports")

            # CSV
            csv_bytes = summary.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv_bytes,
                               file_name=f"{student_id_input}_{subject_choice}_report.csv",
                               mime="text/csv")

            # Excel
            import pandas as pd
            import io
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                summary.to_excel(writer, index=False, sheet_name="Report")
            excel_buffer.seek(0)
            st.download_button("Download Excel", excel_buffer,
                               file_name=f"{student_id_input}_{subject_choice}_report.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            # PDF
            def build_student_pdf(df, student_id, subject_choice):
                buffer = io.BytesIO()
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
                from reportlab.lib.pagesizes import A4
                from reportlab.lib import colors
                from reportlab.lib.styles import getSampleStyleSheet
                styles = getSampleStyleSheet()

                doc = SimpleDocTemplate(buffer, pagesize=A4)
                elements = []

                elements.append(Paragraph(f"Performance Report: {student_id} — {subject_choice}", styles["Title"]))
                elements.append(Spacer(1, 12))

                table_data = [["Subtopic", "Correct", "Incorrect", "Total"]]
                for _, row in df.iterrows():
                    table_data.append([row["Subtopic_ID"], row["Correct"], row["Incorrect"], row["Total"]])

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

            pdf_bytes = build_student_pdf(summary, student_id_input, subject_choice)
            st.download_button("Download PDF", pdf_bytes,
                               file_name=f"{student_id_input}_{subject_choice}_report.pdf",
                               mime="application/pdf")

    except Exception as e:
        st.error(f"Error while fetching student data: {e}")

