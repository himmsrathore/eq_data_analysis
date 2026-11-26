# eq_data_analysis

Analysis of Railway Emergency Quota (HO / EQ) utilization for FY 2025-26.

- **Dashboard** (`app.py`): Streamlit dashboard with month / train / class filters, a daily utilization calendar, week-wise, day-of-week, class-wise and train-wise charts, key findings and a detail table.
- **Report** (`make_report.py`): builds a 2-page PDF summary, saved in `reports/`.

## Setup

```
pip install -r requirements.txt
python -m streamlit run app.py      # dashboard at http://localhost:8501
```

The processed data (`data/cache/*.parquet`) is included, so the dashboard runs as-is. Deploy on Streamlit Community Cloud with `app.py` as the main file.

To refresh from a new Excel export, place it at `data/Emergency Quota - HO Quota Report 2025-26 - Day-wise.xlsx` (not included), then:

```
pip install openpyxl reportlab matplotlib
python prepare_data.py              # converts the Excel to Parquet (about 2 minutes)
python make_report.py               # regenerate the PDF report
```
