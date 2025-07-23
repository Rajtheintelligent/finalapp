
import streamlit as st

# --- Page Config ---
st.set_page_config(
    page_title="ICSE Science",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Sidebar ---
st.sidebar.title("🔧 Select Parameters")
board = st.sidebar.selectbox("Select Board", ["SSC", "ICSE"], index=1)
subject = st.sidebar.selectbox("Select Subject", ["Mathematics", "Science", "English", "Social Studies"], index=1)

branch = None
if board == "ICSE" and subject == "Science":
    branch = st.sidebar.selectbox("Select Branch", ["Physics", "Chemistry", "Biology"])

# Spacer
st.sidebar.markdown("<br><br><br><br><br><br><br><br><br><br><br>", unsafe_allow_html=True)

# Feedback
st.sidebar.link_button("📩 Feedback Form", "https://example.com/feedback-form")

# --- Main Page ---
st.title("📘 ICSE Grade 10 Science Syllabus (2024–25)")
st.markdown("Use the sidebar to select the board, subject, and branch to view relevant topics.")

def show_subtopics(subtopics):
    for topic, links in subtopics.items():
        with st.expander(f"🔹 {topic}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.link_button("Open Form", links["Form"])
            with col2:
                st.link_button("Open Kahoot", links["Kahoot"])
            with col3:
                st.link_button("Open Blooket", links["Blooket"])

if board == "ICSE" and subject == "Science":
    if branch == "Physics":
        chapter = st.selectbox("Select Chapter", [
            "Force, Work, Power and Energy", "Light", "Sound", "Electricity and Magnetism", "Heat", "Modern Physics"
        ])

        subtopics = {}
        if chapter == "Force, Work, Power and Energy":
            subtopics = {
                "Turning Forces & Energy": {
                    "Form": "https://example.com/form-force",
                    "Kahoot": "https://example.com/kahoot-force",
                    "Blooket": "https://example.com/blooket-force"
                }
            }
        elif chapter == "Light":
            subtopics = {
                "Lenses, Refraction, Prism": {
                    "Form": "https://example.com/form-light",
                    "Kahoot": "https://example.com/kahoot-light",
                    "Blooket": "https://example.com/blooket-light"
                }
            }
        elif chapter == "Sound":
            subtopics = {
                "Reflection, Vibrations, Resonance": {
                    "Form": "https://example.com/form-sound",
                    "Kahoot": "https://example.com/kahoot-sound",
                    "Blooket": "https://example.com/blooket-sound"
                }
            }
        elif chapter == "Electricity and Magnetism":
            subtopics = {
                "Circuits, Ohm’s Law, Household Electricity": {
                    "Form": "https://example.com/form-electricity",
                    "Kahoot": "https://example.com/kahoot-electricity",
                    "Blooket": "https://example.com/blooket-electricity"
                }
            }
        elif chapter == "Heat":
            subtopics = {
                "Calorimetry & Mixtures": {
                    "Form": "https://example.com/form-heat",
                    "Kahoot": "https://example.com/kahoot-heat",
                    "Blooket": "https://example.com/blooket-heat"
                }
            }
        elif chapter == "Modern Physics":
            subtopics = {
                "Radioactivity & Nuclear Safety": {
                    "Form": "https://example.com/form-modern",
                    "Kahoot": "https://example.com/kahoot-modern",
                    "Blooket": "https://example.com/blooket-modern"
                }
            }
        show_subtopics(subtopics)
