
import html
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.helper import load_processed_data
from utils.ui import (
    render_chart,
    render_metric_cards,
    render_page_header,
    style_plotly_figure,
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="Student Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# LOAD DATA
# =========================================================
try:
    df = load_processed_data()

except Exception as error:
    st.error(f"Could not load the student dataset: {error}")
    st.info(
        "Check that data/student_performance.csv exists and "
        "contains the required columns."
    )
    st.stop()


SUBJECTS = ["Python", "SQL", "Power BI", "AI"]
REQUIRED_COLUMNS = [
    "Student",
    *SUBJECTS,
    "Attendance",
    "Total Marks",
    "Average",
    "Grade",
    "Rank",
]

missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]

if missing:
    st.error("Missing required columns: " + ", ".join(missing))
    st.stop()

df = df.copy()

# Remove blank student names without modifying the source CSV.
df["Student"] = df["Student"].fillna("").astype(str).str.strip()
df = df[df["Student"] != ""].copy()

if df.empty:
    st.warning("No valid student records were found.")
    st.stop()

# Make sure numeric columns have numeric types.
for column in SUBJECTS + ["Attendance", "Total Marks", "Average", "Rank"]:
    df[column] = pd.to_numeric(df[column], errors="coerce")

df = df.dropna(subset=["Average", "Attendance"]).copy()

if df.empty:
    st.warning("No valid numeric student records are available.")
    st.stop()

# Keep grade values consistent for filtering and reporting.
df["Grade"] = df["Grade"].astype("string").str.strip().str.upper()

# Deterministic order for dropdowns.
student_options = sorted(
    df["Student"].unique().tolist(),
    key=str.casefold,
)


# =========================================================
# REUSABLE SORT FUNCTION
# =========================================================
SORT_OPTIONS = {
    "Rank — best first": ("Rank", True),
    "Average — highest first": ("Average", False),
    "Average — lowest first": ("Average", True),
    "Attendance — highest first": ("Attendance", False),
    "Attendance — lowest first": ("Attendance", True),
    "Total marks — highest first": ("Total Marks", False),
    "Student name — A to Z": ("Student", True),
}


def sort_students(data, sort_option):
    """Return a newly sorted DataFrame without modifying the input."""
    column, ascending = SORT_OPTIONS[sort_option]

    result = data.copy()
    result["_student_sort_key"] = (
        result["Student"].astype("string").fillna("").str.casefold()
    )
    sort_columns = (
        ["_student_sort_key"]
        if column == "Student"
        else [column, "_student_sort_key"]
    )
    sort_order = [True] if column == "Student" else [ascending, True]

    return (
        result.sort_values(
            sort_columns,
            ascending=sort_order,
            kind="stable",
            na_position="last",
        )
        .drop(columns="_student_sort_key")
        .reset_index(drop=True)
    )


available_grades = [
    grade
    for grade in ["A", "B", "C", "F"]
    if grade in set(df["Grade"].dropna().tolist())
]

def filter_students(data, selected_students, average_range, attendance_range, grades):
    """Return records matching one view's local controls."""
    mask = (
        data["Average"].between(*average_range, inclusive="both")
        & data["Attendance"].between(*attendance_range, inclusive="both")
        & data["Grade"].isin(grades)
    )

    if selected_students:
        mask &= data["Student"].isin(selected_students)

    return data.loc[mask].copy()


# =========================================================
# PAGE HEADER
# =========================================================
render_page_header(
    "Student Performance",
    "Explore results, compare students, and identify areas for improvement.",
)

# Class-wide summary; view-specific filters are applied inside each tab.
render_metric_cards(
    [
        ("Class Size", len(df), "Full class size"),
        ("Class Average", f"{df['Average'].mean():.2f}%", None),
        ("Average Attendance", f"{df['Attendance'].mean():.2f}%", None),
    ],
    columns=3,
)


