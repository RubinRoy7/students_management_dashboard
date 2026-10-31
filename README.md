# Student Performance Dashboard

## Project Overview

The Student Performance Dashboard is an interactive web application developed using Python and Streamlit. It analyzes students' academic performance and attendance through data cleaning, statistical analysis, interactive charts, and performance rankings.

## Objectives

- Import and inspect student data from a CSV file.
- Detect missing values, duplicate records, invalid values, and potential outliers.
- Calculate total marks, average marks, grades, and student rankings.
- Summarize class performance using KPI cards.
- Compare individual students and subjects.
- Analyze relationships between attendance and academic performance.
- Export the processed dataset as a CSV file.

## Technology Stack

- Python 3.11
- Streamlit
- Pandas
- NumPy
- Plotly
- Matplotlib
- Seaborn

## Dataset

The dataset contains the following columns:

- Student
- Python
- SQL
- Power BI
- AI
- Attendance

The four subject columns represent marks out of 100. Attendance is represented as a percentage.

## Project Structure

```text
student-performance-dashboard/
├── app.py
├── requirements.txt
├── README.md
├── .streamlit/
│   └── config.toml
├── data/
│   └── student_performance.csv
├── pages/
│   ├── 1_Dataset.py
│   ├── 2_Student_Analysis.py
│   └── 3_Visualizations.py
└── utils/
    └── helper.py
```

## Installation

1. Install Python 3.11.
2. Open the project directory in a terminal.
3. Create and activate a virtual environment.
4. Install dependencies:

   `pip install -r requirements.txt`

5. Place the dataset in the `data` directory.
6. Run the application:

   `streamlit run app.py`

## Features

- Dataset inspection and data-quality reporting
- Duplicate and invalid-value detection
- Calculated performance metrics
- Class overview and KPI cards
- Responsive dark data-studio theme with cyan accents, configured natively in Streamlit
- Native metric cards, headings, columns, dividers, and bordered chart containers
- Coordinated dark Plotly charts with high-contrast axes, legends, and hover states
- Student search, filtering, and comparison
- Interactive charts with clear titles, axis labels, legends, and tooltips
- Attendance and marks correlation analysis
- CSV export of processed data
- Standalone HTML report export from the rankings page

## Limitations

The dashboard analyzes the available dataset. Correlation results do not establish causation. Potential outliers require review before any records are removed.

## Conclusion

This project demonstrates data processing, data cleaning, descriptive statistics, performance analysis, and interactive visualization using Python.
