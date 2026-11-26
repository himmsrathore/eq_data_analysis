"""Emergency Quota (HO / EQ) Utilization Dashboard - Indian Railways 2025-26.

Run:
    python prepare_data.py          # once, converts the Excel to Parquet
    python -m streamlit run app.py
"""
import calendar
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

CACHE = Path(__file__).parent / "data" / "cache"

# ---------- design tokens ----------
ACCENT = "#5b7598"  # muted slate blue
SEQ = ["#eef1f5", "#d3dbe6", "#b3c1d4", "#8fa3bd", "#6c84a3", "#4f6787", "#364b68"]
TEXT, TEXT2, MUTED, GRID, SURFACE = "#111827", "#4b5563", "#9ca3af", "#eef0f3", "#ffffff"
FONT = "Inter, -apple-system, Segoe UI, sans-serif"
COLORSCALE = [[i / (len(SEQ) - 1), c] for i, c in enumerate(SEQ)]
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTH_ORDER = [4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3]  # financial year
CLASS_ORDER = ["1A", "2A", "3A", "3E", "SL", "CC", "EC", "2S", "EV", "FC", "EA", "VS"]

st.set_page_config(page_title="Emergency Quota Analysis", layout="wide")
st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
      html, body, [class*="css"], .stApp, button, input, textarea {font-family:'Inter',sans-serif !important;}
      html, body {font-size:13px;}
      .stApp {background:#f4f5f7;}
      header[data-testid="stHeader"] {background:transparent; height:0;}
      .block-container {padding:1.2rem 1.6rem 2rem; max-width:1440px;}
      div[data-testid="stVerticalBlock"] {gap:.75rem;}
      div[data-testid="stHorizontalBlock"] {gap:.75rem;}

      /* header */
      .hdr {display:flex; justify-content:space-between; align-items:flex-end; gap:1rem; flex-wrap:wrap;
            padding:.2rem .1rem .3rem;}
      .hdr .eyebrow {font-size:.68rem; font-weight:600; letter-spacing:.08em; text-transform:uppercase; color:#6b7280;}
      .hdr h1 {font-size:1.35rem; font-weight:700; color:#111827; margin:.15rem 0 0; padding:0; letter-spacing:-.01em;}
      .pill {display:inline-flex; align-items:center; gap:.5rem; background:#fff; border:1px solid #e5e7eb;
             border-radius:999px; padding:.35rem .85rem; font-size:.78rem; color:#4b5563;}
      .pill b {color:#111827; font-weight:600;}
      .pill .sep {width:1px; height:12px; background:#e5e7eb;}

      /* cards */
      [class*="st-key-card"] {background:#fff; border:1px solid #e7e9ee; border-radius:12px;
             padding:14px 16px 8px; box-shadow:0 1px 2px rgba(16,24,40,.04);}
      .ct {font-size:.85rem; font-weight:600; color:#111827; margin:0;}
      .cs {font-size:.72rem; color:#6b7280; margin:.1rem 0 .2rem;}
      .section {font-size:.7rem; font-weight:600; letter-spacing:.08em; text-transform:uppercase;
                color:#6b7280; margin:.6rem 0 -.2rem .1rem;}

      /* KPI tiles */
      .kpis {display:grid; grid-template-columns:repeat(5,1fr); gap:.75rem;}
      .kpi {background:#fff; border:1px solid #e7e9ee; border-radius:12px; padding:12px 16px;
            box-shadow:0 1px 2px rgba(16,24,40,.04);}
      .kpi .l {font-size:.7rem; color:#6b7280; font-weight:500;}
      .kpi .v {font-size:1.35rem; font-weight:700; color:#111827; margin-top:2px; letter-spacing:-.01em;}
      .kpi .s {font-size:.68rem; color:#9ca3af; margin-top:1px;}
      .bar {height:4px; background:#eef0f3; border-radius:4px; margin-top:8px; overflow:hidden;}
      .bar > div {height:100%; background:#5b7598; border-radius:4px;}

      /* insights */
      .ins {display:grid; grid-template-columns:repeat(3,1fr); gap:.75rem;}
      .in {background:#fff; border:1px solid #e7e9ee; border-radius:12px; padding:12px 14px;}
      .in .l {font-size:.68rem; font-weight:600; letter-spacing:.06em; text-transform:uppercase; color:#6b7280;}
      .in .v {font-size:1rem; font-weight:600; color:#111827; margin:.25rem 0 .1rem;}
      .in .s {font-size:.74rem; color:#4b5563; line-height:1.45;}

      .note {font-size:.74rem; color:#4b5563; background:#f8fafc; border:1px solid #e5e7eb;
             border-radius:8px; padding:.45rem .75rem;}

      /* widgets */
      div[data-testid="stSelectbox"] label p, div[data-testid="stNumberInput"] label p,
      div[data-testid="stSlider"] label p {font-size:.7rem !important; color:#6b7280; font-weight:500;}
      div[data-baseweb="select"] {font-size:.8rem;}
      div[data-baseweb="select"] > div {min-height:34px; border-radius:8px; border-color:#e5e7eb; background:#fff;}
      div[data-testid="stRadio"] label p {font-size:.78rem;}
      div[data-testid="stCaptionContainer"] p {font-size:.7rem; color:#9ca3af;}
      div[data-testid="stDownloadButton"] button {padding:2px 12px; min-height:30px; font-size:.75rem;
             border-radius:8px; border:1px solid #e5e7eb; background:#fff;}
      div[data-testid="stExpander"] details {border-radius:12px; border-color:#e7e9ee; background:#fff;}
      div[data-testid="stExpander"] summary p {font-size:.8rem; font-weight:500;}
      @media (max-width: 900px) {.kpis {grid-template-columns:repeat(2,1fr);} .ins {grid-template-columns:1fr;}}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------- data ----------
@st.cache_data(show_spinner="Loading data...")
def load():
    daily = pd.read_parquet(CACHE / "daily.parquet")
    detail = pd.read_parquet(CACHE / "detail.parquet")
    names = daily.groupby("train_no")["train_name"].agg(lambda s: s.value_counts().index[0])
    daily["train_name"] = daily["train_no"].map(names)
    detail["train_name"] = detail["train_no"].map(names).fillna(detail["train_name"])
    daily["week"] = (daily["date"].dt.day - 1) // 7 + 1
    daily["dow"] = daily["date"].dt.day_of_week
    return daily, detail


def pct(u, a):
    return float(u) / float(a) * 100 if a else 0.0


def util(df, by):
    g = df.groupby(by, as_index=False)[["available", "utilized"]].sum()
    g["pct"] = np.where(g["available"] > 0, g["utilized"] / g["available"] * 100, 0.0)
    return g


def card_head(title, sub=""):
    st.markdown(f"<p class='ct'>{title}</p>" + (f"<p class='cs'>{sub}</p>" if sub else ""),
                unsafe_allow_html=True)


def section(label):
    st.markdown(f"<div class='section'>{label}</div>", unsafe_allow_html=True)


daily, detail = load()

# ---------- filters ----------
months = (detail[["year", "month_no", "month"]].drop_duplicates()
          .assign(k=lambda d: d["month_no"].map(MONTH_ORDER.index)).sort_values("k"))
month_labels = ["All months (FY 2025-26)"] + [f"{m} {y}" for m, y in zip(months["month"], months["year"])]
month_keys = [None] + list(zip(months["year"], months["month_no"]))
trains = daily[["train_no", "train_name"]].drop_duplicates("train_no").sort_values("train_no")
train_labels = ["All trains"] + [f"{n} - {nm}" for n, nm in zip(trains["train_no"], trains["train_name"])]
classes = ["All classes"] + [c for c in CLASS_ORDER if c in set(detail["cls"])]

head = st.container()
with st.container(key="card_filters"):
    c1, c2, c3 = st.columns([1, 2, 1])
    m_idx = c1.selectbox("Month", range(len(month_labels)), format_func=lambda i: month_labels[i])
    t_lbl = c2.selectbox("Train No. / Train Name", train_labels)
    cls = c3.selectbox("Class", classes)

sel_month = month_keys[m_idx]
sel_train = None if t_lbl == "All trains" else t_lbl.split(" - ")[0]
sel_cls = None if cls == "All classes" else cls

d, x = daily, detail
if sel_month:
    d = d[(d["year"] == sel_month[0]) & (d["month_no"] == sel_month[1])]
    x = x[(x["year"] == sel_month[0]) & (x["month_no"] == sel_month[1])]
if sel_train:
    d = d[d["train_no"] == sel_train]
    x = x[x["train_no"] == sel_train]
if sel_cls:
    x = x[x["cls"] == sel_cls]

if sel_month:
    start = pd.Timestamp(sel_month[0], sel_month[1], 1)
    end = start + pd.offsets.MonthEnd(0)
else:
    start, end = daily["date"].min(), daily["date"].max()

# ---------- heading ----------
extra = "".join(f"<span class='sep'></span>{s}" for s in
                [t_lbl if sel_train else None, f"Class {cls}" if sel_cls else None] if s)
head.markdown(
    f"""<div class="hdr"><div><div class="eyebrow">Indian Railways · HO / EQ Quota</div>
    <h1>Emergency Quota Utilization Analysis</h1></div>
    <div class="pill">From <b>{start:%d %b %Y}</b> to <b>{end:%d %b %Y}</b>{extra}</div></div>""",
    unsafe_allow_html=True,
)

if x.empty and d.empty:
    st.warning("No data for this selection.")
    st.stop()

# ---------- KPIs ----------
avail, used = int(x["available"].sum()), int(x["utilized"].sum())
overall = pct(used, avail)
st.markdown(
    f"""<div class="kpis">
      <div class="kpi"><div class="l">Available quota</div><div class="v">{avail:,}</div><div class="s">berths</div></div>
      <div class="kpi"><div class="l">Utilized</div><div class="v">{used:,}</div><div class="s">berths</div></div>
      <div class="kpi"><div class="l">Utilization</div><div class="v">{overall:.1f}%</div>
           <div class="bar"><div style="width:{min(overall, 100):.1f}%"></div></div></div>
      <div class="kpi"><div class="l">Unused</div><div class="v">{avail - used:,}</div><div class="s">{100 - overall:.1f}% of quota</div></div>
      <div class="kpi"><div class="l">Trains</div><div class="v">{x['train_no'].nunique():,}</div><div class="s">with quota</div></div>
    </div>""",
    unsafe_allow_html=True,
)
if sel_cls:
    st.markdown(f"<div class='note'>Day-wise source data is not split by class, so the calendar, week and "
                f"weekday charts include all classes. Totals, class chart and tables use Class {cls} only.</div>",
                unsafe_allow_html=True)


# ---------- chart builders ----------
def base_layout(fig, h, top=8):
    fig.update_layout(height=h, margin=dict(l=4, r=4, t=top, b=4), paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
                      font=dict(family=FONT, size=10, color=TEXT2),
                      hoverlabel=dict(bgcolor="#fff", bordercolor="#e5e7eb", font=dict(family=FONT, size=11, color=TEXT)))
    return fig


def calendar_fig(dd: pd.DataFrame, ym_list):
    day = util(dd, "date").set_index("date")
    n = len(ym_list)
    cols = 1 if n == 1 else 4
    rows = int(np.ceil(n / cols))
    titles = [f"{calendar.month_name[m]} {y}" for y, m in ym_list] if n > 1 else None
    fig = make_subplots(rows=rows, cols=cols, subplot_titles=titles,
                        horizontal_spacing=0.025, vertical_spacing=0.07 if n > 1 else 0.05)
    fs = 11 if n == 1 else 8
    for i, (y, m) in enumerate(ym_list):
        r, c = i // cols + 1, i % cols + 1
        weeks = calendar.Calendar(0).monthdatescalendar(y, m)
        z, cd, txt = [], [], []
        for wk in weeks:
            zr, cr, tr = [], [], []
            for dt in wk:
                ts = pd.Timestamp(dt)
                if dt.month != m or ts not in day.index:
                    zr.append(None); cr.append(["", 0, 0]); tr.append(str(dt.day) if dt.month == m else "")
                else:
                    row = day.loc[ts]
                    zr.append(row["pct"])
                    cr.append([f"{dt:%a, %d %b %Y}", int(row["available"]), int(row["utilized"])])
                    tr.append(f"<b>{dt.day}</b><br>{row['pct']:.0f}%" if n == 1 else f"{dt.day}<br>{row['pct']:.0f}%")
            z.append(zr); cd.append(cr); txt.append(tr)
        fig.add_trace(go.Heatmap(
            z=z, x=DAYS, y=[f"W{j+1}" for j in range(len(weeks))], customdata=cd,
            coloraxis="coloraxis", xgap=3, ygap=3,
            hovertemplate="%{customdata[0]}<br>Available: %{customdata[1]:,}<br>"
                          "Utilized: %{customdata[2]:,}<br><b>Utilization: %{z:.1f}%</b><extra></extra>",
        ), row=r, col=c)
        for wi, tr in enumerate(txt):
            for di, t in enumerate(tr):
                if t:
                    v = z[wi][di]
                    color = "#ffffff" if (v or 0) >= 65 else (TEXT if v is not None else MUTED)
                    fig.add_annotation(x=DAYS[di], y=f"W{wi+1}", text=t, showarrow=False,
                                       font=dict(size=fs, color=color), row=r, col=c)
        fig.update_yaxes(autorange="reversed", showticklabels=False, showgrid=False, row=r, col=c)
        fig.update_xaxes(side="top", showgrid=False, tickfont=dict(size=fs - 1, color=MUTED), row=r, col=c)
    fig.update_layout(coloraxis=dict(
        colorscale=COLORSCALE, cmin=0, cmax=100,
        colorbar=dict(title=dict(text="% used", font=dict(size=10)), ticksuffix="%", thickness=8, len=0.7,
                      tickfont=dict(size=9), outlinewidth=0)))
    base_layout(fig, 310 if n == 1 else 190 * rows, top=8 if n == 1 else 44)
    fig.update_layout(plot_bgcolor="#f7f8fa")
    for a in fig.layout.annotations:
        if a.xref == "paper":
            a.font = dict(size=11, color=TEXT, family=FONT)
            a.yshift = 6
    return fig


def bar_fig(g, labels, h=230, text_fmt="{:.1f}%", hover_name=None):
    cd = np.stack([g["available"], g["utilized"]] + ([hover_name] if hover_name is not None else []), axis=-1)
    fig = go.Figure(go.Bar(
        x=list(labels), y=g["pct"], marker=dict(color=ACCENT, cornerradius=3),
        text=[text_fmt.format(v) for v in g["pct"]], textposition="outside", cliponaxis=False,
        textfont=dict(color=TEXT2, size=9), customdata=cd,
        hovertemplate="<b>%{x}</b>" + (" %{customdata[2]}" if hover_name is not None else "") +
                      "<br>Available: %{customdata[0]:,}<br>Utilized: %{customdata[1]:,}"
                      "<br>Utilization: %{y:.1f}%<extra></extra>",
    ))
    top = max(100, float(g["pct"].max()) * 1.15) if len(g) else 100
    base_layout(fig, h, top=14)
    fig.update_layout(bargap=0.4)
    fig.update_yaxes(range=[0, top], ticksuffix="%", gridcolor=GRID, zeroline=False, tickfont=dict(size=9, color=MUTED))
    fig.update_xaxes(type="category", tickfont=dict(size=9, color=TEXT2), showgrid=False)
    return fig


def chart_card(key, title, sub, fig):
    with st.container(key=f"card_{key}"):
        card_head(title, sub)
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False}, key=f"plot_{key}")


# ---------- aggregates ----------
ym_list = [sel_month] if sel_month else list(zip(months["year"], months["month_no"]))
wk = util(d, "week")
wk_labels = [f"Week {w}" for w in wk["week"]]
dw = util(d, "dow")
cl = util(x, "cls")
cl = cl.set_index("cls").reindex([c for c in CLASS_ORDER if c in set(cl["cls"])]).reset_index()

# ---------- calendar + week ----------
section("Daily pattern")
cal_title = "Daily utilization calendar"
cal_sub = "Share of emergency quota used on each journey date"
week_sub = "Week 1 = days 1–7, Week 2 = 8–14, Week 3 = 15–21, Week 4 = 22–28, Week 5 = 29–31"
if sel_month:
    cc1, cc2 = st.columns([3, 2])
    with cc1:
        chart_card("cal", cal_title, cal_sub, calendar_fig(d, ym_list))
    with cc2:
        chart_card("week", "Week-wise utilization", week_sub, bar_fig(wk, wk_labels, h=310))
else:
    chart_card("cal", cal_title, cal_sub, calendar_fig(d, ym_list))

# ---------- breakdown bars ----------
section("Breakdown")
if sel_month:
    b2, b3, b4 = st.columns(3)
else:
    b1, b2, b3, b4 = st.columns([1, 1, 1, 1.6])
    with b1:
        chart_card("week", "Week-wise utilization", "Week of month, all months combined", bar_fig(wk, wk_labels))
with b2:
    chart_card("dow", "Day-of-week utilization", "By journey day", bar_fig(dw, [DAYS[i] for i in dw["dow"]]))
with b3:
    chart_card("cls", "Class-wise utilization", "By travel class", bar_fig(cl, cl["cls"]))
with b4:
    if not sel_month:
        mo = util(x, ["year", "month_no"])
        mo = mo.assign(k=mo["month_no"].map(MONTH_ORDER.index)).sort_values("k")
        chart_card("mon", "Month-wise utilization", "April 2025 – March 2026",
                   bar_fig(mo, [f"{calendar.month_abbr[m]} {str(y)[2:]}" for y, m in zip(mo["year"], mo["month_no"])]))
    else:
        qc = util(x, "quota_code")
        chart_card("qc", "Quota-code-wise utilization", "HO, HORS, EQ", bar_fig(qc, qc["quota_code"]))

# ---------- insights ----------
section("Key findings")
tr = util(x, ["train_no", "train_name"])
cards = [("Overall", f"{overall:.1f}% used",
          f"{used:,} of {avail:,} berths used; {avail - used:,} released unused.")]
if len(wk):
    hi, lo = wk.loc[wk["pct"].idxmax()], wk.loc[wk["pct"].idxmin()]
    cards.append(("Week of month", f"Week {int(hi['week'])} busiest · {hi['pct']:.1f}%",
                  f"Lightest is Week {int(lo['week'])} at {lo['pct']:.1f}%."))
if len(dw):
    hi, lo = dw.loc[dw["pct"].idxmax()], dw.loc[dw["pct"].idxmin()]
    cards.append(("Day of week", f"{calendar.day_name[int(hi['dow'])]} · {hi['pct']:.1f}%",
                  f"Lowest demand on {calendar.day_name[int(lo['dow'])]} ({lo['pct']:.1f}%)."))
dd = util(d, "date")
if len(dd):
    hi, lo = dd.loc[dd["pct"].idxmax()], dd.loc[dd["pct"].idxmin()]
    cards.append(("Peak day", f"{hi['date']:%d %b %Y} · {hi['pct']:.1f}%",
                  f"Lowest day was {lo['date']:%d %b %Y} ({lo['pct']:.1f}%)."))
if len(cl) > 1:
    hi, lo = cl.loc[cl["pct"].idxmax()], cl.loc[cl["pct"].idxmin()]
    cards.append(("Class", f"{hi['cls']} highest · {hi['pct']:.1f}%",
                  f"Lowest is {lo['cls']} at {lo['pct']:.1f}%."))
if not sel_train and len(tr):
    cards.append(("Quota sizing", f"{(tr['pct'] < 25).sum():,} trains under 25%",
                  f"{(tr['pct'] >= 95).sum():,} trains use 95% or more; {(tr['utilized'] == 0).sum():,} used none."))
st.markdown("<div class='ins'>" + "".join(
    f"<div class='in'><div class='l'>{l}</div><div class='v'>{v}</div><div class='s'>{s}</div></div>"
    for l, v, s in cards) + "</div>", unsafe_allow_html=True)

RENAME = {"train_no": "Train No", "train_name": "Train Name", "cls": "Class", "available": "Available",
          "utilized": "Utilized", "unused": "Unused", "pct": "Utilization %"}
PCT_COL = {"Utilization %": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100)}

if not sel_train and len(tr):
    a1, a2 = st.columns(2)
    with a1, st.container(key="card_waste"):
        card_head("Most unused quota", "Top 10 trains by berths released unused — candidates for reduction")
        waste = tr.assign(unused=tr["available"] - tr["utilized"]).nlargest(10, "unused")
        st.dataframe(waste[["train_no", "train_name", "available", "utilized", "unused", "pct"]].rename(columns=RENAME),
                     hide_index=True, width="stretch", column_config=PCT_COL)
    with a2, st.container(key="card_busy"):
        card_head("Highest demand", "Top 10 trains by utilization, quota at or above the median")
        busy = tr[tr["available"] >= tr["available"].median()].nlargest(10, "pct")
        st.dataframe(busy[["train_no", "train_name", "available", "utilized", "pct"]].rename(columns=RENAME),
                     hide_index=True, width="stretch", column_config=PCT_COL)

# ---------- detail table ----------
section("Detail")
with st.container(key="card_table"):
    tbl = util(x, ["train_no", "train_name", "cls"]).sort_values(["train_no", "cls"])
    tbl["unused"] = tbl["available"] - tbl["utilized"]
    tbl = tbl[["train_no", "train_name", "cls", "available", "utilized", "unused", "pct"]].rename(columns=RENAME)
    h1, h2 = st.columns([4, 1])
    with h1:
        card_head("Train × class detail", f"{len(tbl):,} rows")
    h2.download_button("Download CSV", tbl.to_csv(index=False).encode(), width="stretch",
                       file_name=f"eq_utilization_{start:%Y%m%d}_{end:%Y%m%d}.csv", mime="text/csv")
    st.dataframe(tbl, hide_index=True, width="stretch", height=320, column_config=PCT_COL)

with st.expander("Day-wise data for this selection"):
    dt_tbl = util(d, "date").sort_values("date")
    dt_tbl["Day"] = dt_tbl["date"].dt.day_name()
    dt_tbl["Week"] = "Week " + ((dt_tbl["date"].dt.day - 1) // 7 + 1).astype(str)
    st.dataframe(
        dt_tbl[["date", "Day", "Week", "available", "utilized", "pct"]].rename(
            columns={"date": "Journey Date", "available": "Available", "utilized": "Utilized", "pct": "Utilization %"}),
        hide_index=True, width="stretch",
        column_config={"Journey Date": st.column_config.DateColumn(format="DD-MM-YYYY"), **PCT_COL})

# ---------- train no vs utilization ----------
section("Train-wise")
with st.container(key="card_trains"):
    if sel_train:
        trn = util(x, ["train_no", "train_name", "cls"])
        card_head("Train No. vs utilization", f"{t_lbl} — by class (single train selected)")
        st.plotly_chart(bar_fig(trn, trn["cls"], h=280), width="stretch", config={"displayModeBar": False}, key="plot_trains")
    else:
        trn = util(x, ["train_no", "train_name"])
        h1, f1, f2, f3 = st.columns([1.4, 1.6, 1, 1])
        with h1:
            card_head("Train No. vs utilization", "Hover a bar for the train name")
        order = f1.radio("Show", ["Highest utilization", "Lowest utilization", "Most quota"],
                         horizontal=True, label_visibility="collapsed")
        top_n = f2.select_slider("Trains", [10, 20, 30, 50, 75, 100], value=30)
        min_q = f3.number_input("Min. available quota", min_value=0, value=int(trn["available"].median()), step=50)
        trn = trn[trn["available"] >= min_q]
        trn = {"Highest utilization": lambda t: t.nlargest(top_n, "pct"),
               "Lowest utilization": lambda t: t.nsmallest(top_n, "pct"),
               "Most quota": lambda t: t.nlargest(top_n, "available")}[order](trn)
        if len(trn):
            tf = bar_fig(trn, trn["train_no"], h=300, text_fmt="{:.0f}%", hover_name=trn["train_name"])
            tf.update_xaxes(tickangle=-60, tickfont=dict(size=8))
            tf.update_traces(textfont=dict(size=8))
            st.plotly_chart(tf, width="stretch", config={"displayModeBar": False}, key="plot_trains")
        else:
            st.info("No trains match this filter.")

st.caption("Source: Emergency Quota – HO Quota Report 2025-26 (day-wise). Report is based on train start date; "
           "quotas counted: HO, HORS, EQ, EQRS.")