# =========================================================
# CLASS LEADERS — ALWAYS USE THE FULL DATASET
# =========================================================
topper = df.sort_values(
    ["Average", "Student"],
    ascending=[False, True],
    kind="stable",
).iloc[0]

lowest = df.sort_values(
    ["Average", "Student"],
    ascending=[True, True],
    kind="stable",
).iloc[0]


# =========================================================
# TABS
# =========================================================
tab_overview, tab_student, tab_compare, tab_records = st.tabs(
    [
        "Overview",
        "Student Details",
        "Compare Students",
        "Rankings & Report",
    ]
)


# =========================================================
# TAB 1: OVERVIEW
# =========================================================
with tab_overview:
    st.header("Filter overview insights")
    overview_students_col, overview_average_col = st.columns(2)
    with overview_students_col:
        overview_students = st.multiselect(
            "Students",
            options=student_options,
            default=student_options,
            key="overview_student_selection",
        )
    with overview_average_col:
        overview_average = st.slider(
            "Average marks (%)",
            min_value=0,
            max_value=100,
            value=(0, 100),
            key="overview_average_range",
        )

    overview_attendance_col, overview_grade_col = st.columns(2)
    with overview_attendance_col:
        overview_attendance = st.slider(
            "Attendance (%)",
            min_value=0,
            max_value=100,
            value=(0, 100),
            key="overview_attendance_range",
        )
    with overview_grade_col:
        overview_grades = st.multiselect(
            "Grades",
            options=available_grades,
            default=available_grades,
            key="overview_grades",
        )

    def reset_overview_filters():
        st.session_state["overview_student_selection"] = student_options
        st.session_state["overview_average_range"] = (0, 100)
        st.session_state["overview_attendance_range"] = (0, 100)
        st.session_state["overview_grades"] = available_grades

    st.button(
        "Reset overview filters",
        on_click=reset_overview_filters,
        key="reset_overview_filters",
    )

    overview_df = filter_students(
        df,
        overview_students,
        overview_average,
        overview_attendance,
        overview_grades,
    )

    st.divider()
    st.header("Class leaders")

    leader1, leader2 = st.columns(2)

    with leader1:
        with st.container(border=True):
            st.subheader("🏆 Class Topper")
            st.write(f"**{topper['Student']}**")
            st.metric("Average", f"{topper['Average']:.2f}%")
            st.metric("Total marks", f"{topper['Total Marks']:.2f}")
            st.caption(
                f"Grade: {topper['Grade']} · "
                f"Attendance: {topper['Attendance']:.2f}%"
            )

    with leader2:
        with st.container(border=True):
            st.subheader("📘 Lowest Class Average")
            st.write(f"**{lowest['Student']}**")
            st.metric("Average", f"{lowest['Average']:.2f}%")
            st.metric("Total marks", f"{lowest['Total Marks']:.2f}")
            st.caption(
                f"Grade: {lowest['Grade']} · "
                f"Attendance: {lowest['Attendance']:.2f}%"
            )

    st.divider()
    st.header("Insights for selected students")

    st.caption(
        f"{len(overview_df):,} of {len(df):,} students match these overview filters."
    )

    if overview_students:
        st.caption(
            f"Selected students: {len(overview_students):,} | "
            f"Matching rows: {len(overview_df):,}"
        )

        if not overview_df.empty:
            st.dataframe(
                overview_df[
                    ["Student", "Grade", "Average", "Attendance"]
                ],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Average": st.column_config.NumberColumn(
                        "Average (%)",
                        format="%.2f",
                    ),
                    "Attendance": st.column_config.NumberColumn(
                        "Attendance (%)",
                        format="%.2f",
                    ),
                },
            )

    if overview_df.empty:
        st.warning(
            "No students match all of these filters. Adjust the student selection, "
            "score, attendance, or grade controls above."
        )
    else:
        render_metric_cards(
            [
                ("Average Attendance", f"{overview_df['Attendance'].mean():.2f}%", None),
                ("Highest Average", f"{overview_df['Average'].max():.2f}%", None),
                ("Students ≥ 85%", int((overview_df["Average"] >= 85).sum()), None),
                ("Students Below 60%", int((overview_df["Average"] < 60).sum()), None),
            ]
        )

        st.subheader("Subject averages")

        subject_average_df = pd.DataFrame(
            {
                "Subject": SUBJECTS,
                "Average Marks": [
                    overview_df[subject].mean()
                    for subject in SUBJECTS
                ],
            }
        )

        fig_subject = px.bar(
            subject_average_df,
            x="Subject",
            y="Average Marks",
            text="Average Marks",
            color="Subject",
            title="Average marks by subject",
            hover_data={"Average Marks": ":.2f"},
        )

        fig_subject.update_traces(
            texttemplate="%{text:.1f}",
            textposition="outside",
        )

        fig_subject.update_layout(
            showlegend=False,
            yaxis_title="Average marks (%)",
            xaxis_title="",
            yaxis_range=[0, 110],
            margin=dict(l=15, r=15, t=60, b=15),
        )

        render_chart(
            style_plotly_figure(fig_subject),
            config={"displaylogo": False, "scrollZoom": True},
        )

        st.subheader("Attendance and performance")

        fig_attendance = px.scatter(
            overview_df,
            x="Attendance",
            y="Average",
            color="Grade",
            hover_name="Student",
            hover_data=["Total Marks", "Rank"],
            title="Attendance vs average marks",
        )

        fig_attendance.update_layout(
            xaxis_title="Attendance (%)",
            yaxis_title="Average marks (%)",
            xaxis_range=[0, 100],
            yaxis_range=[0, 100],
            margin=dict(l=15, r=15, t=60, b=15),
        )

        render_chart(
            style_plotly_figure(fig_attendance),
            config={"displaylogo": False, "scrollZoom": True},
        )


