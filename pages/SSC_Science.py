import streamlit as st

# --- Page Config ---
st.set_page_config(
    page_title="SSC Science",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Sidebar ---
st.sidebar.title("🔧 Select Parameters")
board = st.sidebar.selectbox("Select Board", ["SSC", "ICSE"], index=0)
subject = st.sidebar.selectbox("Select Subject", ["Mathematics", "Science", "English", "Social Studies"], index=1)

branch = None
if board == "SSC" and subject == "Science":
    branch = st.sidebar.selectbox("Select Branch", ["Science Part 1: Physics & Chemistry", "Science Part 2: Biology & Environmental Science"])

# Spacer
st.sidebar.markdown("<br><br><br><br><br><br><br><br><br><br><br>", unsafe_allow_html=True)

# Feedback
st.sidebar.link_button("📩 Feedback Form", "https://example.com/feedback-form")

# --- Main Page ---
st.title("📘 SSC Maharashtra Class 10 Science Syllabus")
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

if board == "SSC" and subject == "Science":
    if branch == "Science Part 1: Physics & Chemistry":
        chapter = st.selectbox("Select Chapter", [
            "Gravitation", "Periodic Classification of Elements", "Chemical Reactions and Equations",
            "Effects of Electric Current", "Heat", "Refraction of Light", "Lenses"
        ])

        if chapter == "Gravitation":
            subtopics = {
                "Newton's Law, Gravity & Free Fall": {
                    "Form": "https://example.com/form-gravitation",
                    "Kahoot": "https://example.com/kahoot-gravitation",
                    "Blooket": "https://example.com/blooket-gravitation"
                },
                "Acceleration due to Gravity": {
                    "Form": "https://example.com/form-gravitation",
                    "Kahoot": "https://example.com/kahoot-gravitation",
                    "Blooket": "https://example.com/blooket-gravitation"
                }
            }
        elif chapter == "Periodic Classification of Elements":
            subtopics = {
                "Mendeleev & Modern Table": {
                    "Form": "https://example.com/form-periodic",
                    "Kahoot": "https://example.com/kahoot-periodic",
                    "Blooket": "https://example.com/blooket-periodic"
                }
            }
        elif chapter == "Chemical Reactions and Equations":
            subtopics = {
                "Types, Balancing & Oxidation": {
                    "Form": "https://example.com/form-chemical",
                    "Kahoot": "https://example.com/kahoot-chemical",
                    "Blooket": "https://example.com/blooket-chemical"
                }
            }
        elif chapter == "Effects of Electric Current":
            subtopics = {
                "Ohm’s Law & Magnetic Effects": {
                    "Form": "https://example.com/form-electric",
                    "Kahoot": "https://example.com/kahoot-electric",
                    "Blooket": "https://example.com/blooket-electric"
                }
            }
        elif chapter == "Heat":
            subtopics = {
                "Transfer, Specific Heat, Expansion": {
                    "Form": "https://example.com/form-heat",
                    "Kahoot": "https://example.com/kahoot-heat",
                    "Blooket": "https://example.com/blooket-heat"
                }
            }
        elif chapter == "Refraction of Light":
            subtopics = {
                "Refraction Laws & Lenses": {
                    "Form": "https://example.com/form-refraction",
                    "Kahoot": "https://example.com/kahoot-refraction",
                    "Blooket": "https://example.com/blooket-refraction"
                }
            }
        elif chapter == "Lenses":
            subtopics = {
                "Convex/Concave, Ray Diagrams": {
                    "Form": "https://example.com/form-lenses",
                    "Kahoot": "https://example.com/kahoot-lenses",
                    "Blooket": "https://example.com/blooket-lenses"
                }
            }

        show_subtopics(subtopics)

    elif branch == "Science Part 2: Biology & Environmental Science":
        chapter = st.selectbox("Select Chapter", [
            "Heredity and Evolution", "Life Processes – Part 1", "Life Processes – Part 2",
            "Environmental Management", "Towards Green Energy", "Animal Classification",
            "Introduction to Microbiology", "Cell Biology and Biotechnology"
        ])

        if chapter == "Heredity and Evolution":
            subtopics = {
                "Mendel’s Laws & Human Evolution": {
                    "Form": "https://example.com/form-heredity",
                    "Kahoot": "https://example.com/kahoot-heredity",
                    "Blooket": "https://example.com/blooket-heredity"
                }
            }
        elif chapter == "Life Processes – Part 1":
            subtopics = {
                "Nutrition, Respiration, Excretion": {
                    "Form": "https://example.com/form-life1",
                    "Kahoot": "https://example.com/kahoot-life1",
                    "Blooket": "https://example.com/blooket-life1"
                }
            }
        elif chapter == "Life Processes – Part 2":
            subtopics = {
                "Nervous & Endocrine Systems": {
                    "Form": "https://example.com/form-life2",
                    "Kahoot": "https://example.com/kahoot-life2",
                    "Blooket": "https://example.com/blooket-life2"
                }
            }
        elif chapter == "Environmental Management":
            subtopics = {
                "Ecosystem, Problems & Solutions": {
                    "Form": "https://example.com/form-environment",
                    "Kahoot": "https://example.com/kahoot-environment",
                    "Blooket": "https://example.com/blooket-environment"
                }
            }
        elif chapter == "Towards Green Energy":
            subtopics = {
                "Energy Sources & Efficiency": {
                    "Form": "https://example.com/form-energy",
                    "Kahoot": "https://example.com/kahoot-energy",
                    "Blooket": "https://example.com/blooket-energy"
                }
            }
        elif chapter == "Animal Classification":
            subtopics = {
                "Phyla, Symmetry, Examples": {
                    "Form": "https://example.com/form-classification",
                    "Kahoot": "https://example.com/kahoot-classification",
                    "Blooket": "https://example.com/blooket-classification"
                }
            }
        elif chapter == "Introduction to Microbiology":
            subtopics = {
                "Beneficial & Harmful Microbes": {
                    "Form": "https://example.com/form-microbes",
                    "Kahoot": "https://example.com/kahoot-microbes",
                    "Blooket": "https://example.com/blooket-microbes"
                }
            }
        elif chapter == "Cell Biology and Biotechnology":
            subtopics = {
                "DNA, Chromosomes & Uses": {
                    "Form": "https://example.com/form-biotech",
                    "Kahoot": "https://example.com/kahoot-biotech",
                    "Blooket": "https://example.com/blooket-biotech"
                }
            }

        show_subtopics(subtopics)

else:
    st.info("Please select 'Science' as the subject under SSC Board to view content.")
