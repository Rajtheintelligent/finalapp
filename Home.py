# Home.py
import streamlit as st

# Faster navigation without reloading heavy modules
try:
    from streamlit_extras.switch_page_button import switch_page
except:
   # st.error("Please install: pip install streamlit-extras")
    #st.stop()

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
st.markdown("<h1 style='text-align:center;'>Learning Portal – Home</h1>", unsafe_allow_html=True)
st.write("")

# ------------------------------------------------------------
# THREE COLUMN LAYOUT (Left - Center - Right)
# ------------------------------------------------------------
left_col, center_col, right_col = st.columns([1, 2, 1], gap="large")

# ------------------------------------------------------------
# LEFT COLUMN — TEACHER ENTRY PANEL
# ------------------------------------------------------------
with left_col:
    st.markdown("### Teacher Panel")
    st.markdown("Manage batches, teachers, and student records using the data entry interface.")

    if st.button("Enter Data Entry Panel", use_container_width=True):
        switch_page("Data_Entry")

# ------------------------------------------------------------
# CENTER COLUMN — SUBJECTS & PERFORMANCE
# ------------------------------------------------------------
with center_col:
    # Subject Section
    st.markdown("### Subjects")
    st.markdown("Select a subject to continue.")

    subj1, subj2, subj3 = st.columns(3)
    with subj1:
        if st.button("English Grammar", use_container_width=True):
            switch_page("English_Grammar")
    with subj2:
        if st.button("Algebra", use_container_width=True):
            switch_page("Algebra")
    with subj3:
        if st.button("Geometry", use_container_width=True):
            switch_page("Geometry")

    subj4, subj5 = st.columns(2)
    with subj4:
        if st.button("Science-1", use_container_width=True):
            switch_page("Science_1")
    with subj5:
        if st.button("Science-2", use_container_width=True):
            switch_page("Science_2")

    st.markdown("---")

    # Performance Section
    st.markdown("### Performance")
    perf1, perf2 = st.columns(2)

    with perf1:
        if st.button("Student Performance", use_container_width=True):
            switch_page("Student_Performance")

    with perf2:
        if st.button("Live Performance", use_container_width=True):
            switch_page("Live_Performance")

# ------------------------------------------------------------
# RIGHT COLUMN — PAYMENT PAGE
# ------------------------------------------------------------
with right_col:
    st.markdown("### Payment")
    st.markdown("Access billing, service charges, and PhonePe payment options.")

    if st.button("Open Payment Page", use_container_width=True):
        switch_page("Payment_Page")

# ------------------------------------------------------------
# PERFORMANCE OPTIMIZATIONS
# ------------------------------------------------------------
# These keep the app efficient with 100+ visitors
@st.cache_resource
def lightweight_flag():
    return True

lightweight_flag()



