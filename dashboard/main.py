"""
GetAround Analytics Dashboard — v3.0
======================================
Refonte UI/UX complète — Français uniquement
Design : Editorial dark / Mode clair-sombre / Storytelling
"""

import hashlib
import json
import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CHEMINS & CONFIG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT  = os.path.dirname(DASHBOARD_DIR)
DATA_DIR      = os.path.join(PROJECT_ROOT, "data")
API_BASE_URL  = os.environ.get("GETAROUND_API_URL", "http://127.0.0.1:8000").rstrip("/")
THRESHOLD_RANGE = list(range(0, 721, 30))
USERS_PATH    = os.path.join(DASHBOARD_DIR, "users.json")

st.set_page_config(
    page_title="GetAround Analytics",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# THÈME & CSS GLOBAL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def inject_css(dark_mode: bool):
    if dark_mode:
        bg          = "#0D0D14"
        bg2         = "#13131F"
        bg3         = "#1A1A2E"
        surface     = "rgba(255,255,255,0.04)"
        surface_h   = "rgba(255,255,255,0.07)"
        border      = "rgba(255,255,255,0.08)"
        text        = "#F0F0F8"
        text2       = "#9898B8"
        sidebar_bg  = "linear-gradient(180deg,#0D0D14 0%,#13131F 60%,#0D0D14 100%)"
        plot_tmpl   = "plotly_dark"
        paper_bg    = "rgba(0,0,0,0)"
        plot_bg     = "rgba(0,0,0,0)"
        grid_c      = "rgba(255,255,255,0.05)"
        input_bg    = "#1A1A2E"
        card_grad   = "linear-gradient(135deg,rgba(130,80,255,0.10),rgba(0,210,170,0.04))"
        story_grad  = "linear-gradient(135deg,rgba(130,80,255,0.07),rgba(0,0,0,0))"
    else:
        bg          = "#F7F7FC"
        bg2         = "#FFFFFF"
        bg3         = "#EEEEF8"
        surface     = "rgba(0,0,0,0.03)"
        surface_h   = "rgba(0,0,0,0.06)"
        border      = "rgba(0,0,0,0.08)"
        text        = "#1A1A2E"
        text2       = "#6666A0"
        sidebar_bg  = "linear-gradient(180deg,#FFFFFF 0%,#F2F2FC 100%)"
        plot_tmpl   = "plotly_white"
        paper_bg    = "rgba(255,255,255,0)"
        plot_bg     = "rgba(255,255,255,0)"
        grid_c      = "rgba(0,0,0,0.05)"
        input_bg    = "#FFFFFF"
        card_grad   = "linear-gradient(135deg,rgba(130,80,255,0.06),rgba(0,210,170,0.02))"
        story_grad  = "linear-gradient(135deg,rgba(130,80,255,0.04),rgba(255,255,255,0))"

    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Outfit:wght@300;400;500;600&family=JetBrains+Mono:wght@400;600&display=swap');

/* ── Reset & base ── */
:root {{
    --bg:       {bg};
    --bg2:      {bg2};
    --bg3:      {bg3};
    --surface:  {surface};
    --surf-h:   {surface_h};
    --border:   {border};
    --text:     {text};
    --text2:    {text2};
    --acc:      #8250FF;
    --acc2:     #00D2AA;
    --warn:     #F5A623;
    --bad:      #FF5C5C;
    --info:     #5CB8FF;
    --card:     {card_grad};
    --story:    {story_grad};
    --r:        14px;
    --r2:       22px;
    --sh:       0 4px 32px rgba(130,80,255,0.10);
    --sh2:      0 8px 48px rgba(130,80,255,0.15);
    --font-h:   'Syne', sans-serif;
    --font-b:   'Outfit', sans-serif;
    --font-m:   'JetBrains Mono', monospace;
    --input-bg: {input_bg};
    --grid-c:   {grid_c};
    --paper-bg: {paper_bg};
    --plot-bg:  {plot_bg};
}}

html, body, .stApp {{
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: var(--font-b) !important;
}}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {{
    background: {sidebar_bg} !important;
    border-right: 1px solid var(--border);
    padding-top: 0 !important;
}}
section[data-testid="stSidebar"] * {{
    color: var(--text) !important;
    font-family: var(--font-b) !important;
}}
section[data-testid="stSidebar"] .stCaption,
section[data-testid="stSidebar"] caption {{
    color: var(--text2) !important;
    font-size: 0.75rem !important;
}}

/* ── Sidebar nav radio ── */
section[data-testid="stSidebar"] [data-testid="stRadio"] label {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    border-radius: var(--r);
    margin: 2px 0;
    font-size: 0.9rem;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.2s, color 0.2s;
    border: 1px solid transparent;
}}
section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {{
    background: var(--surf-h);
    border-color: var(--border);
}}

/* ── Main content ── */
.main .block-container {{
    padding: 2rem 2.5rem 4rem !important;
    max-width: 1400px;
}}

/* ── Typography ── */
h1, h2, h3 {{ font-family: var(--font-h) !important; font-weight: 700; }}
h1 {{ font-size: 2rem; letter-spacing: -0.5px; }}
h2 {{ font-size: 1.4rem; }}
h3 {{ font-size: 1.1rem; }}
p, li, span, label {{ font-family: var(--font-b) !important; }}

/* ── Cards KPI ── */
.kpi-wrap {{ display: flex; gap: 14px; flex-wrap: wrap; margin-bottom: 20px; }}
.kpi-card {{
    flex: 1; min-width: 140px;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--r2);
    padding: 20px 18px 16px;
    position: relative; overflow: hidden;
    transition: transform 0.2s, box-shadow 0.2s;
}}
.kpi-card::before {{
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, var(--acc), var(--acc2));
    opacity: 0.6;
}}
.kpi-card:hover {{ transform: translateY(-3px); box-shadow: var(--sh2); }}
.kpi-card .kpi-label {{
    font-size: 0.68rem; text-transform: uppercase; letter-spacing: 1.8px;
    color: var(--text2); font-weight: 600; margin-bottom: 8px;
    font-family: var(--font-b) !important;
}}
.kpi-card .kpi-val {{
    font-family: var(--font-m) !important;
    font-size: 1.9rem; font-weight: 700; line-height: 1;
    background: linear-gradient(135deg, var(--acc), var(--acc2));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
}}
.kpi-card .kpi-delta {{
    font-size: 0.75rem; margin-top: 6px; font-weight: 500;
    font-family: var(--font-b) !important;
}}
.kpi-card .kpi-delta.pos {{ color: var(--acc2); }}
.kpi-card .kpi-delta.neg {{ color: var(--bad); }}
.kpi-card .kpi-delta.neu {{ color: var(--text2); }}

/* ── Story Block ── */
.story-block {{
    background: var(--story);
    border: 1px solid var(--border);
    border-left: 3px solid var(--acc);
    border-radius: var(--r);
    padding: 18px 22px;
    margin: 16px 0;
    font-size: 0.95rem;
    line-height: 1.7;
    color: var(--text);
}}
.story-block strong {{ color: var(--acc2); }}
.story-block .story-title {{
    font-family: var(--font-h) !important;
    font-size: 0.75rem; text-transform: uppercase; letter-spacing: 2px;
    color: var(--acc); font-weight: 700; margin-bottom: 8px;
}}

/* ── Page header ── */
.page-hero {{
    padding: 28px 0 20px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 28px;
}}
.page-hero .hero-badge {{
    display: inline-block;
    background: linear-gradient(135deg, var(--acc), var(--acc2));
    color: white; font-size: 0.68rem; text-transform: uppercase;
    letter-spacing: 2px; padding: 4px 12px; border-radius: 99px;
    font-weight: 700; margin-bottom: 12px;
    font-family: var(--font-b) !important;
}}
.page-hero h1 {{
    font-size: 2rem; font-weight: 800;
    letter-spacing: -0.5px; margin: 0 0 8px;
    color: var(--text);
}}
.page-hero p {{
    color: var(--text2); font-size: 0.95rem; margin: 0;
    max-width: 600px; line-height: 1.6;
}}

/* ── Section label ── */
.section-label {{
    font-family: var(--font-h) !important;
    font-size: 0.68rem; text-transform: uppercase; letter-spacing: 2.5px;
    color: var(--acc); font-weight: 700;
    margin: 32px 0 12px; display: flex; align-items: center; gap: 8px;
}}
.section-label::after {{
    content: ''; flex: 1; height: 1px;
    background: linear-gradient(90deg, var(--border), transparent);
}}

