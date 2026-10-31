
import streamlit as st
import pandas as pd

from utils.helper import (
    load_raw_data,
    process_data,
    NUMERIC_COLUMNS,
    SUBJECT_COLUMNS
)
from utils.ui import render_metric_cards, render_page_header

# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Dataset Explorer",
    page_icon="📊",
    layout="wide"
)

render_page_header(
    "📊 Dataset Explorer",
    "Explore raw records, improve data quality, and inspect processed data.",
)

# ==================================================
# LOAD RAW DATA
# ==================================================

try:
    raw_df = load_raw_data()
except Exception as error:
    st.error(f"Unable to load dataset: {error}")
    st.stop()

# ==================================================
# DATA MANAGEMENT OPTIONS
# ==================================================

st.markdown("### Data Management")

raw_tab, cleaning_tab = st.tabs([
    "📄 Raw Data",
    "🧹 Data Cleaning"
])

# ==================================================
# OPTION 1: RAW DATA
# ==================================================

with raw_tab:

    st.header("Raw Dataset Overview")
    st.caption("Information from the original CSV, before cleaning.")

    total_rows, total_columns = raw_df.shape
    missing_count = int(raw_df.isna().sum().sum())
    duplicate_count = int(raw_df.duplicated().sum())

    metrics = [
        ("📄 Total Rows", f"{total_rows:,}", None),
        ("📋 Total Columns", f"{total_columns:,}", None),
        ("⚠️ Missing Values", f"{missing_count:,}", None),
        ("🔁 Duplicate Rows", f"{duplicate_count:,}", None),
    ]

    render_metric_cards(metrics)

    st.write("")

    # Raw dataset search
    st.markdown("#### Original Records")

    search_raw = st.text_input(
        "🔎 Search raw data",
        placeholder="Search names or values...",
        key="search_raw"
    )

    raw_view = raw_df.copy()

    if search_raw.strip():
        search_mask = raw_view.astype("string").apply(
            lambda column: column.str.contains(
                search_raw.strip(),
                case=False,
                na=False,
                regex=False
            )
        ).any(axis=1)

        raw_view = raw_view[search_mask]

    st.caption(
        f"Showing {len(raw_view):,} of {len(raw_df):,} records"
    )

    st.dataframe(
        raw_view,
        use_container_width=True,
        hide_index=True
    )

    # Column information
    st.markdown("#### Column Information")

    column_info = pd.DataFrame({
        "Column": raw_df.columns,
        "Data Type": raw_df.dtypes.astype(str).values,
        "Non-Null Count": raw_df.notna().sum().values,
        "Null Count": raw_df.isna().sum().values,
        "Unique Values": raw_df.nunique().values
    })

    st.dataframe(
        column_info,
        use_container_width=True,
        hide_index=True
    )

    # Missing-value details
    st.markdown("#### Missing Values by Column")

    missing_info = pd.DataFrame({
        "Column": raw_df.columns,
        "Missing Count": raw_df.isna().sum().values,
        "Missing Percentage (%)": (
            raw_df.isna().mean().values * 100
        ).round(2)
    })

    st.dataframe(
        missing_info,
        use_container_width=True,
        hide_index=True
    )

    # Download original dataset
    st.download_button(
        "⬇️ Download Original CSV",
        data=raw_df.to_csv(index=False).encode("utf-8"),
        file_name="student_performance_raw.csv",
        mime="text/csv",
        key="download_raw"
    )

# ==================================================
# OPTION 2: DATA CLEANING
# ==================================================

