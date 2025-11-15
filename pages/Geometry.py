import streamlit as st
from collections import defaultdict

# ------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------
st.set_page_config(
    page_title="SSC Geometry",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------
# HOME BUTTON (TOP LEFT)
# ------------------------------------------------------------
st.page_link("Home.py", label="🏠 Home", icon="↩️")

# ------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------
st.sidebar.title("🔧 Select Parameters")

board = st.sidebar.selectbox("Select Board", ["SSC", "ICSE"], index=0)
subject = st.sidebar.selectbox("Select Subject", ["Mathematics", "Science", "English"], index=0)

st.sidebar.markdown("<br><br><br><br><br><br><br><br>", unsafe_allow_html=True)
st.sidebar.link_button("📩 Feedback Form", "https://example.com/feedback-form")

# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------
st.title("📘 SSC Grade 10 Geometry (2024–25)")
st.markdown("Below are chapter-wise practice sets with linked assessments.")

# ------------------------------------------------------------
# RAW GEOMETRY DATA
# ------------------------------------------------------------
data = [
    ("One", "Similarity", "Practice_Set-1.2"),
    ("One", "Similarity", "Practice_Set-1.3"),
    ("One", "Similarity", "Practice_Set-1.4"),
    ("Two", "Pythagoras Theorem", "Practice_Set-2.1"),
    ("Two", "Pythagoras Theorem", "Practice_Set-2.2"),
    ("Three", "Circle", "Practice_Set-3.1"),
    ("Three", "Circle", "Practice_Set-3.2"),
    ("Three", "Circle", "Practice_Set-3.3"),
    ("Three", "Circle", "Practice_Set-3.4"),
    ("Three", "Circle", "Practice_Set-3.5"),
    ("Five", "Co-ordinate Geometry", "Practice_Set-5.1"),
    ("Five", "Co-ordinate Geometry", "Practice_Set-5.2"),
    ("Five", "Co-ordinate Geometry", "Practice_Set-5.3"),
    ("Six", "Trigonometry", "Practice_Set-6.0"),
    ("Six", "Trigonometry", "Practice_Set-6.1"),
    ("Six", "Trigonometry", "Practice_Set-6.2"),
    ("Seven", "Mensuration", "Practice_Set-7.1"),
    ("Seven", "Mensuration", "Practice_Set-7.3"),
    ("Seven", "Mensuration", "Practice_Set-7.4"),
]

# ------------------------------------------------------------
# GROUP DATA
# ------------------------------------------------------------
chapters = defaultdict(list)
for chap_num, chap_name, practice in data:
    chapters[chap_name].append(practice)

# ------------------------------------------------------------
# DISPLAY CHAPTER BOXES
# ------------------------------------------------------------
if board == "SSC" and subject == "Mathematics":
    st.subheader("📚 Geometry Chapters")

    for chapter_name, practice_sets in chapters.items():
        with st.container(border=True):
            st.markdown(f"### 📘 {chapter_name}")

            for ps in sorted(practice_sets):
                with st.expander(f"📝 {ps.replace('_', ' ')}"):

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.link_button("📄 Form", f"/form_page?chapter={chapter_name}&ps={ps}")
                    with col2:
                        st.link_button("🎯 Kahoot", "https://example.com/kahoot")
                    with col3:
                        st.link_button("🎮 Blooket", "https://example.com/blooket")

else:
    st.info("Please select SSC Board and Mathematics subject to view Geometry content.")