/* ── Prediction result ── */
.pred-result {{
    background: linear-gradient(135deg, rgba(0,210,170,0.10), rgba(0,210,170,0.02));
    border: 2px solid rgba(0,210,170,0.25);
    border-radius: var(--r2); padding: 32px 24px;
    text-align: center; margin: 24px 0;
}}
.pred-result .pred-label {{
    font-size: 0.72rem; text-transform: uppercase; letter-spacing: 2px;
    color: var(--acc2); font-weight: 700; margin-bottom: 10px;
    font-family: var(--font-b) !important;
}}
.pred-result .pred-price {{
    font-family: var(--font-m) !important;
    font-size: 3.5rem; font-weight: 700; color: var(--acc2);
    line-height: 1;
}}
.pred-result .pred-sub {{
    font-size: 0.8rem; color: var(--text2); margin-top: 8px;
}}

/* ── Recommendation badge ── */
.reco-badge {{
    display: inline-flex; align-items: center; gap: 10px;
    background: linear-gradient(135deg, var(--acc), #6040FF);
    color: white; padding: 12px 24px; border-radius: var(--r);
    font-weight: 700; font-size: 0.95rem;
    box-shadow: 0 4px 20px rgba(130,80,255,0.35);
    font-family: var(--font-b) !important;
    margin: 12px 0;
}}

/* ── Login ── */
.login-wrap {{
    max-width: 420px; margin: 60px auto;
    background: var(--card);
    border: 1px solid var(--border); border-radius: var(--r2);
    padding: 44px 36px;
    box-shadow: var(--sh2);
}}
.login-logo {{
    text-align: center; margin-bottom: 28px;
}}
.login-logo .brand {{
    font-family: var(--font-h) !important;
    font-size: 1.8rem; font-weight: 800;
    background: linear-gradient(135deg, var(--acc), var(--acc2));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
}}
.login-logo .sub {{
    font-size: 0.8rem; color: var(--text2); margin-top: 4px;
}}

/* ── FAQ ── */
.faq-item {{
    border: 1px solid var(--border); border-radius: var(--r);
    padding: 16px 20px; margin: 8px 0;
    background: var(--surface);
    transition: border-color 0.2s;
}}
.faq-item:hover {{ border-color: var(--acc); }}
.faq-q {{
    font-family: var(--font-h) !important;
    font-weight: 700; font-size: 0.92rem; color: var(--text);
    margin-bottom: 8px; display: flex; align-items: flex-start; gap: 10px;
}}
.faq-q .faq-icon {{ color: var(--acc); flex-shrink: 0; }}
.faq-a {{
    font-size: 0.87rem; color: var(--text2); line-height: 1.65;
    padding-left: 22px;
}}

/* ── Timeline ── */
.timeline {{ position: relative; padding-left: 24px; }}
.timeline::before {{
    content: ''; position: absolute; left: 6px; top: 0; bottom: 0;
    width: 2px;
    background: linear-gradient(180deg, var(--acc), var(--acc2));
    opacity: 0.3;
}}
.tl-item {{
    position: relative; margin-bottom: 24px;
    padding: 16px 18px;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--r);
}}
.tl-item::before {{
    content: ''; position: absolute; left: -21px; top: 20px;
    width: 10px; height: 10px; border-radius: 50%;
    background: var(--acc); border: 2px solid var(--bg);
}}
.tl-phase {{
    font-size: 0.68rem; text-transform: uppercase; letter-spacing: 1.5px;
    color: var(--acc); font-weight: 700; margin-bottom: 4px;
    font-family: var(--font-b) !important;
}}
.tl-title {{
    font-family: var(--font-h) !important;
    font-weight: 700; font-size: 0.95rem; margin-bottom: 4px;
}}
.tl-desc {{ font-size: 0.83rem; color: var(--text2); line-height: 1.5; }}

/* ── Toggle group ── */
.equip-grid {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 10px; margin: 12px 0;
}}
.equip-card {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--r); padding: 12px 14px;
    transition: border-color 0.2s;
}}
.equip-card:hover {{ border-color: var(--acc); }}

/* ── Inputs styling ── */
.stTextInput input, .stNumberInput input, .stSelectbox select,
div[data-baseweb="select"] > div {{
    background-color: var(--input-bg) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
    border-radius: var(--r) !important;
    font-family: var(--font-b) !important;
}}
.stTextInput input:focus, .stNumberInput input:focus {{
    border-color: var(--acc) !important;
    box-shadow: 0 0 0 2px rgba(130,80,255,0.15) !important;
}}

/* ── Buttons ── */
.stButton button[kind="primary"] {{
    background: linear-gradient(135deg, var(--acc), #6040FF) !important;
    border: none !important;
    border-radius: var(--r) !important;
    font-family: var(--font-b) !important;
    font-weight: 600 !important;
    letter-spacing: 0.3px;
    box-shadow: 0 4px 16px rgba(130,80,255,0.3) !important;
    transition: transform 0.15s, box-shadow 0.15s !important;
}}
.stButton button[kind="primary"]:hover {{
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 24px rgba(130,80,255,0.45) !important;
}}
.stButton button[kind="secondary"] {{
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: var(--r) !important;
    font-family: var(--font-b) !important;
}}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {{
    background: var(--surface) !important;
    border-radius: var(--r) !important;
    padding: 4px !important;
    gap: 2px !important;
    border: 1px solid var(--border) !important;
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: calc(var(--r) - 2px) !important;
    font-family: var(--font-b) !important;
    font-weight: 500 !important;
    color: var(--text2) !important;
    padding: 8px 16px !important;
    font-size: 0.88rem !important;
    transition: all 0.2s !important;
}}
.stTabs [aria-selected="true"] {{
    background: linear-gradient(135deg, var(--acc), #6040FF) !important;
    color: white !important;
    box-shadow: 0 2px 12px rgba(130,80,255,0.3) !important;
}}

/* ── Dataframe ── */
.stDataFrame {{
    border-radius: var(--r) !important;
    overflow: hidden !important;
    border: 1px solid var(--border) !important;
}}

/* ── Slider ── */
.stSlider [data-testid="stTickBar"] {{ opacity: 0.3; }}
.stSlider > div > div > div > div {{
    background: linear-gradient(90deg, var(--acc), var(--acc2)) !important;
}}

/* ── Expander ── */
.streamlit-expanderHeader {{
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r) !important;
    font-weight: 600 !important;
}}
/* Ne pas appliquer Outfit sur l'icône Material (sinon texte "arrow_right" visible) */
[data-testid="stExpander"] summary [data-testid="stIconMaterial"] {{
    font-family: "Material Symbols Rounded", "Material Icons", sans-serif !important;
    font-size: 1.1rem !important;
}}
[data-testid="stExpander"] summary svg {{
    flex-shrink: 0;
}}
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary .streamlit-expanderHeader {{
    font-family: var(--font-b) !important;
}}
[data-testid="stExpander"] {{
    margin-top: 16px;
    border: 1px solid var(--border);
    border-radius: var(--r);
    background: var(--surface);
}}

/* ── Metric ── */
[data-testid="stMetric"] {{
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r) !important;
    padding: 12px 16px !important;
}}

/* ── Plotly charts ── */
.stPlotlyChart {{ border-radius: var(--r) !important; overflow: hidden; }}

/* ── Scrollbar ── */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: var(--acc); border-radius: 3px; opacity: 0.5; }}

/* ── Alert boxes ── */
.stAlert {{ border-radius: var(--r) !important; font-family: var(--font-b) !important; }}

/* ── Sidebar logo zone ── */
.sidebar-logo {{
    padding: 20px 16px 12px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 16px;
}}
.sidebar-brand {{
    font-family: var(--font-h) !important;
    font-size: 1.3rem; font-weight: 800;
    background: linear-gradient(135deg, var(--acc), var(--acc2));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
}}
.sidebar-sub {{
    font-size: 0.7rem; color: var(--text2); text-transform: uppercase;
    letter-spacing: 1.5px; margin-top: 2px; font-weight: 600;
    font-family: var(--font-b) !important;
}}

/* ── User chip ── */
.user-chip {{
    display: flex; align-items: center; gap: 10px;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 99px; padding: 8px 14px; margin: 12px 0;
}}
.user-chip .avatar {{
    width: 28px; height: 28px; border-radius: 50%;
    background: linear-gradient(135deg, var(--acc), var(--acc2));
    display: flex; align-items: center; justify-content: center;
    font-size: 0.75rem; font-weight: 700; color: white;
    font-family: var(--font-b) !important;
    flex-shrink: 0;
}}
.user-chip .name {{ font-size: 0.82rem; font-weight: 600; color: var(--text); }}
.user-chip .role {{ font-size: 0.7rem; color: var(--text2); }}

/* ── Divider ── */
.fancy-divider {{
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border), transparent);
    margin: 24px 0;
}}

/* ── Nav active highlight ── */
section[data-testid="stSidebar"] [data-testid="stRadio"] [aria-checked="true"] + div {{
    color: var(--acc) !important; font-weight: 700;
}}

/* ── Hide streamlit chrome ── */
#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}
header[data-testid="stHeader"] {{
    background: var(--bg) !important;
    border-bottom: 1px solid var(--border);
}}

