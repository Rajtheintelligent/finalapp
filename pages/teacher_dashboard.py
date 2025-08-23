import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import io

# ---------- Page Config ----------
st.set_page_config(page_title="Teacher Dashboard", layout="wide")

# ---------- Query Params ----------
params = st.experimental_get_query_params()
batch = params.get("batch", [""])[0]
subject = params.get("subject", [""])[0]
subtopic_id = params.get("subtopic_id", [""])[0]

st.title(f"📊 Live Dashboard — {subject} ({subtopic_id})")
st.caption(f"Showing results for batch: {batch}")

# ---------- Autorefresh ----------
st_autorefresh = st.experimental_singleton(lambda: None)  # fallback if not imported
try:
    from streamlit_autorefresh import st_autorefresh
except:
    pass

if "refresh_count" not in st.session_state:
    st.session_state.refresh_count = 0

st_autorefresh(interval=5000, key="data_refresh")

# ---------- Load Responses (from DB placeholder) ----------
# Replace this with your Railway DB query
def load_responses(batch, subject, subtopic_id):
    # Example placeholder data (simulate DB query)
    data = [
        {"Student_ID": "1100-001", "Student_Name": "Vinayak Ambat", "Correct": 6, "Incorrect": 2},
        {"Student_ID": "1100-002", "Student_Name": "Rahul Patil", "Correct": 4, "Incorrect": 4},
        {"Student_ID": "1100-003", "Student_Name": "Sneha Kulkarni", "Correct": 7, "Incorrect": 1},
    ]
    return pd.DataFrame(data)

df = load_responses(batch, subject, subtopic_id)

if df.empty:
    st.info("No submissions yet.")
    st.stop()

# ---------- Visualization ----------
st.subheader("📈 Student Performance")

# Sort by total correct descending
df["Total"] = df["Correct"] + df["Incorrect"]
df = df.sort_values(by="Correct", ascending=False)

fig, ax = plt.subplots(figsize=(10, len(df) * 0.6))
ax.barh(df["Student_Name"], df["Correct"], color="#4CAF50", label="Correct")
ax.barh(df["Student_Name"], df["Incorrect"], left=df["Correct"], color="#E53935", label="Incorrect")

# Labels on bars
for i, (c, ic) in enumerate(zip(df["Correct"], df["Incorrect"])):
    ax.text(c / 2, i, str(c), va="center", ha="center", color="white", weight="bold")
    if ic > 0:
        ax.text(c + ic / 2, i, str(ic), va="center", ha="center", color="white", weight="bold")

ax.set_xlabel("Number of Questions")
ax.set_ylabel("Students")
ax.set_title(f"{subject} - {subtopic_id} Performance", fontsize=14, weight="bold")
ax.legend(loc="upper right")
st.pyplot(fig)

# ---------- Download CSV ----------
csv_bytes = df.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download CSV", csv_bytes, file_name=f"{batch}_{subtopic_id}_report.csv", mime="text/csv")

# ---------- Download PDF (placeholder) ----------
def build_pdf(df):
    buffer = io.BytesIO()
    # TODO: replace with real reportlab code
    buffer.write(b"PDF Report Placeholder")
    buffer.seek(0)
    return buffer.read()

pdf_bytes = build_pdf(df)
st.download_button("⬇️ Download PDF", pdf_bytes, file_name=f"{batch}_{subtopic_id}_report.pdf", mime="application/pdf")
