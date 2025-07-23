import streamlit as st

# ------------------------ Page Config ------------------------
st.set_page_config(
    page_title="Grade 10 Assessment Hub",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------ Sidebar ------------------------
st.sidebar.title("🔧 Select Options")
board = st.sidebar.selectbox("Select Board", ["SSC", "ICSE"])
subject = st.sidebar.selectbox("Select Subject", ["Mathematics", "Science", "English", "Social Studies"])
st.sidebar.markdown("""
---
📬 **[Feedback Form](https://forms.gle/your-feedback-form)**
""")

# ------------------------ Main Page ------------------------
st.title("📘 Grade 10 Assessment Web App")
st.markdown("""
Welcome to the Grade 10 Assessment Platform. Select a board and subject from the sidebar to begin.

Use the navigation in the sidebar to access subject-wise assessments, tools, and subtopics.
""")

# ------------------------ Page Guide ------------------------
if board == "SSC":
    if subject == "Mathematics":
        st.markdown("👉 Go to **SSC_Maths** page in the sidebar for Algebra and Geometry assessments.")
    elif subject == "Science":
        st.markdown("👉 Go to **SSC_Science** page for Physics, Chemistry and Biology.")
    elif subject == "English":
        st.markdown("👉 Go to **SSC_English** page for Grammar and Language Tools.")
    elif subject == "Social Studies":
        st.markdown("👉 Go to **SSC_Social_Studies** page for History and Geography.")

elif board == "ICSE":
    if subject == "Mathematics":
        st.markdown("👉 Go to **ICSE_Maths** page in the sidebar for Algebra and Geometry assessments.")
    elif subject == "Science":
        st.markdown("👉 Go to **ICSE_Science** page for Physics, Chemistry and Biology.")
    elif subject == "English":
        st.markdown("👉 Go to **ICSE_English** page for Grammar and Language Tools.")
    elif subject == "Social Studies":
        st.markdown("👉 Go to **ICSE_Social_Studies** page for History and Geography.")