# =========================================================
# TAB 2: INDIVIDUAL STUDENT DETAILS
# =========================================================
with tab_student:
    st.header("Student profile")

    # Uses all students, not only filtered students.
    selected_student = st.selectbox(
        "Choose a student",
        options=student_options,
        key="individual_student",
    )

    student_matches = df[df["Student"] == selected_student]

    if student_matches.empty:
        st.warning("No matching student record was found.")
    else:
        student = student_matches.iloc[0]

        render_metric_cards(
            [
                ("Average", f"{student['Average']:.2f}%", None),
                ("Total Marks", f"{student['Total Marks']:.2f}", None),
                ("Grade", str(student["Grade"]), None),
                ("Class Rank", str(student["Rank"]), None),
            ]
        )

        st.subheader("Subject marks")

        selected_subjects = st.multiselect(
            "Choose subjects",
            options=SUBJECTS,
            default=SUBJECTS,
            key="individual_subjects",
        )

        if selected_subjects:
            student_subject_df = pd.DataFrame(
                {
                    "Subject": selected_subjects,
                    "Marks": [
                        student[subject]
                        for subject in selected_subjects
                    ],
                }
            )

            fig_student = px.bar(
                student_subject_df,
                x="Subject",
                y="Marks",
                color="Subject",
                text="Marks",
                title=f"Subject performance — {selected_student}",
                hover_data={"Marks": ":.2f"},
            )

            fig_student.update_traces(
                texttemplate="%{text:.1f}",
                textposition="outside",
            )

            fig_student.update_layout(
                showlegend=False,
                xaxis_title="",
                yaxis_title="Marks (%)",
                yaxis_range=[0, 110],
                margin=dict(l=15, r=15, t=60, b=15),
            )

            render_chart(
                style_plotly_figure(fig_student),
                config={"displaylogo": False, "scrollZoom": True},
            )
        else:
            st.info("Select at least one subject to display the chart.")

        st.subheader("Complete student information")

        details_df = pd.DataFrame(
            {
                "Metric": [
                    "Student",
                    "Python",
                    "SQL",
                    "Power BI",
                    "AI",
                    "Total Marks",
                    "Average",
                    "Grade",
                    "Rank",
                    "Attendance",
                ],
                "Value": [
                    student["Student"],
                    student["Python"],
                    student["SQL"],
                    student["Power BI"],
                    student["AI"],
                    student["Total Marks"],
                    student["Average"],
                    student["Grade"],
                    student["Rank"],
                    student["Attendance"],
                ],
            }
        )

        st.dataframe(
            details_df,
            use_container_width=True,
            hide_index=True,
        )


