"""
Student Exam Performance Dashboard (Streamlit)
Based on: Mina Nassim - Student Exam Performance Project
Run:  streamlit run app.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# ------------------------------------------------------------------
# Page config & style
# ------------------------------------------------------------------
st.set_page_config(page_title="Student Performance Dashboard", page_icon="🎓", layout="wide")

PRIMARY = "#2f7f79"
PASS_C, FAIL_C = "#2E8B57", "#D94343"

st.markdown(
    f"""
<style>
.banner {{background: linear-gradient(135deg,#376f6b,#55b0a3); padding: 48px 20px;
         border-radius: 14px; text-align:center; color:white; margin-bottom: 14px;}}
.banner h1 {{color:white; margin:0; font-size:2.2rem;}}
.banner p {{margin:8px 0 0 0; font-size:1.05rem; opacity:.95;}}
.note {{background:#f1f5f9; border-left:5px solid {PRIMARY}; padding:12px 16px;
        border-radius:6px; margin: 8px 0 18px 0;}}
[data-testid="stMetric"] {{background:white; border:1px solid #e5e7eb; border-radius:10px;
        padding:14px 18px; box-shadow:0 1px 3px rgba(0,0,0,.05);}}
</style>
""",
    unsafe_allow_html=True,
)


def banner(title: str, subtitle: str):
    st.markdown(f'<div class="banner"><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)


def note(text: str):
    st.markdown(f'<div class="note">{text}</div>', unsafe_allow_html=True)


# ------------------------------------------------------------------
# Data loading + cleaning (same steps as the notebook)
# ------------------------------------------------------------------
CSV_NAME = "student_exam_performance.csv"
CANDIDATES = [Path(__file__).parent / CSV_NAME, Path(__file__).parent / "data" / CSV_NAME]


@st.cache_data(show_spinner="Loading data...")
def load_data(path: str | None, uploaded_bytes: bytes | None = None) -> pd.DataFrame:
    if uploaded_bytes is not None:
        import io
        df = pd.read_csv(io.BytesIO(uploaded_bytes))
    else:
        df = pd.read_csv(path)

    # flags for imputed values (so the user can exclude them)
    df["imputed_flag"] = df[["previous_gpa", "attendance_percentage"]].isna().any(axis=1)

    # --- cleaning (notebook section 2) ---
    for c in ["parent_education", "notes_quality", "sleep_quality", "device_availability"]:
        if c in df.columns:
            df[c] = df[c].fillna("Unknown")
    for c in ["previous_gpa", "attendance_percentage", "time_management_score"]:
        if c in df.columns:
            df[c] = df[c].fillna(df[c].median())

    # --- derived columns ---
    df["pass_status"] = df["pass_status"].astype(str).str.strip().str.title()
    df["is_fail"] = (df["pass_status"] == "Fail").astype(int)
    df["score_change"] = df["exam_score"] - df["previous_exam_score"]

    df["study_hours_group"] = pd.cut(
        df["study_hours_per_day"], [0, 1, 2, 3, 4, 5, np.inf],
        labels=["0–1", "1–2", "2–3", "3–4", "4–5", "5+"], include_lowest=True)
    df["attendance_group"] = pd.cut(
        df["attendance_percentage"], [0, 60, 70, 80, 90, 100.01],
        labels=["<60%", "60–70%", "70–80%", "80–90%", "90–100%"], right=False, include_lowest=True)
    df["sleep_group"] = pd.cut(
        df["sleep_hours"], [0, 5, 6, 7, 8, 24],
        labels=["<5h", "5–6h", "6–7h", "7–8h", "8h+"], right=False, include_lowest=True)
    df["anxiety_group"] = pd.cut(
        df["exam_anxiety_level"], [0, 2, 4, 6, 8, 10],
        labels=["0–2", "2–4", "4–6", "6–8", "8–10"], include_lowest=True)
    df["previous_score_group"] = pd.cut(
        df["previous_exam_score"], [0, 50, 60, 70, 80, 100.01],
        labels=["<50", "50–60", "60–70", "70–80", "80+"], right=False, include_lowest=True)
    return df


def get_df() -> pd.DataFrame:
    path = next((p for p in CANDIDATES if p.exists()), None)
    if path is not None:
        return load_data(str(path))
    st.sidebar.warning(f"`{CSV_NAME}` not found. Upload it below.")
    up = st.sidebar.file_uploader("Upload CSV", type="csv")
    if up is None:
        st.info("Place `student_exam_performance.csv` next to `app.py` (or in `data/`), or upload it from the sidebar.")
        st.stop()
    return load_data(None, up.getvalue())


df = get_df()

# ------------------------------------------------------------------
# Navigation + sidebar filters
# ------------------------------------------------------------------


def overview():
    banner("Student Performance Overview", "High-level exam results and trends")
    d = fdf
    st.caption(f"Active Filters: {len(d):,} rows" + (" | Basis: excluding imputed values" if exclude_imputed else ""))

    st.header("📊 Performance")
    with st.container(border=True):
        c = st.columns(4)
        c[0].metric("Students", f"{len(d):,}")
        c[1].metric("Avg Exam Score", f"{d.exam_score.mean():.1f}")
        c[2].metric("Pass Rate", f"{(1 - d.is_fail.mean()) * 100:.1f}%")
        c[3].metric("Fail Rate", f"{d.is_fail.mean() * 100:.1f}%")
        c = st.columns(4)
        c[0].metric("Avg Previous Score", f"{d.previous_exam_score.mean():.1f}")
        c[1].metric("Score Change", f"{d.score_change.mean():+.1f}")
        c[2].metric("Avg Study Hours / Day", f"{d.study_hours_per_day.mean():.2f}")
        c[3].metric("Avg Attendance", f"{d.attendance_percentage.mean():.1f}%")
    st.caption("Pass = exam score of 50 or more.")

    st.header("🌍 Student Reach")
    with st.container(border=True):
        c = st.columns(4)
        c[0].metric("School Types", d.school_type.nunique())
        c[1].metric("Education Levels", d.education_level.nunique())
        c[2].metric("Avg GPA (previous)", f"{d.previous_gpa.mean():.2f}")
        c[3].metric("Private Tuition", f"{d.private_tuition.mean() * 100:.0f}%")

        by_school = d.groupby("school_type").exam_score.mean().sort_values(ascending=False)
        by_income = d.groupby("family_income").exam_score.mean().sort_values(ascending=False)
        by_area = d.groupby("urban_rural").exam_score.mean().sort_values(ascending=False)
        c = st.columns(3)
        c[0].metric("Best School Type", by_school.index[0], f"{by_school.iloc[0]:.2f}")
        c[1].metric("Best Income Group", by_income.index[0], f"{by_income.iloc[0]:.2f}")
        c[2].metric("Best Area", by_area.index[0], f"{by_area.iloc[0]:.2f}")

    st.header("🎯 Results Distribution")
    c1, c2 = st.columns(2)
    cnt = d.pass_status.value_counts().reset_index()
    cnt.columns = ["Status", "Students"]
    fig = px.pie(cnt, names="Status", values="Students", hole=0.5, color="Status",
                 color_discrete_map={"Pass": PASS_C, "Fail": FAIL_C}, title="Pass vs Fail")
    c1.plotly_chart(fig, width="stretch")
    fig = px.histogram(d, x="exam_score", nbins=40, color="pass_status",
                       color_discrete_map={"Pass": PASS_C, "Fail": FAIL_C}, title="Exam Score Distribution")
    c2.plotly_chart(fig, width="stretch")

    bins = [0, 20, 40, 60, 80, 100.01]
    labels = ["0–20", "20–40", "40–60", "60–80", "80–100"]
    prev = pd.cut(d.previous_exam_score, bins, labels=labels, right=False, include_lowest=True).value_counts(normalize=True)
    curr = pd.cut(d.exam_score, bins, labels=labels, right=False, include_lowest=True).value_counts(normalize=True)
    comp = pd.DataFrame({"Previous": prev * 100, "Current": curr * 100}).reindex(labels).reset_index()
    comp = comp.melt(id_vars="index", var_name="Exam", value_name="% of students")
    fig = px.bar(comp, x="index", y="% of students", color="Exam", barmode="group", text_auto=".1f",
                 labels={"index": "Score group"}, title="Previous vs Current Score Distribution")
    st.plotly_chart(fig, width="stretch")


def drivers():
    banner("Study Habits & Wellbeing", "How effort, attendance and sleep relate to results")
    d = fdf
    st.header("📚 Effort & Routine")

    def rate_bar(col, title, color):
        g = d.groupby(col, observed=True).agg(students=("is_fail", "size"), fail_rate=("is_fail", "mean"),
                                              avg_score=("exam_score", "mean")).reset_index()
        g["fail_rate"] *= 100
        fig = px.bar(g, x=col, y="fail_rate", text=g["fail_rate"].map(lambda v: f"{v:.1f}%"),
                     color_discrete_sequence=[color], title=title,
                     labels={"fail_rate": "Fail rate (%)"}, hover_data=["students", "avg_score"])
        return fig

    c1, c2 = st.columns(2)
    c1.plotly_chart(rate_bar("study_hours_group", "Fail Rate by Study Hours / Day", "#c8514d"), width="stretch")
    c2.plotly_chart(rate_bar("attendance_group", "Fail Rate by Attendance", "#1b3a5c"), width="stretch")
    c1, c2 = st.columns(2)
    c1.plotly_chart(rate_bar("sleep_group", "Fail Rate by Sleep Hours", "#e6a756"), width="stretch")
    c2.plotly_chart(rate_bar("anxiety_group", "Fail Rate by Exam Anxiety", "#7A5BA6"), width="stretch")

    st.header("🧮 Study Hours vs Score")
    corr = d["study_hours_per_day"].corr(d["exam_score"])
    corr_prev = d["previous_exam_score"].corr(d["exam_score"])
    note(f"Correlation between study hours and exam score is <b>{corr:.2f}</b>; "
         f"between previous and current score it is <b>{corr_prev:.2f}</b>.")
    sample = d.sample(min(len(d), 5000), random_state=1)
    fig = px.scatter(sample, x="study_hours_per_day", y="exam_score", color="pass_status", opacity=0.45,
                     color_discrete_map={"Pass": PASS_C, "Fail": FAIL_C}, title="Study Hours vs Exam Score (5k sample)")
    st.plotly_chart(fig, width="stretch")

    st.header("📝 Exam Difficulty & Previous Score")
    c1, c2 = st.columns(2)
    order = ["Easy", "Medium", "Hard"]
    g = d.groupby("exam_difficulty").agg(fail_rate=("is_fail", "mean"), students=("is_fail", "size")).reindex(order).reset_index()
    g["fail_rate"] *= 100
    c1.plotly_chart(px.bar(g, x="exam_difficulty", y="fail_rate", text=g.fail_rate.map(lambda v: f"{v:.1f}%"),
                           title="Fail Rate by Exam Difficulty", color_discrete_sequence=[FAIL_C]), width="stretch")
    c2.plotly_chart(rate_bar("previous_score_group", "Fail Rate by Previous Score", "#c8514d"), width="stretch")


def background():
    banner("Student Background", "Demographics and environment vs. outcomes")
    d = fdf
    dims = {
        "Family Income": "family_income", "School Type": "school_type", "Parent Education": "parent_education",
        "Urban / Rural": "urban_rural", "Gender": "gender", "Education Level": "education_level",
        "Internet Access": "internet_access", "Private Tuition": "private_tuition",
    }
    label = st.selectbox("Group students by", list(dims))
    col = dims[label]
    metric = st.radio("Metric", ["Fail rate (%)", "Average score", "Student count"], horizontal=True)

    g = d.groupby(col).agg(students=("is_fail", "size"), fail_rate=("is_fail", "mean"),
                           avg_score=("exam_score", "mean")).reset_index()
    g["fail_rate"] *= 100
    if col == "family_income":
        order = ["Low", "Lower-Middle", "Middle", "Upper-Middle", "High"]
        g[col] = pd.Categorical(g[col], order, ordered=True)
        g = g.sort_values(col)
    g[col] = g[col].astype(str)
    y = {"Fail rate (%)": "fail_rate", "Average score": "avg_score", "Student count": "students"}[metric]
    fig = px.bar(g, x=col, y=y, text_auto=".1f", color_discrete_sequence=[PRIMARY],
                 title=f"{metric} by {label}", hover_data=["students"])
    st.plotly_chart(fig, width="stretch")
    st.dataframe(g.round(2), width="stretch", hide_index=True)

    pf = pd.crosstab(d[col].astype(str), d["pass_status"]).reset_index().melt(id_vars=col, var_name="Status", value_name="Students")
    st.plotly_chart(px.bar(pf, x=col, y="Students", color="Status", barmode="group", text_auto=",",
                           color_discrete_map={"Pass": PASS_C, "Fail": FAIL_C}, title=f"Pass vs Fail by {label}"),
                    width="stretch")


def risk():
    banner("Risk & Recommendations", "Who needs support and what to do about it")
    d = fdf

    failed_both = d[(d.previous_exam_score < 50) & (d.exam_score < 50)]
    drop = d[(d.previous_exam_score >= 80) & (d.exam_score < 50)]
    top = d[d.exam_score >= 80]

    c = st.columns(4)
    c[0].metric("Failed Both Exams", f"{len(failed_both):,}", f"{len(failed_both) / max(len(d), 1) * 100:.2f}% of students", delta_color="off")
    c[1].metric("80+ Before → Failed Now", f"{len(drop):,}")
    c[2].metric("Currently 80+", f"{len(top):,}")
    c[3].metric("Avg Score Drop (all)", f"{d.score_change.mean():+.1f}")

    st.header("🔍 What separates top students from the rest?")
    factors = ["study_hours_per_day", "self_study_hours", "practice_tests_completed", "exam_preparation_days", "sleep_hours"]
    factors = [f for f in factors if f in d.columns]
    comp = pd.DataFrame({"Currently 80+": top[factors].mean(), "Failed both": failed_both[factors].mean(),
                         "80+ before → failed now": drop[factors].mean()}).round(2)
    st.dataframe(comp, width="stretch")
    cm = comp.reset_index().melt(id_vars="index", var_name="Group", value_name="Average")
    st.plotly_chart(px.bar(cm, x="index", y="Average", color="Group", barmode="group", text_auto=".1f",
                           labels={"index": "Factor"}), width="stretch")

    st.header("⚠️ At-risk students")
    st.caption("Students with a previous score below 60, attendance below 80% **or** study hours under 2 per day — sorted by lowest exam score.")
    mask = (d.previous_exam_score < 60) | (d.attendance_percentage < 80) | (d.study_hours_per_day < 2)
    cols = ["student_id", "school_type", "previous_exam_score", "attendance_percentage", "study_hours_per_day",
            "sleep_hours", "exam_difficulty", "exam_score", "pass_status"]
    risk_df = d.loc[mask & (d.pass_status == "Fail"), cols].sort_values("exam_score")
    st.write(f"**{len(risk_df):,}** failing students match at least one risk rule.")
    st.dataframe(risk_df.head(500), width="stretch", hide_index=True)
    st.download_button("⬇️ Download at-risk list (CSV)", risk_df.to_csv(index=False).encode("utf-8"),
                       "at_risk_students.csv", "text/csv")

    st.header("✅ Recommendations")
    st.markdown(
        """
1. **Raise daily study hours** gradually (fail rate drops sharply above 4–5 hours/day) with progress monitoring.
2. **Keep attendance above 90%** through early identification, monitoring and incentives.
3. **Promote healthy sleep** (7–8+ hours) — average scores rise with every extra sleep hour band.
4. **Target low-income students** with extra support to reduce the gap in failure rates.
5. **Support students who dropped from 80+ to a fail**: more practice tests and structured revision.
6. **Reduce exam anxiety** with stress-management and exam-skills programs.
7. **Investigate the score decline** versus the previous year (attendance, motivation, stress, study methods).
"""
    )


nav = st.navigation(
    [
        st.Page(overview, title="Overview", icon=":material/dashboard:", default=True),
        st.Page(drivers, title="Study Insights", icon=":material/monitoring:", url_path="insights"),
        st.Page(background, title="Background", icon=":material/groups:", url_path="background"),
        st.Page(risk, title="Risk and Support", icon=":material/health_and_safety:", url_path="risk"),
    ]
)

st.sidebar.divider()
st.sidebar.header("Filters")


def ms(label, col):
    opts = sorted(df[col].dropna().astype(str).unique())
    with st.sidebar.expander(label):
        return st.multiselect(label, opts, default=opts, label_visibility="collapsed", key=col)


f_gender = ms("Gender", "gender")
f_school = ms("School Type", "school_type")
f_level = ms("Education Level", "education_level")
f_income = ms("Family Income", "family_income")
f_diff = ms("Exam Difficulty", "exam_difficulty")
exclude_imputed = st.sidebar.toggle("Exclude rows with imputed GPA / attendance", value=False)

fdf = df[
    df.gender.astype(str).isin(f_gender)
    & df.school_type.astype(str).isin(f_school)
    & df.education_level.astype(str).isin(f_level)
    & df.family_income.astype(str).isin(f_income)
    & df.exam_difficulty.astype(str).isin(f_diff)
]
if exclude_imputed:
    fdf = fdf[~fdf.imputed_flag]

if fdf.empty:
    st.warning("No data for the selected filters.")
    st.stop()

nav.run()
