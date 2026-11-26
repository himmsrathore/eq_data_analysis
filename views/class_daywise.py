"""Screen 2 - Class-wise day-level analysis from HO Quota Report 2025-26 (journey date x train x class).

Data: data/cache/ho_daily_class.parquet, built by prepare_ho_data.py.
"""
import calendar

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from common import (CACHE, CLASS_ORDER, DAYS, FONT, GRID, MONTH_ORDER, MUTED, TEXT, TEXT2, base_layout, bar_fig,
                    card_head, pct, section, util)

# teal family for this screen, so it reads as a different view from screen 1 (slate blue)
TEAL = "#13827a"
TSEQ = ["#eef7f6", "#cfe9e5", "#a6d6cf", "#74bcb3", "#4a9f96", "#2f8178", "#1d625b"]
TSCALE = [[i / (len(TSEQ) - 1), c] for i, c in enumerate(TSEQ)]
# day-level fill buckets: zero use is neutral grey, then light -> dark teal as the quota fills up
BUCKETS = ["Not used", "1–25%", "25–50%", "50–75%", "75–99%", "Fully used"]
BUCKET_COLORS = ["#d4d7dd", TSEQ[1], TSEQ[2], TSEQ[3], TSEQ[5], TSEQ[6]]


# ---------- data ----------
@st.cache_data(show_spinner="Loading class-wise day data...")
def load():
    df = pd.read_parquet(CACHE / "ho_daily_class.parquet")
    df = df.copy()
    pairs = df.groupby(["train_no", "train_name"], observed=True).size().reset_index(name="n")
    names = pairs.sort_values("n").drop_duplicates("train_no", keep="last").set_index("train_no")["train_name"]
    df["train_name"] = df["train_no"].map(names.astype(str)).astype("category")
    df["year"] = df["date"].dt.year.astype("int16")
    df["month_no"] = df["date"].dt.month.astype("int8")
    df["dow"] = df["date"].dt.day_of_week.astype("int8")
    # day-level fill stats only where a quota was actually offered (24 rows have 0 available)
    has = df["available"] > 0
    df["offered"] = has
    df["full"] = has & (df["utilized"] >= df["available"])
    df["zero"] = has & (df["utilized"] == 0)
    p = df["utilized"] / df["available"].where(has) * 100
    codes = np.select([p <= 0, p <= 25, p <= 50, p <= 75, p < 100], [0, 1, 2, 3, 4], 5)
    df["bucket"] = pd.Categorical.from_codes(np.where(has, codes, -1), BUCKETS)
    berth = pd.read_parquet(CACHE / "ho_berth_info.parquet").iloc[0]
    return df, berth


df, berth = load()

# ---------- filters ----------
months = (df[["year", "month_no"]].drop_duplicates()
          .assign(k=lambda d: d["month_no"].map(MONTH_ORDER.index)).sort_values("k"))
month_keys = [None] + list(zip(months["year"], months["month_no"]))
month_labels = ["All months (FY 2025-26)"] + [f"{calendar.month_name[m]} {y}" for y, m in month_keys[1:]]
trains = df[["train_no", "train_name"]].drop_duplicates("train_no").sort_values("train_no")
train_labels = ["All trains"] + [f"{n} - {nm}" for n, nm in zip(trains["train_no"], trains["train_name"])]
present = set(df["cls"].unique())
classes = ["All classes"] + [c for c in CLASS_ORDER if c in present]

head = st.container()
with st.container(key="card_filters2"):
    c1, c2, c3 = st.columns([1, 2, 1])
    m_idx = c1.selectbox("Month", range(len(month_labels)), format_func=lambda i: month_labels[i], key="s2_month")
    t_lbl = c2.selectbox("Train No. / Train Name", train_labels, key="s2_train")
    cls = c3.selectbox("Class", classes, key="s2_cls")

sel_month = month_keys[m_idx]
sel_train = None if t_lbl == "All trains" else t_lbl.split(" - ")[0]
sel_cls = None if cls == "All classes" else cls

x = df
if sel_month:
    x = x[(x["year"] == sel_month[0]) & (x["month_no"] == sel_month[1])]
if sel_train:
    x = x[x["train_no"] == sel_train]
if sel_cls:
    x = x[x["cls"] == sel_cls]

if sel_month:
    start = pd.Timestamp(sel_month[0], sel_month[1], 1)
    end = start + pd.offsets.MonthEnd(0)
else:
    start, end = df["date"].min(), df["date"].max()

# ---------- heading (teal banner = screen 2) ----------
extra = "".join(f"<span class='sep'></span>{s}" for s in
                [t_lbl if sel_train else None, f"Class {cls}" if sel_cls else None] if s)