with cleaning_tab:

    st.header("Data Cleaning & Processing")
    st.caption(
        "Validate numeric fields, clean the data in memory, "
        "and prepare it for statistical analysis."
    )

    # --------------------------------------------------
    # VALIDATION REPORT
    # --------------------------------------------------

    numeric_preview = raw_df[NUMERIC_COLUMNS].apply(
        pd.to_numeric,
        errors="coerce"
    )

    validation_rows = []

    for column in NUMERIC_COLUMNS:

        original_values = raw_df[column]

        converted_values = numeric_preview[column]

        nonempty = (
            original_values.notna()
            & original_values.astype("string").str.strip().ne("")
        )

        unreadable_count = int(
            (nonempty & converted_values.isna()).sum()
        )

        validation_rows.append({
            "Column": column,
            "Missing / Unreadable": int(
                converted_values.isna().sum()
            ),
            "Below 0": int(
                (converted_values < 0).sum()
            ),
            "Above 100": int(
                (converted_values > 100).sum()
            ),
            "Unreadable Values": unreadable_count
        })

    validation_report = pd.DataFrame(validation_rows)

    st.markdown("#### Numeric Validation Report")

    st.dataframe(
        validation_report,
        use_container_width=True,
        hide_index=True
    )

    st.info("""
    **Cleaning rules**

    - Remove exact duplicate records.
    - Convert subject marks and attendance into numeric values.
    - Replace missing and unreadable numeric values with 0.
    - Replace values below 0 or above 100 with 0.
    - Calculate Total Marks, Average, Grade, and Rank.
    - Keep the original CSV unchanged.
    - Do not automatically save processed data to a file.
    """)

    st.caption(
        "Grade boundaries: A ≥ 90, B ≥ 75, C ≥ 50, F < 50."
    )

    # --------------------------------------------------
    # PROCESS DATA BUTTON
    # --------------------------------------------------

    confirm_cleaning = st.checkbox(
        "I understand the cleaning rules and want to process the dataset.",
        key="confirm_cleaning"
    )

    if st.button(
        "🧹 Clean and Process Dataset",
        type="primary",
        disabled=not confirm_cleaning,
        key="clean_dataset"
    ):

        try:
            cleaned_df = process_data(raw_df)

            # Keep the result in session memory only.
            st.session_state["processed_student_df"] = cleaned_df

            st.success(
                "Dataset cleaned successfully in memory. "
                "No processed file was saved."
            )

        except Exception as error:
            st.error(f"Data processing failed: {error}")

    # --------------------------------------------------
    # PROCESSED DATA OVERVIEW
    # --------------------------------------------------

    st.divider()

    st.header("📊 Processed Data Overview")

    cleaned_df = st.session_state.get("processed_student_df")

    if cleaned_df is None:

        st.info(
            "Click 'Clean and Process Dataset' above to view the "
            "processed dataset, column descriptions, and statistics."
        )

    else:

        st.markdown("#### About the Processed Dataset")

        st.write(
            "This dataset contains cleaned student records and "
            "calculated academic performance fields. Missing or "
            "unreadable numeric values and values outside the 0–100 "
            "range are replaced with zero. Exact duplicate rows are "
            "removed. The original CSV remains unchanged."
        )

        # --------------------------------------------------
        # PROCESSED DATA METRIC CARDS
        # --------------------------------------------------

        processed_missing = int(
            cleaned_df.isna().sum().sum()
        )

        processed_duplicates = int(
            cleaned_df.duplicated().sum()
        )

        processed_metrics = [
            ("📄 Processed Rows", f"{len(cleaned_df):,}", None),
            ("📋 Total Columns", f"{len(cleaned_df.columns):,}", None),
            ("⚠️ Missing Values", f"{processed_missing:,}", None),
            ("🔁 Duplicate Rows", f"{processed_duplicates:,}", None),
        ]

        render_metric_cards(processed_metrics)

        # --------------------------------------------------
        # PROCESSING SUMMARY
        # --------------------------------------------------

        st.markdown("#### Processing Summary")

        summary_df = pd.DataFrame({
            "Processing Step": [
                "Duplicate records",
                "Missing numeric values",
                "Unreadable numeric values",
                "Values outside 0–100",
                "Calculated columns"
            ],
            "Action": [
                "Exact duplicate rows removed",
                "Replaced with 0",
                "Replaced with 0",
                "Replaced with 0",
                "Total Marks, Average, Grade, Rank"
            ]
        })

        st.dataframe(
            summary_df,
            use_container_width=True,
            hide_index=True
        )

        # --------------------------------------------------
        # PROCESSED RECORDS
        # --------------------------------------------------

        st.markdown("#### Processed Records")

        search_processed = st.text_input(
            "🔎 Search processed records",
            placeholder="Search student names or values...",
            key="search_processed"
        )

        display_df = cleaned_df.copy()

        if search_processed.strip():

            search_mask = display_df.astype("string").apply(
                lambda column: column.str.contains(
                    search_processed.strip(),
                    case=False,
                    na=False,
                    regex=False
                )
            ).any(axis=1)

            display_df = display_df[search_mask]

        st.caption(
            f"Showing {len(display_df):,} of "
            f"{len(cleaned_df):,} records"
        )

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

        # --------------------------------------------------
        # COLUMN DESCRIPTIONS
        # --------------------------------------------------

        st.markdown("#### Processed Column Information")

        column_descriptions = {
            "Student": "Student name or identifier",
            "Python": "Python subject marks (0–100)",
            "SQL": "SQL subject marks (0–100)",
            "Power BI": "Power BI subject marks (0–100)",
            "AI": "AI subject marks (0–100)",
            "Attendance": "Attendance percentage (0–100)",
            "Total Marks": "Sum of four subject marks; maximum 400",
            "Average": "Average of four subject marks; maximum 100",
            "Grade": "Grade based on average: A, B, C, or F",
            "Rank": "Rank based on average; rank 1 is highest"
        }

        processed_column_info = pd.DataFrame({
            "Column": cleaned_df.columns,
            "Data Type": cleaned_df.dtypes.astype(str).values,
            "Non-Null Values": cleaned_df.notna().sum().values,
            "Null Values": cleaned_df.isna().sum().values,
            "Description": [
                column_descriptions.get(
                    column,
                    "Original field retained from source data"
                )
                for column in cleaned_df.columns
            ]
        })

        st.dataframe(
            processed_column_info,
            use_container_width=True,
            hide_index=True
        )

        # --------------------------------------------------
        # STATISTICAL SUMMARY
        # --------------------------------------------------

        st.markdown("#### Statistical Summary")

        numeric_df = cleaned_df.select_dtypes(include="number")

        if not numeric_df.empty:
            st.dataframe(
                numeric_df.describe().T.round(2),
                use_container_width=True
            )
        else:
            st.info("No numeric columns are available for statistics.")

        # --------------------------------------------------
        # GRADE DISTRIBUTION
        # --------------------------------------------------

        st.markdown("#### Grade Distribution")

        grade_counts = (
            cleaned_df["Grade"]
            .value_counts()
            .reindex(["A", "B", "C", "F"], fill_value=0)
            .rename_axis("Grade")
            .reset_index(name="Students")
        )

        st.dataframe(
            grade_counts,
            use_container_width=True,
            hide_index=True
        )

        # --------------------------------------------------
        # OPTIONAL DOWNLOAD
        # --------------------------------------------------

        st.download_button(
            "⬇️ Download Processed Data",
            data=cleaned_df.to_csv(index=False).encode("utf-8"),
            file_name="student_performance_processed.csv",
            mime="text/csv",
            key="download_processed"
        )

        st.caption(
            "Processed data is held in Streamlit session memory only. "
            "It is not automatically saved to your project folder."
        )
