import streamlit as st

# ------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------
st.set_page_config(
    page_title="Science-2",
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
subject = st.sidebar.selectbox("Subject", ["Mathematics", "Science", "English"], index=1)

# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------
st.title("📗 SSC Grade 10 Science — Part 2")
st.markdown("Below are the chapters and subtopics. Paste your Form / Kahoot / Blooket links in the `links` dictionary below.")

# ------------------------------------------------------------
# ---- MANUAL LINK ENTRY SECTION (EDIT THESE) ----
# ------------------------------------------------------------
# Fill your actual Form / Kahoot / Blooket links here. Keys are ChapterName -> SubTopic -> {Form, Kahoot, Blooket}

links = {
    "Heredity_and_Evolution": {
        "DNA": {"Form": "", "Kahoot": "", "Blooket": ""},
        "Evolution": {"Form": "", "Kahoot": "", "Blooket": ""},
    },

    "Life_Process_in_living_organisms_part_2": {
        "Asexual_Reproduction": {"Form": "", "Kahoot": "", "Blooket": ""},
        "Sexual_Reproduction_in_Plants": {"Form": "", "Kahoot": "", "Blooket": ""},
        "Sexual_Reproduction_in_Human_being": {"Form": "", "Kahoot": "", "Blooket": ""},
        "Reproduction_and_Birth": {"Form": "", "Kahoot": "", "Blooket": ""},
    },

    "Life_Process_in_living_organisms_part_1": {
        "Cell_Division": {"Form": "", "Kahoot": "", "Blooket": ""},
        "Energy_Production": {"Form": "", "Kahoot": "", "Blooket": ""},
    },

    "Animal_Classification": {
        "Old_and_New_system_of_Animal_Classification": {"Form": "", "Kahoot": "", "Blooket": ""},
        "Phylum-Porifera,_Coelenterata,_Platyhelminthes,_Aschelminthes": {"Form": "", "Kahoot": "", "Blooket": ""},
        "Phylum-Annelida,_Arthropoda,_Mollusca,_Echinodermata,_Hemichordata": {"Form": "", "Kahoot": "", "Blooket": ""},
        "Phylum-Chordata": {"Form": "", "Kahoot": "", "Blooket": ""},
    },

    "Introduction_to_Microbiology": {
        "Applied_Microbiology_Food": {"Form": "", "Kahoot": "", "Blooket": ""},
        "Applied_Microbiology": {"Form": "", "Kahoot": "", "Blooket": ""},
    },

    "Cell_Biology_and_Biotechnology": {
        "Stem_Cells": {"Form": "", "Kahoot": "", "Blooket": ""},
        "Biotechnology": {"Form": "", "Kahoot": "", "Blooket": ""},
    },
}

# ------------------------------------------------------------
# RENDER CONTENT
# ------------------------------------------------------------
if board == "SSC" and subject == "Science":

    for chapter, subtopics in links.items():

        with st.container(border=True):
            st.subheader(f"📗 {chapter.replace('_', ' ')}")

            # show each subtopic as an expander with three link buttons
            for subtopic, linkset in subtopics.items():

                with st.expander(f"🔬 {subtopic.replace('_', ' ')}"):

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.link_button("📄 Form", linkset.get("Form") or "#")

                    with col2:
                        st.link_button("🎯 Kahoot", linkset.get("Kahoot") or "#")

                    with col3:
                        st.link_button("🎮 Blooket", linkset.get("Blooket") or "#")

else:
    st.info("Please select SSC Board & Science to continue.")
