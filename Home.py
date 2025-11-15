# Home.py
import streamlit as st

try:
    from streamlit_extras.switch_page_button import switch_page
except:
  #  st.error("Please install: pip install streamlit-extras")
   # st.stop()

# ------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------
 st.set_page_config(
    page_title="Learning Portal",
    layout="wide",
)

st.markdown("<h1 style='text-align:center; font-weight:700;'>Learning Portal – Home</h1>", unsafe_allow_html=True)
st.write("")

# ------------------------------------------------------------
# THREE COLUMN LAYOUT
# ------------------------------------------------------------
col_left, col_center, col_right = st.columns([1, 2, 1], gap="large")

# ============================================================
# LEFT COLUMN (Teacher Panel)
# ============================================================
with col_left:
    with st.container(border=True):
        st.markdown("### **Teacher Panel**")
        st.markdown(
            "<div style='font-size:14px; color:grey;'>"
            "Access the panel for managing class, batch, teacher, and student details."
            "</div>",
            unsafe_allow_html=True
        )

        st.write("")
        if st.button("Enter Data Entry Panel", use_container_width=True):
            switch_page("Data_Entry")

# ============================================================
# CENTER COLUMN (Subjects + Performance)
# ============================================================
with col_center:
    with st.container(border=True):
        st.markdown("### **Subjects**")
        st.markdown("<div style='font-size:14px; color:grey;'>Select a subject to continue.</div>", unsafe_allow_html=True)
        st.write("")

        # Subject Buttons
        s1, s2, s3 = st.columns(3)
        with s1:
            if st.button("English Grammar", use_container_width=True):
                switch_page("English_Grammar")
        with s2:
            if st.button("Algebra", use_container_width=True):
                switch_page("Algebra")
        with s3:
            if st.button("Geometry", use_container_width=True):
                switch_page("Geometry")

        s4, s5 = st.columns(2)
        with s4:
            if st.button("Science-1", use_container_width=True):
                switch_page("Science_1")
        with s5:
            if st.button("Science-2", use_container_width=True):
                switch_page("Science_2")

    st.write("")  # spacing

    with st.container(border=True):
        st.markdown("### **Performance**")
        st.markdown("<div style='font-size:14px; color:grey;'>Student progress and real-time performance monitoring.</div>", unsafe_allow_html=True)
        st.write("")

        p1, p2 = st.columns(2)
        with p1:
            if st.button("Student Performance", use_container_width=True):
                switch_page("Student_Performance")

        with p2:
            if st.button("Live Performance", use_container_width=True):
                switch_page("Live_Performance")

# ============================================================
# RIGHT COLUMN (Payment Panel)
# ============================================================
with col_right:
    with st.container(border=True):
        st.markdown("### **Payment**")
        st.markdown(
            "<div style='font-size:14px; color:grey;'>Access billing, payment options and service fee calculations.</div>",
            unsafe_allow_html=True
        )
        st.write("")

        if st.button("Open Payment Page", use_container_width=True):
            switch_page("Payment_Page")

# ------------------------------------------------------------
# PERFORMANCE OPTIMIZATION
# ------------------------------------------------------------
@st.cache_resource
def lightweight_flag():
    return True

lightweight_flag()
