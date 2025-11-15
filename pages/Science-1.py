import streamlit as st

# ------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------
st.set_page_config(
    page_title="SSC Science - Part 1 (Physics & Chemistry)",
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
st.title("📘 SSC Grade 10 Science — Part 1")
st.markdown("Below are the chapters and subtopics you provided. Paste your Form / Kahoot / Blooket links in the `links` dictionary below.")

# ------------------------------------------------------------
# ---- MANUAL LINK ENTRY SECTION (EDIT THESE) ----
# ------------------------------------------------------------
# Fill your actual Form / Kahoot / Blooket links here. Keys are ChapterName -> SubTopic -> {Form, Kahoot, Blooket}

links = {
    "Gravitation": {
        "Keplers_Law_and_Newtons_Law_of_Gravitation": {"Form": "", "Kahoot": "", "Blooket": ""},
        "Mass_Weight_Kinematic_Equation": {"Form": "", "Kahoot": "", "Blooket": ""},
    },

    "Periodic_Classification_of_Elements": {
        "Dobereiner_Triads_Newlands_Octaves_Mendeleev": {"Form": "", "Kahoot": "", "Blooket": ""},
        "Modern_Periodic_Table": {"Form": "", "Kahoot": "", "Blooket": ""},
        "Characteristics_of_Modern_Periodic_Table": {"Form": "", "Kahoot": "", "Blooket": ""},
    },

    "Chemical_Reactions_and_Equations": {
        "Writing_and_Balancing_Chemical_Equations": {"Form": "", "Kahoot": "", "Blooket": ""},
        "Types_of_Chemical_Reaction": {"Form": "", "Kahoot": "", "Blooket": ""},
        "Factors_Affecting_Chemical_Reaction": {"Form": "", "Kahoot": "", "Blooket": ""},
    },

    "Effects_of_Electric_Current": {
        "Electricity_and_Magnetism": {"Form": "", "Kahoot": "", "Blooket": ""},
        "Electric_Motor": {"Form": "", "Kahoot": "", "Blooket": ""},
        "Electric_Generator": {"Form": "", "Kahoot": "", "Blooket": ""},
    },

    "Heat": {
        "Heat_and_its_Properties": {"Form": "", "Kahoot": "", "Blooket": ""},
        "Specific_Heat_Capacity_and_Heat_Exchange": {"Form": "", "Kahoot": "", "Blooket": ""},
    },

    "Refraction_of_Light": {
        "Laws_of_Refraction": {"Form": "", "Kahoot": "", "Blooket": ""},
        "Application_of_Refraction_and_TotalInternal_Reflection": {"Form": "", "Kahoot": "", "Blooket": ""},
    },

    "Lenses": {
        "Lenses,_Images_formed_by_Convex_lenses": {"Form": "", "Kahoot": "", "Blooket": ""},
        "Magnification_Power_of_lens_Images_formed_by_Concave_lens": {"Form": "", "Kahoot": "", "Blooket": ""},
        "Application_of_Lenses": {"Form": "", "Kahoot": "", "Blooket": ""},
    },

    "Carbon_Compounds": {
        "Carbon_and_Bonding": {"Form": "", "Kahoot": "", "Blooket": ""},
        "IUPAC_Types_of_Reaction": {"Form": "", "Kahoot": "", "Blooket": ""},
        "Polymers_and_Chemical_Properties_of_Carbon": {"Form": "", "Kahoot": "", "Blooket": ""},
    },

    "Metallurgy": {
        "Physical_and_Chemical_Properties_of_Metals_&_Non-Metals": {"Form": "", "Kahoot": "", "Blooket": ""},
        "Extraction_of_Metals": {"Form": "", "Kahoot": "", "Blooket": ""},
    },
}

# ------------------------------------------------------------
# RENDER CONTENT
# ------------------------------------------------------------
if board == "SSC" and subject == "Science":

    for chapter, subtopics in links.items():

        with st.container(border=True):
            st.subheader(f"📘 {chapter.replace('_', ' ')}")

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
