"""Builds a 2-page PDF report on Emergency Quota utilization (FY 2025-26).

Run:  python make_report.py   ->  reports/EQ_Utilization_Report_FY2025-26.pdf
"""
import io
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

BASE = Path(__file__).parent
CACHE = BASE / "data" / "cache"
OUT = BASE / "reports" / "EQ_Utilization_Report_FY2025-26.pdf"

# ---------- fonts & colours ----------
FONTS = Path("C:/Windows/Fonts")
pdfmetrics.registerFont(TTFont("UI", str(FONTS / "segoeui.ttf")))
pdfmetrics.registerFont(TTFont("UIB", str(FONTS / "segoeuib.ttf")))
pdfmetrics.registerFont(TTFont("UIS", str(FONTS / "seguisb.ttf")))
pdfmetrics.registerFont(TTFont("UII", str(FONTS / "segoeuii.ttf")))
from reportlab.pdfbase.pdfmetrics import registerFontFamily
registerFontFamily("UI", normal="UI", bold="UIB", italic="UII", boldItalic="UIB")
plt.rcParams.update({"font.family": "Segoe UI", "font.size": 8, "axes.edgecolor": "#d1d5db",
                     "axes.labelcolor": "#4b5563", "xtick.color": "#4b5563", "ytick.color": "#9ca3af"})

INK, INK2, MUTED, LINE, BG = "#111827", "#4b5563", "#9ca3af", "#e5e7eb", "#f4f5f7"
BAR, HI, LO = "#9fb0c7", "#364b68", "#c47a4a"   # base bar, highest (dark slate), lowest (muted copper)
C = colors.HexColor

ST = {
    "h1": ParagraphStyle("h1", fontName="UIB", fontSize=17, leading=20, textColor=C(INK)),
    "sub": ParagraphStyle("sub", fontName="UI", fontSize=8.5, leading=11, textColor=C(INK2)),
    "h2": ParagraphStyle("h2", fontName="UIB", fontSize=10, leading=13, textColor=C(INK), spaceBefore=4, spaceAfter=3),
    "body": ParagraphStyle("body", fontName="UI", fontSize=8, leading=11, textColor=C(INK2)),
    "bul": ParagraphStyle("bul", fontName="UI", fontSize=8, leading=10.6, textColor=C(INK2), leftIndent=8,
                          bulletIndent=0, spaceAfter=1.6),
    "cap": ParagraphStyle("cap", fontName="UIS", fontSize=8.2, leading=10, textColor=C(INK)),
    "note": ParagraphStyle("note", fontName="UI", fontSize=6.8, leading=8.6, textColor=C(MUTED)),
    "cell": ParagraphStyle("cell", fontName="UI", fontSize=7.2, leading=8.6, textColor=C(INK), alignment=TA_LEFT),
}


def P(text, s="body"):
    return Paragraph(text, ST[s])


# ---------- data ----------
daily = pd.read_parquet(CACHE / "daily.parquet")
detail = pd.read_parquet(CACHE / "detail.parquet")
names = daily.groupby("train_no")["train_name"].agg(lambda s: s.value_counts().index[0])


def util(df, by):
    g = df.groupby(by, as_index=False)[["available", "utilized"]].sum()
    g["pct"] = g["utilized"] / g["available"] * 100
    return g


avail, used = int(detail["available"].sum()), int(detail["utilized"].sum())
overall = used / avail * 100
n_trains = detail["train_no"].nunique()

mon = util(detail, ["year", "month_no"])
mon["label"] = pd.to_datetime(dict(year=mon.year, month=mon.month_no, day=1)).dt.strftime("%b %y")
mon = mon.sort_values(["year", "month_no"]).reset_index(drop=True)
daily["week"] = (daily["date"].dt.day - 1) // 7 + 1
daily["dow"] = daily["date"].dt.day_of_week
wk = util(daily, "week")
dw = util(daily, "dow")
cls = util(detail, "cls").sort_values("pct", ascending=False)
qc = util(detail, "quota_code").set_index("quota_code")
days = util(daily, "date")

tr = util(detail, "train_no")
tr["name"] = tr["train_no"].map(names).str.strip()
tr["unused"] = tr["available"] - tr["utilized"]
tr["special"] = tr["train_no"].str.startswith("0")
sp = tr.groupby("special")[["available", "utilized"]].sum()
sp["pct"] = sp["utilized"] / sp["available"] * 100
n_special = int(tr["special"].sum())

