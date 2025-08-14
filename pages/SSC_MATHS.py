import streamlit as st

st.set_page_config(page_title="SSC Mathematics", layout="wide")

def show_subtopics(subject, subtopics):
    for topic, ids in subtopics.items():
        with st.expander(f"🔹 {topic}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                form_url = f"/form_page?subject={subject}&subtopic_id={ids['Form']}"
                st.link_button("Open Form", form_url)
            with col2:
                st.link_button("Open Kahoot", ids["Kahoot"])
            with col3:
                st.link_button("Open Blooket", ids["Blooket"])

# Example chapter
chapter = st.selectbox("Select Chapter", [
    "Linear Equations",
    "Quadratic Equations",
    "Similarity"
])

if chapter == "Similarity":
    subtopics = {
        "Ratios of Areas of Two Triangles": {
            "Form": "Ratio_of_Areas_of_two_triangles",
            "Kahoot": "https://kahoot.com/example-sim1",
            "Blooket": "https://blooket.com/example-sim1"
        },
        "Word Problems on Linear Equations": {
            "Form": "Word_Problems_Linear_Equations",
            "Kahoot": "https://kahoot.com/example-wple",
            "Blooket": "https://blooket.com/example-wple"
        }
    }
    show_subtopics("Mathematics", subtopics)

elif chapter == "Similarity":
    subtopics = {
        "Ratios of Areas of Two Triangles": {
            "Form": "Ratio_of_Areas_of_Two_Triangles",
            "Kahoot": "https://kahoot.com/example-sim1",
            "Blooket": "https://blooket.com/example-sim1"
        }
    }
    show_subtopics("Mathematics", subtopics)
