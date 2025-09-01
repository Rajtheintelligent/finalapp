import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import date, datetime
import re
import os

# ---------------------------
# Page config
# ---------------------------
st.set_page_config(page_title="Student Observation — Differentiated Classroom", layout="centered")

# ---------------------------
# PARAMETERS (9 total)
# ---------------------------
PARAMETERS = [
    {"key": "param_1", "title": "Language Complexity", "left": "Simple", "right": "Complex"},
    {"key": "param_2", "title": "Problem Solving", "left": "Guided", "right": "Independent"},
    {"key": "param_3", "title": "Conceptual Understanding", "left": "Surface", "right": "Deep"},
    {"key": "param_4", "title": "Speed of Work", "left": "Slow", "right": "Fast"},
    {"key": "param_5", "title": "Attention", "left": "Distracted", "right": "Focused"},
    {"key": "param_6", "title": "Accuracy", "left": "Error-prone", "right": "Precise"},
    {"key": "param_7", "title": "Self-help Skills", "left": "Dependent", "right": "Autonomous"},
    {"key": "param_8", "title": "Social Interaction", "left": "Reserved", "right": "Proactive"},
    {"key": "param_9", "title": "Task Persistence", "left": "Gives up", "right": "Perseveres"},
]

# ---------------------------
# Try to import DB helpers from db.py. If not present, fall back to local CSV storage
# ---------------------------
USE_DB = False
try:
    from db import save_observation, get_latest_observation, get_observations_history
    # If import succeeds, assume DB-backed functions exist and will be used
    USE_DB = True
except Exception:
    USE_DB = False

# Local fallback storage
LOCAL_RESPONSES_PATH = "observations_store.csv"


def fallback_get_latest_observation(class_code: str, email: str):
    if not os.path.exists(LOCAL_RESPONSES_PATH):
        return None
    df = pd.read_csv(LOCAL_RESPONSES_PATH)
    mask = (df["class_code"].astype(str) == str(class_code)) & (df["email"].str.lower() == str(email).lower())
    if not mask.any():
        return None
    row = df[mask].sort_values("observation_date", ascending=False).iloc[0]
    return row.to_dict()


def fallback_save_observation(class_code: str, email: str, obs_date: date, params: dict, teacher_email: str = None, notes: str = None):
    # read existing or create
    if os.path.exists(LOCAL_RESPONSES_PATH):
        df = pd.read_csv(LOCAL_RESPONSES_PATH)
    else:
        df = pd.DataFrame(columns=["class_code","email","observation_date"] + [p["key"] for p in PARAMETERS] + ["teacher_email","notes","created_at"])

    # remove previous entries for same class+email+date (we will append)
    mask = (df["class_code"].astype(str) == str(class_code)) & (df["email"].str.lower() == str(email).lower()) & (df["observation_date"] == str(obs_date))
    if mask.any():
        df = df[~mask]

    row = {"class_code": class_code, "email": email, "observation_date": str(obs_date)}
    for k, v in params.items():
        row[k] = int(v)
    row["teacher_email"] = teacher_email
    row["notes"] = notes
    row["created_at"] = datetime.utcnow().isoformat()

    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(LOCAL_RESPONSES_PATH, index=False)
    return True


def fallback_get_observations_history(class_code: str, email: str):
    if not os.path.exists(LOCAL_RESPONSES_PATH):
        return pd.DataFrame()
    df = pd.read_csv(LOCAL_RESPONSES_PATH)
    mask = (df["class_code"].astype(str) == str(class_code)) & (df["email"].str.lower() == str(email).lower())
    return df[mask].sort_values("observation_date")

# Bind functions
if not USE_DB:
    save_observation_fn = fallback_save_observation
    get_latest_observation_fn = fallback_get_latest_observation
    get_observations_history_fn = fallback_get_observations_history
else:
    save_observation_fn = save_observation
    get_latest_observation_fn = get_latest_observation
    get_observations_history_fn = get_observations_history