band_lo = int((tr["pct"] < 25).sum())
band_zero = int((tr["utilized"] == 0).sum())
band_hi = int((tr["pct"] >= 75).sum())
srt = tr.sort_values("unused", ascending=False)
half_unused = int((srt["unused"].cumsum() / srt["unused"].sum() < 0.5).sum() + 1)

tm = util(detail, ["month_no", "train_no"])
steady = tm[tm["pct"] >= 90].groupby("train_no").size()
steady_ids = steady[steady >= 9].index
steady_tr = tr[tr["train_no"].isin(steady_ids)].sort_values("available", ascending=False)

top = tr[tr["available"] >= 10000].nlargest(10, "pct")
bottom = tr[(tr["available"] >= 20000) & ~tr["special"]].nsmallest(10, "pct")
waste = tr.nlargest(8, "unused")

mh, ml = mon.loc[mon["pct"].idxmax()], mon.loc[mon["pct"].idxmin()]
wh, wl = wk.loc[wk["pct"].idxmax()], wk.loc[wk["pct"].idxmin()]
DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DOWF = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
dh, dl = dw.loc[dw["pct"].idxmax()], dw.loc[dw["pct"].idxmin()]
pk, lw = days.loc[days["pct"].idxmax()], days.loc[days["pct"].idxmin()]
q1 = mon[mon.month_no.isin([4, 5, 6])]
q2 = mon[mon.month_no.isin([7, 8, 9])]
q1p = q1.utilized.sum() / q1.available.sum() * 100
q2p = q2.utilized.sum() / q2.available.sum() * 100


# ---------- charts ----------
def bars(ax, labels, values, highlight=True, fmt="{:.1f}%", ref=None, rot=0):
    vals = list(values)
    cols = [BAR] * len(vals)
    if highlight and len(vals) > 1:
        cols[vals.index(max(vals))] = HI
        cols[vals.index(min(vals))] = LO
    ax.bar(range(len(vals)), vals, color=cols, width=0.62, zorder=2)
    for i, v in enumerate(vals):
        ax.text(i, v + max(vals) * 0.02, fmt.format(v), ha="center", va="bottom", fontsize=6.6,
                color=INK if cols[i] != BAR else INK2, fontweight="bold" if cols[i] != BAR else "normal")
    ax.set_xticks(range(len(vals)), labels, rotation=rot, fontsize=7)
    ax.set_ylim(0, max(vals) * 1.18)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    ax.tick_params(axis="y", labelsize=6.5, length=0)
    ax.tick_params(axis="x", length=0)
    ax.grid(axis="y", color="#eef0f3", lw=0.6, zorder=0)
    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    if ref is not None:
        ax.axhline(ref, color=MUTED, lw=0.7, ls=(0, (3, 2)), zorder=1)


def fig_img(fig, width_mm):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=220, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    buf.seek(0)
    w, h = fig.get_size_inches()
    return Image(buf, width=width_mm * mm, height=width_mm * mm * h / w)


def chart(w_in, h_in, draw, width_mm):
    fig, ax = plt.subplots(figsize=(w_in, h_in))
    draw(ax)
    return fig_img(fig, width_mm)


CONTENT_W = 178  # mm (frame width minus padding)

month_chart = chart(7.4, 2.15, lambda ax: bars(ax, mon["label"], mon["pct"], ref=overall), CONTENT_W)
week_chart = chart(3.5, 1.85, lambda ax: bars(ax, [f"Wk {w}" for w in wk["week"]], wk["pct"], ref=overall),
                   CONTENT_W / 2 - 3)
dow_chart = chart(3.5, 1.85, lambda ax: bars(ax, [DOW[i] for i in dw["dow"]], dw["pct"], ref=overall),
                  CONTENT_W / 2 - 3)
cls_chart = chart(3.5, 1.85, lambda ax: bars(ax, cls["cls"], cls["pct"], ref=overall, fmt="{:.0f}%"), CONTENT_W / 2 - 3)


def band_draw(ax):
    edges = [-0.01, 0, 25, 50, 75, 1000]
    lab = ["0%", "0–25%", "25–50%", "50–75%", "75%+"]
    b = pd.cut(tr["pct"], edges, labels=lab)
    cnt = tr.groupby(b, observed=False).size()
    ax.barh(range(len(lab)), cnt.values, color=[LO, "#d8a588", BAR, "#6c84a3", HI], height=0.6, zorder=2)
    for i, v in enumerate(cnt.values):
        ax.text(v + cnt.max() * 0.015, i, f"{v:,} ({v / len(tr) * 100:.0f}%)", va="center", fontsize=6.6, color=INK2)
    ax.set_yticks(range(len(lab)), lab, fontsize=7)
    ax.invert_yaxis()
    ax.set_xlim(0, cnt.max() * 1.3)
    ax.set_xticks([])
    for s in ["top", "right", "bottom"]:
        ax.spines[s].set_visible(False)
    ax.tick_params(length=0)