# =========================================================
# TAB 3: COMPARE STUDENTS
# =========================================================
with tab_compare:
    st.header("Student comparison")

    compare_students = st.multiselect(
        "Select students to compare (up to 10)",
        options=student_options,
        default=student_options[: min(2, len(student_options))],
        max_selections=10,
        key="compare_student_selection",
    )

    compare_subjects = st.multiselect(
        "Select subjects",
        options=SUBJECTS,
        default=SUBJECTS,
        key="compare_subject_selection",
    )
    comparison_sort = st.selectbox(
        "Sort comparison table by",
        options=list(SORT_OPTIONS.keys()),
        index=0,
        key="compare_sort",
    )

    if not compare_students:
        st.info("Select at least one student to begin comparing.")
    elif not compare_subjects:
        st.info("Select at least one subject to compare.")
    else:
        compare_df = df[
            df["Student"].isin(compare_students)
        ].copy()

        compare_long = compare_df.melt(
            id_vars=["Student", "Average", "Grade", "Attendance", "Rank"],
            value_vars=compare_subjects,
            var_name="Subject",
            value_name="Marks",
        )

        fig_compare = px.bar(
            compare_long,
            x="Subject",
            y="Marks",
            color="Student",
            barmode="group",
            hover_data=["Average", "Grade", "Attendance", "Rank"],
            title="Subject-wise comparison",
        )

        fig_compare.update_layout(
            yaxis_title="Marks (%)",
            xaxis_title="",
            yaxis_range=[0, 100],
            margin=dict(l=15, r=15, t=60, b=15),
        )

        render_chart(
            style_plotly_figure(fig_compare),
            config={"displaylogo": False, "scrollZoom": True},
        )

        st.subheader("Overall comparison")

        comparison_columns = [
            "Student",
            *compare_subjects,
            "Total Marks",
            "Average",
            "Grade",
            "Attendance",
            "Rank",
        ]

        comparison_summary = sort_students(
            compare_df,
            comparison_sort,
        )[comparison_columns]

        st.dataframe(
            comparison_summary,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Average": st.column_config.NumberColumn(
                    "Average (%)",
                    format="%.2f",
                ),
                "Attendance": st.column_config.NumberColumn(
                    "Attendance (%)",
                    format="%.2f",
                ),
            },
        )


