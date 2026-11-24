# Student Performance Analytics Dashboard

A multipage Streamlit application for exploring academic results and attendance.
It demonstrates a small analytics workflow: inspect a CSV, report data-quality
issues, clean and derive metrics in memory, explore results, and export a report.

**Stack:** Python 3.11+, Streamlit, pandas, NumPy, Plotly, Matplotlib, and Seaborn.

## What it demonstrates

- **Data preparation:** duplicate detection, numeric conversion, range checks,
  and derived totals, averages, grades, and ranks.
- **Exploratory analysis:** class KPIs, subject comparisons, grade distribution,
  student rankings, and attendance-versus-marks analysis.
- **Interactive reporting:** searchable tables, Plotly charts, and CSV downloads.
- **Application structure:** separate Streamlit pages and shared data/UI helpers.

## Workflow

```text
data/student_performance.csv
          |
          v
inspect and validate -> clean in memory -> calculate metrics
                                            |
                         dashboard pages <-+
                                            |
                                downloadable CSV reports
```

The original CSV is not modified. The current cleaning policy replaces missing,
unreadable, or out-of-range numeric values with `0`; review this policy for the
intended analysis because zero imputation can affect averages and rankings.

## Dataset

The app expects these columns:

| Column | Meaning |
| --- | --- |
| `Student` | Student name or identifier |
| `Python`, `SQL`, `Power BI`, `AI` | Subject marks from 0 to 100 |
| `Attendance` | Attendance percentage from 0 to 100 |

The repository includes a synthetic `data/student_performance.csv` as the
app's input. Do not commit real student records to a public repository; use
synthetic or properly anonymized data.

## Run locally

Requires Python 3.11 or later.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed by Streamlit. The application loads the CSV from
`data/student_performance.csv`.

## Project structure

```text
student-performance-dashboard/
├── app.py                       # Class overview and student ranking
├── data/
│   └── student_performance.csv  # Input dataset
├── pages/
│   ├── 1_Dataset.py             # Data inspection and cleaning
│   ├── 2_Student_Analysis.py    # Individual student analysis
│   └── 3_Visualizations.py      # Charts and visual exploration
├── utils/
│   ├── helper.py                # Loading, validation, and calculations
│   └── ui.py                   # Shared Streamlit and Plotly styling
└── requirements.txt
```

## Limitations

The results describe only the records in the supplied dataset. Correlation does
not establish causation, and replacing invalid or missing values with zero is a
demonstration policy rather than a universal data-cleaning recommendation.