band_chart = chart(3.5, 1.85, band_draw, CONTENT_W / 2 - 3)


# ---------- building blocks ----------
def kpi_row():
    data = [[P(f"<font size=6.8 color='{MUTED}'>{l}</font><br/><font name='UIB' size=13 color='{INK}'>{v}</font>"
               f"<br/><font size=6.5 color='{INK2}'>{s}</font>", "body")
             for l, v, s in [
                 ("AVAILABLE QUOTA", f"{avail / 1e6:.2f} M", "berths, full year"),
                 ("UTILIZED", f"{used / 1e6:.2f} M", "berths booked"),
                 ("UTILIZATION", f"{overall:.1f}%", "of quota used"),
                 ("UNUSED", f"{(avail - used) / 1e6:.2f} M", f"{100 - overall:.1f}% released"),
                 ("TRAINS", f"{n_trains:,}", f"{n_special:,} specials incl."),
             ]]]
    t = Table(data, colWidths=[CONTENT_W / 5 * mm] * 5)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C(BG)),
        ("LINEAFTER", (0, 0), (-2, -1), 3, colors.white),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def two_up(left, right, cap_l, cap_r):
    t = Table([[P(cap_l, "cap"), P(cap_r, "cap")], [left, right]],
              colWidths=[CONTENT_W / 2 * mm, CONTENT_W / 2 * mm])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 1),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
    return t


