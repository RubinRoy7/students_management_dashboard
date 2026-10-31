
import streamlit as st
import pandas as pd
import plotly.express as px

from utils.helper import load_processed_data
from utils.ui import (
    render_chart,
    render_metric_cards,
    render_page_header,
    style_plotly_figure,
)


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="Student Performance Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --------------------------------------------------
# LOAD PROCESSED DATA
# --------------------------------------------------
try:
    df = load_processed_data()

except Exception as error:
    st.error(f"Unable to load student data: {error}")
    st.info(
        "Verify that data/student_performance.csv exists "
        "and contains the required columns."
    )
    st.stop()


# --------------------------------------------------
# VALIDATE DATA
# --------------------------------------------------
required_columns = [
    "Student",
    "Python",
    "SQL",
    "Power BI",
    "AI",
    "Attendance",
    "Total Marks",
    "Average",
    "Grade",
    "Rank"
]

missing_columns = [
    column for column in required_columns
    if column not in df.columns
]

if missing_columns:
    st.error(
        "Missing required columns: "
        + ", ".join(missing_columns)
    )
    st.stop()

if df.empty:
    st.warning("No student records are available.")
    st.stop()

# Keep only students with a valid name for student-level displays.
# The original source file is not modified.
df = df.copy()
df["Student"] = df["Student"].fillna("").astype(str).str.strip()
df = df[df["Student"] != ""].copy()

if df.empty:
    st.warning("No valid student names were found in the dataset.")
    st.stop()


# --------------------------------------------------
# DASHBOARD HEADER
# --------------------------------------------------
render_page_header(
    "🎓 Student Performance Dashboard",
    "A complete overview of academic results, attendance, class performance "
    "and students who may need support.",
)


# --------------------------------------------------
# KPI CALCULATIONS
# --------------------------------------------------
total_students = len(df)

average_attendance = df["Attendance"].mean()
class_average = df["Average"].mean()
highest_average = df["Average"].max()
lowest_average = df["Average"].min()

students_above_85 = int((df["Average"] >= 85).sum())
students_below_60 = int((df["Average"] < 60).sum())

attendance_below_75 = int((df["Attendance"] < 75).sum())

grade_a_count = int((df["Grade"].astype(str) == "A").sum())
grade_b_count = int((df["Grade"].astype(str) == "B").sum())
grade_c_count = int((df["Grade"].astype(str) == "C").sum())
grade_f_count = int((df["Grade"].astype(str) == "F").sum())


# --------------------------------------------------
# KPI CARDS
# --------------------------------------------------
st.header("📊 Class Performance Overview")

kpi_data = [
    (
        "👥 Total Students",
        f"{total_students}",
        "Total valid student records"
    ),
    (
        "📅 Average Attendance",
        f"{average_attendance:.2f}%",
        "Class attendance average"
    ),
    (
        "🏆 Highest Average Marks",
        f"{highest_average:.2f}%",
        "Highest student average"
    ),
    (
        "📉 Lowest Average Marks",
        f"{lowest_average:.2f}%",
        "Lowest student average"
    ),
    (
        "📚 Class Average",
        f"{class_average:.2f}%",
        "Average across all students"
    ),
    (
        "🌟 Students Above 85%",
        f"{students_above_85}",
        "Average marks ≥ 85%"
    ),
    (
        "⚠️ Students Below 60%",
        f"{students_below_60}",
        "Average marks < 60%"
    ),
    (
        "🕒 Low Attendance",
        f"{attendance_below_75}",
        "Attendance below 75%"
    )
]

render_metric_cards(kpi_data, columns=4)
st.divider()


# --------------------------------------------------
# CLASS TOPPER AND STUDENT NEEDING ATTENTION
# --------------------------------------------------
st.header("🏅 Student Highlights")

top_student = df.sort_values(
    ["Average", "Student"],
    ascending=[False, True]
).iloc[0]

lowest_student = df.sort_values(
    ["Average", "Student"],
    ascending=[True, True]
).iloc[0]

low_attendance_student = df.sort_values(
    ["Attendance", "Average"],
    ascending=[True, True]
).iloc[0]

top_col, support_col = st.columns(2)

with top_col:
    with st.container(border=True):
        st.subheader("🏆 Class Topper")
        st.write(f"**{top_student['Student']}**")
        st.metric("Average Marks", f"{top_student['Average']:.2f}%")
        st.metric("Total Marks", f"{top_student['Total Marks']:.0f}")
        st.caption(
            f"Grade: {top_student['Grade']} · "
            f"Attendance: {top_student['Attendance']:.2f}%"
        )

with support_col:
    with st.container(border=True):
        st.subheader("📘 Student Needing Academic Support")
        st.write(f"**{lowest_student['Student']}**")
        st.metric("Average Marks", f"{lowest_student['Average']:.2f}%")
        st.caption(f"Grade: {lowest_student['Grade']}")
        st.caption(f"Attendance: {lowest_student['Attendance']:.2f}%")

st.write("")

st.info(
    f"🕒 **Lowest Attendance:** {low_attendance_student['Student']} "
    f"has attendance of {low_attendance_student['Attendance']:.2f}%. "
    "Consider reviewing attendance and offering support where needed."
)
st.divider()


# --------------------------------------------------
# SUBJECT PERFORMANCE
# --------------------------------------------------
st.header("📈 Subject Performance Analysis")

subject_columns = ["Python", "SQL", "Power BI", "AI"]

subject_averages = (
    df[subject_columns]
    .mean()
    .round(2)
    .rename_axis("Subject")
    .reset_index(name="Average Marks")
)

subject_col1, subject_col2 = st.columns([3, 2])

