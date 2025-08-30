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

with st.expander("SSC", expanded=True):
    st.write("Select an SSC subject to open its page:")

    # three subject buttons in one row
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Mathematics", key="btn_ssc_math"):
            st.switch_page("pages/SSC_Maths.py")
    with col2:
        if st.button("Science", key="btn_ssc_science"):
            st.switch_page("pages/SSC_Science.py")
    with col3:
        if st.button("English", key="btn_ssc_english"):
            st.switch_page("pages/SSC_English.py")
            
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Student Drilldown", key="btn_student_drilldown"):
            st.switch_page("pages/student_drilldown.py")
    with c2:
        if st.button("Teacher Dashboard", key="btn_teacher_dashboard"):
            st.switch_page("pages/teacher_dashboard.py")




