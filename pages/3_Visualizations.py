
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.helper import load_processed_data
from utils.ui import (
    PLOTLY_DIVERGING_SCALE,
    PLOTLY_SEQUENTIAL_SCALE,
    render_chart,
    render_metric_cards,
    render_page_header,
    style_plotly_figure,
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="Data Visualizations",
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
    st.error(f"Unable to load student data: {error}")
    st.info(
        "Check data/student_performance.csv and the required columns "
        "in utils/helper.py."
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

missing_columns = [
    column for column in REQUIRED_COLUMNS
    if column not in df.columns
]

if missing_columns:
    st.error(
        "The dataset is missing: " + ", ".join(missing_columns)
    )
    st.stop()


# Work with a copy. The original CSV is never modified.
df = df.copy()

df["Student"] = (
    df["Student"]
    .astype("string")
    .fillna("")
    .str.strip()
)

df = df[df["Student"] != ""].copy()

student_options = sorted(
    df["Student"].dropna().unique().tolist(),
    key=str.casefold,
)

NUMERIC_COLUMNS = [
    *SUBJECTS,
    "Attendance",
    "Total Marks",
    "Average",
    "Rank",
]

for column in NUMERIC_COLUMNS:
    df[column] = pd.to_numeric(df[column], errors="coerce")

df = df.dropna(
    subset=["Average", "Attendance", "Total Marks"]
).copy()

# FIX: Convert categorical Grade to string BEFORE fillna.
# This prevents "Cannot setitem on a Categorical" errors.
df["Grade"] = (
    df["Grade"]
    .astype("string")
    .fillna("UNKNOWN")
    .str.strip()
    .str.upper()
)

if df.empty:
    st.warning("No valid student data is available.")
    st.stop()


# =========================================================
# CONFIGURATION
# =========================================================
CHART_TYPES = [
    "Bar Chart",
    "Line Chart",
    "Pie Chart",
    "Scatter Plot",
    "Histogram",
    "Box Plot",
    "Heatmap",
    "Area Chart",
    "Bubble Chart",
    "Radar Chart",
    "Sunburst Chart",
    "Treemap",
]

SORT_OPTIONS = [
    "Average — highest first",
    "Average — lowest first",
    "Attendance — highest first",
    "Attendance — lowest first",
    "Total marks — highest first",
    "Student name — A to Z",
    "Rank — best first",
]

SORT_CONFIG = {
    "Average — highest first": ("Average", False),
    "Average — lowest first": ("Average", True),
    "Attendance — highest first": ("Attendance", False),
    "Attendance — lowest first": ("Attendance", True),
    "Total marks — highest first": ("Total Marks", False),
    "Student name — A to Z": ("Student", True),
    "Rank — best first": ("Rank", True),
}

PLOT_CONFIG = {
    "displaylogo": False,
    "scrollZoom": True,
    "responsive": True,
}


def sort_data(data, sort_option):
    """Sort a copy of the DataFrame, with stable tie-breaking."""
    column, ascending = SORT_CONFIG[sort_option]

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


# =========================================================
# PAGE HEADER
# =========================================================
render_page_header(
    "Data Visualization Studio",
    "Explore student performance with interactive charts, "
    "filters and sorting controls.",
)


# =========================================================
# SIDEBAR FILTERS
# =========================================================
st.sidebar.title("Visualization Controls")
st.sidebar.caption("Filter and organize the student data.")
st.sidebar.divider()

st.sidebar.subheader("Filter students")

selected_students = st.sidebar.multiselect(
    "Students",
    options=student_options,
    default=student_options,
    key="viz_selected_students",
)

average_range = st.sidebar.slider(
    "Average marks (%)",
    min_value=0,
    max_value=100,
    value=(0, 100),
    step=1,
    key="viz_average_range",
)

attendance_range = st.sidebar.slider(
    "Attendance (%)",
    min_value=0,
    max_value=100,
    value=(0, 100),
    step=1,
    key="viz_attendance_range",
)

# Grade is now a string column, so these options are safe.
grade_options = [
    grade
    for grade in ["A", "B", "C", "F", "UNKNOWN"]
    if grade in df["Grade"].dropna().unique().tolist()
]

selected_grades = st.sidebar.multiselect(
    "Grade",
    options=grade_options,
    default=grade_options,
    key="viz_grades",
)

sort_option = st.sidebar.selectbox(
    "Sort students by",
    options=SORT_OPTIONS,
    key="viz_sort",
)

st.sidebar.divider()
st.sidebar.subheader("Chart settings")

chart_type = st.sidebar.selectbox(
    "Visualization type",
    options=CHART_TYPES,
    key="viz_chart_type",
)

selected_subjects = st.sidebar.multiselect(
    "Subjects",
    options=SUBJECTS,
    default=SUBJECTS,
    key="viz_subjects",
)

max_students = st.sidebar.slider(
    "Maximum students in student-level charts",
    min_value=1,
    max_value=max(1, min(100, len(df))),
    value=max(1, min(20, len(df))),
    step=1,
    key="viz_max_students",
)

st.sidebar.caption(
    "The student limit applies to student-level charts only. "
    "The filtered table still includes every matching student."
)

def reset_visualization_controls():
    st.session_state["viz_selected_students"] = student_options
    st.session_state["viz_average_range"] = (0, 100)
    st.session_state["viz_attendance_range"] = (0, 100)
    st.session_state["viz_grades"] = grade_options
    st.session_state["viz_sort"] = SORT_OPTIONS[0]
    st.session_state["viz_chart_type"] = CHART_TYPES[0]
    st.session_state["viz_subjects"] = SUBJECTS
    st.session_state["viz_max_students"] = max(1, min(20, len(df)))


st.sidebar.button(
    "Reset all controls",
    use_container_width=True,
    on_click=reset_visualization_controls,
)


# =========================================================
# FILTER AND SORT
# =========================================================
filter_mask = (
    df["Average"].between(
        average_range[0],
        average_range[1],
        inclusive="both",
    )
    & df["Attendance"].between(
        attendance_range[0],
        attendance_range[1],
        inclusive="both",
    )
    & df["Grade"].isin(selected_grades)
)

if selected_students:
    filter_mask &= df["Student"].isin(selected_students)

filtered_df = df.loc[filter_mask].copy()
filtered_df = sort_data(filtered_df, sort_option)


# =========================================================
# SUMMARY CARDS
# =========================================================
render_metric_cards(
    [
        ("All Students", len(df), "Full class size"),
        ("Filtered Students", len(filtered_df), "Students matching current filters"),
        (
            "Average Marks",
            f"{filtered_df['Average'].mean():.2f}%" if not filtered_df.empty else "N/A",
            None,
        ),
        (
            "Average Attendance",
            f"{filtered_df['Attendance'].mean():.2f}%" if not filtered_df.empty else "N/A",
            None,
        ),
    ]
)

st.divider()


# =========================================================
# CHART SECTION
# =========================================================
st.header("Interactive visualization")

st.caption(
    f"{chart_type} · {len(filtered_df)} student(s) match the filters"
)
if selected_students:
    st.caption(
        f"Selected students: {len(selected_students):,} | "
        f"Matching rows: {len(filtered_df):,}"
    )

if filtered_df.empty:
    st.warning(
        "No students match your filters. Adjust the controls "
        "in the sidebar to display a chart."
    )
    st.stop()


# Chart-specific subject requirements.
subject_chart_types = [
    "Bar Chart",
    "Line Chart",
    "Box Plot",
    "Area Chart",
    "Radar Chart",
]

if chart_type in subject_chart_types and not selected_subjects:
    st.warning(
        "Select at least one subject in the sidebar for this chart."
    )
    st.stop()


# This limit applies only to charts where individual students are plotted.
chart_df = filtered_df.head(max_students).copy()


# =========================================================
# 1. BAR CHART
# =========================================================
if chart_type == "Bar Chart":

    display_mode = st.radio(
        "Display",
        ["Subject averages", "Individual student marks"],
        horizontal=True,
        key="bar_display_mode",
    )

    if display_mode == "Subject averages":
        bar_data = pd.DataFrame({
            "Subject": selected_subjects,
            "Average Marks": [
                filtered_df[subject].mean()
                for subject in selected_subjects
            ],
        }).sort_values(
            "Average Marks",
            ascending=False,
        )

        fig = px.bar(
            bar_data,
            x="Subject",
            y="Average Marks",
            color="Subject",
            text="Average Marks",
            hover_data={"Average Marks": ":.2f"},
            title="Average marks by subject",
        )

        fig.update_traces(
            texttemplate="%{text:.1f}",
            textposition="outside",
        )

        fig.update_layout(
            showlegend=False,
            yaxis_title="Average marks (%)",
            xaxis_title="",
            yaxis_range=[0, 110],
        )

    else:
        bar_metric = st.selectbox(
            "Student metric",
            ["Average", "Attendance", "Total Marks"],
            key="bar_student_metric",
        )

        fig = px.bar(
            chart_df,
            x="Student",
            y=bar_metric,
            color="Grade",
            hover_data=["Rank", "Average", "Attendance"],
            title=f"Student comparison by {bar_metric}",
        )

        fig.update_layout(
            xaxis_title="Student",
            yaxis_title=bar_metric,
        )

        if bar_metric != "Total Marks":
            fig.update_layout(yaxis_range=[0, 100])

        fig.update_xaxes(tickangle=-35)


# =========================================================
# 2. LINE CHART
# =========================================================
elif chart_type == "Line Chart":

    line_mode = st.radio(
        "Display",
        ["Subject averages", "Individual student"],
        horizontal=True,
        key="line_display_mode",
    )

    if line_mode == "Subject averages":
        line_data = pd.DataFrame({
            "Subject": selected_subjects,
            "Average Marks": [
                filtered_df[subject].mean()
                for subject in selected_subjects
            ],
        })

        fig = px.line(
            line_data,
            x="Subject",
            y="Average Marks",
            markers=True,
            text="Average Marks",
            title="Class subject performance",
        )

        fig.update_traces(
            texttemplate="%{text:.1f}",
            textposition="top center",
            line=dict(width=3),
            marker=dict(size=9),
        )

        fig.update_layout(
            xaxis_title="Subject",
            yaxis_title="Average marks (%)",
            yaxis_range=[0, 100],
        )

    else:
        selected_student = st.selectbox(
            "Select student",
            options=sorted(filtered_df["Student"].unique().tolist()),
            key="line_student",
        )

        line_row = filtered_df[
            filtered_df["Student"] == selected_student
        ].iloc[0]

        line_data = pd.DataFrame({
            "Subject": selected_subjects,
            "Marks": [
                line_row[subject]
                for subject in selected_subjects
            ],
        })

        fig = px.line(
            line_data,
            x="Subject",
            y="Marks",
            markers=True,
            text="Marks",
            title=f"Subject marks — {selected_student}",
        )

        fig.update_traces(
            texttemplate="%{text:.1f}",
            textposition="top center",
            line=dict(width=3),
            marker=dict(size=9),
        )

        fig.update_layout(
            xaxis_title="Subject",
            yaxis_title="Marks (%)",
            yaxis_range=[0, 100],
        )


# =========================================================
# 3. PIE CHART
# =========================================================
elif chart_type == "Pie Chart":

    grade_data = (
        filtered_df["Grade"]
        .value_counts()
        .rename_axis("Grade")
        .reset_index(name="Students")
    )

    fig = px.pie(
        grade_data,
        names="Grade",
        values="Students",
        hole=0.4,
        hover_data=["Students"],
        title="Grade distribution",
    )

    fig.update_traces(
        textposition="inside",
        textinfo="label+percent",
    )


# =========================================================
# 4. SCATTER PLOT
# =========================================================
elif chart_type == "Scatter Plot":

    scatter_x = st.selectbox(
        "X-axis",
        ["Attendance", "Python", "SQL", "Power BI", "AI", "Total Marks"],
        index=0,
        key="scatter_x",
    )

    scatter_y = st.selectbox(
        "Y-axis",
        ["Average", "Python", "SQL", "Power BI", "AI", "Attendance"],
        index=0,
        key="scatter_y",
    )

    fig = px.scatter(
        chart_df,
        x=scatter_x,
        y=scatter_y,
        color="Grade",
        hover_name="Student",
        hover_data=["Total Marks", "Average", "Attendance", "Rank"],
        title=f"{scatter_y} vs {scatter_x}",
    )

    fig.update_layout(
        xaxis_title=scatter_x,
        yaxis_title=scatter_y,
    )


# =========================================================
# 5. HISTOGRAM
# =========================================================
elif chart_type == "Histogram":

    histogram_metric = st.selectbox(
        "Distribution metric",
        ["Average", "Attendance", "Python", "SQL", "Power BI", "AI"],
        key="histogram_metric",
    )

    bin_count = st.slider(
        "Number of bins",
        min_value=5,
        max_value=30,
        value=10,
        key="histogram_bins",
    )

    fig = px.histogram(
        filtered_df,
        x=histogram_metric,
        nbins=bin_count,
        color="Grade",
        marginal="box",
        title=f"Distribution of {histogram_metric}",
    )

    fig.update_layout(
        xaxis_title=histogram_metric,
        yaxis_title="Number of students",
        barmode="overlay",
    )


# =========================================================
# 6. BOX PLOT
# =========================================================
elif chart_type == "Box Plot":

    box_data = filtered_df.melt(
        id_vars=["Student", "Grade"],
        value_vars=selected_subjects,
        var_name="Subject",
        value_name="Marks",
    )

    fig = px.box(
        box_data,
        x="Subject",
        y="Marks",
        color="Subject",
        points="all",
        hover_data=["Student", "Grade"],
        title="Subject mark distributions",
    )

    fig.update_layout(
        showlegend=False,
        xaxis_title="Subject",
        yaxis_title="Marks (%)",
        yaxis_range=[0, 100],
    )


# =========================================================
# 7. HEATMAP
# =========================================================
elif chart_type == "Heatmap":

    heatmap_mode = st.radio(
        "Heatmap type",
        ["Subject correlation", "Student marks"],
        horizontal=True,
        key="heatmap_mode",
    )

    if heatmap_mode == "Subject correlation":

        if len(selected_subjects) < 2:
            st.warning(
                "Select at least two subjects to calculate correlations."
            )
            st.stop()

        correlation_data = filtered_df[selected_subjects].corr()

        fig = px.imshow(
            correlation_data,
            text_auto=".2f",
            color_continuous_scale=PLOTLY_DIVERGING_SCALE,
            zmin=-1,
            zmax=1,
            aspect="auto",
            title="Subject score correlation",
        )

        fig.update_layout(
            xaxis_title="Subject",
            yaxis_title="Subject",
        )

    else:
        heatmap_students = chart_df.sort_values(
            "Average",
            ascending=False,
        )

        heatmap_data = heatmap_students.set_index(
            "Student"
        )[selected_subjects]

        fig = px.imshow(
            heatmap_data,
            text_auto=".0f",
            color_continuous_scale=PLOTLY_SEQUENTIAL_SCALE,
            zmin=0,
            zmax=100,
            aspect="auto",
            title="Student marks by subject",
            labels={
                "x": "Subject",
                "y": "Student",
                "color": "Marks",
            },
        )


# =========================================================
# 8. AREA CHART
# =========================================================
elif chart_type == "Area Chart":

    area_mode = st.radio(
        "Display",
        ["Subject averages", "Individual student"],
        horizontal=True,
        key="area_display_mode",
    )

    if area_mode == "Subject averages":
        area_data = pd.DataFrame({
            "Subject": selected_subjects,
            "Average Marks": [
                filtered_df[subject].mean()
                for subject in selected_subjects
            ],
        })

        fig = px.area(
            area_data,
            x="Subject",
            y="Average Marks",
            markers=True,
            title="Class average across subjects",
        )

        fig.update_layout(
            xaxis_title="Subject",
            yaxis_title="Average marks (%)",
            yaxis_range=[0, 100],
        )

    else:
        selected_student = st.selectbox(
            "Select student",
            options=sorted(filtered_df["Student"].unique().tolist()),
            key="area_student",
        )

        area_row = filtered_df[
            filtered_df["Student"] == selected_student
        ].iloc[0]

        area_data = pd.DataFrame({
            "Subject": selected_subjects,
            "Marks": [
                area_row[subject]
                for subject in selected_subjects
            ],
        })

        fig = px.area(
            area_data,
            x="Subject",
            y="Marks",
            markers=True,
            title=f"Subject marks — {selected_student}",
        )

        fig.update_layout(
            xaxis_title="Subject",
            yaxis_title="Marks (%)",
            yaxis_range=[0, 100],
        )


# =========================================================
# 9. BUBBLE CHART
# =========================================================
elif chart_type == "Bubble Chart":

    bubble_x = st.selectbox(
        "Bubble chart X-axis",
        ["Attendance", "Average", "Python", "SQL", "Power BI", "AI"],
        index=0,
        key="bubble_x",
    )

    bubble_y = st.selectbox(
        "Bubble chart Y-axis",
        ["Average", "Attendance", "Python", "SQL", "Power BI", "AI"],
        index=0,
        key="bubble_y",
    )

    fig = px.scatter(
        chart_df,
        x=bubble_x,
        y=bubble_y,
        size="Total Marks",
        color="Grade",
        hover_name="Student",
        hover_data=["Total Marks", "Average", "Attendance", "Rank"],
        size_max=45,
        title="Student performance bubble chart",
    )

    fig.update_layout(
        xaxis_title=bubble_x,
        yaxis_title=bubble_y,
    )


# =========================================================
# 10. RADAR CHART
# =========================================================
elif chart_type == "Radar Chart":

    radar_student = st.selectbox(
        "Select student",
        options=sorted(filtered_df["Student"].unique().tolist()),
        key="radar_student",
    )

    radar_row = filtered_df[
        filtered_df["Student"] == radar_student
    ].iloc[0]

    radar_values = [
        radar_row[subject]
        for subject in selected_subjects
    ]

    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=radar_values + radar_values[:1],
            theta=selected_subjects + selected_subjects[:1],
            fill="toself",
            name=radar_student,
            hovertemplate="%{theta}: %{r:.2f}%<extra></extra>",
        )
    )

    fig.update_layout(
        title=f"Subject performance — {radar_student}",
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                gridcolor="rgba(133,167,201,0.2)",
                linecolor="#29425D",
                tickfont=dict(color="#A8BCD2"),
            ),
            angularaxis=dict(
                gridcolor="rgba(133,167,201,0.2)",
                linecolor="#29425D",
                tickfont=dict(color="#C6D9ED"),
            )
        ),
        showlegend=False,
    )


