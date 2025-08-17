import streamlit as st

# --- Page Config ---
st.set_page_config(
    page_title="SSC English Grammar",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Sidebar ---
st.sidebar.title("🔧 Select Parameters")
board = st.sidebar.selectbox("Select Board", ["SSC", "ICSE"], index=0)
subject = st.sidebar.selectbox("Select Subject", ["Mathematics", "Science", "English", "Social Studies"], index=2)

# Spacer to push feedback button down
st.sidebar.markdown("<br><br><br><br><br><br><br><br><br><br>", unsafe_allow_html=True)

# --- Feedback Button ---
st.sidebar.link_button("📩 Feedback Form", "https://example.com/feedback-form")

# --- Main Title ---
st.title("📘 SSC Grade 10 English Grammar (2024–25)")
st.markdown("Use the sidebar to choose the board and subject. Below are grammar topics with linked assessments.")

# --- Function to Display Subtopics with Buttons ---
def show_subtopics(subtopics):
    for topic, links in subtopics.items():
        with st.expander(f"🔹 {topic}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                form_url = f"/form_page?subject=english&bank=ssc_english&subtopic_id={links['Form']}"
                st.link_button("📄 Open Form", form_url)
            with col2:
                st.link_button("🎯 Open Kahoot", links["Kahoot"])
            with col3:
                st.link_button("🎮 Open Blooket", links["Blooket"])

# --- Grammar Subtopics ---
if board == "SSC" and subject == "English":
    st.subheader("📚 Grammar Topics")
    subtopics = {
        "Tenses (Past, Present, Future)": {
            "Form": "tenses",
            "Kahoot": "https://example.com/kahoot-tenses",
            "Blooket": "https://example.com/blooket-tenses"
        },
        "Articles (a, an, the)": {
            "Form": "https://example.com/form-articles",
            "Kahoot": "https://example.com/kahoot-articles",
            "Blooket": "https://example.com/blooket-articles"
        },
        "Prepositions": {
            "Form": "https://example.com/form-prepositions",
            "Kahoot": "https://example.com/kahoot-prepositions",
            "Blooket": "https://example.com/blooket-prepositions"
        },
        "Conjunctions": {
            "Form": "https://example.com/form-conjunctions",
            "Kahoot": "https://example.com/kahoot-conjunctions",
            "Blooket": "https://example.com/blooket-conjunctions"
        },
        "Transformation of Sentences": {
            "Form": "https://example.com/form-transformations",
            "Kahoot": "https://example.com/kahoot-transformations",
            "Blooket": "https://example.com/blooket-transformations"
        },
        "Reported Speech (Direct / Indirect)": {
            "Form": "https://example.com/form-reported",
            "Kahoot": "https://example.com/kahoot-reported",
            "Blooket": "https://example.com/blooket-reported"
        },
        "Degrees of Comparison": {
            "Form": "https://example.com/form-degrees",
            "Kahoot": "https://example.com/kahoot-degrees",
            "Blooket": "https://example.com/blooket-degrees"
        },
        "Voice (Active & Passive)": {
            "Form": "https://example.com/form-voice",
            "Kahoot": "https://example.com/kahoot-voice",
            "Blooket": "https://example.com/blooket-voice"
        },
        "Subject-Verb Agreement": {
            "Form": "https://example.com/form-agreement",
            "Kahoot": "https://example.com/kahoot-agreement",
            "Blooket": "https://example.com/blooket-agreement"
        },
        "Punctuation": {
            "Form": "https://example.com/form-punctuation",
            "Kahoot": "https://example.com/kahoot-punctuation",
            "Blooket": "https://example.com/blooket-punctuation"
        },
        "Question Tags": {
            "Form": "https://example.com/form-questiontags",
            "Kahoot": "https://example.com/kahoot-questiontags",
            "Blooket": "https://example.com/blooket-questiontags"
        },
        "Homophones & Homonyms": {
            "Form": "https://example.com/form-homophones",
            "Kahoot": "https://example.com/kahoot-homophones",
            "Blooket": "https://example.com/blooket-homophones"
        },
        "Common Errors in English": {
            "Form": "https://example.com/form-errors",
            "Kahoot": "https://example.com/kahoot-errors",
            "Blooket": "https://example.com/blooket-errors"
        }
    }

    show_subtopics(subtopics)
else:
    st.info("Please select SSC Board and English subject to view grammar topics.")




