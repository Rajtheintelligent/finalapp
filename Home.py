import streamlit as st
# --- Sidebar lock state (persistent in session) ---
if "sidebar_unlocked" not in st.session_state:
    st.session_state.sidebar_unlocked = False

# Replace this with a password of your choice
SIDEBAR_PASSWORD = "aaaa"  # <<< change this!

# Sidebar content - only visible when unlocked
if st.session_state.sidebar_unlocked:
    st.sidebar.title("🔧 Select Options (Unlocked)")
    board = st.sidebar.selectbox("Select Board", ["SSC", "ICSE"])
    subject = st.sidebar.selectbox("Select Subject", ["Mathematics", "Science", "English", "Social Studies"])
    st.sidebar.markdown("---")
    st.sidebar.markdown("📬 **[Feedback Form](https://forms.gle/your-feedback-form)**")
    # small control to lock again
    if st.sidebar.button("🔒 Lock sidebar"):
        st.session_state.sidebar_unlocked = False
        st.experimental_rerun()
else:
    # minimal locked sidebar
    st.sidebar.title("🔒 Sidebar Locked")
    st.sidebar.info("Sidebar is hidden. Unlock from the main page to edit.")

# ---------------------- Main Page UI (box + buttons) ----------------------
# Use an expander (native Streamlit widget that provides a boxed look) as the "rectangular border"
with st.expander("SSC", expanded=True):
    st.write("Select an SSC subject to open its page:")

    # three subject buttons in one row
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Mathematics", key="btn_ssc_math"):
            # navigate to the multipage app page named "SSC_Maths"
            st.experimental_set_query_params(page="SSC_Maths")
            st.experimental_rerun()
    with col2:
        if st.button("Science", key="btn_ssc_science"):
            st.experimental_set_query_params(page="SSC_Science")
            st.experimental_rerun()
    with col3:
        if st.button("English", key="btn_ssc_english"):
            st.experimental_set_query_params(page="SSC_English")
            st.experimental_rerun()

    st.markdown("---")
    # two additional buttons underneath
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Student Drilldown", key="btn_student_drilldown"):
            st.experimental_set_query_params(page="student_Drilldown")
            st.experimental_rerun()
    with c2:
        if st.button("Teacher Dashboard", key="btn_teacher_dashboard"):
            st.experimental_set_query_params(page="teacher_Dashboard")
            st.experimental_rerun()

# ---------------------- Sidebar Unlock controls in MAIN area ----------------------
st.write("")  # spacer
if not st.session_state.sidebar_unlocked:
    st.subheader("🔐 Unlock Sidebar (for your edits)")
    pwd = st.text_input("Enter sidebar password", type="password", key="unlock_pwd")
    if st.button("Unlock Sidebar", key="unlock_btn"):
        if pwd == SIDEBAR_PASSWORD:
            st.session_state.sidebar_unlocked = True
            st.success("Sidebar unlocked. You can now edit the sidebar (visible only to you while unlocked).")
            st.experimental_rerun()
        else:
            st.error("Wrong password. Try again.")
else:
    st.info("Sidebar is unlocked for you. Use the sidebar to make edits; press 'Lock sidebar' inside the sidebar when done.")