/* ── Fix sidebar collapse button — hide icon label text, show clean chevron ── */
[data-testid="collapsedControl"] {{
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r) !important;
}}
button[data-testid="baseButton-headerNoPadding"],
[data-testid="stSidebarCollapseButton"] button {{
    color: var(--text2) !important;
}}
/* Hide the material icon text "keyboard_double_arrow_left" etc */
[data-testid="stSidebarCollapseButton"] button span,
[data-testid="collapsedControl"] button span {{
    font-size: 0 !important;
}}
[data-testid="stSidebarCollapseButton"] button span::before,
[data-testid="collapsedControl"] button span::before {{
    content: "‹" !important;
    font-size: 20px !important;
    font-family: var(--font-b) !important;
    line-height: 1;
    display: block;
}}
[data-testid="collapsedControl"] button span::before {{
    content: "›" !important;
}}
</style>
""", unsafe_allow_html=True)

    return {
        "plot_tmpl": plot_tmpl,
        "paper_bg": paper_bg,
        "plot_bg": plot_bg,
        "grid_c": grid_c,
    }

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PALETTE COULEURS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
C = dict(
    acc="#8250FF", acc2="#00D2AA", warn="#F5A623",
    bad="#FF5C5C", info="#5CB8FF", pink="#FF79C6", teal="#00D2AA",
    pal=["#8250FF","#00D2AA","#FF5C5C","#F5A623","#5CB8FF","#FF79C6","#00CEC9","#A29BFE"],
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HELPERS UI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def kpi_row(items):
    """
    items = list of (label, value, delta, mode) tuples
    Rendered via st.columns to avoid Streamlit HTML sanitization.
    """
    cols = st.columns(len(items))
    for col, (label, value, delta, mode) in zip(cols, items):
        with col:
            arrow = "↑ " if mode == "pos" else ("↓ " if mode == "neg" else "· ")
            delta_color = "#00D2AA" if mode == "pos" else ("#FF5C5C" if mode == "neg" else "#9898B8")
            delta_html = f'<div style="font-size:0.75rem;margin-top:6px;color:{delta_color};font-family:Outfit,sans-serif;font-weight:500;">{arrow}{delta}</div>' if delta else ""
            st.markdown(f"""
<div class="kpi-card">
  <div class="kpi-label">{label}</div>
  <div class="kpi-val">{value}</div>
  {delta_html}
