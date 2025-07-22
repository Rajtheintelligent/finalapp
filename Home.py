import streamlit as st

# --- Page Config ---
st.set_page_config(
    page_title="Grade 10 Assessment Hub",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Sidebar Navigation ---
st.sidebar.title("🔧 Select Parameters")

board = st.sidebar.selectbox("Select Board", ["SSC", "ICSE"])
subject = st.sidebar.selectbox("Select Subject", ["Mathematics", "Science", "English", "Social Studies"])

# Spacer to push feedback button to the bottom
st.sidebar.markdown("<br>" * 10, unsafe_allow_html=True)

# --- Feedback Button at Bottom ---
st.sidebar.link_button("📩 Feedback Form", "https://example.com/feedback-form")

# --- Main Title ---
st.title("🎓 Grade 10 Assessment Hub")
st.markdown("Welcome to the Assessment Hub! Use the sidebar to choose a board and subject to navigate to the assessments.")

# --- Button to Navigate to Pages ---
if st.button("Go to Selected Page"):
    # Logic to switch pages
    if board == "SSC":
        if subject == "Mathematics":
            st.switch_page("pages/SSC_Maths.py")
        elif subject == "Science":
            st.switch_page("pages/SSC_Science.py")
        elif subject == "English":
            st.switch_page("pages/SSC_English.py")
        elif subject == "Social Studies":
            st.switch_page("pages/SSC_Social_Studies.py")

    elif board == "ICSE":
        if subject == "Mathematics":
            st.switch_page("pages/ICSE_Maths.py")
        elif subject == "Science":
            st.switch_page("pages/ICSE_Science.py")
        elif subject == "English":
            st.switch_page("pages/ICSE_English.py")
        elif subject == "Social Studies":
            st.switch_page("pages/ICSE_Social_Studies.py")
