"""Shared design tokens, styles and chart helpers for both dashboard screens."""
import calendar
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

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



def inject_css():
    st.markdown(
        """
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
          html, body, [class*="css"], .stApp, button, input, textarea {font-family:'Inter',sans-serif !important;}
          html, body {font-size:13px;}
          .stApp {background:#f4f5f7;}
          header[data-testid="stHeader"] {background:#f4f5f7; border-bottom:1px solid #e7e9ee;}
          .block-container, [data-testid="stMainBlockContainer"] {padding:4.2rem 1.6rem 2rem !important; max-width:1440px;}
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

      /* screen 2 header: teal banner so it reads as a different screen */
      .hdr.alt {background:linear-gradient(120deg,#0f5e57 0%,#13827a 100%); border-radius:12px;
                padding:.9rem 1.1rem; align-items:center;}
      .hdr.alt .eyebrow {color:#bfe6e1;}
      .hdr.alt h1 {color:#ffffff;}
      .hdr.alt .pill {background:rgba(255,255,255,.12); border-color:rgba(255,255,255,.28); color:#e6f4f2;}
      .hdr.alt .pill b {color:#ffffff;}
      .hdr.alt .pill .sep {background:rgba(255,255,255,.3);}
      .alt-scope .kpi .bar > div {background:#13827a;}

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


def base_layout(fig, h, top=8):
    fig.update_layout(height=h, margin=dict(l=4, r=4, t=top, b=4), paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
                      font=dict(family=FONT, size=10, color=TEXT2),
                      hoverlabel=dict(bgcolor="#fff", bordercolor="#e5e7eb", font=dict(family=FONT, size=11, color=TEXT)))
    return fig


def bar_fig(g, labels, h=230, text_fmt="{:.1f}%", hover_name=None, color=ACCENT):
    cd = np.stack([g["available"], g["utilized"]] + ([hover_name] if hover_name is not None else []), axis=-1)
    fig = go.Figure(go.Bar(
        x=list(labels), y=g["pct"], marker=dict(color=color, cornerradius=3),
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
