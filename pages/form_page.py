import streamlit as st

# Get query parameters from URL
params = st.query_params
subject = params.get("subject", "Unknown")
subtopic = params.get("subtopic", "Unknown")

st.title("📄 Assessment Form")
st.write(f"**Subject:** {subject}")
st.write(f"**Subtopic:** {subtopic}")

# Dynamic form loading
if subject == "SSC_Maths" and subtopic == "ratio_of_areas_of_two_triangles":
    st.write("🔹 This is the SSC Maths form for 'Ratios of areas of two triangles'.")
    st.text_input("Enter your answer")
    st.button("Submit")

elif subject == "ICSE_Science" and subtopic == "photosynthesis":
    st.write("🔹 This is the ICSE Science form for 'Photosynthesis'.")
    st.text_input("Enter your answer")
    st.button("Submit")

else:
    st.warning("No form found for this subject and subtopic yet.")
