import streamlit as st

# --- Page Config ---
st.set_page_config(
    page_title="ICSE English Grammar",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Sidebar ---
st.sidebar.title("🔧 Select Parameters")
board = st.sidebar.selectbox("Select Board", ["SSC", "ICSE"], index=1)
subject = st.sidebar.selectbox("Select Subject", ["Mathematics", "Science", "English", "Social Studies"], index=2)

# Feedback
st.sidebar.markdown("<br><br><br><br><br><br><br><br>", unsafe_allow_html=True)
st.sidebar.link_button("📩 Feedback Form", "https://example.com/feedback-form")

# --- Main Content ---
st.title("📘 ICSE Grade 10 English Grammar (2024–25)")
st.markdown("Below is the complete grammar syllabus for ICSE Grade 10 with interactive resources.")

# Function to Display Subtopics
def show_subtopics(subtopics):
    for topic, links in subtopics.items():
        with st.expander(f"🔹 {topic}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.link_button("📄 Form", links["Form"])
            with col2:
                st.link_button("🎯 Kahoot", links["Kahoot"])
            with col3:
                st.link_button("🎮 Blooket", links["Blooket"])

# --- Subtopics Dictionary ---
if board == "ICSE" and subject == "English":
    subtopics = {
        "Tenses – Present, Past, Future (All Forms)": {
            "Form": "https://example.com/form-tenses",
            "Kahoot": "https://example.com/kahoot-tenses",
            "Blooket": "https://example.com/blooket-tenses"
        },
        "Subject-Verb Agreement (Concord)": {
            "Form": "https://example.com/form-concord",
            "Kahoot": "https://example.com/kahoot-concord",
            "Blooket": "https://example.com/blooket-concord"
        },
        "Transformation of Sentences (Assertive, Interrogative, Exclamatory)": {
            "Form": "https://example.com/form-transformations",
            "Kahoot": "https://example.com/kahoot-transformations",
            "Blooket": "https://example.com/blooket-transformations"
        },
        "Degrees of Comparison": {
            "Form": "https://example.com/form-comparison",
            "Kahoot": "https://example.com/kahoot-comparison",
            "Blooket": "https://example.com/blooket-comparison"
        },
        "Voice – Active and Passive": {
            "Form": "https://example.com/form-voice",
            "Kahoot": "https://example.com/kahoot-voice",
            "Blooket": "https://example.com/blooket-voice"
        },
        "Reported Speech – Direct and Indirect": {
            "Form": "https://example.com/form-speech",
            "Kahoot": "https://example.com/kahoot-speech",
            "Blooket": "https://example.com/blooket-speech"
        },
        "Prepositions (Types and Usage)": {
            "Form": "https://example.com/form-prepositions",
            "Kahoot": "https://example.com/kahoot-prepositions",
            "Blooket": "https://example.com/blooket-prepositions"
        },
        "Conjunctions – Coordinating, Subordinating": {
            "Form": "https://example.com/form-conjunctions",
            "Kahoot": "https://example.com/kahoot-conjunctions",
            "Blooket": "https://example.com/blooket-conjunctions"
        },
        "Articles – A, An, The": {
            "Form": "https://example.com/form-articles",
            "Kahoot": "https://example.com/kahoot-articles",
            "Blooket": "https://example.com/blooket-articles"
        },
        "Modals and Auxiliaries (Can, Could, Must, Should...)": {
            "Form": "https://example.com/form-modals",
            "Kahoot": "https://example.com/kahoot-modals",
            "Blooket": "https://example.com/blooket-modals"
        },
        "Phrasal Verbs (Common Usage)": {
            "Form": "https://example.com/form-phrasal",
            "Kahoot": "https://example.com/kahoot-phrasal",
            "Blooket": "https://example.com/blooket-phrasal"
        },
        "Punctuation (Full Stop, Comma, Quotes...)": {
            "Form": "https://example.com/form-punctuation",
            "Kahoot": "https://example.com/kahoot-punctuation",
            "Blooket": "https://example.com/blooket-punctuation"
        },
        "Sentence Rewriting / Do as Directed": {
            "Form": "https://example.com/form-do-as-directed",
            "Kahoot": "https://example.com/kahoot-do-as-directed",
            "Blooket": "https://example.com/blooket-do-as-directed"
        },
        "Homophones / Homonyms": {
            "Form": "https://example.com/form-homophones",
            "Kahoot": "https://example.com/kahoot-homophones",
            "Blooket": "https://example.com/blooket-homophones"
        },
        "Common Errors in Grammar": {
            "Form": "https://example.com/form-errors",
            "Kahoot": "https://example.com/kahoot-errors",
            "Blooket": "https://example.com/blooket-errors"
        },
        "Combining / Synthesis of Sentences": {
            "Form": "https://example.com/form-synthesis",
            "Kahoot": "https://example.com/kahoot-synthesis",
            "Blooket": "https://example.com/blooket-synthesis"
        },
        "Sentence Reordering / Jumbled Sentences": {
            "Form": "https://example.com/form-reordering",
            "Kahoot": "https://example.com/kahoot-reordering",
            "Blooket": "https://example.com/blooket-reordering"
        }
    }

    show_subtopics(subtopics)

else:
    st.info("Please select ICSE Board and English subject to view grammar topics.")
