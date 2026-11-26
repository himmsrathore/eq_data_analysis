"""One-time conversion: Excel report -> clean Parquet files for the dashboard.

Run:  python prepare_data.py
"""
from pathlib import Path

import pandas as pd

BASE = Path(__file__).parent
SRC = BASE / "data" / "Emergency Quota - HO Quota Report 2025-26 - Day-wise.xlsx"
OUT = BASE / "data" / "cache"


def clean_text(s: pd.Series) -> pd.Series:
    """Values come as "'22710'" -> strip quotes and padding."""
    return s.astype(str).str.strip().str.strip("'").str.strip()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("Reading Excel (this takes a few minutes)...")
    sheets = pd.read_excel(SRC, sheet_name=None, header=1, engine="openpyxl")
    names = {n.strip(): n for n in sheets}

    # --- Month x Train x Class detail ---
    det = sheets[names["detail"]].iloc[:, :10].dropna(subset=["Train_No"])
    det.columns = ["year", "month", "month_no", "train_no", "train_name",
                   "cls", "quota_code", "available", "utilized", "pct"]
    for c in ["month", "train_no", "train_name", "cls", "quota_code"]:
        det[c] = clean_text(det[c])
    det[["year", "month_no"]] = det[["year", "month_no"]].astype(int)
    det[["available", "utilized"]] = det[["available", "utilized"]].fillna(0).astype(int)
    det["train_no"] = det["train_no"].str.zfill(5)
    det.to_parquet(OUT / "detail.parquet", index=False)
    print(f"detail: {len(det):,} rows")

    # --- Day x Train ---
    day = sheets[names["date-wise data"]].iloc[:, :9].dropna(subset=["Train_No"])
    day.columns = ["year", "month_no", "date", "day", "train_no", "train_name",
                   "available", "utilized", "pct"]
    day["date"] = pd.to_datetime(day["date"])
    for c in ["day", "train_no", "train_name"]:
        day[c] = clean_text(day[c])
    day["train_no"] = day["train_no"].str.zfill(5)
    day[["available", "utilized"]] = day[["available", "utilized"]].fillna(0).astype(int)
    day.to_parquet(OUT / "daily.parquet", index=False)
    print(f"daily: {len(day):,} rows  ({day['date'].min().date()} to {day['date'].max().date()})")


if __name__ == "__main__":
    main()
