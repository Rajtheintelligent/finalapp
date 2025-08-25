# student_drilldown.py
"""
Student Drill-Down page for teachers.

Features:
 - Independent page (no auto-refresh) so teacher input/results won't disappear.
 - Formal horizontal stacked bar chart (Correct vs Incorrect) per subtopic.
 - Class-average comparison alongside student's performance.
 - Table summary, downloads (CSV/Excel), and per-question drill-down.
 - Resilient: supports either get_student_summary() from db or computes from get_batch_performance().
"""

import streamlit as st
import pandas as pd
import numpy as np
import io
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

# --- Import DB helpers (adjust to your project's db module) ---
from db import get_batch_performance, get_student_responses
# Try to import get_student_summary if available; otherwise we'll compute below.
try:
    from db import get_student_summary  # optional
    HAS_SUMMARY = True
except Exception:
    HAS_SUMMARY = False

# ---------------------------
# Page config & small helpers
# ---------------------------
st.set_page_config(page_title="Student Drill-Down", layout="wide")

def df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Report")
    buf.seek(0)
    return buf.read()

def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")

def percent_str(num, denom):
    if denom == 0:
        return "—"
    return f"{100 * num/denom:.0f}%"

# ---------------------------
# Subject label mapping
# ---------------------------
# If your DB stores different subject strings than you want to show the teacher,
# put them here. Example: show "Geometry" in UI but query "Mathematics" in DB.
LABEL_MAP = {
    # UI label : DB value
    "Geometry": "Mathematics",   # <-- adjust if your DB uses 'Mathematics' for geometry forms
    "Algebra": "Mathematics",    # (if both Algebra & Geometry were grouped under Mathematics)
    "English": "english",        # example of lower-case entry in DB
    # Add more mappings if needed (UI_label: DB_value)
}

# ---------------------------
# Inputs (persist with session_state)
# ---------------------------
st.title("🔍 Student Drill-Down — Teacher View")
st.markdown("Enter the batch, subject and student email to view subject-wise performance. "
            "The chart shows correct vs incorrect counts per subtopic and compares with class average.")

# Keep inputs in session_state so teacher can interact without losing selections
if "dd_batch" not in st.session_state:
    st.session_state.dd_batch = ""
if "dd_subject_ui" not in st.session_state:
    st.session_state.dd_subject_ui = list(LABEL_MAP.keys())[0] if LABEL_MAP else ""
if "dd_subject_custom" not in st.session_state:
    st.session_state.dd_subject_custom = ""
if "dd_email" not in st.session_state:
    st.session_state.dd_email = ""

col1, col2, col3 = st.columns([2, 2, 2])
with col1:
    st.session_state.dd_batch = st.text_input("Batch (Tuition Code)", value=st.session_state.dd_batch)
with col2:
    # show labels from LABEL_MAP + an option "Other"
    ui_subject_options = list(LABEL_MAP.keys()) + ["Other"]
    st.session_state.dd_subject_ui = st.selectbox("Subject (UI)", options=ui_subject_options,
                                                  index=ui_subject_options.index(st.session_state.dd_subject_ui)
                                                  if st.session_state.dd_subject_ui in ui_subject_options else 0)
    if st.session_state.dd_subject_ui == "Other":
        st.session_state.dd_subject_custom = st.text_input("Enter DB subject value (exact)", value=st.session_state.dd_subject_custom)
with col3:
    st.session_state.dd_email = st.text_input("Student Email", value=st.session_state.dd_email)

# Button to trigger query
go = st.button("Show Student Summary", type="primary")

# ---------------------------
# Resolve subject (UI -> DB)
# ---------------------------
def resolve_subject_value(ui_label, custom):
    if ui_label == "Other":
        return (custom or "").strip()
    return LABEL_MAP.get(ui_label, ui_label)

subject_db = resolve_subject_value(st.session_state.dd_subject_ui, st.session_state.dd_subject_custom)
batch_code = st.session_state.dd_batch.strip()
student_email = st.session_state.dd_email.strip()

