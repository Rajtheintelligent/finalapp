# pages/4_Geometry.py
import streamlit as st

# ------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------
st.set_page_config(
    page_title="Geometry",
    layout="wide",
)

# ------------------------------------------------------------
# PAGE HEADER
# ------------------------------------------------------------
st.markdown(
    "<h1 style='text-align:center; font-weight:700;'>Geometry</h1>",
    unsafe_allow_html=True,
)
st.write("")

# ------------------------------------------------------------
# MAIN CONTENT CONTAINER
# ------------------------------------------------------------
with st.container(border=True):
    st.markdown("### **Overview**")
    st.markdown(
        """
        Welcome to the Geometry section.  
        This page will contain chapter-wise explanations, solved examples, diagrams,
        interactive tools, and assessments for SSC Maharashtra (Class 10).
        """
    )

    st.markdown("---")

    # Chapter buttons or navigation
    st.markdown("### **Chapters**")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.button("1. Basic Geometrical Concepts", use_container_width=True)

    with c2:
        st.button("2. Lines & Angles", use_container_width=True)

    with c3:
        st.button("3. Triangles", use_container_width=True)

    c4, c5, c6 = st.columns(3)

    with c4:
        st.button("4. Quadrilaterals", use_container_width=True)

    with c5:
        st.button("5. Circles", use_container_width=True)

    with c6:
        st.button("6. Coordinate Geometry", use_container_width=True)

    st.markdown("---")

    st.markdown("### **Upcoming Features**")
    st.markdown(
        """
        - Interactive Geometry diagrams  
        - Problem sets with step-by-step solutions  
        - Objective practice (MCQ)  
        - Previous year board exam questions  
        - Chapter-wise tests  
        """
    )
