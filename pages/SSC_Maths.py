import streamlit as st

# --- Page Config ---
st.set_page_config(
    page_title="SSC Mathematics",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Sidebar ---
st.sidebar.title("🔧 Select Parameters")
board = st.sidebar.selectbox("Select Board", ["SSC", "ICSE"])
subject = st.sidebar.selectbox("Select Subject", ["Mathematics", "Science", "English", "Social Studies"])

branch = None
if subject == "Mathematics":
    branch = st.sidebar.selectbox("Select Branch", ["Algebra", "Geometry"])

# Spacer to push feedback button to bottom
st.sidebar.markdown("<br>" * 12, unsafe_allow_html=True)

# --- Feedback Button ---
st.sidebar.markdown(
    "[📩 Feedback Form](https://example.com/feedback-form)",
    unsafe_allow_html=True
)

# --- Main Page ---
st.title("📘 SSC Mathematics")
st.markdown("""
Use the sidebar to choose the board, subject, and branch. Assessment content will appear below based on your selection.
""")

# --- Function to Display Subtopics ---
def show_subtopics(subtopics):
    for topic, links in subtopics.items():
        with st.expander(f"🔹 {topic}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"[Open Form]({links['Form']})", unsafe_allow_html=True)
            with col2:
                st.markdown(f"[Open Kahoot]({links['Kahoot']})", unsafe_allow_html=True)
            with col3:
                st.markdown(f"[Open Blooket]({links['Blooket']})", unsafe_allow_html=True)

# ---------------- Algebra Branch ----------------
if subject == "Mathematics" and branch == "Algebra":
    chapter = st.selectbox("Select Chapter", [
        "Linear Equations in Two Variables",
        "Quadratic Equation",
        "Arithmetic Progression",
        "Probability",
        "Statistics",
        "Financial Planning"
    ])

    if chapter == "Linear Equations in Two Variables":
        st.subheader("📂 Subtopics in Linear Equations in Two Variables")
        subtopics = {
            "Graphical Representation": {
                "Form": "https://example.com/form-linear-graph",
                "Kahoot": "https://example.com/kahoot-linear-graph",
                "Blooket": "https://example.com/blooket-linear-graph"
            },
            "Algebraic Methods (Substitution, Elimination)": {
                "Form": "https://example.com/form-algebraic",
                "Kahoot": "https://example.com/kahoot-algebraic",
                "Blooket": "https://example.com/blooket-algebraic"
            },
            "Word Problems": {
                "Form": "https://example.com/form-wordproblems",
                "Kahoot": "https://example.com/kahoot-wordproblems",
                "Blooket": "https://example.com/blooket-wordproblems"
            }
        }

    elif chapter == "Quadratic Equation":
        st.subheader("📂 Subtopics in Quadratic Equations")
        subtopics = {
            "Standard Form and Roots": {
                "Form": "https://example.com/form-standard",
                "Kahoot": "https://example.com/kahoot-standard",
                "Blooket": "https://example.com/blooket-standard"
            },
            "Nature of Roots (Discriminant)": {
                "Form": "https://example.com/form-discriminant",
                "Kahoot": "https://example.com/kahoot-discriminant",
                "Blooket": "https://example.com/blooket-discriminant"
            },
            "Factorisation Method": {
                "Form": "https://example.com/form-factorisation",
                "Kahoot": "https://example.com/kahoot-factorisation",
                "Blooket": "https://example.com/blooket-factorisation"
            },
            "Formula Method": {
                "Form": "https://example.com/form-formula",
                "Kahoot": "https://example.com/kahoot-formula",
                "Blooket": "https://example.com/blooket-formula"
            },
            "Completing the Square Method": {
                "Form": "https://example.com/form-square",
                "Kahoot": "https://example.com/kahoot-square",
                "Blooket": "https://example.com/blooket-square"
            },
            "Word Problems on Quadratic Equations": {
                "Form": "https://example.com/form-wordquad",
                "Kahoot": "https://example.com/kahoot-wordquad",
                "Blooket": "https://example.com/blooket-wordquad"
            }
        }

    elif chapter == "Arithmetic Progression":
        st.subheader("📂 Subtopics in Arithmetic Progression")
        subtopics = {
            "Introduction to A.P.": {
                "Form": "https://example.com/form-ap-intro",
                "Kahoot": "https://example.com/kahoot-ap-intro",
                "Blooket": "https://example.com/blooket-ap-intro"
            },
            "nth Term of an A.P.": {
                "Form": "https://example.com/form-ap-nth",
                "Kahoot": "https://example.com/kahoot-ap-nth",
                "Blooket": "https://example.com/blooket-ap-nth"
            },
            "Sum of First n Terms": {
                "Form": "https://example.com/form-ap-sum",
                "Kahoot": "https://example.com/kahoot-ap-sum",
                "Blooket": "https://example.com/blooket-ap-sum"
            },
            "Applications and Word Problems": {
                "Form": "https://example.com/form-ap-word",
                "Kahoot": "https://example.com/kahoot-ap-word",
                "Blooket": "https://example.com/blooket-ap-word"
            }
        }

    elif chapter == "Probability":
        st.subheader("📂 Subtopics in Probability")
        subtopics = {
            "Empirical Probability": {
                "Form": "https://example.com/form-prob-empirical",
                "Kahoot": "https://example.com/kahoot-prob-empirical",
                "Blooket": "https://example.com/blooket-prob-empirical"
            },
            "Sample Space and Events": {
                "Form": "https://example.com/form-prob-sample",
                "Kahoot": "https://example.com/kahoot-prob-sample",
                "Blooket": "https://example.com/blooket-prob-sample"
            },
            "Problems on Coins, Dice, Cards": {
                "Form": "https://example.com/form-prob-games",
                "Kahoot": "https://example.com/kahoot-prob-games",
                "Blooket": "https://example.com/blooket-prob-games"
            }
        }

    elif chapter == "Statistics":
        st.subheader("📂 Subtopics in Statistics")
        subtopics = {
            "Mean (Grouped Data)": {
                "Form": "https://example.com/form-mean",
                "Kahoot": "https://example.com/kahoot-mean",
                "Blooket": "https://example.com/blooket-mean"
            },
            "Median (Grouped Data)": {
                "Form": "https://example.com/form-median",
                "Kahoot": "https://example.com/kahoot-median",
                "Blooket": "https://example.com/blooket-median"
            },
            "Mode (Grouped Data)": {
                "Form": "https://example.com/form-mode",
                "Kahoot": "https://example.com/kahoot-mode",
                "Blooket": "https://example.com/blooket-mode"
            },
            "Histogram and Ogive": {
                "Form": "https://example.com/form-histogram",
                "Kahoot": "https://example.com/kahoot-histogram",
                "Blooket": "https://example.com/blooket-histogram"
            }
        }

    elif chapter == "Financial Planning":
        st.subheader("📂 Subtopics in Financial Planning")
        subtopics = {
            "Income and Expenditure": {
                "Form": "https://example.com/form-income",
                "Kahoot": "https://example.com/kahoot-income",
                "Blooket": "https://example.com/blooket-income"
            },
            "Savings and Budgeting": {
                "Form": "https://example.com/form-savings",
                "Kahoot": "https://example.com/kahoot-savings",
                "Blooket": "https://example.com/blooket-savings"
            },
            "GST and Taxes": {
                "Form": "https://example.com/form-gst",
                "Kahoot": "https://example.com/kahoot-gst",
                "Blooket": "https://example.com/blooket-gst"
            },
            "Simple and Compound Interest": {
                "Form": "https://example.com/form-interest",
                "Kahoot": "https://example.com/kahoot-interest",
                "Blooket": "https://example.com/blooket-interest"
            }
        }

    show_subtopics(subtopics)

# ---------------- Geometry Branch ----------------
# ---------------- Geometry Branch ----------------
elif subject == "Mathematics" and branch == "Geometry":
    chapter = st.selectbox("Select Chapter", [
        "Similarity",
        "Pythagoras Theorem",
        "Circles",
        "Constructions",
        "Co-ordinate Geometry",
        "Mensuration (Surface Area and Volume)"
    ])

    if chapter == "Similarity":
        st.subheader("📂 Subtopics in Similarity")

        st.markdown("### Ratios of areas of two triangles")
        if st.button("Open Form - Ratios of areas of two triangles", key="btn_sim_ratios"):
            render_form(subject="SSC_Maths", subtopic="ratio_of_areas_of_two_triangles")
        st.markdown("[Kahoot](https://example.com/kahoot-ratios-areas)")
        st.markdown("[Blooket](https://example.com/blooket-ratios-areas)")

        st.markdown("### Criteria for Similarity of Triangles")
        if st.button("Open Form - Criteria for Similarity of Triangles", key="btn_sim_criteria"):
            render_form(subject="SSC_Maths", subtopic="criteria_for_similarity_of_triangles")
        st.markdown("[Kahoot](https://example.com/kahoot-similarity-criteria)")
        st.markdown("[Blooket](https://example.com/blooket-similarity-criteria)")

        st.markdown("### Basic Proportionality Theorem (BPT)")
        if st.button("Open Form - Basic Proportionality Theorem (BPT)", key="btn_sim_bpt"):
            render_form(subject="SSC_Maths", subtopic="bpt")
        st.markdown("[Kahoot](https://example.com/kahoot-bpt)")
        st.markdown("[Blooket](https://example.com/blooket-bpt)")

        st.markdown("### Converse of BPT")
        if st.button("Open Form - Converse of BPT", key="btn_sim_bpt_conv"):
            render_form(subject="SSC_Maths", subtopic="bpt_converse")
        st.markdown("[Kahoot](https://example.com/kahoot-bpt-converse)")
        st.markdown("[Blooket](https://example.com/blooket-bpt-converse)")

        st.markdown("### Areas of Similar Triangles")
        if st.button("Open Form - Areas of Similar Triangles", key="btn_sim_area"):
            render_form(subject="SSC_Maths", subtopic="similarity_area")
        st.markdown("[Kahoot](https://example.com/kahoot-similarity-area)")
        st.markdown("[Blooket](https://example.com/blooket-similarity-area)")

        st.markdown("### Pythagoras Theorem via Similarity")
        if st.button("Open Form - Pythagoras Theorem via Similarity", key="btn_sim_pyth"):
            render_form(subject="SSC_Maths", subtopic="similarity_pythagoras")
        st.markdown("[Kahoot](https://example.com/kahoot-similarity-pythagoras)")
        st.markdown("[Blooket](https://example.com/blooket-similarity-pythagoras)")

    elif chapter == "Pythagoras Theorem":
        st.subheader("📂 Subtopics in Pythagoras Theorem")

        st.markdown("### Statement and Proof")
        if st.button("Open Form - Statement and Proof", key="btn_pyth_proof"):
            render_form(subject="SSC_Maths", subtopic="pythagoras_proof")
        st.markdown("[Kahoot](https://example.com/kahoot-pythagoras-proof)")
        st.markdown("[Blooket](https://example.com/blooket-pythagoras-proof)")

        st.markdown("### Converse")
        if st.button("Open Form - Converse", key="btn_pyth_conv"):
            render_form(subject="SSC_Maths", subtopic="pythagoras_converse")
        st.markdown("[Kahoot](https://example.com/kahoot-pythagoras-converse)")
        st.markdown("[Blooket](https://example.com/blooket-pythagoras-converse)")

        st.markdown("### Applications in Numerical Problems")
        if st.button("Open Form - Applications in Numerical Problems", key="btn_pyth_apps"):
            render_form(subject="SSC_Maths", subtopic="pythagoras_apps")
        st.markdown("[Kahoot](https://example.com/kahoot-pythagoras-apps)")
        st.markdown("[Blooket](https://example.com/blooket-pythagoras-apps)")

    # ⬇️ Your next chapter continues here
    elif chapter == "Circles":
        st.subheader("📂 Subtopics in Circles")
    elif chapter == "Circles":
        st.subheader("📂 Subtopics in Circles")
        subtopics = {
            "Tangents to a Circle": {
                "Form": "https://example.com/form-circle-tangent",
                "Kahoot": "https://example.com/kahoot-circle-tangent",
                "Blooket": "https://example.com/blooket-circle-tangent"
            },
            "Number of Tangents from a Point": {
                "Form": "https://example.com/form-circle-numtangent",
                "Kahoot": "https://example.com/kahoot-circle-numtangent",
                "Blooket": "https://example.com/blooket-circle-numtangent"
            },
            "Properties of Tangents": {
                "Form": "https://example.com/form-circle-properties",
                "Kahoot": "https://example.com/kahoot-circle-properties",
                "Blooket": "https://example.com/blooket-circle-properties"
            },
            "Angle Between Tangent and Radius": {
                "Form": "https://example.com/form-circle-angle",
                "Kahoot": "https://example.com/kahoot-circle-angle",
                "Blooket": "https://example.com/blooket-circle-angle"
            },
            "Proofs and Applications": {
                "Form": "https://example.com/form-circle-proof",
                "Kahoot": "https://example.com/kahoot-circle-proof",
                "Blooket": "https://example.com/blooket-circle-proof"
            }
        }

    elif chapter == "Constructions":
        st.subheader("📂 Subtopics in Constructions")
        subtopics = {
            "Division of a Line Segment": {
                "Form": "https://example.com/form-construct-division",
                "Kahoot": "https://example.com/kahoot-construct-division",
                "Blooket": "https://example.com/blooket-construct-division"
            },
            "Tangents from a Point to a Circle": {
                "Form": "https://example.com/form-construct-tangent",
                "Kahoot": "https://example.com/kahoot-construct-tangent",
                "Blooket": "https://example.com/blooket-construct-tangent"
            },
            "Similar Triangles": {
                "Form": "https://example.com/form-construct-triangle",
                "Kahoot": "https://example.com/kahoot-construct-triangle",
                "Blooket": "https://example.com/blooket-construct-triangle"
            },
            "Construction with Given Conditions": {
                "Form": "https://example.com/form-construct-given",
                "Kahoot": "https://example.com/kahoot-construct-given",
                "Blooket": "https://example.com/blooket-construct-given"
            }
        }

    elif chapter == "Co-ordinate Geometry":
        st.subheader("📂 Subtopics in Co-ordinate Geometry")
        subtopics = {
            "Distance Formula": {
                "Form": "https://example.com/form-geometry-distance",
                "Kahoot": "https://example.com/kahoot-geometry-distance",
                "Blooket": "https://example.com/blooket-geometry-distance"
            },
            "Section Formula": {
                "Form": "https://example.com/form-geometry-section",
                "Kahoot": "https://example.com/kahoot-geometry-section",
                "Blooket": "https://example.com/blooket-geometry-section"
            },
            "Mid-point Formula": {
                "Form": "https://example.com/form-geometry-midpoint",
                "Kahoot": "https://example.com/kahoot-geometry-midpoint",
                "Blooket": "https://example.com/blooket-geometry-midpoint"
            },
            "Area of Triangle using Coordinates": {
                "Form": "https://example.com/form-geometry-area",
                "Kahoot": "https://example.com/kahoot-geometry-area",
                "Blooket": "https://example.com/blooket-geometry-area"
            }
        }

    elif chapter == "Mensuration (Surface Area and Volume)":
        st.subheader("📂 Subtopics in Mensuration")
        subtopics = {
            "Surface Area and Volume of Solids": {
                "Form": "https://example.com/form-mensuration-solids",
                "Kahoot": "https://example.com/kahoot-mensuration-solids",
                "Blooket": "https://example.com/blooket-mensuration-solids"
            },
            "Conversion and Melting of Solids": {
                "Form": "https://example.com/form-mensuration-conversion",
                "Kahoot": "https://example.com/kahoot-mensuration-conversion",
                "Blooket": "https://example.com/blooket-mensuration-conversion"
            },
            "Frustum of a Cone (Conceptual)": {
                "Form": "https://example.com/form-mensuration-frustum",
                "Kahoot": "https://example.com/kahoot-mensuration-frustum",
                "Blooket": "https://example.com/blooket-mensuration-frustum"
            }
        }

    show_subtopics(subtopics)

# ---------------- Other Subjects ----------------
elif subject != "Mathematics":
    st.info("Content for the selected subject is coming soon.")