# Validation message area
def show_validation(msg):
    st.warning(msg)

# ---------------------------
# Main logic: fetch & render
# ---------------------------
if go:
    if not batch_code:
        show_validation("Please provide Batch (Tuition Code).")
    elif not subject_db:
        show_validation("Please select a subject (or enter the DB subject in 'Other').")
    elif not student_email:
        show_validation("Please enter a student's email.")
    else:
        try:
            # 1) Load class-level performance (all students) for this batch & subject
            class_perf_df = get_batch_performance(batch_code, subject_db, None)  # DataFrame: per-student per-subtopic

            if class_perf_df.empty:
                st.info("No submissions found for this batch & subject combination.")
            else:
                # Compute class totals per subtopic (sum across students)
                class_group = class_perf_df.groupby("Subtopic", as_index=False).agg(
                    Class_Correct=("Correct", "sum"),
                    Class_Incorrect=("Incorrect", "sum")
                )
                class_group["Class_Total"] = class_group["Class_Correct"] + class_group["Class_Incorrect"]
                class_group["Class_AccuracyPct"] = class_group.apply(
                    lambda r: (r.Class_Correct / r.Class_Total * 100) if r.Class_Total > 0 else np.nan, axis=1
                )

                # 2) Student-level summary: try get_student_summary() if available; otherwise compute
                if HAS_SUMMARY:
                    student_summary = get_student_summary(batch_code, subject_db, student_email)
                    # expected columns: Subtopic, Correct, Incorrect, Total
                else:
                    # compute from class_perf_df: select rows for this student
                    sdf = class_perf_df[class_perf_df["Student_Email"].astype(str).str.strip() == student_email]
                    if sdf.empty:
                        student_summary = pd.DataFrame(columns=["Subtopic", "Correct", "Incorrect", "Total"])
                    else:
                        student_summary = (
                            sdf.groupby("Subtopic", as_index=False).agg(
                                Correct=("Correct", "sum"),
                                Incorrect=("Incorrect", "sum")
                            )
                        )
                        student_summary["Total"] = student_summary["Correct"] + student_summary["Incorrect"]

                if student_summary.empty:
                    st.warning("No records found for this student in the selected batch & subject.")
                else:
                    # Merge with class_group to get class comparison
                    merged = pd.merge(student_summary, class_group, on="Subtopic", how="left")
                    merged["Student_AccuracyPct"] = merged.apply(
                        lambda r: (r.Correct / r.Total * 100) if r.Total > 0 else np.nan, axis=1
                    )
                    # fill NaNs in class accuracy (if no class data) with NaN; ok
                    merged = merged.sort_values(by="Student_AccuracyPct", ascending=True, na_position="last").reset_index(drop=True)

                    # Summary cards
                    total_q_student = merged["Total"].sum()
                    total_correct_student = merged["Correct"].sum()
                    overall_student_pct = (100 * total_correct_student / total_q_student) if total_q_student > 0 else np.nan

                    # Class overall for this subject (all subtopics in class_group)
                    class_total_all = class_group["Class_Total"].sum()
                    class_correct_all = class_group["Class_Correct"].sum()
                    overall_class_pct = (100 * class_correct_all / class_total_all) if class_total_all > 0 else np.nan

                    # Top area: KPIs
                    k1, k2, k3, k4 = st.columns([1.6,1.6,1.6,2])
                    k1.metric("Student — Total Questions", f"{int(total_q_student)}", delta=None)
                    k2.metric("Student — Correct", f"{int(total_correct_student)}",
                             delta=f"{overall_student_pct:.0f}%" if not np.isnan(overall_student_pct) else "—")
                    k3.metric("Class — Overall Accuracy", f"{overall_class_pct:.0f}%" if not np.isnan(overall_class_pct) else "—")
                    k4.metric("Student — Overall Accuracy", f"{overall_student_pct:.0f}%" if not np.isnan(overall_student_pct) else "—",
                              help="Student accuracy across all subtopics (higher is better)")

                    st.markdown("---")


                    # ---------------------------
                    # Vertical Stacked Bar Chart (by Subtopic for now)
                    # ---------------------------

                    # 1) Optional: let teacher control bar ordering
                    order_choice = st.selectbox(
                        "Order bars by",
                        ["Original (weakest first)", "Student Accuracy ↑", "Student Accuracy ↓", "Total Questions ↑", "Total Questions ↓"],
                        index=0
                    )
                        
                    if order_choice == "Student Accuracy ↑":
                        merged = merged.sort_values("Student_AccuracyPct", ascending=True, na_position="last")
                    elif order_choice == "Student Accuracy ↓":
                        merged = merged.sort_values("Student_AccuracyPct", ascending=False, na_position="last")
                    elif order_choice == "Total Questions ↑":
                        merged = merged.sort_values("Total", ascending=True, na_position="last")
                    elif order_choice == "Total Questions ↓":
                        merged = merged.sort_values("Total", ascending=False, na_position="last")
                    # else keep the existing order (which you already set to weakest first)
                            
                    merged = merged.reset_index(drop=True)

                    # 2) Prepare series
                    labels = merged["Subtopic"].astype(str).tolist()
                    corrects = merged["Correct"].astype(int).to_numpy()
                    incorrects = merged["Incorrect"].astype(int).to_numpy()
                    totals = corrects + incorrects
                    student_accs = merged["Student_AccuracyPct"].to_numpy()
                    class_accs = merged["Class_AccuracyPct"].to_numpy()
                       
                    x = np.arange(len(labels))

                    # 3) Sizing/colors
                    n = max(1, len(labels))
                    # Wider and taller than before; width grows a bit with number of bars
                    fig_width = max(12, 0.45 * n + 8)
                    fig_height = 9  # taller chart as requested

                    fig, ax1 = plt.subplots(figsize=(fig_width, fig_height))

                    correct_color = "#2E7D32"   # green
                    incorrect_color = "#C62828" # red

                    # 4) Stacked vertical bars
                    ax1.bar(x, corrects, label="Correct", color=correct_color, edgecolor="none")
                    ax1.bar(x, incorrects, bottom=corrects, label="Incorrect", color=incorrect_color, edgecolor="none")

                    # 5) Count labels inside stacks
                    for i, (c, ic, tot) in enumerate(zip(corrects, incorrects, totals)):
                        # center of the green segment
                        if c > 0:
                            ax1.text(i, c * 0.5, f"{int(c)}", ha="center", va="center", color="white", fontsize=9, weight="bold")
                        # center of the red segment
                        if ic > 0:
                            ax1.text(i, c + ic * 0.5, f"{int(ic)}", ha="center", va="center", color="white", fontsize=9, weight="bold")
                        # accuracy text just above the bar
                        stud_txt = f"{student_accs[i]:.0f}%" if not np.isnan(student_accs[i]) else "—"
                        cls_txt = f"{class_accs[i]:.0f}%" if not np.isnan(class_accs[i]) else "—"
                        ax1.text(i, tot + max(1, tot * 0.03), f"{stud_txt}  (Class {cls_txt})",
                                 ha="center", va="bottom", fontsize=9, color="#222")
                                   
                    # 6) Axes & ticks
                    ax1.set_xticks(x)
                    ax1.set_xticklabels(labels, rotation=45, ha="right", fontsize=10)
                    ax1.yaxis.set_major_locator(MaxNLocator(integer=True))
                    ax1.set_ylabel("Number of Questions", fontsize=11)
                    ax1.set_xlabel("Subtopic", fontsize=11)
                    ax1.set_title(f"{student_email} — {subject_db} (by Subtopic)", fontsize=13, weight="bold", pad=12)

                    # 7) Accuracy overlay (secondary axis). Helpful for trend.
                    ax2 = ax1.twinx()
                    ax2.plot(x, student_accs, marker="o", linestyle="--", label="Student Accuracy %")
                    ax2.plot(x, class_accs, marker="s", linestyle=":", label="Class Accuracy %")
                    ax2.set_ylim(0, 100)
                    ax2.set_ylabel("Accuracy (%)")
                               
                    # 8) Weakness highlight (optional): outline bars where student < 50%
                    for i, (acc, tot) in enumerate(zip(student_accs, totals)):
                        if not np.isnan(acc) and acc < 50:
                            # Draw a subtle outline rectangle around that bar
                            ax1.add_patch(plt.Rectangle((i - 0.5, 0), 1.0, tot if tot > 0 else 0.1,
                                         fill=False, linewidth=1.5))
                         
                    # 9) Legends and layout 
                    ax1.legend(loc="upper left", fontsize=9)
                    ax2.legend(loc="upper right", fontsize=9)
                    plt.tight_layout()
                    st.pyplot(fig, use_container_width=True)

                    # ---------------------------
                    # Tabbed view: Summary table & Per-question detail
                    # ---------------------------
                    tab1, tab2 = st.tabs(["Subtopic Summary", "Per-question Drill-down"])

                    with tab1:
                        st.subheader("Subtopic Summary Table")
                        display_df = merged[["Subtopic", "Correct", "Incorrect", "Total", "Student_AccuracyPct", "Class_AccuracyPct"]].copy()
                        # rename columns for display
                        display_df = display_df.rename(columns={
                            "Subtopic": "Subtopic",
                            "Correct": "Correct",
                            "Incorrect": "Incorrect",
                            "Total": "Total",
                            "Student_AccuracyPct": "Student (%)",
                            "Class_AccuracyPct": "Class (%)"
                        })
                        # format percents
                        display_df["Student (%)"] = display_df["Student (%)"].apply(lambda v: f"{v:.0f}%" if not np.isnan(v) else "—")
                        display_df["Class (%)"] = display_df["Class (%)"].apply(lambda v: f"{v:.0f}%" if not np.isnan(v) else "—")

                        st.dataframe(display_df, use_container_width=True)

                        # Downloads
                        col_d1, col_d2 = st.columns([1,1])
                        with col_d1:
                            csv_bytes = df_to_csv_bytes(display_df)
                            st.download_button("⬇️ Download CSV (Summary)", data=csv_bytes,
                                               file_name=f"{student_email}_{subject_db}_summary.csv",
                                               mime="text/csv")
                        with col_d2:
                            xlsx = df_to_excel_bytes(display_df)
                            st.download_button("⬇️ Download Excel (Summary)", data=xlsx,
                                               file_name=f"{student_email}_{subject_db}_summary.xlsx",
                                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

                    with tab2:
                        st.subheader("Per-question Drill-down")
                        # choose subtopic to inspect
                        chosen_subtopic = st.selectbox("Pick Subtopic", options=merged["Subtopic"].tolist())
                        # fetch question-level responses for that student+subtopic
                        detail_df = get_student_responses(student_email, subject_db, chosen_subtopic)
                        if detail_df.empty:
                            st.info("No per-question data found for this student & subtopic.")
                        else:
                            # show obvious columns and neat formatting
                            detail_df = detail_df.rename(columns={
                                "Question_No": "Q.No",
                                "Student_Answer": "Student Answer",
                                "Correct_Answer": "Correct Answer",
                                "Is_Correct": "Is Correct"
                            })
                            # show 'Is Correct' as tick/cross
                            detail_df["Is Correct"] = detail_df["Is Correct"].apply(lambda v: "✅" if v else "❌")
                            st.dataframe(detail_df, use_container_width=True)

                            # downloads
                            col_a, col_b = st.columns([1,1])
                            with col_a:
                                st.download_button("⬇️ Download CSV (Details)", data=df_to_csv_bytes(detail_df),
                                                   file_name=f"{student_email}_{subject_db}_{chosen_subtopic}_details.csv",
                                                   mime="text/csv")
                            with col_b:
                                st.download_button("⬇️ Download Excel (Details)", data=df_to_excel_bytes(detail_df),
                                                   file_name=f"{student_email}_{subject_db}_{chosen_subtopic}_details.xlsx",
                                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        except Exception as e:
            st.error(f"Error fetching data: {e}")
