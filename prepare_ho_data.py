"""One-time conversion for the second screen: HO Quota Report 2025-26 (day x train x class) -> Parquet.

Run:  python prepare_ho_data.py
"""
from pathlib import Path

import pandas as pd

BASE = Path(__file__).parent
SRC = BASE / "data" / "HO Quota Report 2025-26.xlsx"
OUT = BASE / "data" / "cache"
PERIOD_SHEETS = ["Apr25-Aug25", "Sep25-Dec25", "Jan26-Mar-26"]
COLS = ["year", "month", "date", "day", "train_no", "train_name", "cls", "available", "utilized", "pct"]


def read_sheet(name: str) -> pd.DataFrame:
    """Header sits on row 1 or row 2 depending on the sheet, so locate it."""
    raw = pd.read_excel(SRC, sheet_name=name, header=None, engine="calamine")
    hdr = raw.index[raw.iloc[:, 0].astype(str).str.strip() == "Year"][0]
    df = raw.iloc[hdr + 1:, :10]
    df.columns = COLS
    return df.dropna(subset=["train_no"])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("Reading Excel...")
    df = pd.concat([read_sheet(s) for s in PERIOD_SHEETS], ignore_index=True)
    for c in ["month", "day", "train_no", "train_name", "cls"]:
        df[c] = df[c].astype(str).str.strip().str.strip("'").str.strip()
    df["train_no"] = df["train_no"].str.zfill(5)
    df["date"] = pd.to_datetime(df["date"])
    for c in ["available", "utilized"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype("int32")
    df = df[["date", "train_no", "train_name", "cls", "available", "utilized"]]
    for c in ["train_no", "train_name", "cls"]:
        df[c] = df[c].astype("category")
    df.to_parquet(OUT / "ho_daily_class.parquet", index=False, compression="zstd")
    print(f"ho_daily_class: {len(df):,} rows  ({df['date'].min().date()} to {df['date'].max().date()}), "
          f"available {df['available'].sum():,}, utilized {df['utilized'].sum():,}")

    # Berth info: end-to-end vs redefined berths
    b = pd.read_excel(SRC, sheet_name="Berth Info`", header=None, engine="calamine")
    row = b.index[b.iloc[:, 0].astype(str).str.contains("End-to-End", na=False)][0] + 1
    e2e, redef = int(b.iloc[row, 0]), int(b.iloc[row, 1])
    pd.DataFrame([{"end_to_end": e2e, "redefined": redef}]).to_parquet(OUT / "ho_berth_info.parquet", index=False)
    print(f"berth info: end-to-end {e2e:,}, redefined {redef:,}")


if __name__ == "__main__":
    main()
