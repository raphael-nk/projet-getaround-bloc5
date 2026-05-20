"""
GetAround Analytics Dashboard
==============================
Modern Streamlit dashboard with authentication, delay analysis,
ML pricing predictor, and settings panel.

Local files (dashboard/):
  - users.json

Project files (resolved automatically):
  - data/get_around_delay_analysis.xlsx
  - data/get_around_pricing_project.csv

Pricing predictions via FastAPI (GETAROUND_API_URL, default http://127.0.0.1:8000).
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
# PATHS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DASHBOARD_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
API_BASE_URL = os.environ.get("GETAROUND_API_URL", "http://127.0.0.1:8000").rstrip("/")
THRESHOLD_RANGE = list(range(0, 721, 30))
USERS_PATH = os.path.join(DASHBOARD_DIR, "users.json")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.set_page_config(
    page_title="GetAround Analytics",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MODERN CSS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

:root {
    --accent: #6C5CE7; --accent-l: #A29BFE; --ok: #00B894;
    --warn: #FDCB6E; --bad: #E17055; --info: #74B9FF;
}
.stApp { font-family: 'DM Sans', sans-serif; }
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0c29 0%, #1a1a2e 50%, #16213e 100%);
    border-right: 1px solid rgba(255,255,255,0.06);
}

/* ── KPI cards ── */
.kpi-row { display: flex; gap: 12px; margin-bottom: 16px; }
.kpi {
    flex: 1; text-align: center; padding: 22px 14px;
    background: linear-gradient(145deg, rgba(108,92,231,.10) 0%, rgba(162,155,254,.04) 100%);
    border: 1px solid rgba(108,92,231,.18); border-radius: 16px;
    transition: transform .15s, box-shadow .15s;
}
.kpi:hover { transform: translateY(-2px); box-shadow: 0 6px 24px rgba(108,92,231,.12); }
.kpi .v {
    font: 700 2rem/1.15 'JetBrains Mono', monospace;
    background: linear-gradient(135deg,#6C5CE7,#A29BFE);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.kpi .l { font-size:.72rem; text-transform:uppercase; letter-spacing:1.4px; opacity:.5; font-weight:500; }
.kpi .d { font-size:.82rem; margin-top:4px; font-weight:500; }
.kpi .d.g { color:#00B894; } .kpi .d.r { color:#E17055; }

/* ── Login ── */
.login-box {
    max-width:410px; margin:70px auto; padding:44px 36px;
    background: linear-gradient(145deg, rgba(108,92,231,.08), rgba(22,33,62,.35));
    border:1px solid rgba(108,92,231,.2); border-radius:22px;
}
.login-box h1 { text-align:center; font-size:1.7rem; margin-bottom:4px; }
.login-box p  { text-align:center; opacity:.45; font-size:.88rem; margin-bottom:28px; }

/* ── Prediction ── */
.pred-box {
    background: linear-gradient(145deg, rgba(0,184,148,.13), rgba(0,184,148,.04));
    border:2px solid rgba(0,184,148,.28); border-radius:20px;
    padding:30px; text-align:center; margin:20px 0;
}
.pred-box .price { font:700 3.4rem/1.1 'JetBrains Mono',monospace; color:#00B894; }
.pred-box .tag   { font-size:.8rem; text-transform:uppercase; letter-spacing:2px; opacity:.45; margin-top:6px; }

/* ── Section header ── */
.sh {
    font-size:1.05rem; font-weight:700; letter-spacing:.4px;
    margin:28px 0 12px; padding-bottom:6px;
    border-bottom:2px solid var(--accent); display:inline-block;
}

/* ── Badge ── */
.badge {
    background:linear-gradient(135deg,#6C5CE7,#A29BFE); color:#fff;
    padding:10px 22px; border-radius:10px; font-weight:600;
    display:inline-block; font-size:.92rem;
}

#MainMenu, header, footer { visibility:hidden; }
.stPlotlyChart { border-radius:10px; overflow:hidden; }
</style>
""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COLOR PALETTE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
C = dict(
    pri="#6C5CE7", sec="#A29BFE", ok="#00B894", warn="#FDCB6E",
    bad="#E17055", info="#74B9FF", pink="#FD79A8", teal="#00CEC9",
    pal=["#6C5CE7","#00B894","#E17055","#FDCB6E","#74B9FF","#FD79A8","#00CEC9","#A29BFE"],
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def kpi(label, value, delta=None, good=True):
    d = ""
    if delta:
        cls = "g" if good else "r"
        d = f'<div class="d {cls}">{delta}</div>'
    return f'<div class="kpi"><div class="l">{label}</div><div class="v">{value}</div>{d}</div>'

def kpi_row(cards):
    """Render a row of KPI cards from a list of HTML strings."""
    inner = "".join(cards)
    st.markdown(f'<div class="kpi-row">{inner}</div>', unsafe_allow_html=True)

def dark_layout(fig, title="", h=420):
    fig.update_layout(
        title=dict(text=title, font=dict(size=15, family="DM Sans")),
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=h, font=dict(family="DM Sans", size=12),
        margin=dict(l=40, r=40, t=55, b=40),
        legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0, font=dict(size=11)),
        xaxis=dict(gridcolor="rgba(255,255,255,.05)", zerolinecolor="rgba(255,255,255,.08)"),
        yaxis=dict(gridcolor="rgba(255,255,255,.05)", zerolinecolor="rgba(255,255,255,.08)"),
    )
    return fig

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AUTH
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
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.markdown("<h1>🚗 GetAround</h1>", unsafe_allow_html=True)
    st.markdown("<p>Analytics Dashboard — Sign In</p>", unsafe_allow_html=True)
    user = st.text_input("Username", placeholder="username")
    pw   = st.text_input("Password", type="password", placeholder="password")
    st.checkbox("Remember me", value=True)
    if st.button("Sign In", use_container_width=True, type="primary"):
        if user and pw:
            ok, data = _auth(user, pw)
            if ok:
                st.session_state.update(authenticated=True, username=user, user_data=data)
                st.rerun()
            else:
                st.error("Invalid credentials")
        else:
            st.warning("Enter username and password")
    st.markdown("</div>", unsafe_allow_html=True)
    with st.expander("Demo credentials"):
        st.code("admin / getaround2024\nmanager / manager123\nanalyst / analyst123")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DATA LOADERS
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
    """GET /health — returns JSON or None if API unreachable."""
    try:
        r = requests.get(f"{API_BASE_URL}/health", timeout=3)
        if r.status_code == 200:
            return r.json()
    except requests.RequestException:
        pass
    return None


def predict_via_api(vehicle: dict) -> float | None:
    """POST /predict — returns first prediction or None on failure."""
    try:
        r = requests.post(
            f"{API_BASE_URL}/predict",
            json={"input": [vehicle]},
            timeout=15,
        )
        r.raise_for_status()
        return float(r.json()["prediction"][0])
    except requests.RequestException as exc:
        st.error(f"❌ API request failed: {exc}")
        return None


def build_consecutive(df):
    cons = df[df["previous_ended_rental_id"].notna()].copy()
    prev = df[["rental_id","delay_at_checkout_in_minutes"]].rename(
        columns={"rental_id":"previous_ended_rental_id","delay_at_checkout_in_minutes":"prev_delay"})
    cons = cons.merge(prev, on="previous_ended_rental_id", how="left")
    cons["is_problematic"] = (cons["prev_delay"] > cons["time_delta_with_previous_rental_in_minutes"]) & (cons["prev_delay"] > 0)
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
# PAGE 1 — DELAY ANALYSIS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def page_delay():
    df = load_delay()
    delay = df["delay_at_checkout_in_minutes"].dropna()
    cons = build_consecutive(df)

    # ── KPIs ──
    st.markdown('<div class="sh">📊 Key Performance Indicators</div>', unsafe_allow_html=True)
    late_n = int((delay > 0).sum())
    kpi_row([
        kpi("Total Rentals", f"{len(df):,}"),
        kpi("Completion Rate", f"{(df['state']=='ended').mean()*100:.1f}%", "vs 85% target"),
        kpi("Late Returns", f"{(delay>0).mean()*100:.1f}%", f"{late_n:,} rentals", False),
        kpi("Avg Delay", f"{delay.mean():.0f} min", f"median {delay.median():.0f} min"),
        kpi("Problematic", f"{cons['is_problematic'].sum()}", f"{cons['is_problematic'].mean()*100:.1f}% of consec.", False),
    ])
    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview","⏱️ Late Returns","🎛️ Threshold Simulator","✅ Recommendation"])

    # ════════ OVERVIEW ════════
    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            vals = df["checkin_type"].value_counts()
            fig = px.pie(values=vals.values, names=vals.index, hole=.55,
                         color_discrete_sequence=[C["pri"],C["teal"]])
            fig.update_traces(textinfo="label+percent", textfont_size=13)
            st.plotly_chart(dark_layout(fig,"Checkin Type Distribution"), use_container_width=True)

        with c2:
            vals = df["state"].value_counts()
            fig = px.pie(values=vals.values, names=vals.index, hole=.55,
                         color_discrete_sequence=[C["ok"],C["bad"]])
            fig.update_traces(textinfo="label+percent", textfont_size=13)
            st.plotly_chart(dark_layout(fig,"Rental State Distribution"), use_container_width=True)

        # Cancel rate by checkin
        cross = pd.crosstab(df["checkin_type"], df["state"], normalize="index").reset_index()
        cross_m = cross.melt(id_vars="checkin_type", var_name="state", value_name="rate")
        cross_m["rate"] = (cross_m["rate"]*100).round(1)
        fig = px.bar(cross_m, x="checkin_type", y="rate", color="state", barmode="group",
                     color_discrete_sequence=[C["bad"],C["ok"]], text="rate")
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        st.plotly_chart(dark_layout(fig,"Completion vs Cancellation by Checkin Type"), use_container_width=True)

        # Funnel
        funnel = pd.DataFrame(dict(
            stage=["All Rentals","Consecutive","Previous Late","Problematic"],
            count=[len(df), len(cons), int((cons["prev_delay"]>0).sum()), int(cons["is_problematic"].sum())]
        ))
        fig = go.Figure(go.Funnel(y=funnel["stage"], x=funnel["count"],
                                   textinfo="value+percent initial",
                                   marker_color=[C["pri"],C["sec"],C["warn"],C["bad"]],
                                   connector_line_color="rgba(255,255,255,.08)"))
        st.plotly_chart(dark_layout(fig,"Problem Funnel — All Rentals → Problematic",380), use_container_width=True)

    # ════════ LATE RETURNS ════════
    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            fig = go.Figure()
            fig.add_trace(go.Histogram(x=delay.clip(-300,600), nbinsx=80,
                                       marker_color=C["pri"], opacity=.85, name="Delay"))
            fig.add_vline(x=0, line_dash="dash", line_color=C["bad"], line_width=2,
                          annotation_text="On time", annotation_position="top right")
            fig.add_vline(x=delay.median(), line_dash="dash", line_color=C["ok"], line_width=2,
                          annotation_text=f"Median ({delay.median():.0f}m)", annotation_position="top left")
            fig.update_layout(xaxis_title="Delay (minutes)", yaxis_title="Count")
            st.plotly_chart(dark_layout(fig,"Delay Distribution (clipped ±300/600)"), use_container_width=True)

        with c2:
            bins = [-np.inf, -60, 0, 30, 60, 120, 180, np.inf]
            labels = ["Early >1h","On time","0-30m late","30-60m","1-2h late","2-3h late","3h+ late"]
            cat = pd.cut(delay, bins=bins, labels=labels).value_counts().reset_index()
            cat.columns = ["Category","Count"]
            cat["Pct"] = (cat["Count"]/cat["Count"].sum()*100).round(1)
            fig = px.bar(cat, x="Category", y="Count", color="Category",
                         color_discrete_sequence=[C["ok"],C["teal"],C["warn"],"#F39C12",C["bad"],"#D63031","#6D214F"],
                         text="Pct")
            fig.update_traces(texttemplate="%{text}%", textposition="outside")
            fig.update_layout(showlegend=False)
            st.plotly_chart(dark_layout(fig,"Delay Categories Breakdown"), use_container_width=True)

        # Boxplot
        ended = df[df["state"]=="ended"].dropna(subset=["delay_at_checkout_in_minutes"]).copy()
        ended["d_clip"] = ended["delay_at_checkout_in_minutes"].clip(-200,400)
        fig = px.box(ended, x="checkin_type", y="d_clip", color="checkin_type",
                     color_discrete_sequence=[C["pri"],C["teal"]], points=False)
        fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Delay (min, clipped)")
        st.plotly_chart(dark_layout(fig,"Delay by Checkin Type"), use_container_width=True)

        # Cumulative distribution
        c1, c2 = st.columns(2)
        with c1:
            sorted_d = np.sort(delay.values)
            cumul = np.arange(1, len(sorted_d)+1) / len(sorted_d) * 100
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=sorted_d, y=cumul, mode="lines",
                                     line=dict(color=C["pri"], width=2.5), name="CDF"))
            fig.add_hline(y=50, line_dash="dot", line_color="rgba(255,255,255,.2)")
            fig.add_vline(x=0, line_dash="dash", line_color=C["bad"], line_width=1.5)
            fig.update_layout(xaxis_title="Delay (min)", yaxis_title="Cumulative %",
                              xaxis_range=[-200, 500])
            st.plotly_chart(dark_layout(fig,"Cumulative Distribution of Delays",350), use_container_width=True)

        with c2:
            # Stats table
            st.markdown('<div class="sh">📋 Stats by Checkin Type</div>', unsafe_allow_html=True)
            rows = []
            for ct in ["mobile","connect"]:
                sub = ended[ended["checkin_type"]==ct]["delay_at_checkout_in_minutes"]
                rows.append(dict(
                    Type=ct.title(), Count=f"{len(sub):,}",
                    Mean=f"{sub.mean():.1f}m", Median=f"{sub.median():.0f}m",
                    Late=f"{(sub>0).mean()*100:.1f}%",
                    VeryLate=f"{(sub>60).mean()*100:.1f}%",
                ))
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # ════════ THRESHOLD SIMULATOR ════════
    with tab3:
        st.markdown("### 🎛️ Simulate minimum delay between consecutive rentals")
        c1, c2 = st.columns(2)
        with c1:
            thresh = st.slider("Threshold (minutes)", 0, 720, 120, 30,
                                help="Buffer time between consecutive rentals on the same car")
        with c2:
            scope = st.radio("Scope", ["All vehicles","Connect only","Mobile only"], horizontal=True, index=1)

        cons_f = cons.copy()
        if scope == "Connect only":
            cons_f = cons[cons["checkin_type"]=="connect"]
        elif scope == "Mobile only":
            cons_f = cons[cons["checkin_type"]=="mobile"]

        sim = sim_threshold(cons_f, THRESHOLD_RANGE)
        r = sim[sim["threshold"]==thresh]
        if len(r):
            r = r.iloc[0]
            rev_risk = r["pct_blocked"] * len(cons_f) / len(df) * 100
            kpi_row([
                kpi("Problems Solved", f"{r['pct_solved']}%", f"{r['solved']}/{r['n_problems']} cases"),
                kpi("Rentals Blocked", f"{r['pct_blocked']}%", f"{r['blocked']}/{len(cons_f)} consec.", False),
                kpi("Efficiency", f"{r['efficiency']}x",
                    "> 1 = net positive" if r["efficiency"]>1 else "< 1 net negative", r["efficiency"]>1),
                kpi("Revenue Risk", f"~{rev_risk:.1f}%", "of total rentals", False),
            ])

        st.markdown("")
        c1, c2 = st.columns(2)
        with c1:
            fig = go.Figure()
            s = sim[sim["threshold"]>0]
            fig.add_trace(go.Scatter(x=s["threshold"], y=s["pct_solved"], name="% Solved",
                                     line=dict(color=C["ok"], width=3, dash="dash"),
                                     fill="tozeroy", fillcolor="rgba(0,184,148,.06)"))
            fig.add_trace(go.Scatter(x=s["threshold"], y=s["pct_blocked"], name="% Blocked",
                                     line=dict(color=C["bad"], width=3),
                                     fill="tozeroy", fillcolor="rgba(225,112,85,.06)"))
            fig.add_vline(x=thresh, line_dash="dot", line_color=C["warn"], line_width=2,
                          annotation_text=f"{thresh}min")
            fig.update_layout(xaxis_title="Threshold (min)", yaxis_title="%")
            st.plotly_chart(dark_layout(fig,f"Trade-off — {scope}"), use_container_width=True)

        with c2:
            se = sim[(sim["threshold"]>0)&(sim["threshold"]<=420)]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=se["threshold"], y=se["efficiency"], name="Efficiency",
                                     line=dict(color=C["pri"], width=3), mode="lines+markers",
                                     marker=dict(size=5)))
            fig.add_hline(y=1, line_dash="dot", line_color="rgba(255,255,255,.2)",
                          annotation_text="Neutral", annotation_position="bottom right")
            fig.add_vline(x=thresh, line_dash="dot", line_color=C["warn"], line_width=2)
            fig.update_layout(xaxis_title="Threshold (min)", yaxis_title="Ratio")
            st.plotly_chart(dark_layout(fig,"Efficiency (% solved / % blocked)"), use_container_width=True)

        # Cross-scope comparison
        st.markdown('<div class="sh">📊 Cross-Scope Comparison</div>', unsafe_allow_html=True)
        comp = []
        for sn, ss in [("All", cons),
                        ("Connect", cons[cons["checkin_type"]=="connect"]),
                        ("Mobile", cons[cons["checkin_type"]=="mobile"])]:
            sr = sim_threshold(ss, [thresh]).iloc[0]
            comp.append(dict(Scope=sn, Consecutive=len(ss), Problems=sr["n_problems"],
                             Solved=f"{sr['solved']} ({sr['pct_solved']}%)",
                             Blocked=f"{sr['blocked']} ({sr['pct_blocked']}%)",
                             Efficiency=f"{sr['efficiency']}x"))
        st.dataframe(pd.DataFrame(comp), use_container_width=True, hide_index=True)

        # Time delta distribution
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=cons_f["time_delta_with_previous_rental_in_minutes"],
                                   nbinsx=25, marker_color=C["sec"], opacity=.8))
        fig.add_vline(x=thresh, line_dash="dash", line_color=C["bad"], line_width=3,
                      annotation_text=f"Threshold: {thresh}min")
        fig.update_layout(xaxis_title="Time delta (min)", yaxis_title="Count")
        st.plotly_chart(dark_layout(fig,"Time Gaps Between Consecutive Rentals",340), use_container_width=True)

    # ════════ RECOMMENDATION ════════
    with tab4:
        st.markdown("### ✅ Data-Driven Recommendation")
        st.markdown("")
        st.markdown('<div class="badge">🎯 Connect-only — 120-minute minimum delay</div>', unsafe_allow_html=True)
        st.markdown("")

        kpi_row([
            kpi("Problems Solved","84.1%","58/69 Connect cases"),
            kpi("Rentals Blocked","36.3%","295/813 consecutive", False),
            kpi("Efficiency","2.32x","Net positive impact"),
        ])
        st.markdown("---")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Why Connect-only?")
            st.markdown("""