# =========================================================
# HTML REPORT GENERATOR
# =========================================================
def create_performance_report(data):
    """Build a full-class HTML report in memory."""

    report_df = data.copy()

    topper_row = report_df.sort_values(
        ["Average", "Student"],
        ascending=[False, True],
        kind="stable",
    ).iloc[0]

    lowest_row = report_df.sort_values(
        ["Average", "Student"],
        ascending=[True, True],
        kind="stable",
    ).iloc[0]

    total_students = len(report_df)
    class_average = report_df["Average"].mean()
    avg_attendance = report_df["Attendance"].mean()

    subject_rows = "".join(
        f"""
        <tr>
            <td>{html.escape(subject)}</td>
            <td>{report_df[subject].mean():.2f}%</td>
        </tr>
        """
        for subject in SUBJECTS
    )

    sorted_report = report_df.sort_values(
        ["Rank", "Student"],
        ascending=[True, True],
        kind="stable",
    )

    ranking_rows = ""

    for _, row in sorted_report.iterrows():
        ranking_rows += f"""
        <tr>
            <td>{html.escape(str(row['Rank']))}</td>
            <td>{html.escape(str(row['Student']))}</td>
            <td>{row['Python']:.2f}</td>
            <td>{row['SQL']:.2f}</td>
            <td>{row['Power BI']:.2f}</td>
            <td>{row['AI']:.2f}</td>
            <td>{row['Total Marks']:.2f}</td>
            <td>{row['Average']:.2f}%</td>
            <td>{html.escape(str(row['Grade']))}</td>
            <td>{row['Attendance']:.2f}%</td>
        </tr>
        """

    attention_df = report_df[
        (report_df["Average"] < 60)
        | (report_df["Attendance"] < 75)
    ].sort_values(
        ["Average", "Attendance"],
        ascending=[True, True],
        kind="stable",
    )

    attention_rows = ""

    for _, row in attention_df.iterrows():
        reasons = []

        if row["Average"] < 60:
            reasons.append("Average below 60%")

        if row["Attendance"] < 75:
            reasons.append("Attendance below 75%")

        attention_rows += f"""
        <tr>
            <td>{html.escape(str(row['Student']))}</td>
            <td>{row['Average']:.2f}%</td>
            <td>{html.escape(str(row['Grade']))}</td>
            <td>{row['Attendance']:.2f}%</td>
            <td>{html.escape(', '.join(reasons))}</td>
        </tr>
        """

    if not attention_rows:
        attention_rows = (
            '<tr><td colspan="5">No students meet the criteria.</td></tr>'
        )

    generated_time = datetime.now().strftime("%d %B %Y, %I:%M %p")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Student Performance Insights</title>
