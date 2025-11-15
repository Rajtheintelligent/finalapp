import streamlit as st

# ------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------
st.set_page_config(
    page_title="SSC Algebra",
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
subject = st.sidebar.selectbox("Subject", ["Mathematics", "Science", "English"], index=0)

# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------
st.title("📘 SSC Grade 10 Algebra")
st.markdown("Below are all chapters and practice sets. Please paste your links manually inside this file.")

# ------------------------------------------------------------
# MANUAL LINK ENTRY AREA — EDIT ONLY THIS DICTIONARY
# ------------------------------------------------------------

links = {

    # --------------------------------------------------------
    # CHAPTER 1: Linear Equations in Two Variables
    # --------------------------------------------------------
    "Linear Equations in Two Variables": {
        "Practice_Set-1.0":   {"Form": "", "Kahoot": "", "Blooket": ""},
        "Practice_Set-1.1":   {"Form": "", "Kahoot": "", "Blooket": ""},
        "Practice_Set-1.2":   {"Form": "", "Kahoot": "", "Blooket": ""},
        "Practice_Set-1.3":   {"Form": "", "Kahoot": "", "Blooket": ""},
        "Practice_Set-1.4":   {"Form": "", "Kahoot": "", "Blooket": ""},
    },

    # --------------------------------------------------------
    # CHAPTER 2: Quadratic Equations
    # --------------------------------------------------------
    "Quadratic Equations": {
        "Practice_Set-2.0":   {"Form": "", "Kahoot": "", "Blooket": ""},
        "Practice_Set-2.1":   {"Form": "", "Kahoot": "", "Blooket": ""},
        "Practice_Set-2.2":   {"Form": "", "Kahoot": "", "Blooket": ""},
        "Practice_Set-2.3":   {"Form": "", "Kahoot": "", "Blooket": ""},
        "Practice_Set-2.4":   {"Form": "", "Kahoot": "", "Blooket": ""},
        "Practice_Set-2.5":   {"Form": "", "Kahoot": "", "Blooket": ""},
        "Practice_Set-2.6":   {"Form": "", "Kahoot": "", "Blooket": ""},
    },

    # --------------------------------------------------------
    # CHAPTER 3: Arithmetic Progression
    # --------------------------------------------------------
    "Arithmetic Progression": {
        "Practice_Set-3.1":   {"Form": "", "Kahoot": "", "Blooket": ""},
        "Practice_Set-3.2":   {"Form": "", "Kahoot": "", "Blooket": ""},
        "Practice_Set-3.3":   {"Form": "", "Kahoot": "", "Blooket": ""},
        "Practice_Set-3.4":   {"Form": "", "Kahoot": "", "Blooket": ""},
    },

    # --------------------------------------------------------
    # CHAPTER 4: Financial Planning
    # --------------------------------------------------------
    "Financial Planning": {
        "Practice_Set-4.1":   {"Form": "", "Kahoot": "", "Blooket": ""},
        "Practice_Set-4.2":   {"Form": "", "Kahoot": "", "Blooket": ""},
        "Practice_Set-4.3":   {"Form": "", "Kahoot": "", "Blooket": ""},
        "Practice_Set-4.4":   {"Form": "", "Kahoot": "", "Blooket": ""},
    },

    # --------------------------------------------------------
    # CHAPTER 5: Probability
    # --------------------------------------------------------
    "Probability": {
        "Practice_Set-5.1":   {"Form": "", "Kahoot": "", "Blooket": ""},
        "Practice_Set-5.3":   {"Form": "", "Kahoot": "", "Blooket": ""},
        "Practice_Set-5.4":   {"Form": "", "Kahoot": "", "Blooket": ""},
    }
}

# ------------------------------------------------------------
# RENDER CHAPTERS + PRACTICE SETS
# ------------------------------------------------------------
if board == "SSC" and subject == "Mathematics":

    for chapter, practice_sets in links.items():

        with st.container(border=True):
            st.subheader(f"📘 {chapter}")

            for ps, linkset in practice_sets.items():

                with st.expander(f"📝 {ps.replace('_', ' ')}"):

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.link_button("📄 Form", linkset["Form"] or "#")

                    with col2:
                        st.link_button("🎯 Kahoot", linkset["Kahoot"] or "#")

                    with col3:
                        st.link_button("🎮 Blooket", linkset["Blooket"] or "#")

else:
    st.info("Please select SSC Board & Mathematics to view Algebra content.")
