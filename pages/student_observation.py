import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import date, datetime
import re
import os
from matplotlib.backends.backend_pdf import PdfPages

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
    if os.path.exists(LOCAL_RESPONSES_PATH):
        df = pd.read_csv(LOCAL_RESPONSES_PATH)
    else:
        df = pd.DataFrame(columns=["class_code","email","observation_date"] + [p["key"] for p in PARAMETERS] + ["teacher_email","notes","created_at"])

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
# CSS for boxed sliders and buttons
# ---------------------------
st.markdown(
    "<style>
"
    ".slider-box{border:1px solid #e6e6e6;border-radius:10px;padding:12px;margin-bottom:12px;background:#ffffff;box-shadow:0 1px 3px rgba(0,0,0,0.04);}
"
    ".scale-row{display:flex;justify-content:space-between;padding:0 6px;font-size:0.9rem;color:#444;}
"
    ".scale-legend{font-size:0.85rem;color:#666;margin-top:6px;}
"
    ".graph-btn{display:inline-block;padding:8px 16px;margin-right:6px;border-radius:8px;border:1px solid #cfcfcf;background:#f6f6f6;cursor:pointer;}
"
    ".graph-btn.active{background:#17549a;color:white;border-color:#17549a;}
"
    "@media (max-width:600px){ .slider-box{padding:10px} .scale-row{font-size:0.8rem} }
"
    "</style>", unsafe_allow_html=True
)

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

# Optional: teacher email and notes (these notes will be included in the PDF/PNG downloads)
teacher_col1, teacher_col2 = st.columns([3, 7])
with teacher_col1:
    teacher_email = st.text_input("Your (teacher) email (optional)")
with teacher_col2:
    notes = st.text_area("Notes (these will be included in downloaded report)", height=100)

# Verify student
verify = st.button("🔎 Verify student")
register_df = load_register_df()
verified = False
if verify:
    if register_df.empty:
        st.warning("Register sheet not loaded; please check st.secrets['google']['register_sheet_url'].")
    else:
        cols = {c.lower(): c for c in register_df.columns}
        tuition_col = None
        email_col = None
        for k in register_df.columns:
            lk = k.lower()
            if lk in ("tuition_code", "class_code", "tuition", "batch", "batch_code"):
                tuition_col = k
            if "email" in lk and ("student" in lk or "parent" not in lk):
                # prefer student email
                email_col = k
        if not tuition_col or not email_col:
            st.warning("Register sheet doesn't contain expected Tuition_Code / Student_Email columns. Found: " + ", ".join(register_df.columns))
        else:
            matches = register_df[
                (register_df[tuition_col].astype(str).str.strip() == str(class_code).strip()) &
                (register_df[email_col].astype(str).str.lower().str.strip() == str(email).lower().strip())
            ]
            if not matches.empty:
                st.success("Student verified in register ✔️")
                std_name = matches.iloc[0].get("Student_Name") if "Student_Name" in matches.columns else None
                if pd.notna(std_name):
                    st.write(f"**Student:** {std_name}")
                verified = True
            else:
                st.error("No match found for the provided Tuition_Code and Student_Email.")

# Load existing observation
existing_obs = None
if class_code and email:
    try:
        existing_obs = get_latest_observation_fn(class_code, email)
    except Exception:
        existing_obs = None

if existing_obs is not None:
    date_str = existing_obs.get('observation_date') if isinstance(existing_obs, dict) else getattr(existing_obs, 'observation_date', None)
    st.info(f"Found previous observation on {date_str} — values loaded below. You can edit and Save to update.")

st.write("---")

# Render sliders inside boxes with clear 1-6 scale
st.subheader("Observation Sliders")
st.caption("Scale: 1 (very weak) — 6 (excellent)")

slider_values = {}
for p in PARAMETERS:
    # boxed area
    st.markdown(f"<div class=\"slider-box\">", unsafe_allow_html=True)
    st.markdown(f"**{p['title']}**")
    cols = st.columns([1, 6, 1])
    with cols[0]:
        st.write(p['left'])
    with cols[1]:
        default_val = 3
        if existing_obs is not None:
            if isinstance(existing_obs, dict):
                default_val = int(existing_obs.get(p['key'], 3) if existing_obs.get(p['key'], 3) is not None else 3)
            else:
                default_val = int(getattr(existing_obs, p['key'], 3) or 3)
        # slider
        slider_values[p['key']] = st.slider(label="", min_value=1, max_value=6, value=int(default_val), key=p['key'])
        # visual ticks row
        st.markdown(
            "<div class=\"scale-row\">
" +
            "<div>1</div><div>2</div><div>3</div><div>4</div><div>5</div><div>6</div>
" +
            "</div>", unsafe_allow_html=True
        )
        st.markdown(f"<div class=\"scale-legend\">1 = Very weak · 6 = Excellent</div>", unsafe_allow_html=True)
    with cols[2]:
        st.write(p['right'])
    st.markdown("</div>", unsafe_allow_html=True)

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
                existing_obs = get_latest_observation_fn(class_code, email)
            else:
                st.warning("Save function did not return True. Check logs.")
        except Exception as e:
            st.error(f"Error saving observation: {e}")

