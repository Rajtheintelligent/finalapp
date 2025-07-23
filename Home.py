import streamlit as st

# --- Page Config ---
st.set_page_config(
    page_title="Education Hub - Home",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Sidebar ---
st.sidebar.title("🔧 Select Parameters")
board = st.sidebar.selectbox("Select Board", ["SSC", "ICSE"])
subject = st.sidebar.selectbox("Select Subject", ["Mathematics", "Science", "English", "Social Studies"])

# Spacer
st.sidebar.markdown("<br><br><br><br><br><br><br><br><br><br><br>", unsafe_allow_html=True)

# --- Feedback Button ---
st.sidebar.link_button("📩 Feedback Form", "https://example.com/feedback-form")

# --- Main Area ---
st.title("📘 Welcome to the Smart Learning Hub")
st.markdown("Choose your Board and Subject from the sidebar to begin learning and testing your knowledge.")

# --- Navigation Buttons ---
st.subheader("➡️ Navigate to Your Subject Page")

if board == "SSC":
    if subject == "Mathematics":
        st.page_link("pages/SSC_Maths.py", label="📗 Go to SSC Mathematics", icon="📐")
    elif subject == "Science":
        st.page_link("pages/SSC_Science.py", label="🔬 Go to SSC Science", icon="🧪")
    else:
        st.info(f"🚧 {subject} for SSC is coming soon!")

elif board == "ICSE":
    if subject == "Mathematics":
        st.page_link("pages/ICSE_Maths.py", label="📗 Go to ICSE Mathematics", icon="🧮")
    elif subject == "Science":
        st.page_link("pages/ICSE_Science.py", label="🔬 Go to ICSE Science", icon="🧪")
    else:
        st.info(f"🚧 {subject} for ICSE is coming soon!")

else:
    st.warning("Please select both Board and Subject to proceed.")