with subject_col1:
    st.subheader("Average Marks by Subject")

    subject_chart = px.bar(
        subject_averages,
        x="Subject",
        y="Average Marks",
        color="Subject",
        title="Average marks by subject",
        labels={"Average Marks": "Average marks (%)"},
        hover_data={"Average Marks": ":.2f"},
    )
    subject_chart.update_layout(showlegend=False, yaxis_range=[0, 100])
    render_chart(
        style_plotly_figure(subject_chart),
        config={"displaylogo": False, "responsive": True},
    )

with subject_col2:
    best_subject = subject_averages.loc[
        subject_averages["Average Marks"].idxmax()
    ]

    weakest_subject = subject_averages.loc[
        subject_averages["Average Marks"].idxmin()
    ]

    st.subheader("Subject Insights")

    render_metric_cards(
        [
            (
                "💪 Strongest Subject",
                str(best_subject["Subject"]),
                f"{best_subject['Average Marks']:.2f}% average",
            ),
            (
                "🎯 Subject Needing Improvement",
                str(weakest_subject["Subject"]),
                f"{weakest_subject['Average Marks']:.2f}% average",
            ),
        ],
        columns=1,
    )

st.divider()

# --------------------------------------------------
# GRADE DISTRIBUTION
# --------------------------------------------------
st.header("🎖️ Grade Distribution")

grade_col1, grade_col2 = st.columns([3, 2])

with grade_col1:
    grade_counts = (
        df["Grade"]
        .astype(str)
        .value_counts()
        .reindex(["A", "B", "C", "F"], fill_value=0)
        .rename_axis("Grade")
        .to_frame("Number of Students")
    )

    grade_chart = px.bar(
        grade_counts.reset_index(),
        x="Grade",
        y="Number of Students",
        color="Grade",
        title="Student count by grade",
        labels={"Number of Students": "Number of students"},
        hover_data={"Number of Students": True},
    )
    grade_chart.update_layout(showlegend=False)
    render_chart(
        style_plotly_figure(grade_chart),
        config={"displaylogo": False, "responsive": True},
    )

with grade_col2:
    render_metric_cards(
        [
            ("Grade A", grade_a_count, None),
            ("Grade B", grade_b_count, None),
            ("Grade C", grade_c_count, None),
            ("Grade F", grade_f_count, None),
        ],
        columns=2,
    )

st.divider()

# --------------------------------------------------
# ATTENDANCE VS AVERAGE
# --------------------------------------------------
st.header("🔍 Attendance vs Academic Performance")

st.caption(
    "Each point represents one student. "
    "Use this chart to explore the relationship between attendance and marks."
)

attendance_chart = px.scatter(
    df,
    x="Attendance",
    y="Average",
    color="Grade",
    hover_name="Student",
    hover_data={
        "Attendance": ":.2f",
        "Average": ":.2f",
        "Total Marks": ":.0f",
        "Rank": True,
    },
    title="Attendance and academic performance",
    labels={
        "Attendance": "Attendance (%)",
        "Average": "Average marks (%)",
    },
)
attendance_chart.update_xaxes(range=[0, 100])
attendance_chart.update_yaxes(range=[0, 100])
render_chart(
    style_plotly_figure(attendance_chart),
    config={"displaylogo": False, "responsive": True},
)
st.divider()


# --------------------------------------------------
# STUDENT RANKING TABLE
# --------------------------------------------------
st.header("📋 Student Ranking")

ranking_df = (
    df[
        [
            "Rank",
            "Student",
            "Python",
            "SQL",
            "Power BI",
            "AI",
            "Total Marks",
            "Average",
            "Grade",
            "Attendance"
        ]
    ]
    .sort_values(["Rank", "Student"], ascending=[True, True])
    .reset_index(drop=True)
)

st.dataframe(
    ranking_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Rank": st.column_config.NumberColumn(
            "Rank",
            format="%d"
        ),
        "Total Marks": st.column_config.NumberColumn(
            "Total Marks",
            format="%.0f"
        ),
        "Average": st.column_config.NumberColumn(
            "Average (%)",
            format="%.2f"
        ),
        "Attendance": st.column_config.NumberColumn(
            "Attendance (%)",
            format="%.2f"
        )
    }
)


# --------------------------------------------------
# STUDENTS WHO NEED ATTENTION
# --------------------------------------------------
st.header("🆘 Students Who May Need Attention")

needs_attention = df[
    (df["Average"] < 60) | (df["Attendance"] < 75)
].copy()

if needs_attention.empty:
    st.success(
        "No students currently meet the low-marks or low-attendance "
        "attention criteria."
    )
else:
    needs_attention["Reason"] = needs_attention.apply(
        lambda row: ", ".join(
            reason for condition, reason in [
                (row["Average"] < 60, "Average below 60%"),
                (row["Attendance"] < 75, "Attendance below 75%")
            ]
            if condition
        ),
        axis=1
    )

    attention_table = needs_attention[
        ["Student", "Average", "Grade", "Attendance", "Reason"]
    ].sort_values(
        ["Average", "Attendance"],
        ascending=[True, True]
    )

    st.dataframe(
        attention_table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Average": st.column_config.NumberColumn(
                "Average (%)",
                format="%.2f"
            ),
            "Attendance": st.column_config.NumberColumn(
                "Attendance (%)",
                format="%.2f"
            )
        }
    )


# --------------------------------------------------
# DOWNLOAD REPORT
# --------------------------------------------------
st.header("📥 Download Report")

csv_data = ranking_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Student Performance Report",
    data=csv_data,
    file_name="student_performance_report.csv",
    mime="text/csv"
)

st.caption(
    "The original CSV remains unchanged. Processed data is generated "
    "in memory, and a report is downloaded only when you click the button."
)

st.divider()

st.caption(
    "Student Performance Dashboard | Python • Pandas • Streamlit"
)
