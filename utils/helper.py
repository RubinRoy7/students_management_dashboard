
from pathlib import Path
import re
import unicodedata

import pandas as pd

# ==================================================
# CONFIGURATION
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DATA_PATH = BASE_DIR / "data" / "student_performance.csv"

SUBJECT_COLUMNS = [
    "Python",
    "SQL",
    "Power BI",
    "AI"
]

NUMERIC_COLUMNS = SUBJECT_COLUMNS + ["Attendance"]

REQUIRED_COLUMNS = ["Student"] + NUMERIC_COLUMNS


# ==================================================
# LOAD RAW DATA
# ==================================================

def load_raw_data():
    """
    Load the original CSV without modifying it.
    """

    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {RAW_DATA_PATH}"
        )

    df = pd.read_csv(RAW_DATA_PATH)

    # Remove accidental whitespace from column names.
    df.columns = df.columns.str.strip()

    return df


# ==================================================
# VALIDATE REQUIRED COLUMNS
# ==================================================

def validate_columns(df):
    """
    Check whether the required dataset columns exist.
    """

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "The dataset is missing required columns: "
            + ", ".join(missing_columns)
        )


def student_name_matches(names, query):
    """Match all search terms regardless of case, accents, or extra spaces."""
    normalized_query = unicodedata.normalize("NFKD", str(query))
    normalized_query = "".join(
        character
        for character in normalized_query
        if not unicodedata.combining(character)
    )
    search_terms = re.sub(r"\s+", " ", normalized_query).strip().casefold().split()

    normalized_names = (
        names.astype("string")
        .fillna("")
        .str.normalize("NFKD")
        .str.replace(r"[\u0300-\u036f]", "", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
        .str.casefold()
    )

    matches = pd.Series(True, index=names.index, dtype=bool)
    for term in search_terms:
        matches &= normalized_names.str.contains(
            term,
            regex=False,
            na=False,
        )

    return matches


# ==================================================
# CLEAN AND PROCESS DATA IN MEMORY
# ==================================================

def process_data(raw_df):
    """
    Clean a copy of the raw dataset and calculate:
    - Total Marks
    - Average
    - Grade
    - Rank

    This function does not save any file.
    The original DataFrame remains unchanged.
    """

    if raw_df is None:
        raise ValueError("The input dataset is empty or missing.")

    # Work on a copy so the source remains unchanged.
    df = raw_df.copy()

    # Normalize column names.
    df.columns = df.columns.str.strip()

    # Validate the required columns.
    validate_columns(df)

    # --------------------------------------------------
    # 1. REMOVE EXACT DUPLICATE ROWS
    # --------------------------------------------------

    df = df.drop_duplicates().copy()

    # --------------------------------------------------
    # 2. CLEAN NUMERIC COLUMNS
    # --------------------------------------------------

    for column in NUMERIC_COLUMNS:

        # Convert non-numeric values to NaN.
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

        # Identify values outside the permitted range.
        invalid_range = ~df[column].between(0, 100)

        # Replace out-of-range values with zero.
        df.loc[invalid_range, column] = 0

        # Replace missing or unreadable values with zero.
        df[column] = df[column].fillna(0)

    # --------------------------------------------------
    # 3. CLEAN STUDENT NAMES
    # --------------------------------------------------

    df["Student"] = (
        df["Student"]
        .astype("string")
        .str.strip()
    )

    # --------------------------------------------------
    # 4. CALCULATE TOTAL MARKS
    # --------------------------------------------------

    df["Total Marks"] = df[SUBJECT_COLUMNS].sum(axis=1)

    # --------------------------------------------------
    # 5. CALCULATE AVERAGE
    # --------------------------------------------------

    df["Average"] = (
        df[SUBJECT_COLUMNS]
        .mean(axis=1)
        .round(2)
    )

    # --------------------------------------------------
    # 6. ASSIGN GRADES
    # --------------------------------------------------

    df["Grade"] = pd.cut(
        df["Average"],
        bins=[
            -float("inf"),
            50,
            75,
            90,
            float("inf")
        ],
        labels=["F", "C", "B", "A"],
        right=False
    )

    # --------------------------------------------------
    # 7. CALCULATE RANK
    # --------------------------------------------------

    df["Rank"] = (
        df["Average"]
        .rank(
            method="min",
            ascending=False
        )
        .astype("Int64")
    )

    return df


# ==================================================
# LOAD PROCESSED DATA FOR STATISTICAL USE
# ==================================================

def load_processed_data():
    """
    Load raw data and return a freshly cleaned DataFrame.
    No processed file is created or read.
    """

    raw_df = load_raw_data()

    return process_data(raw_df)