def train_table(df, cols, widths, head):
    rows = [[P(f"<font name='UIB'>{h}</font>", "cell") for h in head]]
    for _, r in df.iterrows():
        rows.append([P(str(c(r)), "cell") for c in cols])
    t = Table(rows, colWidths=[w * mm for w in widths], repeatRows=1)
    t.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, C(INK2)),
        ("LINEBELOW", (0, 1), (-1, -1), 0.3, C(LINE)),
        ("TOPPADDING", (0, 0), (-1, -1), 1.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.8),
        ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def heat_table():
    main = ["2A", "3A", "SL", "3E", "1A", "CC", "2S"]
    cm = util(detail[detail["cls"].isin(main)], ["cls", "year", "month_no"])
    cm["label"] = pd.to_datetime(dict(year=cm.year, month=cm.month_no, day=1)).dt.strftime("%b")
    order = mon["label"].str[:3].tolist()
    pv = cm.pivot(index="cls", columns="label", values="pct").reindex(index=main, columns=order)
    ramp = ["#f3f5f8", "#dfe5ed", "#c6d1de", "#a7b7cb", "#8197b3", "#5f7898", "#455c7c"]
    rows = [[P("<b>Class</b>", "cell")] + [P(f"<b>{m}</b>", "cell") for m in order]]
    style = [("FONTNAME", (0, 0), (-1, -1), "UI"), ("FONTSIZE", (0, 0), (-1, -1), 7),
             ("ALIGN", (1, 1), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
             ("LINEBELOW", (0, 0), (-1, 0), 0.8, C(INK2)),
             ("TOPPADDING", (0, 0), (-1, -1), 1.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
             ("LINEAFTER", (1, 1), (-2, -1), 1.2, colors.white), ("LINEBELOW", (0, 1), (-1, -1), 1.2, colors.white)]
    for i, c in enumerate(main, start=1):
        rows.append([c] + [f"{v:.0f}%" for v in pv.loc[c]])
        for j, v in enumerate(pv.loc[c], start=1):
            k = min(int(v / 52 * (len(ramp) - 1)), len(ramp) - 1)
            style.append(("BACKGROUND", (j, i), (j, i), C(ramp[k])))
            style.append(("TEXTCOLOR", (j, i), (j, i), colors.white if k >= 5 else C(INK)))
    w = (CONTENT_W - 16) / 12
    t = Table(rows, colWidths=[16 * mm] + [w * mm] * 12)
    t.setStyle(TableStyle(style))
    return t


def bullets(items):
    return [Paragraph(i, ST["bul"], bulletText="•") for i in items]


# ---------- page 1 ----------
story = [
    P("Emergency Quota Utilization Report", "h1"),
    P(f"HO / EQ quota · FY 2025-26 · Journey dates 01 Apr 2025 – 31 Mar 2026 · "
      f"{n_trains:,} trains · {len(daily):,} train-days", "sub"),
    Spacer(1, 6), kpi_row(), Spacer(1, 6),
    P("Summary", "h2"),
    *bullets([
        f"<b>Only {overall:.1f}% of emergency quota was used.</b> Of {avail / 1e6:.1f} M berths set aside, "
        f"{(avail - used) / 1e6:.1f} M (almost two in three) went back to the general pool unused.",
        f"<b>Highest month: {mh['label'].replace(' ', ' 20')} at {mh['pct']:.1f}%</b>; lowest: "
        f"<b>{ml['label'].replace(' ', ' 20')} at {ml['pct']:.1f}%</b>. Use falls from {q1p:.1f}% in Apr–Jun to "
        f"{q2p:.1f}% in Jul–Sep, then recovers through Nov–Dec.",
        f"<b>Week of month makes little difference:</b> Week {int(wh['week'])} is highest ({wh['pct']:.1f}%) and "
        f"Week {int(wl['week'])} lowest ({wl['pct']:.1f}%), a gap of only {wh['pct'] - wl['pct']:.1f} points. "
        f"<b>Day of week matters more:</b> {DOWF[int(dh['dow'])]} {dh['pct']:.1f}% vs "
        f"{DOWF[int(dl['dow'])]} {dl['pct']:.1f}%.",
        f"<b>Most trains are over-allotted:</b> {band_lo:,} trains ({band_lo / n_trains * 100:.0f}%) used less than "
        f"25% of their quota and {band_zero:,} used none. Only {band_hi:,} trains used 75% or more.",
        f"<b>Sleeper and AC berth classes drive use</b> (2A {cls.set_index('cls').loc['2A', 'pct']:.1f}%, "
        f"3A {cls.set_index('cls').loc['3A', 'pct']:.1f}%, SL {cls.set_index('cls').loc['SL', 'pct']:.1f}%); "
        f"seating classes stay low (CC {cls.set_index('cls').loc['CC', 'pct']:.1f}%, "
        f"2S {cls.set_index('cls').loc['2S', 'pct']:.1f}%).",
    ]),
    Spacer(1, 4),
    P("Month-wise utilization", "cap"),
    P(f"<font color='{HI}'>■</font> highest month &nbsp; <font color='{LO}'>■</font> lowest month &nbsp; "
      f"dashed line = full-year average ({overall:.1f}%) on all charts", "note"),
    month_chart,
    Spacer(1, 4),
    two_up(week_chart, dow_chart, "Week-of-month utilization",
           "Day-of-week utilization"),
    P("Week 1 = days 1–7, Week 2 = 8–14, Week 3 = 15–21, Week 4 = 22–28, Week 5 = 29–31 (shorter, so fewer "
      "train-days). Day-wise figures are by train start date.", "note"),
    Spacer(1, 4),
    two_up(cls_chart, band_chart, "Class-wise utilization", "Trains by share of their quota used"),
    PageBreak(),
]

# ---------- page 2 ----------
pct_f = lambda r: f"{r['pct']:.1f}%"
num = lambda k: (lambda r: f"{int(r[k]):,}")
half = CONTENT_W / 2 - 2
story += [
    P("Train-wise view", "h1"), Spacer(1, 2),
    P("Trains are ranked over the full year. To avoid small quotas distorting the ranking, the most-utilized "
      "list only includes trains with at least 10,000 quota berths in the year, and the least-utilized list only "
      "regular (non-special) trains with at least 20,000.", "sub"),
    Spacer(1, 6),
]
tt = Table([[P("Most utilized trains", "cap"), P("Least utilized trains (large quota)", "cap")],
            [train_table(top, [lambda r: r["train_no"], lambda r: r["name"], num("available"), pct_f],
                         [13, 38, 17, half - 13 - 38 - 17], ["No.", "Train", "Quota", "Used"]),
             train_table(bottom, [lambda r: r["train_no"], lambda r: r["name"], num("available"), pct_f],
                         [13, 38, 17, half - 13 - 38 - 17], ["No.", "Train", "Quota", "Used"])]],
           colWidths=[CONTENT_W / 2 * mm] * 2)
tt.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, 0), 3)]))
story += [tt, Spacer(1, 8)]

