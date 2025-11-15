\import streamlit as st

# ------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------
st.set_page_config(
    page_title="SSC Geometry",
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
st.title("📘 SSC Grade 10 Geometry")
st.markdown("Below are the chapters and practice sets. Please paste links manually inside this file.")

# ------------------------------------------------------------
# ---- MANUAL LINK ENTRY SECTION (EDIT THESE) ----
# ------------------------------------------------------------
# You will fill your actual Form / Kahoot / Blooket links here!

links = {

    "Similarity": {
        "Practice_Set-1.2": {
            "Form": "",
            "Kahoot": "",
            "Blooket": ""
        },
        "Practice_Set-1.3": {
            "Form": "",
            "Kahoot": "",
            "Blooket": ""
        },
        "Practice_Set-1.4": {
            "Form": "",
            "Kahoot": "",
            "Blooket": ""
        }
    },

    "Pythagoras Theorem": {
        "Practice_Set-2.1": {
            "Form": "",
            "Kahoot": "",
            "Blooket": ""
        },
        "Practice_Set-2.2": {
            "Form": "",
            "Kahoot": "",
            "Blooket": ""
        }
    },

    "Circle": {
        "Practice_Set-3.1": {
            "Form": "",
            "Kahoot": "",
            "Blooket": ""
        },
        "Practice_Set-3.2": {
            "Form": "",
            "Kahoot": "",
            "Blooket": ""
        },
        "Practice_Set-3.3": {
            "Form": "",
            "Kahoot": "",
            "Blooket": ""
        },
        "Practice_Set-3.4": {
            "Form": "",
            "Kahoot": "",
            "Blooket": ""
        },
        "Practice_Set-3.5": {
            "Form": "",
            "Kahoot": "",
            "Blooket": ""
        }
    },

    "Co-ordinate Geometry": {
        "Practice_Set-5.1": {
            "Form": "",
            "Kahoot": "",
            "Blooket": ""
        },
        "Practice_Set-5.2": {
            "Form": "",
            "Kahoot": "",
            "Blooket": ""
        },
        "Practice_Set-5.3": {
            "Form": "",
            "Kahoot": "",
            "Blooket": ""
        }
    },

    "Trigonometry": {
        "Practice_Set-6.0": {
            "Form": "",
            "Kahoot": "",
            "Blooket": ""
        },
        "Practice_Set-6.1": {
            "Form": "",
            "Kahoot": "",
            "Blooket": ""
        },
        "Practice_Set-6.2": {
            "Form": "",
            "Kahoot": "",
            "Blooket": ""
        }
    },

    "Mensuration": {
        "Practice_Set-7.1": {
            "Form": "",
            "Kahoot": "",
            "Blooket": ""
        },
        "Practice_Set-7.3": {
            "Form": "",
            "Kahoot": "",
            "Blooket": ""
        },
        "Practice_Set-7.4": {
            "Form": "",
            "Kahoot": "",
            "Blooket": ""
        }
    },

}

# ------------------------------------------------------------
# RENDER CONTENT
# ------------------------------------------------------------
if board == "SSC" and subject == "Mathematics":

    for chapter, practice_sets in links.items():

        with st.container(border=True):
            st.subheader(f"📘 {chapter}")

            for ps, linkset in practice_sets.items():

                with st.expander(f"📝 {ps.replace('_',' ')}"):

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.link_button("📄 Form", linkset["Form"] or "#")

                    with col2:
                        st.link_button("🎯 Kahoot", linkset["Kahoot"] or "#")

                    with col3:
                        st.link_button("🎮 Blooket", linkset["Blooket"] or "#")

else:
    st.info("Please select SSC Board & Mathematics to continue.")