head.markdown(
    f"""<div class="hdr alt"><div><div class="eyebrow">Screen 2 · HO Quota Report 2025-26 · Day × Train × Class</div>
    <h1>Class-wise Day-level Quota Analysis</h1></div>
    <div class="pill">From <b>{start:%d %b %Y}</b> to <b>{end:%d %b %Y}</b>{extra}</div></div>""",
    unsafe_allow_html=True,
)

if x.empty:
    st.warning("No data for this selection.")
    st.stop()

# ---------- KPIs ----------
avail, used = int(x["available"].sum()), int(x["utilized"].sum())
overall = pct(used, avail)
n_days = int((x["available"] > 0).sum())
full_share = pct(x["full"].sum(), n_days)
zero_share = pct(x["zero"].sum(), n_days)
st.markdown(
    f"""<div class="kpis alt-scope">
      <div class="kpi"><div class="l">Available quota</div><div class="v">{avail:,}</div>
           <div class="s">berths over {n_days:,} train-class-days</div></div>
      <div class="kpi"><div class="l">Utilized</div><div class="v">{used:,}</div><div class="s">berths</div></div>
      <div class="kpi"><div class="l">Utilization</div><div class="v">{overall:.1f}%</div>
           <div class="bar"><div style="width:{min(overall, 100):.1f}%"></div></div></div>
      <div class="kpi"><div class="l">Quota exhausted</div><div class="v">{full_share:.1f}%</div>
           <div class="s">of train-class-days fully used</div></div>
      <div class="kpi"><div class="l">Not used at all</div><div class="v">{zero_share:.1f}%</div>
           <div class="s">of train-class-days with 0 used</div></div>
    </div>""",
    unsafe_allow_html=True,
)
if not (sel_month or sel_train or sel_cls):
    st.markdown(
        f"<div class='note'><b>Berth context (2025-26):</b> {int(berth['end_to_end']):,} end-to-end berths and "
        f"{int(berth['redefined']):,} redefined berths (ratio {berth['end_to_end'] / berth['redefined']:.1%}). "
        f"The emergency quota of {avail:,} berths is {avail / berth['end_to_end']:.2%} of end-to-end berths.</div>",
        unsafe_allow_html=True)


# ---------- chart builders ----------
def heat_fig(g, row, col, row_labels, col_labels, h):
    """g has row, col, available, utilized, pct -> utilization heatmap with values printed in cells."""
    piv = g.pivot(index=row, columns=col, values="pct").reindex(index=row_labels, columns=col_labels)
    av = g.pivot(index=row, columns=col, values="available").reindex(index=row_labels, columns=col_labels)
    ut = g.pivot(index=row, columns=col, values="utilized").reindex(index=row_labels, columns=col_labels)
    xl = [str(c) for c in col_labels] if not isinstance(col_labels[0], (int, np.integer)) else None
    z = piv.values
    txt = [["" if np.isnan(v) else f"{v:.0f}%" for v in r] for r in z]
    fig = go.Figure(go.Heatmap(
        z=z, x=xl or col_labels, y=row_labels, text=txt, texttemplate="%{text}",
        textfont=dict(size=9, family=FONT), customdata=np.dstack([av.fillna(0).values, ut.fillna(0).values]),
        colorscale=TSCALE, zmin=0, zmax=100, xgap=2, ygap=2,
        colorbar=dict(title=dict(text="% used", font=dict(size=10)), ticksuffix="%", thickness=8, len=0.8,
                      tickfont=dict(size=9), outlinewidth=0),
        hovertemplate="<b>%{y} · %{x}</b><br>Available: %{customdata[0]:,.0f}<br>"
                      "Utilized: %{customdata[1]:,.0f}<br><b>Utilization: %{z:.1f}%</b><extra></extra>",
    ))
    base_layout(fig, h, top=6)
    fig.update_layout(plot_bgcolor="#f7f8fa")
    fig.update_xaxes(side="top", showgrid=False, tickfont=dict(size=9, color=TEXT2), type="category")
    fig.update_yaxes(autorange="reversed", showgrid=False, tickfont=dict(size=9, color=TEXT2), type="category")
    return fig


def chart_card(key, title, sub, fig):
    with st.container(key=f"card_{key}"):
        card_head(title, sub)
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False}, key=f"plot2_{key}")


cls_present = [c for c in CLASS_ORDER if c in set(x["cls"].unique())]
cl = util(x.assign(cls=x["cls"].astype(str)), "cls").set_index("cls").reindex(cls_present).reset_index()

# ---------- class patterns ----------
section("Class patterns")
heat_h = 60 + 26 * len(cls_present)
if sel_month:
    h1, h2 = st.columns([1, 1])
    with h1:
        chart_card("cls_bar", "Class-wise utilization", "Share of quota used, by travel class",
                   bar_fig(cl, cl["cls"], h=max(heat_h, 240), color=TEAL))
