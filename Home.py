# Home.py
import streamlit as st

# ------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------
st.set_page_config(
    page_title="Learning Portal",
    layout="wide",
)

# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------
st.markdown(
    "<h1 style='text-align:center; font-weight:700;'>Learning Portal – Home</h1>",
    unsafe_allow_html=True
)
st.write("")

# ------------------------------------------------------------
# 3 COLUMN LAYOUT
# ------------------------------------------------------------
col_left, col_center, col_right = st.columns([1, 2, 1], gap="large")

# ------------------------------------------------------------
# LEFT COLUMN — TEACHER PANEL
# ------------------------------------------------------------
with col_left:
    with st.container(border=True):
        st.markdown("### **Teacher Panel**")
        st.markdown(
            "<div style='font-size:14px; color:grey;'>Manage classes, batches, teachers, and students.</div>",
            unsafe_allow_html=True,
        )
        st.write("")

        if st.button("Enter Data Entry Panel", use_container_width=True):
            st.switch_page("pages/Data_Entry.py")

# ------------------------------------------------------------
# CENTER COLUMN — SUBJECTS & PERFORMANCE
# ------------------------------------------------------------
with col_center:
    # Subject Box
    with st.container(border=True):
        st.markdown("### **Subjects**")
        st.markdown("<div style='font-size:14px; color:grey;'>Select a subject to continue.</div>", unsafe_allow_html=True)
        st.write("")

        s1, s2, s3 = st.columns(3)

        with s1:
            if st.button("English Grammar", use_container_width=True):
                st.switch_page("pages/English_Grammar.py")

        with s2:
            if st.button("Algebra", use_container_width=True):
                st.switch_page("pages/Algebra.py")

        with s3:
            if st.button("Geometry", use_container_width=True):
                st.switch_page("pages/Geometry.py")

        s4, s5 = st.columns(2)

        with s4:
            if st.button("Science-1", use_container_width=True):
                st.switch_page("pages/Science_1.py")

        with s5:
            if st.button("Science-2", use_container_width=True):
                st.switch_page("pages/Science_2.py")

    st.write("")

    # Performance Box
    with st.container(border=True):
        st.markdown("### **Performance**")
        st.markdown(
            "<div style='font-size:14px; color:grey;'>Student progress & live tracking.</div>",
            unsafe_allow_html=True,
        )
        st.write("")

        p1, p2 = st.columns(2)

        with p1:
            if st.button("Student Performance", use_container_width=True):
                st.switch_page("pages/Student_Performance.py")

        with p2:
            if st.button("Live Performance", use_container_width=True):
                st.switch_page("pages/Live_Performance.py")

# ------------------------------------------------------------
# RIGHT COLUMN — PAYMENT PAGE
# ------------------------------------------------------------
with col_right:
    with st.container(border=True):
        st.markdown("### **Payment**")
        st.markdown(
            "<div style='font-size:14px; color:grey;'>Billing, UPI payments and pricing.</div>",
            unsafe_allow_html=True
        )
        st.write("")

        if st.button("Open Payment Page", use_container_width=True):
            st.switch_page("pages/Payment_Page.py")

# ------------------------------------------------------------
# PERFORMANCE OPTIMIZATION
# ------------------------------------------------------------
@st.cache_resource
def lightweight_flag():
    return True

lightweight_flag()
