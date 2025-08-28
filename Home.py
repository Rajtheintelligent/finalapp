import streamlit as st

# ------------------------ Page Config ------------------------
st.set_page_config(
    page_title="Grade 10 Assessment Hub",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------ Sidebar ------------------------
st.sidebar.title("🔧 Select Options")
board = st.sidebar.selectbox("Select Board", ["SSC", "ICSE"])
subject = st.sidebar.selectbox("Select Subject", ["Mathematics", "Science", "English", "Social Studies"])
st.sidebar.markdown("""
---
📬 **[Feedback Form](https://forms.gle/your-feedback-form)**
""")

# ------------------------ Main Page ------------------------
st.title("📘 Grade 10 Assessment Web App")
st.markdown("""
Welcome to the Grade 10 Assessment Platform. Select a board and subject from the sidebar to begin.

Use the navigation in the sidebar to access subject-wise assessments, tools, and subtopics.
""")

# ------------------------ Page Guide ------------------------
if board == "SSC":
    if subject == "Mathematics":
        st.markdown("👉 Go to **SSC_Maths** page in the sidebar for Algebra and Geometry assessments.")
    elif subject == "Science":
        st.markdown("👉 Go to **SSC_Science** page for Physics, Chemistry and Biology.")
    elif subject == "English":
        st.markdown("👉 Go to **SSC_English** page for Grammar and Language Tools.")
    elif subject == "Social Studies":
        st.markdown("👉 Go to **SSC_Social_Studies** page for History and Geography.")

elif board == "ICSE":
    if subject == "Mathematics":
        st.markdown("👉 Go to **ICSE_Maths** page in the sidebar for Algebra and Geometry assessments.")
    elif subject == "Science":
        st.markdown("👉 Go to **ICSE_Science** page for Physics, Chemistry and Biology.")
    elif subject == "English":
        st.markdown("👉 Go to **ICSE_English** page for Grammar and Language Tools.")
    elif subject == "Social Studies":
        st.markdown("👉 Go to **ICSE_Social_Studies** page for History and Geography.")
# ------------------------ NEW: SSC Section on MAIN PAGE (added feature) ------------------------
st.markdown("---")
st.header("SSC — Quick Access")
st.markdown(
    "Below are the primary SSC subjects. Select a subject to reveal related subtopics (Algebra / Geometry for Mathematics; Physics/Chemistry/Biology for Science)."
)

# Visible subject selector for SSC (radio is formal and clear)
# If you prefer buttons or selectbox, we can switch later.
ssc_subject_choice = st.radio(
    label="Choose SSC Subject",
    options=["— Select a subject —", "SSC Mathematics", "SSC Science", "SSC English"],
    index=0,
    horizontal=True
)

# SSC Mathematics: show algebra/geometry choice
if ssc_subject_choice == "SSC Mathematics":
    st.subheader("SSC Mathematics — Subtopic")
    st.markdown("Choose a subtopic to proceed to subject-specific assessment pages or tools.")
    math_subtopic = st.radio(
        label="Select Mathematics subtopic",
        options=["Algebra", "Geometry"],
        index=0
    )
    st.info(f"Selected: **SSC Mathematics → {math_subtopic}**")

    # Example: show an open button (adjust page name to your project pages)
    if st.button(f"Open SSC Mathematics — {math_subtopic} Page"):
        # Replace these with your actual navigation calls (st.switch_page or query params)
        st.experimental_set_query_params(board="SSC", subject="Mathematics", subtopic=math_subtopic)
        st.experimental_rerun()

# SSC Science: show physics/chemistry/biology choice
elif ssc_subject_choice == "SSC Science":
    st.subheader("SSC Science — Subtopic")
    st.markdown("Choose a science stream to proceed to the corresponding assessments.")
    science_subtopic = st.radio(
        label="Select Science subtopic",
        options=["Physics", "Chemistry", "Biology"],
        index=0
    )
    st.info(f"Selected: **SSC Science → {science_subtopic}**")

    if st.button(f"Open SSC Science — {science_subtopic} Page"):
        st.experimental_set_query_params(board="SSC", subject="Science", subtopic=science_subtopic)
        st.experimental_rerun()

# SSC English: short description (no subtopic dropdown yet)
elif ssc_subject_choice == "SSC English":
    st.subheader("SSC English")
    st.markdown("English resources include Grammar, Comprehension and Writing practice. If you want subtopics for English, tell me which (Grammar / Comprehension / Writing) and I'll add a selector.")
    if st.button("Open SSC English Page"):
        st.experimental_set_query_params(board="SSC", subject="English")
        st.experimental_rerun()

# If user hasn't chosen any SSC subject
else:
    st.write("Select an SSC subject above to reveal subtopics and open the relevant page.")

# ------------------------ end of NEW SSC section ------------------------

# (Everything else in your original file remains unchanged and in place)
# ------------------------ Footer (formal) ------------------------
st.markdown("---")
st.markdown(
    """
**Contact / Feedback:** For operational issues or feedback, please use the feedback form.  
© 2025 Grade 10 Assessment Hub — All rights reserved.
"""
)