- **Limited blast radius** — Connect = 20% of rentals, 44% of consecutive
- **No human contact** — Drivers can't call owner on Connect; delays = frustration
- **Diminishing returns** — 1h→2h = +13pp solved; beyond 2h gains taper off
- **A/B testable** — Measure impact before extending to Mobile
""")
            st.markdown("#### Rollout Plan")
            st.dataframe(pd.DataFrame({
                "Phase": ["1","2","3"],
                "Action": ["Deploy 2h buffer on Connect","Measure impact (cancels, CSAT, revenue)","Extend to Mobile @ 60-90min"],
                "Duration": ["4-6 weeks","2-4 weeks","TBD"],
            }), use_container_width=True, hide_index=True)

        with c2:
            sim_a = sim_threshold(cons, THRESHOLD_RANGE)
            sim_c = sim_threshold(cons[cons["checkin_type"]=="connect"], THRESHOLD_RANGE)
            sim_m = sim_threshold(cons[cons["checkin_type"]=="mobile"], THRESHOLD_RANGE)
            fig = go.Figure()
            for sd, nm, cl in [(sim_a,"All",C["info"]),(sim_c,"Connect",C["pri"]),(sim_m,"Mobile",C["warn"])]:
                s = sd[(sd["threshold"]>0)&(sd["threshold"]<=360)]
                fig.add_trace(go.Scatter(x=s["pct_blocked"], y=s["pct_solved"], name=nm,
                                         mode="lines+markers", line=dict(color=cl,width=2), marker=dict(size=4)))
                r120 = s[s["threshold"]==120]
                if len(r120):
                    fig.add_trace(go.Scatter(x=r120["pct_blocked"], y=r120["pct_solved"],
                                             mode="markers", showlegend=False,
                                             marker=dict(size=15, color=cl, line=dict(width=3, color=C["bad"]))))
            fig.update_layout(xaxis_title="% Blocked (cost)", yaxis_title="% Solved (benefit)")
            st.plotly_chart(dark_layout(fig,"Trade-off Landscape (red ring = 120min)"), use_container_width=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE 2 — PRICING PREDICTOR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def page_pricing():
    df = load_pricing()
    health = api_health()

    tab1, tab2, tab3 = st.tabs(["🔮 Price Predictor","📊 Pricing EDA","🏆 Feature Insights"])

    # ════════ PREDICTOR ════════
    with tab1:
        st.markdown("### 🔮 Estimate Optimal Daily Rental Price")
        st.markdown("Configure vehicle characteristics and get an ML-powered price estimate.")
        st.markdown("")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**🚘 Vehicle**")
            model_key = st.selectbox("Brand", sorted(df["model_key"].unique()), index=3)
            car_type = st.selectbox("Car Type", sorted(df["car_type"].unique()), index=3)
            fuel = st.selectbox("Fuel", sorted(df["fuel"].unique()), index=0)
            paint_color = st.selectbox("Paint Color", sorted(df["paint_color"].unique()), index=1)
        with c2:
            st.markdown("**⚙️ Specs**")
            mileage = st.number_input("Mileage (km)", 0, 1_000_000, 120_000, 5000)
            engine_power = st.number_input("Engine Power (hp)", 0, 500, 120, 5)
        with c3:
            st.markdown("**🎛️ Equipment**")
            has_gps = st.toggle("GPS", True)
            has_ac  = st.toggle("Air Conditioning", True)
            auto    = st.toggle("Automatic", False)
            connect = st.toggle("GetAround Connect", True)
            parking = st.toggle("Private Parking", False)
            speed_r = st.toggle("Speed Regulator", True)
            winter  = st.toggle("Winter Tires", True)

        st.markdown("---")

        if health is None or not health.get("model_loaded"):
            st.warning(
                f"⚠️ API unavailable or model not loaded. Start FastAPI: "
                f"`uvicorn api.main:app --reload` — `{API_BASE_URL}/health`"
            )

        if st.button("⚡ Predict Price", use_container_width=True, type="primary"):
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

                st.markdown(
                    f'<div class="pred-box">'
                    f'<div class="tag">Estimated Daily Rental Price</div>'
                    f'<div class="price">{pred:.0f}€</div>'
                    f'<div class="tag">per day</div></div>',
                    unsafe_allow_html=True)

                pctile = (df["rental_price_per_day"] <= pred).mean() * 100
                avg = df["rental_price_per_day"].mean()
                diff = pred - avg
                n_eq = sum([has_gps, has_ac, auto, connect, parking, speed_r, winter])

                kpi_row([
                    kpi("Market Percentile", f"{pctile:.0f}th", "position in fleet"),
                    kpi("vs Market Avg", f"{diff:+.0f}€", f"avg = {avg:.0f}€/day", diff > 0),
                    kpi("Equipment Score", f"{n_eq}/7", "features enabled"),
                ])

                # Context chart
                fig = go.Figure()
                fig.add_trace(go.Histogram(x=df["rental_price_per_day"], nbinsx=50,
                                           marker_color=C["pri"], opacity=.55, name="Fleet"))
                fig.add_vline(x=pred, line_dash="dash", line_color=C["ok"], line_width=3,
                              annotation_text=f"Your car: {pred:.0f}€")
                fig.add_vline(x=avg, line_dash="dot", line_color=C["warn"], line_width=2,
                              annotation_text=f"Fleet avg: {avg:.0f}€")
                fig.update_layout(xaxis_title="Price (€/day)", yaxis_title="Count")
                st.plotly_chart(dark_layout(fig,"Market Position",350), use_container_width=True)

                # Similar vehicles in dataset
                st.markdown('<div class="sh">🔍 Similar Vehicles in Fleet</div>', unsafe_allow_html=True)
                similar = df[
                    (df["car_type"]==car_type) &
                    (df["fuel"]==fuel) &
                    (df["mileage"].between(mileage-30000, mileage+30000)) &
                    (df["engine_power"].between(engine_power-20, engine_power+20))
                ]
                if len(similar) > 0:
                    st.markdown(f"Found **{len(similar)}** similar vehicles (same type, fuel, ±30k km, ±20hp)")
                    st.markdown(f"Their price range: **{similar['rental_price_per_day'].min()}€ — {similar['rental_price_per_day'].max()}€** "
                                f"(avg **{similar['rental_price_per_day'].mean():.0f}€**)")
                    st.dataframe(similar.head(10), use_container_width=True, hide_index=True)
                else:
                    st.info("No similar vehicles found in fleet with these exact specs.")

    # ════════ PRICING EDA ════════
    with tab2:
        st.markdown('<div class="sh">💰 Pricing KPIs</div>', unsafe_allow_html=True)
        target = "rental_price_per_day"
        kpi_row([
            kpi("Fleet Size", f"{len(df):,}"),
            kpi("Avg Price", f"{df[target].mean():.0f}€"),
            kpi("Median", f"{df[target].median():.0f}€"),
            kpi("Range", f"{df[target].min()}–{df[target].max()}€"),
            kpi("Brands", f"{df['model_key'].nunique()}"),
        ])
        st.markdown("---")

        c1, c2 = st.columns(2)
        with c1:
            fig = go.Figure()
            fig.add_trace(go.Histogram(x=df[target], nbinsx=50, marker_color=C["pri"], opacity=.8))
            fig.add_vline(x=df[target].mean(), line_dash="dash", line_color=C["bad"],
                          annotation_text=f"Mean: {df[target].mean():.0f}€")
            fig.add_vline(x=df[target].median(), line_dash="dot", line_color=C["ok"],
                          annotation_text=f"Median: {df[target].median():.0f}€")
            fig.update_layout(xaxis_title="Price (€/day)", yaxis_title="Count")
            st.plotly_chart(dark_layout(fig,"Price Distribution"), use_container_width=True)

        with c2:
            ct_p = df.groupby("car_type")[target].mean().sort_values().reset_index()
            fig = px.bar(ct_p, x=target, y="car_type", orientation="h",
                         color=target, color_continuous_scale=[C["pri"],C["ok"]], text=target)
            fig.update_traces(texttemplate="%{text:.0f}€", textposition="outside")
            fig.update_layout(coloraxis_showscale=False, xaxis_title="Price (€)", yaxis_title="")
            st.plotly_chart(dark_layout(fig,"Average Price by Car Type"), use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            bp = df.groupby("model_key")[target].agg(["mean","count"]).reset_index()
            bp = bp[bp["count"]>=5].sort_values("mean", ascending=False).head(15)
            fig = px.bar(bp, x="model_key", y="mean", color="mean",
                         color_continuous_scale=[C["bad"],C["pri"],C["ok"]], text="mean")
            fig.update_traces(texttemplate="%{text:.0f}€", textposition="outside")
            fig.update_layout(coloraxis_showscale=False, xaxis_title="", yaxis_title="Price (€)", xaxis_tickangle=-45)
            st.plotly_chart(dark_layout(fig,"Top 15 Brands (min 5 vehicles)"), use_container_width=True)

        with c2:
            fig = px.scatter(df, x="engine_power", y=target, color="fuel", opacity=.35,
                             color_discrete_sequence=C["pal"], trendline="ols")
            fig.update_layout(xaxis_title="Engine Power (hp)", yaxis_title="Price (€/day)")
            st.plotly_chart(dark_layout(fig,"Engine Power vs Price"), use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            fig = px.scatter(df, x="mileage", y=target, color="car_type", opacity=.35,
                             color_discrete_sequence=C["pal"], trendline="ols")
            fig.update_layout(xaxis_title="Mileage (km)", yaxis_title="Price (€/day)")
            st.plotly_chart(dark_layout(fig,"Mileage vs Price"), use_container_width=True)

        with c2:
            fuel_c = df["fuel"].value_counts().reset_index()
            fuel_c.columns = ["fuel","count"]
            fig = px.pie(fuel_c, values="count", names="fuel", hole=.5,
                         color_discrete_sequence=C["pal"])
            fig.update_traces(textinfo="label+percent", textfont_size=12)
            st.plotly_chart(dark_layout(fig,"Fuel Type Distribution"), use_container_width=True)

        # Paint color
        cp = df.groupby("paint_color")[target].mean().sort_values().reset_index()
        fig = px.bar(cp, x=target, y="paint_color", orientation="h",
                     color=target, color_continuous_scale=[C["pri"],C["ok"]], text=target)
        fig.update_traces(texttemplate="%{text:.0f}€", textposition="outside")
        fig.update_layout(coloraxis_showscale=False, xaxis_title="Price (€)", yaxis_title="")
        st.plotly_chart(dark_layout(fig,"Average Price by Paint Color",380), use_container_width=True)

    # ════════ FEATURE INSIGHTS ════════
    with tab3:
        st.markdown("### 🏆 Feature Impact on Price")
        bool_cols = ["has_gps","has_air_conditioning","automatic_car",
                     "has_getaround_connect","private_parking_available",
                     "has_speed_regulator","winter_tires"]

        impacts = []
        for col in bool_cols:
            y = df[df[col]==True][target].mean()
            n = df[df[col]==False][target].mean()
            impacts.append(dict(
                feature=col.replace("_"," ").replace("has ","").title(),
                With=round(y,1), Without=round(n,1), diff=round(y-n,1)))
        imp_df = pd.DataFrame(impacts).sort_values("diff", ascending=True)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=imp_df["feature"], x=imp_df["diff"], orientation="h",
            marker_color=[C["ok"] if d>10 else C["info"] if d>5 else C["warn"] for d in imp_df["diff"]],
            text=[f"+{d:.0f}€" for d in imp_df["diff"]], textposition="outside"))
        fig.update_layout(xaxis_title="Price premium (€/day)", yaxis_title="")
        st.plotly_chart(dark_layout(fig,"Price Premium per Feature",400), use_container_width=True)

        # Correlation heatmap
        st.markdown('<div class="sh">🔗 Correlation Matrix</div>', unsafe_allow_html=True)
        df_c = df.copy()
        for c_ in bool_cols:
            df_c[c_] = df_c[c_].astype(int)
        corr_cols = ["mileage","engine_power"] + bool_cols + [target]
        corr = df_c[corr_cols].corr()
        fig = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1, aspect="auto")
        st.plotly_chart(dark_layout(fig,"Feature Correlations",520), use_container_width=True)

        # Equipment count vs price
        df_t = df.copy()
        df_t["n_equip"] = df_t[bool_cols].sum(axis=1)
        ep = df_t.groupby("n_equip")[target].agg(["mean","std","count"]).reset_index()
        fig = go.Figure()
        fig.add_trace(go.Bar(x=ep["n_equip"], y=ep["mean"], marker_color=C["pri"], opacity=.8,
                             error_y=dict(type="data", array=ep["std"], visible=True, color=C["bad"]),
                             text=[f"{m:.0f}€" for m in ep["mean"]], textposition="outside"))
        fig.update_layout(xaxis_title="Number of features (0-7)", yaxis_title="Avg Price (€/day)")
        st.plotly_chart(dark_layout(fig,"Price vs Equipment Count",400), use_container_width=True)

        # Summary table
        st.markdown('<div class="sh">📋 Feature Impact Summary</div>', unsafe_allow_html=True)
        disp = imp_df.rename(columns={"feature":"Feature","With":"With (€)","Without":"Without (€)","diff":"Δ (€)"})
        disp = disp.sort_values("Δ (€)", ascending=False)
        st.dataframe(disp, use_container_width=True, hide_index=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE 3 — SETTINGS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def page_settings():
    tab1, tab2, tab3 = st.tabs(["👤 Account","📁 Data Overview","⚙️ App Config"])

    # ════════ ACCOUNT ════════
    with tab1:
        st.markdown("### 👤 Account Settings")
        u = st.session_state.get("user_data", {})
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"**Name:** {u.get('name','—')}")
        with c2:
            st.markdown(f"**Username:** {st.session_state.get('username','—')}")
        with c3:
            st.markdown(f"**Role:** {u.get('role','—').title()}")

        st.markdown("---")
        st.markdown("#### 🔑 Change Password")
        cur = st.text_input("Current password", type="password", key="s_cur")
        new = st.text_input("New password", type="password", key="s_new")
        cnf = st.text_input("Confirm new password", type="password", key="s_cnf")
        if st.button("Update Password"):
            if not cur or not new:
                st.warning("Fill all fields")
            elif new != cnf:
                st.error("New passwords don't match")
            else:
                users = _load_users()
                uname = st.session_state.get("username","")
                stored = users.get(uname,{}).get("password","")
                if stored == cur or stored == _hash(cur):
                    users[uname]["password"] = new
                    _save_users(users)
                    st.success("✅ Password updated")
                else:
                    st.error("Current password is incorrect")

        st.markdown("---")

        # Admin-only user management
        if u.get("role") == "admin":
            st.markdown("#### 👥 User Management")
            users = _load_users()
            st.dataframe(pd.DataFrame([
                {"Username":k, "Name":v.get("name",""), "Role":v.get("role","")}
                for k,v in users.items()
            ]), use_container_width=True, hide_index=True)

            with st.expander("➕ Add New User"):
                c1,c2,c3,c4 = st.columns(4)
                with c1: nu = st.text_input("Username", key="au")
                with c2: nn = st.text_input("Full Name", key="an")
                with c3: nr = st.selectbox("Role", ["analyst","manager","admin"], key="ar")
                with c4: np_ = st.text_input("Password", type="password", key="ap")
                if st.button("Create User"):
                    if nu and nn and np_:
                        if nu in users:
                            st.error("Username exists")
                        else:
                            users[nu] = dict(password=np_, name=nn, role=nr)
                            _save_users(users)
                            st.success(f"User '{nu}' created")
                            st.rerun()
                    else:
                        st.warning("Fill all fields")

            with st.expander("🗑️ Remove User"):
                opts = [k for k in users if k != st.session_state.get("username")]
                if opts:
                    du = st.selectbox("Select user", opts, key="du")
                    if st.button("Remove", type="secondary"):
                        del users[du]
                        _save_users(users)
                        st.success(f"Removed '{du}'")
                        st.rerun()
                else:
                    st.info("No other users to remove")

    # ════════ DATA OVERVIEW ════════
    with tab2:
        st.markdown("### 📁 Data Overview")
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("#### Delay Dataset")
            try:
                dd = load_delay()
                st.markdown(f"**Shape:** {dd.shape[0]:,} rows × {dd.shape[1]} cols")
                st.markdown(f"**Memory:** {dd.memory_usage(deep=True).sum()/1024:.0f} KB")
                miss = dd.isnull().sum()
                miss = miss[miss>0]
                if len(miss):
                    st.markdown("**Missing:**")
                    for col, cnt in miss.items():
                        st.markdown(f"- `{col}`: {cnt:,} ({cnt/len(dd)*100:.1f}%)")
                else:
                    st.markdown("**Missing:** None ✅")
                st.dataframe(dd.describe().round(1).T, use_container_width=True)
            except Exception as e:
                st.error(str(e))

        with c2:
            st.markdown("#### Pricing Dataset")
            try:
                dp = load_pricing()
                st.markdown(f"**Shape:** {dp.shape[0]:,} rows × {dp.shape[1]} cols")
                st.markdown(f"**Memory:** {dp.memory_usage(deep=True).sum()/1024:.0f} KB")
                st.markdown("**Missing:** None ✅")
                st.dataframe(dp.describe().round(1).T, use_container_width=True)
            except Exception as e:
                st.error(str(e))

        st.markdown("---")
        st.markdown("#### 🤖 Pricing API")
        st.markdown(f"**Base URL:** `{API_BASE_URL}`")
        health = api_health()
        if health:
            st.markdown(f"**Status:** {'✅ OK' if health.get('model_loaded') else '⚠️ Degraded'}")
            st.json(health)
        else:
            st.warning(
                f"API unreachable at `{API_BASE_URL}`. "
                "Start with: `uvicorn api.main:app --reload`"
            )

    # ════════ APP CONFIG ════════
    with tab3:
        st.markdown("### ⚙️ Application Config")

        st.markdown("#### Required Files")
        api_model_path = os.path.join(PROJECT_ROOT, "api", "models", "best_pricing_model_xgb.pkl")
        files = {
            "users.json": USERS_PATH,
            "Delay data (.xlsx)": os.path.join(DATA_DIR, "get_around_delay_analysis.xlsx"),
            "Pricing data (.csv)": os.path.join(DATA_DIR, "get_around_pricing_project.csv"),
            "API model (.pkl)": api_model_path,
        }
        st.markdown(f"**API URL:** `{API_BASE_URL}`")
        for name, path in files.items():
            icon = "✅" if os.path.exists(path) else "❌"
            size = f" ({os.path.getsize(path)/1024:.0f} KB)" if os.path.exists(path) else ""
            st.markdown(f"- {icon} **{name}**{size}")

        st.markdown("---")
        st.markdown("#### System Info")
        c1,c2,c3 = st.columns(3)
        with c1:
            st.markdown(f"**Streamlit:** {st.__version__}")
        with c2:
            st.markdown(f"**Python:** {sys.version.split()[0]}")
        with c3:
            st.markdown(f"**Pandas:** {pd.__version__}")

        st.markdown(f"**Working dir:** `{os.getcwd()}`")
        st.markdown(f"**App dir:** `{DASHBOARD_DIR}`")
        st.markdown(f"**Session:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        st.markdown("---")
        st.markdown("#### Export Data")
        c1, c2 = st.columns(2)
        with c1:
            try:
                dd = load_delay()
                st.download_button("📥 Download Delay Data (CSV)",
                                   dd.to_csv(index=False).encode(),
                                   "delay_analysis.csv", "text/csv")
            except:
                pass
        with c2:
            try:
                dp = load_pricing()
                st.download_button("📥 Download Pricing Data (CSV)",
                                   dp.to_csv(index=False).encode(),
                                   "pricing_data.csv", "text/csv")
            except:
                pass

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIDEBAR + ROUTING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def main_app():
    with st.sidebar:
        st.markdown("# 🚗 GetAround")
        st.markdown("**Analytics Dashboard**")
        st.markdown("---")

        u = st.session_state.get("user_data", {})
        st.markdown(f"👤 **{u.get('name','User')}**")
        st.markdown(f"*{u.get('role','').title()}*")
        st.markdown("")

        page = st.radio("Navigation", [
            "⏱️ Delay Analysis",
            "💰 Pricing Predictor",
            "⚙️ Settings",
        ], label_visibility="collapsed")

        st.markdown("---")
        st.markdown("##### 📌 Quick Stats")
        try:
            dd = load_delay()
            dp = load_pricing()
            st.caption(f"📊 {len(dd):,} rentals • {len(dp):,} vehicles")
            h = api_health()
            api_ok = h is not None and h.get("model_loaded")
            st.caption(f"🤖 API: {'✅' if api_ok else '❌'} ({API_BASE_URL})")
        except:
            st.caption("Data not loaded")

        st.markdown("---")
        if st.button("🚪 Sign Out", use_container_width=True):
            for k in ["authenticated","username","user_data"]:
                st.session_state.pop(k, None)
            st.rerun()

        st.markdown("")
        st.markdown("")
        st.caption("GetAround Analytics v2.0")
        st.caption("Jedha Bootcamp Project")

    # Route
    if "Delay" in page:
        st.markdown("# ⏱️ Delay Analysis")
        st.caption("Analyze late returns and simulate minimum delay thresholds between consecutive rentals.")
        page_delay()
    elif "Pricing" in page:
        st.markdown("# 💰 Pricing Predictor")
        st.caption("Predict optimal daily rental prices using ML and explore pricing insights.")
        page_pricing()
    else:
        st.markdown("# ⚙️ Settings")
        st.caption("Manage account, review data, and configure the application.")
        page_settings()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ENTRY POINT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if st.session_state.get("authenticated"):
    main_app()
else:
    login_page()