st.write("---")

# ---------------------------
# Graph type selection using buttons (persisted in session_state)
# ---------------------------
if 'graph_type' not in st.session_state:
    st.session_state['graph_type'] = 'combined'

col_a, col_b = st.columns([1,1])
with col_a:
    if st.button("Combined view"):
        st.session_state['graph_type'] = 'combined'
with col_b:
    if st.button("Separate tiles"):
        st.session_state['graph_type'] = 'tiles'

# Small CSS to visually indicate active button (Streamlit won't change button HTML; show a small text)
st.markdown(f"**Selected graph:** {st.session_state['graph_type'].capitalize()}")

# ---------------------------
# Graph generation (more professional styling)
# ---------------------------
labels = [p['title'] for p in PARAMETERS]
values = [slider_values[p['key']] for p in PARAMETERS]

# Helper: create combined professional chart
def create_combined_figure(labels, values):
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(labels))
    # line with markers
    ax.plot(x, values, marker='o', linewidth=3, markersize=8)
    # fill under curve for emphasis
    ax.fill_between(x, values, 1, alpha=0.12)
    # highlight low scores
    for xi, yi in zip(x, values):
        color = '#d9534f' if yi <= 2 else ('#f0ad4e' if yi <= 3 else '#5cb85c')
        ax.scatter([xi], [yi], s=140, color=color, zorder=5)
        ax.annotate(str(yi), (xi, yi+0.12), ha='center', fontsize=10, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha='right')
    ax.set_ylim(0.8, 6.4)
    ax.set_yticks([1,2,3,4,5,6])
    ax.set_ylabel('Score (1-6)')
    ax.set_title('Differentiated Observation — Combined View')
    # summary box for teacher
    avg = np.mean(values)
    low_count = sum(1 for v in values if v <= 3)
    summary_text = f"Average: {avg:.2f} · Parameters needing attention (<=3): {low_count}"
    ax.text(0.01, 0.98, summary_text, transform=ax.transAxes, fontsize=10, va='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    ax.grid(axis='y', linestyle='--', alpha=0.6)
    plt.tight_layout()
    return fig

# Helper: create tiles figure (3x3 grid of horizontal bars)
def create_tiles_figure(labels, values):
    n = len(labels)
    cols = 3
    rows = int(np.ceil(n/cols))
    fig, axs = plt.subplots(rows, cols, figsize=(10, 3*rows))
    axs = axs.flatten()
    for i, (lab, val) in enumerate(zip(labels, values)):
        ax = axs[i]
        ax.barh([0], [val], height=0.6)
        ax.set_xlim(0, 6)
        ax.set_yticks([])
        ax.set_title(f"{lab} — {val}")
        ax.set_xticks([1,2,3,4,5,6])
        # color indicating level
        bar = ax.patches[0]
        if val <= 2:
            bar.set_color('#d9534f')
        elif val <= 3:
            bar.set_color('#f0ad4e')
        else:
            bar.set_color('#5cb85c')
    # hide unused axes
    for j in range(n, len(axs)):
        fig.delaxes(axs[j])
    plt.suptitle('Parameter Tiles — quick teacher view')
    plt.tight_layout(rect=[0,0,1,0.96])
    return fig

# Create figure based on selection
if st.session_state['graph_type'] == 'combined':
    fig = create_combined_figure(labels, values)
else:
    fig = create_tiles_figure(labels, values)

st.pyplot(fig)

# ---------------------------
# Downloads: create PDF (preferred) and PNG. Include teacher notes on PDF.
# ---------------------------
# Prepare filename-safe email
filename_safe_email = email.replace('@', '_at_').replace('.', '_') if email else "unknown"

# PDF creation
pdf_buf = BytesIO()
with PdfPages(pdf_buf) as pdf:
    # first page: the figure
    pdf.savefig(fig, bbox_inches='tight')
    # second page: teacher notes + metadata
    fig2 = plt.figure(figsize=(8.27, 11.69))  # A4
    fig2.text(0.01, 0.98, f"Student: {filename_safe_email}    Batch: {class_code}    Date: {obs_date}", fontsize=10)
    fig2.text(0.01, 0.92, "Teacher Notes:", fontsize=12, fontweight='bold')
    wrapped = notes or "--"
    # simple wrapping
    fig2.text(0.01, 0.86, wrapped, fontsize=10)
    pdf.savefig(fig2, bbox_inches='tight')

pdf_buf.seek(0)

# PNG creation
png_buf = BytesIO()
fig.savefig(png_buf, format='png', bbox_inches='tight')
png_buf.seek(0)

st.download_button(label="📥 Download report (PDF)", data=pdf_buf, file_name=f"observation_report_{class_code}_{filename_safe_email}_{obs_date}.pdf", mime="application/pdf")
st.download_button(label="📥 Download graph (PNG)", data=png_buf, file_name=f"observation_{class_code}_{filename_safe_email}_{obs_date}.png", mime="image/png")

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

st.caption("Notes: the PDF download includes the chart and the teacher notes. If you are using DB mode, notes are saved to the DB. Otherwise they are stored in the local CSV fallback.")