else:
    h1, h2 = st.columns([1.5, 1])
    with h1:
        mo = util(x.assign(cls=x["cls"].astype(str)), ["cls", "year", "month_no"])
        mo["mon"] = [f"{calendar.month_abbr[m]} {str(y)[2:]}" for y, m in zip(mo["year"], mo["month_no"])]
        mon_order = [f"{calendar.month_abbr[m]} {str(y)[2:]}" for y, m in month_keys[1:]]
        chart_card("cls_mon", "Class × month", "Utilization % by class and journey month",
                   heat_fig(mo, "cls", "mon", cls_present, mon_order, heat_h))
with h2:
    dw = util(x.assign(cls=x["cls"].astype(str)), ["cls", "dow"])
    dw["dname"] = dw["dow"].map(lambda i: DAYS[i])
    chart_card("cls_dow", "Class × day of week", "Utilization % by class and journey weekday",
               heat_fig(dw, "cls", "dname", cls_present, DAYS, heat_h))

# ---------- fill distribution + daily trend ----------
section("How fully is the quota used each day")
f1, f2 = st.columns([1, 1.3])
with f1:
    dist = (x.assign(cls=x["cls"].astype(str)).groupby(["cls", "bucket"], observed=False).size()
            .unstack(fill_value=0).reindex(index=cls_present, columns=BUCKETS, fill_value=0))
    share = dist.div(dist.sum(axis=1).replace(0, np.nan), axis=0) * 100
    fig = go.Figure()
    for b, c in zip(BUCKETS, BUCKET_COLORS):
        fig.add_trace(go.Bar(
            y=share.index, x=share[b], name=b, orientation="h", marker=dict(color=c, line=dict(color="#fff", width=1)),
            customdata=dist[b], hovertemplate=f"<b>%{{y}}</b> · {b}<br>%{{x:.1f}}% of days (%{{customdata:,}})<extra></extra>"))
    base_layout(fig, max(heat_h + 40, 260), top=6)
    fig.update_layout(barmode="stack", bargap=0.3,
                      legend=dict(orientation="h", y=-0.12, x=0, font=dict(size=9, color=TEXT2), traceorder="normal"))
    fig.update_xaxes(range=[0, 100], ticksuffix="%", gridcolor=GRID, tickfont=dict(size=9, color=MUTED))
    fig.update_yaxes(autorange="reversed", type="category", tickfont=dict(size=9, color=TEXT2))
    chart_card("dist", "Daily fill level by class",
               "Each train-class-day placed in a bucket by the share of its quota used", fig)
with f2:
    day = util(x, "date").sort_values("date")
    day["roll"] = day["utilized"].rolling(7, min_periods=1).sum() / day["available"].rolling(7, min_periods=1).sum() * 100
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=day["date"], y=day["pct"], name="Daily", mode="lines",
                             line=dict(color=TSEQ[3], width=1), customdata=np.stack([day["available"], day["utilized"]], -1),
                             hovertemplate="%{x|%a, %d %b %Y}<br>Available: %{customdata[0]:,}<br>"
                                           "Utilized: %{customdata[1]:,}<br><b>%{y:.1f}%</b><extra>Daily</extra>"))
    fig.add_trace(go.Scatter(x=day["date"], y=day["roll"], name="7-day average", mode="lines",
                             line=dict(color=TSEQ[6], width=2.2),
                             hovertemplate="%{x|%d %b %Y}<br><b>%{y:.1f}%</b><extra>7-day avg</extra>"))
    base_layout(fig, max(heat_h + 40, 260), top=6)
    fig.update_layout(hovermode="x unified", legend=dict(orientation="h", y=1.08, x=0, font=dict(size=9, color=TEXT2)))
    fig.update_yaxes(ticksuffix="%", gridcolor=GRID, zeroline=False, tickfont=dict(size=9, color=MUTED), rangemode="tozero")
    fig.update_xaxes(showgrid=False, tickfont=dict(size=9, color=TEXT2))
    chart_card("trend", "Daily utilization trend", "Journey-date utilization with a 7-day rolling average", fig)

# ---------- train x class stats ----------
tc = (x.groupby(["train_no", "cls"], observed=True)
      .agg(days=("offered", "sum"), available=("available", "sum"), utilized=("utilized", "sum"),
           full_days=("full", "sum"), zero_days=("zero", "sum"))
      .reset_index())