story += [
    P("Where the unused quota sits: trains with the most berths released unused", "cap"), Spacer(1, 3),
    train_table(waste, [lambda r: r["train_no"], lambda r: r["name"], num("available"), num("utilized"),
                        num("unused"), pct_f],
                [18, 60, 26, 26, 26, CONTENT_W - 18 - 60 - 78],
                ["No.", "Train", "Quota", "Used", "Unused", "Used %"]),
    P(f"These are busy long-distance trains with large quotas, not low-demand services; even moderate use leaves "
      f"many berths idle. Just {half_unused:,} trains ({half_unused / n_trains * 100:.0f}% of all trains) account "
      f"for half of all unused berths.", "note"),
    Spacer(1, 6),
    P("Class × month utilization (main classes)", "cap"), Spacer(1, 3),
    heat_table(),
    P("Darker cells = higher use. Every class dips in Jul–Sep; AC classes (2A, 3A) peak in Apr–May and December.",
      "note"),
    Spacer(1, 2),
    P("Other perspectives", "h2"),
    *bullets([
        f"<b>Special trains:</b> {n_special:,} special trains (numbers starting with 0) used only "
        f"{sp.loc[True, 'pct']:.1f}% of their quota, against {sp.loc[False, 'pct']:.1f}% for regular trains. "
        f"Many specials used none at all.",
        f"<b>Quota codes:</b> HO quota used {qc.loc['HO', 'pct']:.1f}%, while HORS ({qc.loc['HORS', 'pct']:.1f}%) "
        f"and EQ ({qc.loc['EQ', 'pct']:.1f}%) were barely used.",
        f"<b>Peak and low days:</b> the busiest day was {pk['date']:%d %b %Y} ({pk['pct']:.1f}%, Christmas Eve"
        f"); the quietest was {lw['date']:%d %b %Y} ({lw['pct']:.1f}%, Diwali day). Mid-September weekdays were "
        f"consistently near 20%.",
        f"<b>Consistently full trains:</b> {len(steady_tr)} trains used 90% or more of their quota in at least 9 "
        f"of 12 months: " + ", ".join(f"{r.name} ({r.train_no})" for r in steady_tr.itertuples()) + ".",
        "<b>Premium and seating classes stay low all year:</b> 1A ranges from 19% to 32% by month, CC and EC stay at or below about 21%, and FC/VS "
        "classes were near 0% from July to September.",
    ]),
    P("Recommendations", "h2"),
    *bullets([
        f"<b>Right-size quotas on low-use trains.</b> Start with the {half_unused:,} trains that hold half of all "
        f"unused berths, and the {band_lo:,} trains below 25%. Releasing berths earlier would make them available "
        f"to waitlisted passengers.",
        "<b>Make quotas seasonal.</b> Allot less in July–September, when use falls to about 25–29%, and keep "
        "current levels for April–June and December.",
        f"<b>Shift by day of week, not by week of month.</b> Weeks barely differ, but Friday–Sunday run 4–8 points "
        f"above Monday–Thursday. Weight allotments toward weekend departures.",
        "<b>Protect or raise quota on the consistently full trains</b> listed above, where emergency requests "
        "are likely being turned away.",
        "<b>Keep special-train, seating-class (CC, 2S) and HORS/EQ quotas minimal</b> unless there is a "
        "specific event-driven need.",
    ]),
    Spacer(1, 4),
    P("Source: Emergency Quota – HO Quota Report 2025-26 (day-wise and train × class detail sheets). Quotas "
      "counted: HO, HORS, EQ, EQRS. Utilization = utilized berths ÷ available quota berths. Report is based on "
      "train start date.", "note"),
]


def on_page(c, doc):
    c.saveState()
    c.setFillColor(C(HI))
    c.rect(0, A4[1] - 4 * mm, A4[0], 4 * mm, stroke=0, fill=1)
    c.setFont("UI", 7)
    c.setFillColor(C(MUTED))
    c.drawString(14 * mm, 8 * mm, "Emergency Quota Utilization · FY 2025-26")
    c.drawRightString(A4[0] - 14 * mm, 8 * mm, f"Page {doc.page} of 2")
    c.restoreState()


OUT.parent.mkdir(exist_ok=True)
doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=14 * mm, rightMargin=14 * mm,
                        topMargin=11 * mm, bottomMargin=13 * mm, title="Emergency Quota Utilization Report FY 2025-26")
doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
print(OUT)
