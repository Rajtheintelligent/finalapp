import streamlit as st
from urllib.parse import quote

# ------------------------ Page Config ------------------------
st.set_page_config(
    page_title="Grade 10 Assessment Hub",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ------------------------ Hide Sidebar (for users) ------------------------
# Keeps the sidebar hidden so only you (developer) can use it from IDE/dev environment.
hide_sidebar_style = """
    <style>
        /* Hide Streamlit's sidebar entirely for visitors */
        [data-testid="stSidebar"] {display: none !important;}
        [data-testid="stSidebarNav"] {display: none !important;}
        /* Tighter top spacing for the main container */
        .block-container {padding-top: 1.5rem; padding-left: 2rem; padding-right: 2rem;}
        /* Card style used for subjects */
        .subject-card {
            border: 1px solid #e6e6e6;
            padding: 16px;
            border-radius: 10px;
            background: #ffffff;
            box-shadow: 0 1px 4px rgba(20,20,20,0.03);
            height: 100%;
        }
        .subject-title {font-size: 18px; font-weight: 600; margin-bottom: 6px;}
        .subject-sub {color: #555; margin-bottom: 10px; font-size: 13px;}
        .small-meta {font-size:12px; color:#666;}
        .board-header {font-size:20px; font-weight:700; margin-bottom:6px;}
        .board-desc {color:#444; margin-bottom:10px;}
    </style>
"""
st.markdown(hide_sidebar_style, unsafe_allow_html=True)

# ------------------------ Header ------------------------
st.title("📘 Grade 10 Assessment Hub")
st.markdown(
    """
A formal, organised hub for Grade 10 assessments.  
Use the sections below to access board-specific assessments and tools.  
Everything is laid out clearly — no sidebar navigation is required for teachers or students.
"""
)

# ------------------------ Helper: navigation function ------------------------
def open_page_via_query(page_name: str):
    """
    Set a query parameter to indicate the desired page and rerun.
    Multipage Streamlit apps can read the query param to switch or you can implement your own page router.
    If your app uses a different navigation approach, adjust this function accordingly.
    """
    st.experimental_set_query_params(page=page_name)
    st.experimental_rerun()


# ------------------------ Board Section Template ------------------------
def render_board_section(board_name: str, board_description: str, pages: dict):
    st.markdown("---")
    st.markdown(f'<div class="board-header">{board_name}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="board-desc">{board_description}</div>', unsafe_allow_html=True)

    cols = st.columns(4, gap="large")
    i = 0
    for subject, meta in pages.items():
        with cols[i % 4]:
            # Card markup
            card_html = f"""
            <div class="subject-card">
                <div class="subject-title">{subject}</div>
                <div class="subject-sub">{meta.get('short','')}</div>
                <div class="small-meta"><strong>Includes:</strong> {', '.join(meta.get('includes', []))}</div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)

            # Buttons (primary navigation and fallback link)
            # Primary: try to navigate via query param (adjust if your router differs).
            page_name = meta.get("page", "")
            if page_name:
                if st.button(f"Open {subject}", key=f"open_{board_name}_{subject}"):
                    open_page_via_query(page_name)

                # Fallback: direct link to the pages file (useful if server exposes pages folder directly)
                # Encode the page name so markdown link is safe. The exact internal link depends on your deployment.
                fallback_link = f"./pages/{page_name}.py" if not page_name.endswith(".py") else f"./pages/{page_name}"
                st.markdown(f"[Open {subject} (fallback link)]({fallback_link})", unsafe_allow_html=True)
            else:
                st.button("No page configured", key=f"nopage_{board_name}_{subject}")

        i += 1


# ------------------------ Board data ------------------------
ssc_pages = {
    "Mathematics": {
        "short": "Assessment bank for Algebra, Geometry and Problem Solving.",
        "includes": ["Algebra", "Geometry", "Trigonometry"],
        "page": "SSC_Maths"
    },
    "Science": {
        "short": "Physics, Chemistry and Biology assessments and practice modules.",
        "includes": ["Physics", "Chemistry", "Biology"],
        "page": "SSC_Science"
    },
    "English": {
        "short": "Grammar, comprehension and writing skills practice.",
        "includes": ["Grammar", "Comprehension", "Writing"],
        "page": "SSC_English"
    },
    "Social Studies": {
        "short": "History and Geography — topic-wise assessments and timelines.",
        "includes": ["History", "Geography"],
        "page": "SSC_Social_Studies"
    },
}

icse_pages = {
    "Mathematics": {
        "short": "ICSE syllabus math assessments — algebra through coordinate geometry.",
        "includes": ["Algebra", "Geometry", "Coordinate Geometry"],
        "page": "ICSE_Maths"
    },
    "Science": {
        "short": "Comprehensive science practice: Physics, Chemistry, Biology.",
        "includes": ["Physics", "Chemistry", "Biology"],
        "page": "ICSE_Science"
    },
    "English": {
        "short": "Language and literature practice modules and assessments.",
        "includes": ["Language", "Literature", "Composition"],
        "page": "ICSE_English"
    },
    "Social Studies": {
        "short": "ICSE-focused History and Geography materials and tests.",
        "includes": ["History", "Geography", "Civics"],
        "page": "ICSE_Social_Studies"
    },
}

# ------------------------ Render SSC (top) ------------------------
render_board_section("SSC", "Board: State Secondary Certificate (SSC). Choose a subject below to open that board's assessment pages.", ssc_pages)

# ------------------------ Render ICSE (beneath, well separated) ------------------------
render_board_section("ICSE", "Board: Indian Certificate of Secondary Education (ICSE). Subject pages and assessments listed below.", icse_pages)


# ------------------------ Teacher / Admin Tools (optional protection) ------------------------
st.markdown("---")
st.subheader("👩‍🏫 Teacher & Admin Tools")
st.markdown("Teacher tools are intentionally separated. If you want to restrict access, set `ADMIN_PASSWORD` in `st.secrets`.")

admin_pw = st.secrets.get("ADMIN_PASSWORD") if hasattr(st, "secrets") else None
if admin_pw:
    pw = st.text_input("Enter admin password to reveal teacher tools", type="password", key="admin_pw_input")
    if pw and pw == admin_pw:
        st.success("Admin access granted")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Open Teacher Dashboard"):
                open_page_via_query("teacher_dashboard")
        with col2:
            if st.button("Open Student Drilldown"):
                open_page_via_query("student_drilldown")
    elif pw:
        st.error("Incorrect password")
else:
    # No secret set — show buttons (you can enable secret to hide)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Open Teacher Dashboard"):
            open_page_via_query("teacher_dashboard")
    with col2:
        if st.button("Open Student Drilldown"):
            open_page_via_query("student_drilldown")


# ------------------------ Footer (formal) ------------------------
st.markdown("---")
st.markdown(
    """
**Contact / Feedback:** For operational issues or feedback, please use the feedback form.  
© 2025 Grade 10 Assessment Hub — All rights reserved.
"""
)
