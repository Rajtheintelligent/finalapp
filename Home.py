import streamlit as st

st.set_page_config(
    page_title="EduApp Home",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.sidebar.title("📚 Subject Navigation")

# --- SSC Section ---
st.sidebar.markdown("### 📘 SSC Subjects")
st.sidebar.page_link("pages/SSC_English.py", label="SSC English")
st.sidebar.page_link("pages/SSC_Maths.py", label="SSC Maths")
st.sidebar.page_link("pages/SSC_Science.py", label="SSC Science")

# Spacer
st.sidebar.markdown(" ")

# --- ICSE Section ---
st.sidebar.markdown("### 📙 ICSE Subjects")
st.sidebar.page_link("pages/ICSE_English.py", label="ICSE English")
st.sidebar.page_link("pages/ICSE_Maths.py", label="ICSE Maths")
st.sidebar.page_link("pages/ICSE_Science.py", label="ICSE Science")

# --- Feedback Button ---
st.sidebar.markdown("---")
st.sidebar.link_button("📩 Feedback Form", "https://example.com/feedback-form")
