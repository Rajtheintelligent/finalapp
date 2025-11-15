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
# HOME BUTTON
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
# RAW GEOMETRY DATA (STATIC)
# ------------------------------------------------------------
@st.cache_data
def load_geometry_structure():
    return [
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
    ]

raw_data = load_geometry_structure()

# ------------------------------------------------------------
# GROUP DATA BY CHAPTERS
# ------------------------------------------------------------
chapters = defaultdict(list)

for chap_num, chap_name, practice in raw_data:
    chapters[chap_name].append(practice)

# ------------------------------------------------------------
# CHECK LINKS STORAGE
# ------------------------------------------------------------
if "geometry_links" not in st.session_state:
    st.warning("⚠️ No saved links found. Please visit the Geometry Link Manager page.")
    st.stop()

stored_links = st.session_state.geometry_links

# ------------------------------------------------------------
# RENDER CHAPTERS
# ------------------------------------------------------------
if board == "SSC" and subject == "Mathematics":
    st.subheader("📚 Geometry Chapters")

    for chapter_name, practice_sets in chapters.items():

        with st.container(border=True):
            st.markdown(f"### 📘 {chapter_name}")

            for ps in sorted(practice_sets):

                with st.expander(f"📝 {ps.replace('_',' ')}"):

                    links = stored_links.get(ps, {"Form": "", "Kahoot": "", "Blooket": ""})

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.link_button("📄 Form", links["Form"])
                    with col2:
                        st.link_button("🎯 Kahoot", links["Kahoot"])
                    with col3:
                        st.link_button("🎮 Blooket", links["Blooket"])

else:
    st.info("Please select SSC Board and Mathematics subject to view Geometry content.")