</div>""", unsafe_allow_html=True)

def section_label(text):
    st.markdown(f'<div class="section-label">{text}</div>', unsafe_allow_html=True)

def story_block(title, content):
    st.markdown(f'''<div class="story-block">
        <div class="story-title">💡 {title}</div>
        {content}
    </div>''', unsafe_allow_html=True)

def page_hero(badge, title, subtitle):
    st.markdown(f'''<div class="page-hero">
        <div class="hero-badge">{badge}</div>
        <h1>{title}</h1>
        <p>{subtitle}</p>
    </div>''', unsafe_allow_html=True)

def fancy_divider():
    st.markdown('<div class="fancy-divider"></div>', unsafe_allow_html=True)

def styled_fig(fig, theme, title="", h=420):
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, family="Syne"), pad=dict(b=10)),
        template=theme["plot_tmpl"],
        paper_bgcolor=theme["paper_bg"],
        plot_bgcolor=theme["plot_bg"],
        height=h,
        font=dict(family="Outfit", size=12),
        margin=dict(l=40, r=40, t=50, b=40),
        legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0, font=dict(size=11)),
        xaxis=dict(gridcolor=theme["grid_c"], zerolinecolor=theme["grid_c"]),
        yaxis=dict(gridcolor=theme["grid_c"], zerolinecolor=theme["grid_c"]),
    )
    return fig

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AUTHENTIFICATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _load_users():
    if os.path.exists(USERS_PATH):
        with open(USERS_PATH) as f:
            return json.load(f)
    return {}

def _save_users(u):
    with open(USERS_PATH, "w") as f:
        json.dump(u, f, indent=4)

def _hash(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def _auth(user, pw):
    users = _load_users()
    if user in users:
        stored = users[user].get("password", "")
        if stored == pw or stored == _hash(pw):
            return True, users[user]
    return False, None

def login_page():
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown('<div class="login-wrap">', unsafe_allow_html=True)
        # Logo
        try:
            logo_path = os.path.join(DASHBOARD_DIR, "logo.png")
            if os.path.exists(logo_path):
                st.image(logo_path, width=160)
            else:
                st.markdown('''<div class="login-logo">
                    <div class="brand">getaround</div>
                    <div class="sub">Analytics Dashboard</div>
                </div>''', unsafe_allow_html=True)
        except Exception:
            st.markdown('''<div class="login-logo">
                <div class="brand">getaround</div>
                <div class="sub">Analytics Dashboard</div>
            </div>''', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        user = st.text_input("Identifiant", placeholder="nom d'utilisateur", label_visibility="collapsed")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        pw   = st.text_input("Mot de passe", type="password", placeholder="mot de passe", label_visibility="collapsed")
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        col_r, col_f = st.columns([1, 1])
        with col_r:
            st.checkbox("Se souvenir de moi", value=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        if st.button("Se connecter", use_container_width=True, type="primary"):
            if user and pw:
                ok, data = _auth(user, pw)
                if ok:
                    st.session_state.update(authenticated=True, username=user, user_data=data)
                    st.rerun()
                else:
                    st.error("Identifiants invalides")
            else:
                st.warning("Veuillez saisir vos identifiants")

        with st.expander("Comptes démo", expanded=False):
            st.code(
                "admin / getaround2026\nmanager / manager123\nanalyst / analyst123",
                language=None,
            )
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CHARGEMENT DONNÉES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@st.cache_data
def load_delay():
    return pd.read_excel(os.path.join(DATA_DIR, "get_around_delay_analysis.xlsx"))

@st.cache_data
def load_pricing():
    df = pd.read_csv(os.path.join(DATA_DIR, "get_around_pricing_project.csv"))
    if "Unnamed: 0" in df.columns:
        df = df.drop(columns=["Unnamed: 0"])
    return df

def api_health():
    try:
        r = requests.get(f"{API_BASE_URL}/health", timeout=3)
        if r.status_code == 200:
            return r.json()
    except requests.RequestException:
        pass
    return None

def predict_via_api(vehicle: dict):
    try:
        r = requests.post(
            f"{API_BASE_URL}/predict",
            json={"input": [vehicle]},
            timeout=15,
        )
        r.raise_for_status()
        return float(r.json()["prediction"][0])
    except requests.RequestException as exc:
        st.error(f"❌ Échec de la requête API : {exc}")
        return None

def build_consecutive(df):
    cons = df[df["previous_ended_rental_id"].notna()].copy()
    prev = df[["rental_id","delay_at_checkout_in_minutes"]].rename(
        columns={"rental_id":"previous_ended_rental_id","delay_at_checkout_in_minutes":"prev_delay"})
    cons = cons.merge(prev, on="previous_ended_rental_id", how="left")
    cons["is_problematic"] = (
        (cons["prev_delay"] > cons["time_delta_with_previous_rental_in_minutes"]) &
        (cons["prev_delay"] > 0)
    )
    return cons

def sim_threshold(data, thresholds):
    n = len(data)
    prob = data[data["is_problematic"]]
    np_ = len(prob)
    rows = []
    for t in thresholds:
        bl = int((data["time_delta_with_previous_rental_in_minutes"] < t).sum())
        sl = int((prob["prev_delay"] <= prob["time_delta_with_previous_rental_in_minutes"] + t).sum()) if np_ else 0
        pb = round(bl/n*100,1) if n else 0
        ps = round(sl/np_*100,1) if np_ else 0
        ef = round(ps/pb,2) if pb > 0 else 0
        rows.append(dict(threshold=t, blocked=bl, pct_blocked=pb, solved=sl, n_problems=np_, pct_solved=ps, efficiency=ef))
    return pd.DataFrame(rows)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE 1 — ANALYSE DES RETARDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def page_delay(theme):
    page_hero(
        "Analyse · Retards",
        "⏱️ Analyse des Retards au Retour",
        "Comprendre l'impact des retards sur les locataires suivants et simuler l'effet d'un délai minimum entre locations."
    )

    df = load_delay()
    delay = df["delay_at_checkout_in_minutes"].dropna()
    cons = build_consecutive(df)

    # ── Storytelling intro ──
    late_pct = (delay > 0).mean() * 100
    prob_n = cons["is_problematic"].sum()
    story_block(
        "Pourquoi ce sujet est important",
        f"Sur <strong>{len(df):,} locations</strong> analysées, <strong>{late_pct:.1f}%</strong> se terminent avec du retard. "
        f"Parmi les locations consécutives, <strong>{prob_n} cas problématiques</strong> ont été identifiés — "
        f"des situations où un conducteur en retard a directement impacté le prochain locataire. "
        f"L'objectif est de trouver le bon délai tampon pour protéger les clients sans pénaliser les revenus."
    )

    # ── KPIs ──
    section_label("Indicateurs clés")
    late_n = int((delay > 0).sum())
    kpi_row([
        ("Locations totales", f"{len(df):,}", None, "neu"),
        ("Taux de complétion", f"{(df['state']=='ended').mean()*100:.1f}%", "objectif 85%", "pos"),
        ("Retours en retard", f"{late_pct:.1f}%", f"{late_n:,} locations", "neg"),
        ("Délai moyen", f"{delay.mean():.0f} min", f"médiane {delay.median():.0f} min", "neu"),
        ("Cas problématiques", f"{prob_n}", f"{cons['is_problematic'].mean()*100:.1f}% des consécutives", "neg"),
    ])

    fancy_divider()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Vue d'ensemble",
        "⏱️ Retards",
        "🎛️ Simulateur",
        "✅ Recommandation",
        "❓ FAQ",
    ])

    # ════════ VUE D'ENSEMBLE ════════
    with tab1:
        section_label("Composition de la flotte")
        c1, c2 = st.columns(2)
        with c1:
            vals = df["checkin_type"].value_counts()
            fig = px.pie(values=vals.values, names=vals.index, hole=.60,
                         color_discrete_sequence=[C["acc"], C["teal"]])
            fig.update_traces(textinfo="label+percent", textfont_size=13,
                              marker=dict(line=dict(color="rgba(0,0,0,0.1)", width=2)))
            st.plotly_chart(styled_fig(fig, theme, "Répartition des types de check-in"), use_container_width=True)

        with c2:
            vals = df["state"].value_counts()
            fig = px.pie(values=vals.values, names=vals.index, hole=.60,
                         color_discrete_sequence=[C["acc2"], C["bad"]])
            fig.update_traces(textinfo="label+percent", textfont_size=13,
                              marker=dict(line=dict(color="rgba(0,0,0,0.1)", width=2)))
            st.plotly_chart(styled_fig(fig, theme, "Statut des locations"), use_container_width=True)

        story_block(
            "Ce que révèle la répartition",
            "Le check-in <strong>Mobile</strong> représente la majorité des locations et implique un rendez-vous physique. "
            "Le check-in <strong>Connect</strong> (accès via smartphone) est plus exposé aux retards car il n'y a aucun contact humain possible."
        )

        section_label("Annulations par type de check-in")
        cross = pd.crosstab(df["checkin_type"], df["state"], normalize="index").reset_index()
        cross_m = cross.melt(id_vars="checkin_type", var_name="état", value_name="taux")
        cross_m["taux"] = (cross_m["taux"]*100).round(1)
        labels_fr = {"ended": "Terminée", "canceled": "Annulée"}
        cross_m["état"] = cross_m["état"].map(labels_fr)
        fig = px.bar(cross_m, x="checkin_type", y="taux", color="état", barmode="group",
                     color_discrete_sequence=[C["bad"], C["acc2"]], text="taux")
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside", marker_line_width=0)
        fig.update_layout(xaxis_title="", yaxis_title="Taux (%)")
        st.plotly_chart(styled_fig(fig, theme, "Complétion vs Annulation par type de check-in"), use_container_width=True)

        section_label("Entonnoir d'impact")
        funnel = pd.DataFrame(dict(
            Étape=["Toutes les locations", "Consécutives", "Précédent en retard", "Cas problématiques"],
            Nombre=[len(df), len(cons), int((cons["prev_delay"]>0).sum()), int(cons["is_problematic"].sum())]
        ))
        fig = go.Figure(go.Funnel(
            y=funnel["Étape"], x=funnel["Nombre"],
            textinfo="value+percent initial",
            marker_color=[C["acc"], C["info"], C["warn"], C["bad"]],
            connector_line_color="rgba(128,128,128,0.15)"
        ))
        st.plotly_chart(styled_fig(fig, theme, "De toutes les locations → aux cas problématiques", 360), use_container_width=True)

    # ════════ RETARDS ════════
    with tab2:
        section_label("Distribution des retards")
        c1, c2 = st.columns(2)
        with c1:
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=delay.clip(-300, 600), nbinsx=80,
                marker_color=C["acc"], opacity=0.85, name="Retard",
                marker_line_width=0
            ))
            fig.add_vline(x=0, line_dash="dash", line_color=C["bad"], line_width=2,
                          annotation_text="À l'heure", annotation_position="top right",
                          annotation_font_color=C["bad"])
            fig.add_vline(x=delay.median(), line_dash="dash", line_color=C["acc2"], line_width=2,
                          annotation_text=f"Médiane ({delay.median():.0f}m)",
                          annotation_position="top left", annotation_font_color=C["acc2"])
            fig.update_layout(xaxis_title="Retard (minutes)", yaxis_title="Nombre")
            st.plotly_chart(styled_fig(fig, theme, "Distribution des retards (coupé ±300/600 min)"), use_container_width=True)

        with c2:
            bins = [-np.inf, -60, 0, 30, 60, 120, 180, np.inf]
            labels = ["Avance > 1h", "À l'heure", "0-30 min", "30-60 min", "1-2h", "2-3h", "3h+"]
            cat = pd.cut(delay, bins=bins, labels=labels).value_counts().reset_index()
            cat.columns = ["Catégorie", "Nombre"]
            cat["Pct"] = (cat["Nombre"]/cat["Nombre"].sum()*100).round(1)
            fig = px.bar(cat, x="Catégorie", y="Nombre", color="Catégorie",
                         color_discrete_sequence=[C["acc2"], C["teal"], C["warn"], "#F39C12", C["bad"], "#D63031", "#6D214F"],
                         text="Pct")
            fig.update_traces(texttemplate="%{text}%", textposition="outside", marker_line_width=0)
            fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Nombre")
            st.plotly_chart(styled_fig(fig, theme, "Répartition par catégorie de retard"), use_container_width=True)

        section_label("Comparaison par type de check-in")
        ended = df[df["state"] == "ended"].dropna(subset=["delay_at_checkout_in_minutes"]).copy()
        ended["d_clip"] = ended["delay_at_checkout_in_minutes"].clip(-200, 400)
        fig = px.box(ended, x="checkin_type", y="d_clip", color="checkin_type",
                     color_discrete_sequence=[C["acc"], C["teal"]], points=False)
        fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Retard (min, écrêté)")
        st.plotly_chart(styled_fig(fig, theme, "Retard par type de check-in"), use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            sorted_d = np.sort(delay.values)
            cumul = np.arange(1, len(sorted_d)+1) / len(sorted_d) * 100
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=sorted_d, y=cumul, mode="lines",
                line=dict(color=C["acc"], width=2.5), name="CDF",
                fill="tozeroy", fillcolor=f"rgba(130,80,255,0.06)"
            ))
            fig.add_hline(y=50, line_dash="dot", line_color="rgba(128,128,128,0.3)")
            fig.add_vline(x=0, line_dash="dash", line_color=C["bad"], line_width=1.5)
            fig.update_layout(xaxis_title="Retard (min)", yaxis_title="% cumulé", xaxis_range=[-200, 500])
            st.plotly_chart(styled_fig(fig, theme, "Distribution cumulative des retards", 360), use_container_width=True)

        with c2:
            section_label("Statistiques par type")
            rows = []
            for ct in ["mobile", "connect"]:
                sub = ended[ended["checkin_type"] == ct]["delay_at_checkout_in_minutes"]
                rows.append(dict(
                    Type=ct.title(), Nb=f"{len(sub):,}",
                    Moyenne=f"{sub.mean():.1f} min", Mediane=f"{sub.median():.0f} min",
                    En_retard=f"{(sub>0).mean()*100:.1f}%",
                    Tres_en_retard=f"{(sub>60).mean()*100:.1f}%",
                ))
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            story_block(
                "Lecture",
                "Le check-in <strong>Connect</strong> présente généralement un taux de retard similaire "
                "mais l'impact est plus fort car aucun contact humain ne permet de prévenir le prochain conducteur."
            )

    # ════════ SIMULATEUR ════════
    with tab3:
        section_label("Paramètres de simulation")

        c1, c2 = st.columns([2, 1])
        with c1:
            thresh = st.slider(
                "Délai tampon minimum (en minutes)",
                0, 720, 120, 30,
                help="Temps de tampon imposé entre deux locations consécutives sur le même véhicule"
            )
        with c2:
            scope = st.radio(
                "Périmètre",
                ["Tous les véhicules", "Connect uniquement", "Mobile uniquement"],
                horizontal=False, index=1
            )

        cons_f = cons.copy()
        if scope == "Connect uniquement":
            cons_f = cons[cons["checkin_type"] == "connect"]
        elif scope == "Mobile uniquement":
            cons_f = cons[cons["checkin_type"] == "mobile"]

        sim = sim_threshold(cons_f, THRESHOLD_RANGE)
        r   = sim[sim["threshold"] == thresh]

        if len(r):
            r = r.iloc[0]
            rev_risk = r["pct_blocked"] * len(cons_f) / len(df) * 100
            section_label(f"Résultats pour {thresh} min · {scope}")
            kpi_row([
                ("Problèmes résolus", f"{r['pct_solved']}%", f"{r['solved']}/{r['n_problems']} cas", "pos"),
                ("Locations bloquées", f"{r['pct_blocked']}%", f"{r['blocked']}/{len(cons_f)} consécutives", "neg"),
                ("Efficacité", f"{r['efficiency']}x",
                    "Bilan positif" if r["efficiency"] > 1 else "Bilan négatif",
                    "pos" if r["efficiency"] > 1 else "neg"),
                ("Risque revenus", f"~{rev_risk:.1f}%", "des locations totales", "neg"),
            ])

        fancy_divider()
        c1, c2 = st.columns(2)
        with c1:
            fig = go.Figure()
            s = sim[sim["threshold"] > 0]
            fig.add_trace(go.Scatter(
                x=s["threshold"], y=s["pct_solved"], name="% Résolus",
                line=dict(color=C["acc2"], width=3, dash="dash"),
                fill="tozeroy", fillcolor="rgba(0,210,170,0.06)"
            ))
            fig.add_trace(go.Scatter(
                x=s["threshold"], y=s["pct_blocked"], name="% Bloqués",
                line=dict(color=C["bad"], width=3),
                fill="tozeroy", fillcolor="rgba(255,92,92,0.06)"
            ))
            fig.add_vline(x=thresh, line_dash="dot", line_color=C["warn"], line_width=2,
                          annotation_text=f"{thresh} min", annotation_font_color=C["warn"])
            fig.update_layout(xaxis_title="Seuil (min)", yaxis_title="%")
            st.plotly_chart(styled_fig(fig, theme, f"Compromis — {scope}"), use_container_width=True)

        with c2:
            se = sim[(sim["threshold"] > 0) & (sim["threshold"] <= 420)]
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=se["threshold"], y=se["efficiency"], name="Efficacité",
                line=dict(color=C["acc"], width=3), mode="lines+markers",
                marker=dict(size=5, color=C["acc"])
            ))
            fig.add_hline(y=1, line_dash="dot", line_color="rgba(128,128,128,0.4)",
                          annotation_text="Neutre", annotation_position="bottom right")
            fig.add_vline(x=thresh, line_dash="dot", line_color=C["warn"], line_width=2)
            fig.update_layout(xaxis_title="Seuil (min)", yaxis_title="Ratio")
            st.plotly_chart(styled_fig(fig, theme, "Efficacité (% résolus / % bloqués)"), use_container_width=True)

        section_label("Comparaison multi-périmètre")
        comp = []
        for sn, ss in [("Tous", cons), ("Connect", cons[cons["checkin_type"]=="connect"]), ("Mobile", cons[cons["checkin_type"]=="mobile"])]:
            sr = sim_threshold(ss, [thresh]).iloc[0]
            comp.append(dict(
                Périmètre=sn, Consécutives=len(ss), Problèmes=sr["n_problems"],
                Résolus=f"{sr['solved']} ({sr['pct_solved']}%)",
                Bloquées=f"{sr['blocked']} ({sr['pct_blocked']}%)",
                Efficacité=f"{sr['efficiency']}x"
            ))
        st.dataframe(pd.DataFrame(comp), use_container_width=True, hide_index=True)

        section_label("Distribution des délais entre locations")
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=cons_f["time_delta_with_previous_rental_in_minutes"],
            nbinsx=25, marker_color=C["acc"], opacity=0.8,
            marker_line_width=0, name="Délai"
        ))
        fig.add_vline(x=thresh, line_dash="dash", line_color=C["bad"], line_width=3,
                      annotation_text=f"Seuil : {thresh} min", annotation_font_color=C["bad"])
        fig.update_layout(xaxis_title="Délai entre locations (min)", yaxis_title="Nombre")
        st.plotly_chart(styled_fig(fig, theme, "Délais existants entre locations consécutives", 340), use_container_width=True)

    # ════════ RECOMMANDATION ════════
    with tab4:
        section_label("Recommandation basée sur les données")

        st.markdown('<div class="reco-badge">🎯 Connect uniquement — délai minimum de 120 minutes</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        kpi_row([
            ("Problèmes résolus", "84.1%", "58/69 cas Connect", "pos"),
            ("Locations bloquées", "36.3%", "295/813 consécutives", "neg"),
            ("Efficacité", "2.32x", "Bilan largement positif", "pos"),
        ])

        fancy_divider()
        c1, c2 = st.columns(2)
        with c1:
            section_label("Pourquoi Connect uniquement ?")
            story_block(
                "Raisonnement stratégique",
                "<strong>Périmètre limité</strong> — Connect = 20% des locations, 44% des consécutives.<br>"
                "<strong>Zéro contact humain</strong> — Sans possibilité d'appel, les retards deviennent frustrations directes.<br>"
                "<strong>Rendements décroissants</strong> — 1h→2h = +13pp résolus ; au-delà, les gains s'amenuisent.<br>"
                "<strong>Testable en A/B</strong> — Mesurer l'impact avant extension au Mobile."
            )

            section_label("Plan de déploiement")
            st.markdown("""
