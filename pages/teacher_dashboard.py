import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io

from db import get_batch_performance  # ✅ import your DB query

# ---------- CONFIG ----------
st.set_page_config(page_title="Teacher Dashboard", layout="wide")

# ---------- Query Params ----------
params = st.experimental_get_query_params()
batch = params.get("batch", [""])[0]
subject = params.get("subject", [""])[0]
subtopic_id = params.get("subtopic_id", [""])[0]

st.title(f"📊 Live Dashboard — {subject} ({subtopic_id})")
st.caption(f"Showing results for batch: {batch}")

# ---------- Autorefresh ----------
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=5000, key="data_refresh")  # refresh every 5s
except ImportError:
    st.warning("Auto-refresh not available — install streamlit-autorefresh")

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
