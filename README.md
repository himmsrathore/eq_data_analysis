# eq_data_analysis

Analysis of Railway Emergency Quota (HO / EQ) utilization for FY 2025-26.

- **Dashboard** (`app.py`): Streamlit app with two screens (switch with the tabs at the top):
  1. **EQ Utilization** (`views/eq_utilization.py`): month / train / class filters, a daily utilization calendar, week-wise, day-of-week, class-wise and train-wise charts, key findings and a detail table.
  2. **Class-wise Day Analysis** (`views/class_daywise.py`, teal header): built from the journey-date × train × class sheets of *HO Quota Report 2025-26*. Class × month and class × weekday heatmaps, daily fill-level distribution per class, daily trend with 7-day average, berth context, and rebalancing tables (train-classes whose quota is often exhausted vs. rarely used).
- Shared styles and chart helpers live in `common.py`.
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

For screen 2, place `HO Quota Report 2025-26.xlsx` in `data/` (not included, ~150 MB), then:

```
pip install python-calamine
python prepare_ho_data.py           # writes data/cache/ho_daily_class.parquet and ho_berth_info.parquet (~1 minute)
```