<style>
body {{
    font-family: Arial, sans-serif;
    color: #111827;
    background: #f7f8fa;
    margin: 0;
    padding: 24px;
}}
.container {{
    max-width: 1250px;
    margin: auto;
    background: white;
    padding: 28px;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
}}
header {{
    background: #172554;
    color: white;
    padding: 22px;
    border-radius: 12px;
}}
header p {{ color: #dbeafe; }}
.cards {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px;
}}
.card {{
    padding: 16px;
    background: #f8fafc;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
}}
.card span {{
    display: block;
    color: #6b7280;
    font-size: 13px;
    margin-bottom: 8px;
}}
.card strong {{ font-size: 22px; }}
h2 {{
    color: #1e3a8a;
    margin-top: 28px;
    font-size: 20px;
}}
.table-wrapper {{ overflow-x: auto; }}
table {{
    border-collapse: collapse;
    width: 100%;
    margin: 12px 0 24px;
    font-size: 13px;
}}
th, td {{
    border: 1px solid #e5e7eb;
    padding: 9px;
    text-align: left;
    white-space: nowrap;
}}
th {{ background: #eff6ff; }}
tbody tr:nth-child(even) {{ background: #f8fafc; }}
.leaders {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 12px;
}}
.leader {{
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 16px;
}}
button {{
    padding: 11px 16px;
    background: #1d4ed8;
    color: white;
    border: 0;
    border-radius: 8px;
    cursor: pointer;
}}
@media print {{
    body {{ background: white; padding: 0; }}
    .container {{ border: none; padding: 0; }}
    .print-button {{ display: none; }}
    h2 {{ break-after: avoid; }}
    tr {{ break-inside: avoid; }}
    th, td {{ padding: 5px; font-size: 10px; }}
}}
</style>
</head>
<body>
<div class="container">
<header>
    <h1>Student Performance Insights</h1>
    <p>Complete class analysis and student rankings</p>
    <p>Generated: {generated_time}</p>
</header>

<p>
    <button class="print-button" onclick="window.print()">
        Print / Save as PDF
    </button>
</p>

<h2>1. Class Summary</h2>
<div class="cards">
    <div class="card"><span>Total Students</span><strong>{total_students}</strong></div>
    <div class="card"><span>Class Average</span><strong>{class_average:.2f}%</strong></div>
    <div class="card"><span>Average Attendance</span><strong>{avg_attendance:.2f}%</strong></div>
    <div class="card"><span>Highest Average</span><strong>{report_df['Average'].max():.2f}%</strong></div>
    <div class="card"><span>Lowest Average</span><strong>{report_df['Average'].min():.2f}%</strong></div>
    <div class="card"><span>Students ≥ 85%</span><strong>{int((report_df['Average'] >= 85).sum())}</strong></div>
    <div class="card"><span>Students Below 60%</span><strong>{int((report_df['Average'] < 60).sum())}</strong></div>
    <div class="card"><span>Attendance Below 75%</span><strong>{int((report_df['Attendance'] < 75).sum())}</strong></div>
</div>

<h2>2. Class Leaders</h2>
<div class="leaders">
    <div class="leader">
        <h3>🏆 Class Topper</h3>
        <h2>{html.escape(str(topper_row['Student']))}</h2>
        <p>Average: <b>{topper_row['Average']:.2f}%</b></p>
        <p>Total marks: {topper_row['Total Marks']:.2f}</p>
        <p>Grade: {html.escape(str(topper_row['Grade']))}</p>
        <p>Attendance: {topper_row['Attendance']:.2f}%</p>
    </div>
    <div class="leader">
        <h3>📘 Lowest Average</h3>
        <h2>{html.escape(str(lowest_row['Student']))}</h2>
        <p>Average: <b>{lowest_row['Average']:.2f}%</b></p>
        <p>Total marks: {lowest_row['Total Marks']:.2f}</p>
        <p>Grade: {html.escape(str(lowest_row['Grade']))}</p>
        <p>Attendance: {lowest_row['Attendance']:.2f}%</p>
    </div>
</div>

<h2>3. Subject Averages</h2>
<div class="table-wrapper">
<table>
<thead><tr><th>Subject</th><th>Class Average</th></tr></thead>
<tbody>{subject_rows}</tbody>
</table>
</div>

<h2>4. Complete Student Rankings</h2>
<div class="table-wrapper">
<table>
<thead><tr>
<th>Rank</th><th>Student</th><th>Python</th><th>SQL</th>
<th>Power BI</th><th>AI</th><th>Total Marks</th>
<th>Average</th><th>Grade</th><th>Attendance</th>
</tr></thead>
<tbody>{ranking_rows}</tbody>
</table>
</div>

<h2>5. Students Needing Attention</h2>
<p>Criteria: average below 60% or attendance below 75%.</p>
<div class="table-wrapper">
<table>
<thead><tr>
<th>Student</th><th>Average</th><th>Grade</th>
<th>Attendance</th><th>Reason</th>
</tr></thead>
<tbody>{attention_rows}</tbody>
</table>
</div>

<footer>
    <p>Generated from in-memory processed data. The original CSV is unchanged.</p>
</footer>
</div>
</body>
</html>
"""


# =========================================================
# TAB 4: RANKINGS AND FULL-CLASS REPORT
# =========================================================
with tab_records:
    st.header("Filter and sort rankings")

    ranking_students_col, ranking_sort_col = st.columns(2)
    with ranking_students_col:
        ranking_students = st.multiselect(
            "Students",
            options=student_options,
            default=student_options,
            key="ranking_student_selection",
        )
    with ranking_sort_col:
        ranking_sort = st.selectbox(
            "Sort rankings by",
            options=list(SORT_OPTIONS.keys()),
            index=0,
            key="ranking_sort",
        )

    ranking_average_col, ranking_attendance_col = st.columns(2)
    with ranking_average_col:
        ranking_average = st.slider(
            "Average marks (%)",
            min_value=0,
            max_value=100,
            value=(0, 100),
            key="ranking_average_range",
        )
    with ranking_attendance_col:
        ranking_attendance = st.slider(
            "Attendance (%)",
            min_value=0,
            max_value=100,
            value=(0, 100),
            key="ranking_attendance_range",
        )
    ranking_grades = st.multiselect(
        "Grades",
        options=available_grades,
        default=available_grades,
        key="ranking_grades",
    )

    def reset_ranking_filters():
        st.session_state["ranking_student_selection"] = student_options
        st.session_state["ranking_sort"] = list(SORT_OPTIONS.keys())[0]
        st.session_state["ranking_average_range"] = (0, 100)
        st.session_state["ranking_attendance_range"] = (0, 100)
        st.session_state["ranking_grades"] = available_grades

    st.button(
        "Reset ranking filters",
        on_click=reset_ranking_filters,
        key="reset_ranking_filters",
    )

    ranking_filtered_df = filter_students(
        df,
        ranking_students,
        ranking_average,
        ranking_attendance,
        ranking_grades,
    )
    ranking_filtered_df = sort_students(ranking_filtered_df, ranking_sort)

    st.divider()
    st.caption(
        f"{len(ranking_filtered_df):,} of {len(df):,} students match these ranking filters."
    )
    if ranking_students:
        st.caption(
            f"Selected students: {len(ranking_students):,} | "
            f"Matching rows: {len(ranking_filtered_df):,}"
        )

    st.subheader("Student rankings")

    if ranking_filtered_df.empty:
        st.warning(
            "No students match these filters. Adjust the controls above to view rankings."
        )
    else:
        ranking_columns = [
            "Rank",
            "Student",
            *SUBJECTS,
            "Total Marks",
            "Average",
            "Grade",
            "Attendance",
        ]

        ranking_df = ranking_filtered_df[ranking_columns].copy()

        st.dataframe(
            ranking_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Rank": st.column_config.NumberColumn(
                    "Rank",
                    format="%d",
                ),
                "Total Marks": st.column_config.NumberColumn(
                    "Total Marks",
                    format="%.2f",
                ),
                "Average": st.column_config.NumberColumn(
                    "Average (%)",
                    format="%.2f",
                ),
                "Attendance": st.column_config.NumberColumn(
                    "Attendance (%)",
                    format="%.2f",
                ),
            },
        )

    st.divider()
    st.subheader("Students needing attention")

    attention_df = ranking_filtered_df[
        (ranking_filtered_df["Average"] < 60)
        | (ranking_filtered_df["Attendance"] < 75)
    ].copy()

    if attention_df.empty:
        st.success("No matching students meet the support criteria.")
    else:
        def attention_reason(row):
            reasons = []

            if row["Average"] < 60:
                reasons.append("Average below 60%")

            if row["Attendance"] < 75:
                reasons.append("Attendance below 75%")

            return ", ".join(reasons)

        attention_df["Reason"] = attention_df.apply(
            attention_reason,
            axis=1,
        )

        attention_df = attention_df[
            ["Student", "Average", "Grade", "Attendance", "Reason"]
        ]

        st.dataframe(
            attention_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Average": st.column_config.NumberColumn(
                    "Average (%)",
                    format="%.2f",
                ),
                "Attendance": st.column_config.NumberColumn(
                    "Attendance (%)",
                    format="%.2f",
                ),
            },
        )

    st.divider()

    st.subheader("Save performance report")

    st.write(
        "Create a report containing all students, class statistics, "
        "subject averages, rankings, class leaders and students needing "
        "attention. View filters do not affect this full-class report."
    )

    html_report = create_performance_report(df)

    st.download_button(
        label="Download full-class report (HTML)",
        data=html_report,
        file_name="student_performance_insights.html",
        mime="text/html",
        use_container_width=True,
    )

    st.caption(
        "Open the downloaded HTML file in your browser and select "
        "'Print / Save as PDF' to create a PDF. "
        "No processed dataset is automatically saved."
    )


# =========================================================
# FOOTER
# =========================================================
st.divider()
st.caption(
    "Student Performance Analysis · Streamlit · Pandas · Plotly"
)
