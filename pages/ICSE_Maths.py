
import streamlit as st

# --- Page Config ---
st.set_page_config(
    page_title="ICSE Mathematics",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Sidebar ---
st.sidebar.title("🔧 Select Parameters")
board = st.sidebar.selectbox("Select Board", ["SSC", "ICSE"])
subject = st.sidebar.selectbox("Select Subject", ["Mathematics", "Science", "English", "Social Studies"])

branch = None
if board == "ICSE" and subject == "Mathematics":
    branch = st.sidebar.selectbox("Select Branch", ["Algebra", "Geometry", "Mensuration", "Trigonometry", "Statistics & Probability", "Commercial Math"])

# Spacer to push feedback button to bottom
st.sidebar.markdown("<br><br><br><br><br><br><br><br><br><br><br>", unsafe_allow_html=True)

# --- Feedback Button (at bottom of sidebar) ---
st.sidebar.link_button("📩 Feedback Form", "https://example.com/feedback-form")

# --- Main Page ---
st.title("📗 ICSE Mathematics")
st.markdown("""
Use the sidebar to choose the board, subject, and branch. Assessment content will appear below based on your selection.
""")

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

if subject == "Mathematics" and board == "ICSE":
    if branch == "Algebra":
        chapter = st.selectbox("Select Chapter", [
            "Linear Inequations",
            "Quadratic Equations",
            "Ratio and Proportion",
            "Remainder and Factor Theorems",
            "Matrices",
            "Arithmetic Progression",
            "Co-ordinate Geometry"
        ])

        if chapter == "Linear Inequations":
            subtopics = {
                "Solving Linear Inequations on Number Line": {
                    "Form": "https://example.com/form-ineq",
                    "Kahoot": "https://example.com/kahoot-ineq",
                    "Blooket": "https://example.com/blooket-ineq"
                }
            }

        elif chapter == "Quadratic Equations":
            subtopics = {
                "Solving Quadratic Equations": {
                    "Form": "https://example.com/form-quadratic",
                    "Kahoot": "https://example.com/kahoot-quadratic",
                    "Blooket": "https://example.com/blooket-quadratic"
                },
                "Word Problems": {
                    "Form": "https://example.com/form-quadratic-word",
                    "Kahoot": "https://example.com/kahoot-quadratic-word",
                    "Blooket": "https://example.com/blooket-quadratic-word"
                }
            }

        elif chapter == "Ratio and Proportion":
            subtopics = {
                "Continued and Mean Proportion": {
                    "Form": "https://example.com/form-ratio",
                    "Kahoot": "https://example.com/kahoot-ratio",
                    "Blooket": "https://example.com/blooket-ratio"
                }
            }

        elif chapter == "Remainder and Factor Theorems":
            subtopics = {
                "Remainder Theorem": {
                    "Form": "https://example.com/form-remainder",
                    "Kahoot": "https://example.com/kahoot-remainder",
                    "Blooket": "https://example.com/blooket-remainder"
                },
                "Factor Theorem": {
                    "Form": "https://example.com/form-factor",
                    "Kahoot": "https://example.com/kahoot-factor",
                    "Blooket": "https://example.com/blooket-factor"
                }
            }

        elif chapter == "Matrices":
            subtopics = {
                "Matrix Basics and Operations (2x2)": {
                    "Form": "https://example.com/form-matrix",
                    "Kahoot": "https://example.com/kahoot-matrix",
                    "Blooket": "https://example.com/blooket-matrix"
                }
            }

        elif chapter == "Arithmetic Progression":
            subtopics = {
                "nth Term and Sum of A.P.": {
                    "Form": "https://example.com/form-ap",
                    "Kahoot": "https://example.com/kahoot-ap",
                    "Blooket": "https://example.com/blooket-ap"
                }
            }

        elif chapter == "Co-ordinate Geometry":
            subtopics = {
                "Distance, Section, and Mid-point Formula": {
                    "Form": "https://example.com/form-coord",
                    "Kahoot": "https://example.com/kahoot-coord",
                    "Blooket": "https://example.com/blooket-coord"
                }
            }

        show_subtopics(subtopics)

    elif branch == "Geometry":
        chapter = st.selectbox("Select Chapter", ["Similarity", "Circles", "Constructions"])

        if chapter == "Similarity":
            subtopics = {
                "Criteria for Similarity and Applications": {
                    "Form": "https://example.com/form-similarity",
                    "Kahoot": "https://example.com/kahoot-similarity",
                    "Blooket": "https://example.com/blooket-similarity"
                }
            }

        elif chapter == "Circles":
            subtopics = {
                "Circle Properties and Theorems": {
                    "Form": "https://example.com/form-circles",
                    "Kahoot": "https://example.com/kahoot-circles",
                    "Blooket": "https://example.com/blooket-circles"
                }
            }

        elif chapter == "Constructions":
            subtopics = {
                "Tangent and Triangle Constructions": {
                    "Form": "https://example.com/form-construct",
                    "Kahoot": "https://example.com/kahoot-construct",
                    "Blooket": "https://example.com/blooket-construct"
                }
            }

        show_subtopics(subtopics)

    elif branch == "Mensuration":
        subtopics = {
            "Surface Area and Volume of Solids": {
                "Form": "https://example.com/form-mensuration",
                "Kahoot": "https://example.com/kahoot-mensuration",
                "Blooket": "https://example.com/blooket-mensuration"
            }
        }
        show_subtopics(subtopics)

    elif branch == "Trigonometry":
        subtopics = {
            "Trigonometric Identities": {
                "Form": "https://example.com/form-trig-identities",
                "Kahoot": "https://example.com/kahoot-trig-identities",
                "Blooket": "https://example.com/blooket-trig-identities"
            },
            "Heights and Distances": {
                "Form": "https://example.com/form-trig-heights",
                "Kahoot": "https://example.com/kahoot-trig-heights",
                "Blooket": "https://example.com/blooket-trig-heights"
            }
        }
        show_subtopics(subtopics)

    elif branch == "Statistics & Probability":
        subtopics = {
            "Mean, Median, Mode (Grouped Data)": {
                "Form": "https://example.com/form-stats",
                "Kahoot": "https://example.com/kahoot-stats",
                "Blooket": "https://example.com/blooket-stats"
            },
            "Probability (Single Event)": {
                "Form": "https://example.com/form-prob",
                "Kahoot": "https://example.com/kahoot-prob",
                "Blooket": "https://example.com/blooket-prob"
            }
        }
        show_subtopics(subtopics)

    elif branch == "Commercial Math":
        subtopics = {
            "Goods and Services Tax (GST)": {
                "Form": "https://example.com/form-gst",
                "Kahoot": "https://example.com/kahoot-gst",
                "Blooket": "https://example.com/blooket-gst"
            },
            "Banking (RD Accounts, Interest)": {
                "Form": "https://example.com/form-banking",
                "Kahoot": "https://example.com/kahoot-banking",
                "Blooket": "https://example.com/blooket-banking"
            },
            "Shares and Dividends": {
                "Form": "https://example.com/form-shares",
                "Kahoot": "https://example.com/kahoot-shares",
                "Blooket": "https://example.com/blooket-shares"
            }
        }
        show_subtopics(subtopics)

else:
    st.info("Please select 'Mathematics' as the subject under ICSE Board to view content.")