# =========================================================
# 11. SUNBURST CHART
# =========================================================
elif chart_type == "Sunburst Chart":

    sunburst_data = filtered_df.copy()

    # Unique leaf labels prevent duplicate names from merging.
    sunburst_data["Student Leaf"] = [
        f"{name} · record {i + 1}"
        for i, name in enumerate(sunburst_data["Student"])
    ]

    fig = px.sunburst(
        sunburst_data,
        path=["Grade", "Student Leaf"],
        values="Average",
        color="Average",
        color_continuous_scale=PLOTLY_SEQUENTIAL_SCALE,
        hover_data={
            "Student": True,
            "Average": ":.2f",
            "Attendance": ":.2f",
        },
        title="Grade and student performance hierarchy",
    )


# =========================================================
# 12. TREEMAP
# =========================================================
elif chart_type == "Treemap":

    treemap_data = filtered_df.copy()

    treemap_data["Student Leaf"] = [
        f"{name} · record {i + 1}"
        for i, name in enumerate(treemap_data["Student"])
    ]

    fig = px.treemap(
        treemap_data,
        path=["Grade", "Student Leaf"],
        values="Average",
        color="Average",
        color_continuous_scale=PLOTLY_SEQUENTIAL_SCALE,
        hover_data={
            "Student": True,
            "Average": ":.2f",
            "Attendance": ":.2f",
            "Total Marks": ":.2f",
        },
        title="Student performance by grade",
    )


# =========================================================
# DISPLAY CHART
# =========================================================
# A few chart types can show an informational message and stop
# above; all other paths produce a Plotly figure.
render_chart(
    style_plotly_figure(fig),
    config=PLOT_CONFIG,
)


# =========================================================
# FILTERED STUDENT TABLE
# =========================================================
st.divider()

st.header("Filtered student records")

st.caption(
    f"{len(filtered_df)} student record(s) match your filters. "
    "The table includes all matching students, even if charts are "
    "limited to a smaller number."
)

table_columns = [
    "Rank",
    "Student",
    *SUBJECTS,
    "Total Marks",
    "Average",
    "Grade",
    "Attendance",
]

st.dataframe(
    filtered_df[table_columns],
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


# =========================================================
# FOOTER
# =========================================================
st.divider()

st.caption(
    "Data Visualization Studio · Streamlit · Pandas · Plotly"
)
