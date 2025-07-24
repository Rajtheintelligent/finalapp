
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
    elif branch == "Chemistry":
        chapter = st.selectbox("Select Chapter", [
            "Periodic Table",
            "Chemical Bonding",
            "Acids, Bases and Salts",
            "Analytical Chemistry",
            "Mole Concept and Stoichiometry",
            "Electrolysis",
            "Metallurgy",
            "Study of Compounds"
        ])

        subtopics = {}

        if chapter == "Periodic Table":
            subtopics = {
                "Modern Periodic Law and Table": {
                    "Form": "https://example.com/form-periodic",
                    "Kahoot": "https://example.com/kahoot-periodic",
                    "Blooket": "https://example.com/blooket-periodic"
                }
            }

        elif chapter == "Chemical Bonding":
            subtopics = {
                "Types of Bonds (Ionic, Covalent)": {
                    "Form": "https://example.com/form-bonding",
                    "Kahoot": "https://example.com/kahoot-bonding",
                    "Blooket": "https://example.com/blooket-bonding"
                }
            }

        elif chapter == "Acids, Bases and Salts":
            subtopics = {
                "pH, Properties & Reactions": {
                    "Form": "https://example.com/form-acidbase",
                    "Kahoot": "https://example.com/kahoot-acidbase",
                    "Blooket": "https://example.com/blooket-acidbase"
                }
            }

        elif chapter == "Analytical Chemistry":
            subtopics = {
                "Flame Test & Precipitation": {
                    "Form": "https://example.com/form-analytical",
                    "Kahoot": "https://example.com/kahoot-analytical",
                    "Blooket": "https://example.com/blooket-analytical"
                }
            }

        elif chapter == "Mole Concept and Stoichiometry":
            subtopics = {
                "Avogadro’s Law & Calculations": {
                    "Form": "https://example.com/form-mole",
                    "Kahoot": "https://example.com/kahoot-mole",
                    "Blooket": "https://example.com/blooket-mole"
                }
            }

        elif chapter == "Electrolysis":
            subtopics = {
                "Electrolytic Cells & Reactions": {
                    "Form": "https://example.com/form-electrolysis",
                    "Kahoot": "https://example.com/kahoot-electrolysis",
                    "Blooket": "https://example.com/blooket-electrolysis"
                }
            }

        elif chapter == "Metallurgy":
            subtopics = {
                "Extraction & Alloys": {
                    "Form": "https://example.com/form-metallurgy",
                    "Kahoot": "https://example.com/kahoot-metallurgy",
                    "Blooket": "https://example.com/blooket-metallurgy"
                }
            }

        elif chapter == "Study of Compounds":
            subtopics = {
                "Ammonia & Nitric Acid": {
                    "Form": "https://example.com/form-compounds1",
                    "Kahoot": "https://example.com/kahoot-compounds1",
                    "Blooket": "https://example.com/blooket-compounds1"
                },
                "Sulphuric Acid & Organic Chemistry": {
                    "Form": "https://example.com/form-compounds2",
                    "Kahoot": "https://example.com/kahoot-compounds2",
                    "Blooket": "https://example.com/blooket-compounds2"
                }
            }

        show_subtopics(subtopics)
    elif branch == "Biology":
        chapter = st.selectbox("Select Chapter", [
            "Basic Biology",
            "Plant Physiology",
            "Human Anatomy and Physiology",
            "Health and Hygiene",
            "Waste Generation and Management"
        ])

        subtopics = {}

        if chapter == "Basic Biology":
            st.subheader("📗 Basic Biology")
            subtopics = {
                "Cell Cycle and Cell Division": {
                    "Form": "https://example.com/form-cell-cycle",
                    "Kahoot": "https://example.com/kahoot-cell-cycle",
                    "Blooket": "https://example.com/blooket-cell-cycle"
                },
                "Structure of Chromosomes, DNA & Genes": {
                    "Form": "https://example.com/form-dna",
                    "Kahoot": "https://example.com/kahoot-dna",
                    "Blooket": "https://example.com/blooket-dna"
                }
            }

        elif chapter == "Plant Physiology":
            st.subheader("📗 Plant Physiology")
            subtopics = {
                "Photosynthesis": {
                    "Form": "https://example.com/form-photosynthesis",
                    "Kahoot": "https://example.com/kahoot-photosynthesis",
                    "Blooket": "https://example.com/blooket-photosynthesis"
                },
                "Transpiration": {
                    "Form": "https://example.com/form-transpiration",
                    "Kahoot": "https://example.com/kahoot-transpiration",
                    "Blooket": "https://example.com/blooket-transpiration"
                }
            }

        elif chapter == "Human Anatomy and Physiology":
            st.subheader("📗 Human Anatomy and Physiology")
            subtopics = {
                "Circulatory System": {
                    "Form": "https://example.com/form-circulatory",
                    "Kahoot": "https://example.com/kahoot-circulatory",
                    "Blooket": "https://example.com/blooket-circulatory"
                },
                "Excretory System": {
                    "Form": "https://example.com/form-excretory",
                    "Kahoot": "https://example.com/kahoot-excretory",
                    "Blooket": "https://example.com/blooket-excretory"
                },
                "Nervous System": {
                    "Form": "https://example.com/form-nervous",
                    "Kahoot": "https://example.com/kahoot-nervous",
                    "Blooket": "https://example.com/blooket-nervous"
                },
                "Endocrine System": {
                    "Form": "https://example.com/form-endocrine",
                    "Kahoot": "https://example.com/kahoot-endocrine",
                    "Blooket": "https://example.com/blooket-endocrine"
                },
                "Reproductive System": {
                    "Form": "https://example.com/form-reproductive",
                    "Kahoot": "https://example.com/kahoot-reproductive",
                    "Blooket": "https://example.com/blooket-reproductive"
                }
            }

        elif chapter == "Health and Hygiene":
            st.subheader("📗 Health and Hygiene")
            subtopics = {
                "AIDS and STD Awareness": {
                    "Form": "https://example.com/form-aids-std",
                    "Kahoot": "https://example.com/kahoot-aids-std",
                    "Blooket": "https://example.com/blooket-aids-std"
                },
                "Personal and Public Hygiene": {
                    "Form": "https://example.com/form-hygiene",
                    "Kahoot": "https://example.com/kahoot-hygiene",
                    "Blooket": "https://example.com/blooket-hygiene"
                }
            }

        elif chapter == "Waste Generation and Management":
            st.subheader("📗 Waste Generation and Management")
            subtopics = {
                "Biodegradable vs Non-biodegradable Waste": {
                    "Form": "https://example.com/form-waste-types",
                    "Kahoot": "https://example.com/kahoot-waste-types",
                    "Blooket": "https://example.com/blooket-waste-types"
                },
                "Eco-Friendly Waste Disposal Methods": {
                    "Form": "https://example.com/form-waste-disposal",
                    "Kahoot": "https://example.com/kahoot-waste-disposal",
                    "Blooket": "https://example.com/blooket-waste-disposal"
                }
            }

        show_subtopics(subtopics)

