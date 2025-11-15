import streamlit as st

# ------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------
st.set_page_config(
    page_title="SSC English Grammar",
    layout="wide"
)

# ------------------------------------------------------------
# HOME NAVIGATION
# ------------------------------------------------------------
st.page_link("Home.py", label="🏠 Home", icon="↩️")

# ------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------
st.sidebar.title("🔧 Select Parameters")
board = st.sidebar.selectbox("Board", ["SSC", "ICSE"], index=0)
subject = st.sidebar.selectbox("Subject", ["Mathematics", "Science", "English"], index=2)

# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------
st.title("📚 SSC Grade 10 — English Grammar")
st.markdown("Each box below is a main topic. Click a topic to expand its subtopics and open the Form link. Paste your Form URLs in the `links` dictionary.")

# ------------------------------------------------------------
# ---- MANUAL LINK ENTRY SECTION (EDIT THESE) ----
# ------------------------------------------------------------
# Only 'Form' is used for English grammar (no Kahoot or Blooket).
# Keys: ChapterName -> SubTopic -> {Form}

links = {
    "Noun": {
        "Common_Noun": {"Form": ""},
        "Collective_Noun": {"Form": ""},
        "Proper_Noun": {"Form": ""},
        "Abstract_Noun": {"Form": ""},
        "Material_Noun": {"Form": ""},
        "Countable_Noun": {"Form": ""},
        "Uncountable_Noun": {"Form": ""},
        "Singular_Noun": {"Form": ""},
        "Plural_Noun": {"Form": ""},
        "Gender_Noun": {"Form": ""},
        "Subjective_Noun": {"Form": ""},
        "Objective_Noun": {"Form": ""},
        "Possesive_Noun": {"Form": ""},
    },

    "Pronoun": {
        "Personal_Pronoun": {"Form": ""},
        "Reflexive_Pronoun": {"Form": ""},
        "Demonstrative_Pronoun": {"Form": ""},
        "Interrogative_Pronoun": {"Form": ""},
        "Relative_Pronoun": {"Form": ""},
        "Indefinite_Pronoun": {"Form": ""},
        "Distributive_Pronoun": {"Form": ""},
        "Reciprocal_Pronoun": {"Form": ""},
        "Possessive_Pronoun": {"Form": ""},
    },

    "Verb": {
        "Main_Verb": {"Form": ""},
        "Auxillary_Verb": {"Form": ""},
        "Transitive_Verb": {"Form": ""},
        "Intransitive_Verb": {"Form": ""},
        "Finite_Verb": {"Form": ""},
        "infinitives": {"Form": ""},
        "Participle": {"Form": ""},
        "Gerund": {"Form": ""},
        "Regular_Verb": {"Form": ""},
        "Irregular_Verb": {"Form": ""},
        "Linking_Verbs": {"Form": ""},
        "Phrasal_Verbs": {"Form": ""},
        "Can_Verb": {"Form": ""},
        "Could_Verb": {"Form": ""},
        "May_Verb": {"Form": ""},
        "Must_Verb": {"Form": ""},
    },

    "Adjective": {
        "Discriptive_and_Quantitative": {"Form": ""},
        "Demonstrative_and_Interragative": {"Form": ""},
        "Adjectives": {"Form": ""},
        "Degrees_of_Comparison": {"Form": ""},
        "Ofder_of_Adjectives": {"Form": ""},
    },

    "Adverb": {
        "Adverbs": {"Form": ""},
        "Adverb_Manner": {"Form": ""},
        "Adverb_of_Time": {"Form": ""},
        "Place_and_Degree": {"Form": ""},
        "Comparison_of_Adverb": {"Form": ""},
        "Position_of_Adverb": {"Form": ""},
    },

    "Preposition": {
        "Preposition": {"Form": ""},
        "Preposition_of_Time": {"Form": ""},
        "Preposition_of_Place": {"Form": ""},
        "Cause_and_Agent": {"Form": ""},
        "Phrasal_Proposition": {"Form": ""},
        "Errors_in_Preposition": {"Form": ""},
    },

    "Conjuctions": {
        "Conjunction": {"Form": ""},
        "Co-ordinating_Conjunctions": {"Form": ""},
        "Subordinate_Conjunction": {"Form": ""},
        "Correlative_Conjunction": {"Form": ""},
    },

    "Interjection": {
        "Interjections": {"Form": ""},
    },

    "Types_of_Sentences": {
        "Assertive": {"Form": ""},
        "Interragative": {"Form": ""},
        "Imperative": {"Form": ""},
        "Exclamatory": {"Form": ""},
    },

    "Types_of_Sentences_by_Structure": {
        "Simple_Sentences": {"Form": ""},
        "Compound_Sentence": {"Form": ""},
        "Complex_Sentence": {"Form": ""},
    },

    "Clause": {
        "Main_Clause": {"Form": ""},
        "Subordinte_Clause": {"Form": ""},
        "Noun_Clause": {"Form": ""},
        "Relative_Clause": {"Form": ""},
        "Adjective_Clause": {"Form": ""},
        "Adverb_Clause": {"Form": ""},
    },

    "Phrase": {
        "Noun_Phrase": {"Form": ""},
        "Verb_Phrase": {"Form": ""},
        "Adjective_Phrase": {"Form": ""},
        "Adverb_Phrase": {"Form": ""},
        "Gerund_Infinitive_Participial_Phrases": {"Form": ""},
    },

    "Tenses": {
        "Present_Tense": {"Form": ""},
        "Past_Tense": {"Form": ""},
        "Future_Tense": {"Form": ""},
        "simple_Tense": {"Form": ""},
        "Continous_Tense": {"Form": ""},
        "Perfect_Tense": {"Form": ""},
        "Perfect_Continous_Tense": {"Form": ""},
    },

    "Rules_for_Conversion": {
        "Active_to_Passive_Voice": {"Form": ""},
        "Passive_with_Modals": {"Form": ""},
        "Direct_Indirect_Speech": {"Form": ""},
        "Speech_Conversion_Rule": {"Form": ""},
    },

    "Articles": {
        "The": {"Form": ""},
        "A_An": {"Form": ""},
    },

    "Modal": {
        "Modal": {"Form": ""},
    }
}

# ------------------------------------------------------------
# RENDER CONTENT
# ------------------------------------------------------------
if board == "SSC" and subject == "English":

    for chapter, subtopics in links.items():

        with st.container(border=True):
            st.subheader(f"🗂 {chapter.replace('_', ' ')}")

            for subtopic, linkset in subtopics.items():

                cols = st.columns([6,1])
                with cols[0]:
                    st.write(f"- {subtopic.replace('_', ' ')}")
                with cols[1]:
                    st.link_button("📄 Form", linkset.get("Form") or "#")

else:
    st.info("Please select SSC Board & English to continue.")
