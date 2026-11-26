# eq_data_analysis

Analysis of Railway Emergency Quota (HO / EQ) utilization for FY 2025-26.

- **Dashboard** (`app.py`): Streamlit dashboard with month / train / class filters, a daily utilization calendar, week-wise, day-of-week, class-wise and train-wise charts, key findings and a detail table.
- **Report** (`make_report.py`): builds a 2-page PDF summary, saved in `reports/`.

## Setup

```
pip install streamlit plotly pandas pyarrow openpyxl reportlab matplotlib
```

Put the source Excel file at `data/Emergency Quota - HO Quota Report 2025-26 - Day-wise.xlsx` (not included in this repository), then:

```
python prepare_data.py              # one-time: converts the Excel to Parquet (about 2 minutes)
python -m streamlit run app.py      # dashboard at http://localhost:8501
python make_report.py               # regenerate the PDF report
```