tc["train_name"] = tc["train_no"].map(dict(zip(trains["train_no"], trains["train_name"])))
tc["pct"] = np.where(tc["available"] > 0, tc["utilized"] / tc["available"].clip(lower=1) * 100, 0.0)
tc["full_pct"] = np.where(tc["days"] > 0, tc["full_days"] / tc["days"].clip(lower=1) * 100, 0.0)
tc["zero_pct"] = np.where(tc["days"] > 0, tc["zero_days"] / tc["days"].clip(lower=1) * 100, 0.0)
tc["unused"] = tc["available"] - tc["utilized"]
min_days = 4 if sel_month else 20
tc_ok = tc[tc["days"] >= min_days]
short = tc_ok[tc_ok["full_pct"] >= 50].sort_values(["full_pct", "available"], ascending=False)
idle = tc_ok[tc_ok["zero_pct"] >= 90].sort_values("unused", ascending=False)

# ---------- key findings ----------
section("Key findings")
cards = [("Overall", f"{overall:.1f}% used",
          f"{used:,} of {avail:,} berths used across {n_days:,} train-class-days.")]
if len(cl) > 1:
    hi, lo = cl.loc[cl["pct"].idxmax()], cl.loc[cl["pct"].idxmin()]
    cards.append(("Class", f"{hi['cls']} highest · {hi['pct']:.1f}%", f"Lowest is {lo['cls']} at {lo['pct']:.1f}%."))
dwt = util(x, "dow")
if len(dwt) > 1:
    hi, lo = dwt.loc[dwt["pct"].idxmax()], dwt.loc[dwt["pct"].idxmin()]
    cards.append(("Day of week", f"{calendar.day_name[int(hi['dow'])]} · {hi['pct']:.1f}%",
                  f"Lowest on {calendar.day_name[int(lo['dow'])]} ({lo['pct']:.1f}%)."))
cards.append(("Fill level", f"{zero_share:.0f}% of days unused",
              f"Quota ran out on {full_share:.1f}% of train-class-days; "
              f"{(x['utilized'] > x['available']).sum():,} days show more used than available."))
cards.append(("Often short", f"{len(short):,} train-classes",
              f"Quota fully used on half or more of their days (min. {min_days} days running)."))
cards.append(("Rarely used", f"{len(idle):,} train-classes",
              f"Nothing used on 90%+ of days, {int(idle['unused'].sum()):,} berths released unused."))
st.markdown("<div class='ins'>" + "".join(
    f"<div class='in'><div class='l'>{l}</div><div class='v'>{v}</div><div class='s'>{s}</div></div>"
    for l, v, s in cards) + "</div>", unsafe_allow_html=True)

# ---------- rebalancing tables ----------
RENAME = {"train_no": "Train No", "train_name": "Train Name", "cls": "Class", "days": "Days run",
          "available": "Available", "utilized": "Utilized", "unused": "Unused", "pct": "Utilization %",
          "full_pct": "Days fully used %", "zero_pct": "Days not used %"}
PCT = lambda: st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100)  # noqa: E731
COLCFG = {"Utilization %": PCT(), "Days fully used %": PCT(), "Days not used %": PCT()}

section("Rebalancing signals")
r1, r2 = st.columns(2)
with r1, st.container(key="card_short"):
    card_head("Quota often exhausted — consider increasing",
              f"Train-class with quota fully used on ≥50% of days · {len(short):,} found")
    st.dataframe(short.head(50)[["train_no", "train_name", "cls", "days", "available", "utilized", "full_pct", "pct"]]
                 .rename(columns=RENAME), hide_index=True, width="stretch", height=300, column_config=COLCFG)
with r2, st.container(key="card_idle"):
    card_head("Quota rarely used — consider reducing",
              f"Train-class with nothing used on ≥90% of days · {len(idle):,} found, most unused first")
    st.dataframe(idle.head(50)[["train_no", "train_name", "cls", "days", "available", "unused", "zero_pct", "pct"]]
                 .rename(columns=RENAME), hide_index=True, width="stretch", height=300, column_config=COLCFG)

# ---------- detail ----------
section("Detail")
with st.container(key="card_table2"):
    tbl = tc.sort_values(["train_no", "cls"])[
        ["train_no", "train_name", "cls", "days", "available", "utilized", "unused", "pct", "full_pct", "zero_pct"]
    ].rename(columns=RENAME)
    tbl["Class"] = tbl["Class"].astype(str)
    d1, d2 = st.columns([4, 1])
    with d1:
        card_head("Train × class day-level detail", f"{len(tbl):,} rows")
    d2.download_button("Download CSV", tbl.to_csv(index=False).encode(), width="stretch", key="dl2",
                       file_name=f"ho_class_daywise_{start:%Y%m%d}_{end:%Y%m%d}.csv", mime="text/csv")
    st.dataframe(tbl, hide_index=True, width="stretch", height=340, column_config=COLCFG)

st.caption("Source: HO Quota Report 2025-26 (journey date × train × class sheets: Apr25-Aug25, Sep25-Dec25, "
           "Jan26-Mar-26) and the Berth Info sheet. Day-level fill statistics (exhausted / not used / buckets / days run) "
           "exclude the few train-class-days with zero available quota.")