# ---------------------------
# Register loader (from st.secrets)
# ---------------------------
@st.cache_data(ttl=300)
def load_register_df():
    raw = None
    try:
        raw = st.secrets.get("google", {}).get("register_sheet_url") if st.secrets else None
    except Exception:
        raw = None

    if not raw:
        return pd.DataFrame()

    m = re.search(r"/d/([a-zA-Z0-9-_]+)", raw)
    if m:
        sid = m.group(1)
        csv_url = f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv&gid=0"
    else:
        csv_url = raw

    try:
        df = pd.read_csv(csv_url)
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception as e:
        st.warning(f"Could not load register sheet as CSV. Error: {e}")
        return pd.DataFrame()

# ---------------------------
# UI
# ---------------------------
# Top bar with Home link (top-left)
home_col1, home_col2 = st.columns([1, 9])
with home_col1:
    if st.button("🏠 Home"):
        # If your app uses multipage navigation, replace the next line with your preferred navigation action
        try:
            st.experimental_set_query_params(page="home")
        except Exception:
            pass
with home_col2:
    st.markdown("# Teacher — Differentiated Observation")

st.write("---")

st.markdown("""
This page lets a teacher record personal observations for a student across multiple differentiated-classroom parameters.

Provide the batch/class code and the student's email; the app will verify them against your register (Google Sheet). Then move the sliders to record the student's current level. You can save and later re-open or update these values.
""")


# Input boxes
col1, col2, col3 = st.columns([3, 4, 3])
with col1:
    class_code = st.text_input("Class / Batch Code", placeholder="e.g. 1100")
with col2:
    email = st.text_input("Student Email ID", placeholder="student@example.com")
with col3:
    obs_date = st.date_input("Observation Date", value=date.today())

# Optional: teacher email and notes
teacher_col1, teacher_col2 = st.columns([3, 7])
with teacher_col1:
    teacher_email = st.text_input("Your (teacher) email (optional)")
with teacher_col2:
    notes = st.text_area("Notes (optional)", height=80)

# Verify button
verify = st.button("🔎 Verify student")

register_df = load_register_df()
verified = False
if verify:
    if register_df.empty:
        st.warning("Register sheet not loaded; please check st.secrets['google']['register_sheet_url'].")
    else:
        cols = {c.lower(): c for c in register_df.columns}
        tuition_col = cols.get("tuition_code") or cols.get("tuition_code") or None
        email_col = cols.get("student_email") or cols.get("student_email") or cols.get("student_email") or None
        # be lenient: try variations
        if not tuition_col:
            for k in register_df.columns:
                if k.lower().strip() in ("tuition_code", "class_code", "batch", "batch_code"):
                    tuition_col = k
                    break
        if not email_col:
            for k in register_df.columns:
                if "email" in k.lower() and ("student" in k.lower() or True):
                    email_col = k
                    break

        if not tuition_col or not email_col:
            st.warning("Register sheet doesn't contain expected columns. Found: " + ", ".join(register_df.columns))
        else:
            matches = register_df[
                (register_df[tuition_col].astype(str).str.strip() == str(class_code).strip()) &
                (register_df[email_col].astype(str).str.lower().str.strip() == str(email).lower().strip())
            ]
            if not matches.empty:
                st.success("Student verified in register ✔️")
                # show some helpful info if present
                std_name = None
                for key in ("Student_Name", "StudentName", "student_name", "studentname", "Student_Name "):
                    if key in matches.columns:
                        std_name = matches.iloc[0][key]
                        break
                if pd.notna(std_name):
                    st.write(f"**Student:** {std_name}")
                verified = True
            else:
                st.error("No match found for the provided Tuition_Code and Student_Email.")

# Load latest observation (DB or fallback)
existing_obs = None
if class_code and email:
    try:
        existing_obs = get_latest_observation_fn(class_code, email)
    except Exception:
        existing_obs = None

if existing_obs is not None:
    st.info(f"Found previous observation on {existing_obs.get('observation_date') if isinstance(existing_obs, dict) else getattr(existing_obs, 'observation_date', None)} — values loaded below. You can edit and Save to update.")

st.write("---")

# Sliders
st.subheader("Observation Sliders")
st.caption("Scale: 1 (very weak) — 6 (excellent)")