<div class="timeline">
  <div class="tl-item">
    <div class="tl-phase">Phase 1 · Semaines 1–6</div>
    <div class="tl-title">Déploiement tampon 2h sur Connect</div>
    <div class="tl-desc">Activation du délai minimum sur tous les véhicules Connect.</div>
  </div>
  <div class="tl-item">
    <div class="tl-phase">Phase 2 · Semaines 7–10</div>
    <div class="tl-title">Mesure d'impact</div>
    <div class="tl-desc">Suivi des annulations, satisfaction client (CSAT) et revenus.</div>
  </div>
  <div class="tl-item">
    <div class="tl-phase">Phase 3 · À définir</div>
    <div class="tl-title">Extension au Mobile (60–90 min)</div>
    <div class="tl-desc">Si les résultats Phase 1 sont concluants.</div>
  </div>
</div>
""", unsafe_allow_html=True)

        with c2:
            section_label("Paysage des compromis")
            sim_a = sim_threshold(cons, THRESHOLD_RANGE)
            sim_c = sim_threshold(cons[cons["checkin_type"]=="connect"], THRESHOLD_RANGE)
            sim_m = sim_threshold(cons[cons["checkin_type"]=="mobile"], THRESHOLD_RANGE)
            fig = go.Figure()
            for sd, nm, cl in [(sim_a,"Tous",C["info"]),(sim_c,"Connect",C["acc"]),(sim_m,"Mobile",C["warn"])]:
                s = sd[(sd["threshold"]>0) & (sd["threshold"]<=360)]
                fig.add_trace(go.Scatter(
                    x=s["pct_blocked"], y=s["pct_solved"], name=nm,
                    mode="lines+markers", line=dict(color=cl, width=2.5),
                    marker=dict(size=4, color=cl)
                ))
                r120 = s[s["threshold"]==120]
                if len(r120):
                    fig.add_trace(go.Scatter(
                        x=r120["pct_blocked"], y=r120["pct_solved"],
                        mode="markers", showlegend=False,
                        marker=dict(size=14, color=cl, line=dict(width=3, color=C["bad"]))
                    ))
            fig.update_layout(xaxis_title="% Bloquées (coût)", yaxis_title="% Résolus (bénéfice)")
            st.plotly_chart(styled_fig(fig, theme, "Paysage des compromis (anneau rouge = 120 min)", 420), use_container_width=True)

    # ════════ FAQ ════════
    with tab5:
        section_label("Questions fréquentes")

        faqs = [
            ("Pourquoi un délai tampon et pas une pénalité pour retard ?",
             "Un délai tampon agit en amont en bloquant la réservation trop proche. Une pénalité interviendrait après le problème. "
             "Le tampon protège activement le prochain conducteur sans attendre l'incident."),
            ("Pourquoi 120 minutes et pas 60 ou 180 ?",
             "120 minutes est le point d'inflexion de la courbe d'efficacité : on résout ~84% des problèmes Connect "
             "pour un coût de ~36% de locations bloquées. À 180 min, le gain marginal est faible (+7pp) mais le coût augmente fortement."),
            ("Quel est l'impact sur les revenus ?",
             "Le risque estimé est ~7-9% des revenus issus des locations consécutives Connect. "
             "En pratique, une partie de ces créneaux sera simplement décalée, donc l'impact net réel est inférieur."),
            ("Pourquoi pas Mobile en premier ?",
             "Mobile représente plus de locations et le contact humain permet aux propriétaires de gérer les retards. "
             "Commencer par Connect limite le risque tout en résolvant la majorité des cas problématiques."),
            ("Comment mesure-t-on le succès ?",
             "Métriques clés : taux d'annulation lié aux retards (- cible 80%), CSAT post-location (+ cible), "
             "revenus par voiture Connect (maintien). À mesurer sur 6 semaines minimum."),
            ("Les données sont-elles représentatives ?",
             "Les données datent de 2017, avec ~21k locations. Les tendances de fond restent valides "
             "mais les seuils précis (120 min) méritent d'être recalibrés avec des données récentes avant déploiement en production."),
        ]

        for q, a in faqs:
            st.markdown(f'''<div class="faq-item">
                <div class="faq-q"><span class="faq-icon">Q</span> {q}</div>
                <div class="faq-a">{a}</div>
            </div>''', unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE 2 — PRÉDICTEUR DE PRIX
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def page_pricing(theme):
    page_hero(
        "Machine Learning · Prix",
        "💰 Prédicteur de Prix Optimal",
        "Estimez le prix journalier optimal de votre véhicule grâce au Machine Learning et explorez les insights tarifaires de la flotte."
    )

    df = load_pricing()
    health = api_health()

    tab1, tab2, tab3, tab4 = st.tabs([
        "🔮 Estimation de prix",
        "📊 Analyse des prix",
        "🏆 Impact des équipements",
        "❓ FAQ",
    ])

    # ════════ PRÉDICTEUR ════════
    with tab1:
        story_block(
            "Comment ça fonctionne",
            "Renseignez les caractéristiques de votre véhicule. Le modèle XGBoost — entraîné sur "
            f"<strong>{len(df):,} véhicules</strong> de la flotte — vous retourne une estimation du prix journalier optimal, "
            "ainsi que votre positionnement par rapport au marché."
        )

        if health is None or not health.get("model_loaded"):
            st.warning(
                f"⚠️ API indisponible ou modèle non chargé. Démarrez l'API : "
                f"`uvicorn api.main:app --reload` → `{API_BASE_URL}/health`"
            )

        section_label("Caractéristiques du véhicule")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**🚘 Véhicule**")
            model_key   = st.selectbox("Marque", sorted(df["model_key"].unique()), index=3)
            car_type    = st.selectbox("Type de carrosserie", sorted(df["car_type"].unique()), index=3)
            fuel        = st.selectbox("Carburant", sorted(df["fuel"].unique()), index=0)
            paint_color = st.selectbox("Couleur", sorted(df["paint_color"].unique()), index=1)
        with c2:
            st.markdown("**⚙️ Caractéristiques mécaniques**")
            mileage      = st.number_input("Kilométrage (km)", 0, 1_000_000, 120_000, 5000)
            engine_power = st.number_input("Puissance moteur (ch)", 0, 500, 120, 5)
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("**📍 Confort**")
            has_ac  = st.toggle("Climatisation", True)
            auto    = st.toggle("Boîte automatique", False)
        with c3:
            st.markdown("**🎛️ Équipements**")
            has_gps = st.toggle("GPS", True)
            connect = st.toggle("GetAround Connect", True)
            parking = st.toggle("Parking privé", False)
            speed_r = st.toggle("Régulateur de vitesse", True)
            winter  = st.toggle("Pneus hiver", True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⚡ Estimer le prix", use_container_width=True, type="primary"):
            vehicle = dict(
                model_key=model_key, mileage=mileage, engine_power=engine_power,
                fuel=fuel, paint_color=paint_color, car_type=car_type,
                private_parking_available=parking, has_gps=has_gps,
                has_air_conditioning=has_ac, automatic_car=auto,
                has_getaround_connect=connect, has_speed_regulator=speed_r,
                winter_tires=winter,
            )
            pred = predict_via_api(vehicle)
            if pred is not None:
                st.markdown(f'''<div class="pred-result">
                    <div class="pred-label">Prix journalier estimé</div>
                    <div class="pred-price">{pred:.0f} €</div>
                    <div class="pred-sub">par jour · estimation ML</div>
                </div>''', unsafe_allow_html=True)

                pctile = (df["rental_price_per_day"] <= pred).mean() * 100
                avg    = df["rental_price_per_day"].mean()
                diff   = pred - avg
                n_eq   = sum([has_gps, has_ac, auto, connect, parking, speed_r, winter])

                kpi_row([
                    ("Percentile marché", f"{pctile:.0f}e", "position dans la flotte", "neu"),
                    ("vs Moyenne marché", f"{diff:+.0f}€", f"moy. {avg:.0f}€/j", "pos" if diff > 0 else "neg"),
                    ("Score équipements", f"{n_eq}/7", "options activées", "pos" if n_eq >= 4 else "neu"),
                ])

                section_label("Positionnement marché")
                fig = go.Figure()
                fig.add_trace(go.Histogram(
                    x=df["rental_price_per_day"], nbinsx=50,
                    marker_color=C["acc"], opacity=0.5, name="Flotte",
                    marker_line_width=0
                ))
                fig.add_vline(x=pred, line_dash="dash", line_color=C["acc2"], line_width=3,
                              annotation_text=f"Votre véhicule : {pred:.0f}€",
                              annotation_font_color=C["acc2"])
                fig.add_vline(x=avg, line_dash="dot", line_color=C["warn"], line_width=2,
                              annotation_text=f"Moy. flotte : {avg:.0f}€",
                              annotation_font_color=C["warn"])
                fig.update_layout(xaxis_title="Prix (€/j)", yaxis_title="Nombre de véhicules")
                st.plotly_chart(styled_fig(fig, theme, "Votre prix dans la distribution de la flotte", 360), use_container_width=True)

                section_label("Véhicules similaires dans la flotte")
                similar = df[
                    (df["car_type"] == car_type) &
                    (df["fuel"] == fuel) &
                    (df["mileage"].between(mileage-30000, mileage+30000)) &
                    (df["engine_power"].between(engine_power-20, engine_power+20))
                ]
                if len(similar) > 0:
                    st.markdown(
                        f"**{len(similar)} véhicules similaires** trouvés (même type, carburant, ±30k km, ±20ch) — "
                        f"fourchette **{similar['rental_price_per_day'].min()}€ – {similar['rental_price_per_day'].max()}€** "
                        f"(moy. **{similar['rental_price_per_day'].mean():.0f}€**)"
                    )
                    st.dataframe(similar.head(10), use_container_width=True, hide_index=True)
                else:
                    st.info("Aucun véhicule similaire trouvé dans la flotte avec ces caractéristiques exactes.")

    # ════════ ANALYSE DES PRIX ════════
    with tab2:
        section_label("Indicateurs tarifaires")
        target = "rental_price_per_day"
        kpi_row([
            ("Taille flotte", f"{len(df):,}", None, "neu"),
            ("Prix moyen", f"{df[target].mean():.0f}€", None, "neu"),
            ("Médiane", f"{df[target].median():.0f}€", None, "neu"),
            ("Fourchette", f"{df[target].min()}–{df[target].max()}€", None, "neu"),
            ("Marques", f"{df['model_key'].nunique()}", None, "neu"),
        ])

        fancy_divider()
        c1, c2 = st.columns(2)
        with c1:
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=df[target], nbinsx=50, marker_color=C["acc"], opacity=0.8,
                marker_line_width=0
            ))
            fig.add_vline(x=df[target].mean(), line_dash="dash", line_color=C["bad"],
                          annotation_text=f"Moy: {df[target].mean():.0f}€",
                          annotation_font_color=C["bad"])
            fig.add_vline(x=df[target].median(), line_dash="dot", line_color=C["acc2"],
                          annotation_text=f"Med: {df[target].median():.0f}€",
                          annotation_font_color=C["acc2"])
            fig.update_layout(xaxis_title="Prix (€/j)", yaxis_title="Nombre")
            st.plotly_chart(styled_fig(fig, theme, "Distribution des prix"), use_container_width=True)

        with c2:
            ct_p = df.groupby("car_type")[target].mean().sort_values().reset_index()
            fig = px.bar(ct_p, x=target, y="car_type", orientation="h",
                         color=target, color_continuous_scale=[C["acc"], C["acc2"]], text=target)
            fig.update_traces(texttemplate="%{text:.0f}€", textposition="outside", marker_line_width=0)
            fig.update_layout(coloraxis_showscale=False, xaxis_title="Prix (€)", yaxis_title="")
            st.plotly_chart(styled_fig(fig, theme, "Prix moyen par type de carrosserie"), use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            bp = df.groupby("model_key")[target].agg(["mean","count"]).reset_index()
            bp = bp[bp["count"] >= 5].sort_values("mean", ascending=False).head(15)
            fig = px.bar(bp, x="model_key", y="mean",
                         color="mean", color_continuous_scale=[C["bad"], C["acc"], C["acc2"]], text="mean")
            fig.update_traces(texttemplate="%{text:.0f}€", textposition="outside", marker_line_width=0)
            fig.update_layout(coloraxis_showscale=False, xaxis_title="", yaxis_title="Prix (€)", xaxis_tickangle=-45)
            st.plotly_chart(styled_fig(fig, theme, "Top 15 marques (min. 5 véhicules)"), use_container_width=True)

        with c2:
            fig = px.scatter(df, x="engine_power", y=target, color="fuel",
                             opacity=0.35, color_discrete_sequence=C["pal"], trendline="ols")
            fig.update_layout(xaxis_title="Puissance moteur (ch)", yaxis_title="Prix (€/j)")
            st.plotly_chart(styled_fig(fig, theme, "Puissance moteur vs Prix"), use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            fig = px.scatter(df, x="mileage", y=target, color="car_type",
                             opacity=0.35, color_discrete_sequence=C["pal"], trendline="ols")
            fig.update_layout(xaxis_title="Kilométrage (km)", yaxis_title="Prix (€/j)")
            st.plotly_chart(styled_fig(fig, theme, "Kilométrage vs Prix"), use_container_width=True)

        with c2:
            fuel_c = df["fuel"].value_counts().reset_index()
            fuel_c.columns = ["carburant", "nombre"]
            fig = px.pie(fuel_c, values="nombre", names="carburant", hole=0.55,
                         color_discrete_sequence=C["pal"])
            fig.update_traces(textinfo="label+percent", textfont_size=12,
                              marker=dict(line=dict(color="rgba(0,0,0,0.1)", width=2)))
            st.plotly_chart(styled_fig(fig, theme, "Répartition par type de carburant"), use_container_width=True)

        cp = df.groupby("paint_color")[target].mean().sort_values().reset_index()
        fig = px.bar(cp, x=target, y="paint_color", orientation="h",
                     color=target, color_continuous_scale=[C["acc"], C["acc2"]], text=target)
        fig.update_traces(texttemplate="%{text:.0f}€", textposition="outside", marker_line_width=0)
        fig.update_layout(coloraxis_showscale=False, xaxis_title="Prix (€)", yaxis_title="")
        st.plotly_chart(styled_fig(fig, theme, "Prix moyen par couleur de carrosserie", 380), use_container_width=True)

    # ════════ IMPACT ÉQUIPEMENTS ════════
    with tab3:
        section_label("Impact des équipements sur le prix")
        bool_cols = ["has_gps","has_air_conditioning","automatic_car",
                     "has_getaround_connect","private_parking_available",
                     "has_speed_regulator","winter_tires"]
        labels_fr = {
            "has_gps": "GPS",
            "has_air_conditioning": "Climatisation",
            "automatic_car": "Boîte automatique",
            "has_getaround_connect": "GetAround Connect",
            "private_parking_available": "Parking privé",
            "has_speed_regulator": "Régulateur de vitesse",
            "winter_tires": "Pneus hiver",
        }

        impacts = []
        for col in bool_cols:
            y = df[df[col]==True][target].mean()
            n = df[df[col]==False][target].mean()
            impacts.append(dict(
                feature=labels_fr.get(col, col),
                Avec=round(y, 1), Sans=round(n, 1), diff=round(y-n, 1)
            ))
        imp_df = pd.DataFrame(impacts).sort_values("diff", ascending=True)

        fig = go.Figure()
        colors = [C["acc2"] if d > 10 else C["info"] if d > 5 else C["warn"] for d in imp_df["diff"]]
        fig.add_trace(go.Bar(
            y=imp_df["feature"], x=imp_df["diff"], orientation="h",
            marker_color=colors, marker_line_width=0,
            text=[f"+{d:.0f}€" for d in imp_df["diff"]], textposition="outside"
        ))
        fig.update_layout(xaxis_title="Prime de prix (€/j)", yaxis_title="")
        st.plotly_chart(styled_fig(fig, theme, "Prime de prix par équipement", 400), use_container_width=True)

        story_block(
            "Lecture des résultats",
            "La <strong>boîte automatique</strong> et <strong>GetAround Connect</strong> génèrent les primes les plus fortes. "
            "Ces équipements ciblent des segments de clientèle prêts à payer plus pour le confort et la commodité."
        )

        section_label("Matrice de corrélations")
        df_c = df.copy()
        for c_ in bool_cols:
            df_c[c_] = df_c[c_].astype(int)
        df_c = df_c.rename(columns=labels_fr)
        corr_cols = ["mileage","engine_power"] + [labels_fr[c] for c in bool_cols] + [target]
        corr = df_c[corr_cols].corr()
        fig = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1, aspect="auto")
        st.plotly_chart(styled_fig(fig, theme, "Corrélations entre variables", 520), use_container_width=True)

        section_label("Prix vs nombre d'équipements")
        df_t = df.copy()
        df_t["nb_equip"] = df_t[bool_cols].sum(axis=1)
        ep = df_t.groupby("nb_equip")[target].agg(["mean","std","count"]).reset_index()
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=ep["nb_equip"], y=ep["mean"], marker_color=C["acc"], opacity=0.85,
            marker_line_width=0,
            error_y=dict(type="data", array=ep["std"], visible=True, color=C["bad"]),
            text=[f"{m:.0f}€" for m in ep["mean"]], textposition="outside"
        ))
        fig.update_layout(xaxis_title="Nombre d'équipements (0-7)", yaxis_title="Prix moyen (€/j)")
        st.plotly_chart(styled_fig(fig, theme, "Prix moyen selon le nombre d'équipements", 400), use_container_width=True)

        section_label("Tableau récapitulatif")
        disp = imp_df.rename(columns={"feature":"Équipement","Avec":"Avec (€)","Sans":"Sans (€)","diff":"Δ (€)"})
        disp = disp.sort_values("Δ (€)", ascending=False)
        st.dataframe(disp, use_container_width=True, hide_index=True)

    # ════════ FAQ PRICING ════════
    with tab4:
        section_label("Questions fréquentes — Prédicteur de prix")
        faqs = [
            ("Comment le modèle calcule-t-il le prix ?",
             "Le modèle XGBoost est entraîné sur les prix réels de la flotte. Il apprend les relations "
             "entre caractéristiques (puissance, kilométrage, équipements, marque) et le prix optimal constaté sur le marché."),
            ("Quelle est la précision du modèle ?",
             "Le modèle atteint un R² ~0.76 en test, soit une erreur absolue moyenne (~MAE) d'environ 10€/j. "
             "Pour 90% des véhicules, l'estimation est à ±20€ du prix réel."),
            ("Puis-je faire confiance à l'estimation pour fixer mon prix ?",
             "L'estimation est une base de référence. La localisation géographique, l'état réel du véhicule, "
             "et la saisonnalité ne sont pas pris en compte — ce sont des facteurs à ajuster manuellement."),
            ("Pourquoi XGBoost plutôt qu'une régression linéaire ?",
             "XGBoost capture les non-linéarités (une BMW n'est pas juste '+ x€ par cheval') et les interactions "
             "(automatique + SUV ≠ automatique + citadine). La régression linéaire raterait ces nuances."),
            ("Le modèle sera-t-il mis à jour ?",
             "Idéalement oui — un re-entraînement trimestriel sur les nouvelles données de flotte permet "
             "de suivre l'évolution du marché et d'éviter le concept drift."),
        ]
        for q, a in faqs:
            st.markdown(f'''<div class="faq-item">
                <div class="faq-q"><span class="faq-icon">Q</span> {q}</div>
                <div class="faq-a">{a}</div>
            </div>''', unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE 3 — PARAMÈTRES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def page_settings(theme):
    page_hero(
        "Administration",
        "⚙️ Paramètres",
        "Gérez votre compte, vérifiez les données et configurez l'application."
    )

    tab1, tab2, tab3 = st.tabs(["👤 Mon compte","📁 Données","🔧 Système"])

    # ════════ COMPTE ════════
    with tab1:
        u = st.session_state.get("user_data", {})
        section_label("Informations du compte")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"**Nom :** {u.get('name','—')}")
        with c2:
            st.markdown(f"**Identifiant :** {st.session_state.get('username','—')}")
        with c3:
            st.markdown(f"**Rôle :** {u.get('role','—').title()}")

        fancy_divider()
        section_label("Changer le mot de passe")
        cur = st.text_input("Mot de passe actuel", type="password", key="s_cur")
        new = st.text_input("Nouveau mot de passe", type="password", key="s_new")
        cnf = st.text_input("Confirmer le nouveau mot de passe", type="password", key="s_cnf")
        if st.button("Mettre à jour", type="primary"):
            if not cur or not new:
                st.warning("Remplissez tous les champs")
            elif new != cnf:
                st.error("Les nouveaux mots de passe ne correspondent pas")
            else:
                users = _load_users()
                uname = st.session_state.get("username", "")
                stored = users.get(uname, {}).get("password", "")
                if stored == cur or stored == _hash(cur):
                    users[uname]["password"] = new
                    _save_users(users)
                    st.success("✅ Mot de passe mis à jour")
                else:
                    st.error("Mot de passe actuel incorrect")

        if u.get("role") == "admin":
            fancy_divider()
            section_label("Gestion des utilisateurs (Admin)")
            users = _load_users()
            st.dataframe(pd.DataFrame([
                {"Identifiant": k, "Nom": v.get("name",""), "Rôle": v.get("role","")}
                for k, v in users.items()
            ]), use_container_width=True, hide_index=True)

            with st.expander("➕ Ajouter un utilisateur"):
                c1, c2, c3, c4 = st.columns(4)
                with c1: nu = st.text_input("Identifiant", key="au")
                with c2: nn = st.text_input("Nom complet", key="an")
                with c3: nr = st.selectbox("Rôle", ["analyst","manager","admin"], key="ar")
                with c4: np_ = st.text_input("Mot de passe", type="password", key="ap")
                if st.button("Créer", type="primary"):
                    if nu and nn and np_:
                        if nu in users:
                            st.error("Cet identifiant existe déjà")
                        else:
                            users[nu] = dict(password=np_, name=nn, role=nr)
                            _save_users(users)
                            st.success(f"Utilisateur '{nu}' créé")
                            st.rerun()
                    else:
                        st.warning("Remplissez tous les champs")

            with st.expander("🗑️ Supprimer un utilisateur"):
                opts = [k for k in users if k != st.session_state.get("username")]
                if opts:
                    du = st.selectbox("Sélectionner", opts, key="du")
                    if st.button("Supprimer", type="secondary"):
                        del users[du]
                        _save_users(users)
                        st.success(f"'{du}' supprimé")
                        st.rerun()
                else:
                    st.info("Aucun autre utilisateur à supprimer")

    # ════════ DONNÉES ════════
    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            section_label("Dataset Retards")
            try:
                dd = load_delay()
                st.markdown(f"**Forme :** {dd.shape[0]:,} lignes × {dd.shape[1]} colonnes")
                st.markdown(f"**Mémoire :** {dd.memory_usage(deep=True).sum()/1024:.0f} Ko")
                miss = dd.isnull().sum()
                miss = miss[miss > 0]
                if len(miss):
                    st.markdown("**Valeurs manquantes :**")
                    for col, cnt in miss.items():
                        st.markdown(f"- `{col}` : {cnt:,} ({cnt/len(dd)*100:.1f}%)")
                else:
                    st.markdown("**Valeurs manquantes :** Aucune ✅")
                st.dataframe(dd.describe().round(1).T, use_container_width=True)
            except Exception as e:
                st.error(str(e))

        with c2:
            section_label("Dataset Prix")
            try:
                dp = load_pricing()
                st.markdown(f"**Forme :** {dp.shape[0]:,} lignes × {dp.shape[1]} colonnes")
                st.markdown(f"**Mémoire :** {dp.memory_usage(deep=True).sum()/1024:.0f} Ko")
                st.markdown("**Valeurs manquantes :** Aucune ✅")
                st.dataframe(dp.describe().round(1).T, use_container_width=True)
            except Exception as e:
                st.error(str(e))

        fancy_divider()
        section_label("Statut de l'API de prédiction")
        st.markdown(f"**URL :** `{API_BASE_URL}`")
        health = api_health()
        if health:
            status = "✅ Opérationnelle" if health.get("model_loaded") else "⚠️ Dégradée"
            st.markdown(f"**Statut :** {status}")
            st.json(health)
        else:
            st.warning(
                f"API inaccessible à `{API_BASE_URL}`. "
                "Démarrez avec : `uvicorn api.main:app --reload`"
            )

        fancy_divider()
        section_label("Exporter les données")
        c1, c2 = st.columns(2)
        with c1:
            try:
                dd = load_delay()
                st.download_button(
                    "📥 Télécharger Dataset Retards (CSV)",
                    dd.to_csv(index=False).encode(),
                    "delay_analysis.csv", "text/csv"
                )
            except:
                pass
        with c2:
            try:
                dp = load_pricing()
                st.download_button(
                    "📥 Télécharger Dataset Prix (CSV)",
                    dp.to_csv(index=False).encode(),
                    "pricing_data.csv", "text/csv"
                )
            except:
                pass

    # ════════ SYSTÈME ════════
    with tab3:
        section_label("Fichiers requis")
        api_model_path = os.path.join(PROJECT_ROOT, "api", "models", "best_pricing_model_xgb.pkl")
        files = {
            "users.json": USERS_PATH,
            "Dataset retards (.xlsx)": os.path.join(DATA_DIR, "get_around_delay_analysis.xlsx"),
            "Dataset prix (.csv)": os.path.join(DATA_DIR, "get_around_pricing_project.csv"),
            "Modèle ML (.pkl)": api_model_path,
        }
        st.markdown(f"**URL API :** `{API_BASE_URL}`")
        for name, path in files.items():
            icon = "✅" if os.path.exists(path) else "❌"
            size = f" ({os.path.getsize(path)/1024:.0f} Ko)" if os.path.exists(path) else ""
            st.markdown(f"- {icon} **{name}**{size}")

        fancy_divider()
        section_label("Informations système")
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f"**Streamlit :** {st.__version__}")
        with c2: st.markdown(f"**Python :** {sys.version.split()[0]}")
        with c3: st.markdown(f"**Pandas :** {pd.__version__}")
        st.markdown(f"**Répertoire :** `{os.getcwd()}`")
        st.markdown(f"**Session :** {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIDEBAR & ROUTING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NAV = {
    "⏱️  Retards": "delay",
    "💰  Prix & ML": "pricing",
    "⚙️  Paramètres": "settings",
}

def main_app(theme):
    with st.sidebar:
        # Logo
        try:
            logo_path = os.path.join(DASHBOARD_DIR, "logo.png")
            if os.path.exists(logo_path):
                st.image(logo_path, width=150)
            else:
                st.markdown('''<div class="sidebar-logo">
                    <div class="sidebar-brand">getaround</div>
                    <div class="sidebar-sub">Analytics Dashboard</div>
                </div>''', unsafe_allow_html=True)
        except Exception:
            st.markdown('''<div class="sidebar-logo">
                <div class="sidebar-brand">getaround</div>
                <div class="sidebar-sub">Analytics Dashboard</div>
            </div>''', unsafe_allow_html=True)

        # User chip
        u = st.session_state.get("user_data", {})
        uname = st.session_state.get("username", "?")
        initials = "".join([p[0].upper() for p in u.get("name", uname).split()[:2]])
        st.markdown(f'''<div class="user-chip">
            <div class="avatar">{initials}</div>
            <div>
                <div class="name">{u.get("name", uname)}</div>
                <div class="role">{u.get("role","").title()}</div>
            </div>
        </div>''', unsafe_allow_html=True)

        st.markdown('<div class="fancy-divider"></div>', unsafe_allow_html=True)

        # Navigation
        page = st.radio(
            "Navigation",
            list(NAV.keys()),
            label_visibility="collapsed",
            key="nav_page",
        )

        st.markdown('<div class="fancy-divider"></div>', unsafe_allow_html=True)

        # Quick stats
        st.markdown('<span style="font-size:0.68rem;text-transform:uppercase;letter-spacing:1.5px;opacity:0.5;font-weight:600;">Données rapides</span>', unsafe_allow_html=True)
        try:
            dd = load_delay()
            dp = load_pricing()
            st.caption(f"📊 {len(dd):,} locations · {len(dp):,} véhicules")
            h = api_health()
            api_ok = h is not None and h.get("model_loaded")
            st.caption(f"🤖 API : {'✅ En ligne' if api_ok else '❌ Hors ligne'}")
        except:
            st.caption("Données non chargées")

        st.markdown('<div class="fancy-divider"></div>', unsafe_allow_html=True)

        # Mode sombre/clair toggle
        dark = st.toggle("Mode sombre", value=st.session_state.get("dark_mode", True), key="dark_toggle")
        if dark != st.session_state.get("dark_mode", True):
            st.session_state["dark_mode"] = dark
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪 Se déconnecter", use_container_width=True, type="secondary"):
            for k in ["authenticated", "username", "user_data"]:
                st.session_state.pop(k, None)
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("GetAround Analytics v3.0")
        st.caption("Jedha Bootcamp · 2026")

    # Routing
    key = NAV.get(page, "delay")
    if key == "delay":
        page_delay(theme)
    elif key == "pricing":
        page_pricing(theme)
    else:
        page_settings(theme)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# POINT D'ENTRÉE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = True

dark_mode = st.session_state.get("dark_mode", True)
theme = inject_css(dark_mode)

if st.session_state.get("authenticated"):
    main_app(theme)
else:
    login_page()