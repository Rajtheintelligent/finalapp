import streamlit as st
import pandas as pd
from io import StringIO

# ------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------
st.set_page_config(page_title="Admin — CSV Data Entry", layout="wide")

# ------------------------------------------------------------
# CACHE HELPERS
# ------------------------------------------------------------
@st.cache_data
def make_template_df():
    # create template with header and one example row
    cols = [
        "ClassesName",
        "Grade",
        "HeadTeacher",
        "HeadTeacherEmail",
        "HeadTeacherPassword",
        "Batch",
        "StudentName",
        "StudentEmail",
        "StudentPassword",
    ]
    example = {
        "ClassesName": "Grade 10 - A",
        "Grade": "10",
        "HeadTeacher": "Ms. Anita Rao",
        "HeadTeacherEmail": "anita@example.com",
        "HeadTeacherPassword": "ExamplePass123",
        "Batch": "Batch-A",
        "StudentName": "Ravi Kumar",
        "StudentEmail": "ravi.kumar@example.com",
        "StudentPassword": "StuPass123",
    }
    df = pd.DataFrame([example], columns=cols)
    return df

@st.cache_data
def parse_uploaded_csv(uploaded) -> pd.DataFrame:
    # returns dataframe or raises
    if uploaded is None:
        return pd.DataFrame()
    try:
        df = pd.read_csv(uploaded)
    except Exception:
        df = pd.read_excel(uploaded)
    return df

# ------------------------------------------------------------
# SESSION STATE INIT
# ------------------------------------------------------------
if "uploaded_df" not in st.session_state:
    st.session_state.uploaded_df = pd.DataFrame()

# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------
st.title("📥 Admin — CSV-based Data Entry")
st.markdown(
    "This page provides a simple, formal CSV workflow so teachers can prepare student lists offline and upload them in one batch."
)
st.markdown("---")

# ------------------------------------------------------------
# Left: Template download + upload area
# ------------------------------------------------------------
left, right = st.columns([2, 2])

with left:
    st.subheader("1) Download CSV template")
    st.write(
        "Click the button below to download a CSV template. The first row is an example for reference. Only use the columns shown in the template."
    )

    template_df = make_template_df()
    csv_bytes = template_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ Download CSV template",
        data=csv_bytes,
        file_name="students_template.csv",
        mime="text/csv",
    )

    st.markdown("---")
    st.subheader("2) Upload completed CSV")
    st.write("Select the completed CSV file using the button below. The file will be validated before import.")

    uploaded_file = st.file_uploader("Upload CSV (required columns: ClassesName, Grade, HeadTeacher, HeadTeacherEmail, HeadTeacherPassword, Batch, StudentName, StudentEmail, StudentPassword)", type=["csv", "xlsx"], accept_multiple_files=False)

    if uploaded_file:
        try:
            df = parse_uploaded_csv(uploaded_file)
            required_cols = [
                "ClassesName",
                "Grade",
                "HeadTeacher",
                "HeadTeacherEmail",
                "HeadTeacherPassword",
                "Batch",
                "StudentName",
                "StudentEmail",
                "StudentPassword",
            ]
            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                st.error(f"Uploaded file is missing required columns: {missing}")
            else:
                # limit check: max 40 students per batch
                counts = df.groupby('Batch').size().to_dict()
                violating = {b: n for b, n in counts.items() if n > 40}
                if violating:
                    st.error(f"Batch size limit exceeded for: {violating}. Each batch can have up to 40 students.")
                else:
                    st.success("File validated successfully.")
                    st.session_state.uploaded_df = df
                    st.dataframe(df)
                    st.markdown("**Summary by batch:**")
                    st.table(pd.DataFrame(list(counts.items()), columns=['Batch','Count']))

                    # final import button (writes to session storage; replace with DB write later)
                    if st.button("✅ Import to system (session only)"):
                        # In production, replace this with DB write helper
                        st.session_state.imported_df = df.copy()
                        st.success(f"Imported {len(df)} rows into session storage. (Replace with DB write in production)")
        except Exception as e:
            st.exception(e)

# ------------------------------------------------------------
# Right: Actions and utilities
# ------------------------------------------------------------
with right:
    st.subheader("Utilities")
    st.write("After uploading and validating the CSV you may import or use the utilities below.")

    # Download last imported data
    if 'imported_df' in st.session_state and not st.session_state.imported_df.empty:
        st.download_button(
            label="📥 Download last imported (CSV)",
            data=st.session_state.imported_df.to_csv(index=False),
            file_name="last_imported_students.csv",
            mime="text/csv",
        )
    else:
        st.info("No data imported yet. Upload a CSV and use 'Import to system' first.")

    st.markdown("---")
    st.write("**Student password change**")
    st.write("(Placeholder) — click to open password-change workflow for a batch. Implementation details to follow.")
    if st.button("🔁 Student password change"):
        st.info("Student password-change workflow will be implemented here. You can upload a CSV with updated passwords or select individual students once connected to the DB.")

    st.markdown("---")
    st.write("**Get batch details**")
    st.write("(Placeholder) — download batch-wise student and teacher lists. When connected to DB this will query the requested batch(es).")
    if st.button("📂 Get batch details"):
        if 'imported_df' in st.session_state and not st.session_state.imported_df.empty:
            # produce zipped csv per batch or a single file
            df = st.session_state.imported_df
            st.success("Batch details prepared below.")
            # show a table of counts
            st.table(df.groupby('Batch').size().rename('Count').reset_index())
            # provide per-batch CSV downloads
            batches = sorted(df['Batch'].unique())
            for b in batches:
                sub = df[df['Batch'] == b]
                st.download_button(label=f"Download {b} (CSV)", data=sub.to_csv(index=False), file_name=f"batch_{b}.csv", mime="text/csv")
        else:
            st.info("No imported data in session. Upload & import a CSV first.")

st.markdown("---")
st.caption("Notes: This page uses a simple CSV workflow to keep load on the server minimal. Currently imports store data in the Streamlit session; replace the import action with a DB write when you are ready to integrate MySQL.")