slider_values = {}
for p in PARAMETERS:
    st.markdown(f"**{p['title']}**")
    cols = st.columns([1, 6, 1])
    with cols[0]:
        st.write(p['left'])
    with cols[1]:
        default_val = 3
        if existing_obs is not None:
            # existing_obs may be a dict (fallback) or object (DB)
            if isinstance(existing_obs, dict):
                default_val = int(existing_obs.get(p['key'], 3) if existing_obs.get(p['key'], 3) is not None else 3)
            else:
                default_val = int(getattr(existing_obs, p['key'], 3) or 3)
        slider_values[p['key']] = st.slider(label="", min_value=1, max_value=6, value=int(default_val), key=p['key'])
    with cols[2]:
        st.write(p['right'])
    st.write("")

# Save button
if st.button("💾 Save observation"):
    if not class_code or not email:
        st.error("Please enter Class code and Email before saving.")
    else:
        row_params = {k: int(v) for k, v in slider_values.items()}
        try:
            success = save_observation_fn(class_code=class_code, email=email, obs_date=obs_date, params=row_params, teacher_email=teacher_email or None, notes=notes or None)
            if success:
                st.success("Observation saved.")
                # reload latest
                existing_obs = get_latest_observation_fn(class_code, email)
            else:
                st.warning("Save function did not return True. Check logs.")
        except Exception as e:
            st.error(f"Error saving observation: {e}")

st.write("---")

# ---------------------------
# Graph
# ---------------------------
st.subheader("Progress Graph")
view_choice = st.radio("Graph type", options=['Single combined line (all parameters)', 'Separate small plots (each parameter)'], horizontal=True)

labels = [p['title'] for p in PARAMETERS]
values = [slider_values[p['key']] for p in PARAMETERS]

fig = plt.figure(figsize=(8, 4))
ax = fig.add_subplot(111)
if view_choice.startswith('Single'):
    x = np.arange(len(labels))
    ax.plot(x, values, marker='o')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha='right')
    ax.set_ylim(1, 6)
    ax.set_ylabel('Score (1-6)')
    ax.set_title('Observation — combined')
    ax.grid(axis='y', linestyle='--', alpha=0.5)
else:
    fig.clf()
    n = len(labels)
    fig, axs = plt.subplots(nrows=n, ncols=1, figsize=(6, 2*n), constrained_layout=True)
    for i, lab in enumerate(labels):
        axs[i].plot([1, 2], [values[i], values[i]], marker='o')
        axs[i].set_xlim(0.5, 2.5)
        axs[i].set_ylim(1, 6)
        axs[i].set_yticks([1, 2, 3, 4, 5, 6])
        axs[i].set_xticks([])
        axs[i].set_ylabel('')
        axs[i].set_title(lab)

# Show the figure
st.pyplot(fig)

# Downloadable PNG
buf = BytesIO()
fig.savefig(buf, format='png', bbox_inches='tight')
buf.seek(0)
filename_safe_email = email.replace('@', '_at_').replace('.', '_') if email else "unknown"
st.download_button(label="📥 Download graph (PNG)", data=buf, file_name=f"observation_{class_code}_{filename_safe_email}_{obs_date}.png", mime="image/png")

# Download history CSV
if class_code and email:
    try:
        hist_df = get_observations_history_fn(class_code, email)
        if hist_df is not None and not hist_df.empty:
            csv_bytes = hist_df.to_csv(index=False).encode('utf-8')
            st.download_button("📄 Download student's history (CSV)", data=csv_bytes, file_name=f"history_{class_code}_{filename_safe_email}.csv", mime='text/csv')
        else:
            st.info("No historical observations found for this student.")
    except Exception as e:
        st.warning(f"Could not load history: {e}")

st.write("---")

st.caption("Notes: To use PostgreSQL DB, add `Observation` model and helper functions (save_observation, get_latest_observation, get_observations_history) to your db.py and set USE_DB by ensuring those functions import successfully. If no DB is available, this page will fall back to a local CSV file (observations_store.csv).")
