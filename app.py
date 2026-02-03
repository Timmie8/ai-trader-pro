import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import os

# --- PERSISTENTIE ---
def save_list(watchlist):
    with open("swing_watchlist.txt", "w") as f:
        f.write(",".join(watchlist))

def load_list():
    if os.path.exists("swing_watchlist.txt"):
        with open("swing_watchlist.txt", "r") as f:
            data = f.read().strip()
            return [t.strip().upper() for t in data.split(",") if t.strip()]
    return ["AAPL", "NVDA", "TSLA", "AMD"]

# 1. Dashboard Layout
st.set_page_config(page_title="AI Swing Trader 2026", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0b0e11; color: #e9eaeb; }
    .metric-card { background: #161a1e; border: 1px solid #2b2f36; padding: 20px; border-radius: 10px; }
    .status-bold { font-size: 1.5em; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 2. De Swing-AI Engine
def analyze_swing(ticker):
    try:
        # Data ophalen (we gebruiken 1h en 1d voor 1-5 dagen swing)
        data = yf.Ticker(ticker).history(period="60d", interval="1d")
        if data.empty: return None

        curr_p = data['Close'].iloc[-1]
        
        # --- TECHNISCHE INDICATORS ---
        ema9 = data['Close'].ewm(span=9).mean().iloc[-1]
        ema21 = data['Close'].ewm(span=21).mean().iloc[-1]
        vol_avg = data['Volume'].tail(10).mean()
        rsi = 50 # Vereenvoudigde RSI proxy voor dit script
        
        # --- AI MODEL 1: LINEAIRE REGRESSIE (3-DAGS TARGET) ---
        y_reg = data['Close'].tail(20).values.reshape(-1, 1)
        X_reg = np.array(range(len(y_reg))).reshape(-1, 1)
        model = LinearRegression().fit(X_reg, y_reg)
        pred_3d = float(model.predict(np.array([[len(y_reg) + 3]]))[0][0])
        ai_trend_score = ((pred_3d / curr_p) - 1) * 100

        # --- AI MODEL 2: MOMENTUM ENSEMBLE ---
        mom_short = data['Close'].pct_change(3).iloc[-1]
        mom_long = data['Close'].pct_change(10).iloc[-1]
        ai_mom_status = "BULLISH" if mom_short > mom_long else "BEARISH"

        # --- SWING SCORE BEREKENING (0-100) ---
        score = 0
        if curr_p > ema9: score += 20
        if ema9 > ema21: score += 20
        if data['Volume'].iloc[-1] > vol_avg: score += 20
        if ai_trend_score > 1.5: score += 20
        if ai_mom_status == "BULLISH": score += 20

        # Risk Management (1-5 dagen)
        atr = data['High'].tail(14).max() - data['Low'].tail(14).min()
        stop_loss = curr_p - (atr * 1.5)
        target_1 = curr_p + (atr * 2.5) # 1:1.5 tot 1:3 ratio

        # Kleur & Status
        if score >= 80: stat, col = "STRONG BUY", "#00ff88"
        elif score >= 60: stat, col = "MILD BUY", "#7fff00"
        elif score <= 20: stat, col = "STRONG SELL", "#ff4b4b"
        else: stat, col = "NEUTRAL", "#888888"

        return {
            "T": ticker, "P": curr_p, "S": score, "STAT": stat, "COL": col,
            "AI_T": ai_trend_score, "AI_M": ai_mom_status, "SL": stop_loss, "T1": target_1
        }
    except: return None

# 3. Sidebar
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = load_list()

with st.sidebar:
    st.title("⚙️ Swing Control")
    t_input = st.text_input("Voeg Tickers toe (komma-gescheiden)")
    if st.button("Toevoegen"):
        new_list = [x.strip().upper() for x in t_input.split(",") if x.strip()]
        st.session_state.watchlist = list(set(st.session_state.watchlist + new_list))
        save_list(st.session_state.watchlist)
        st.rerun()
    if st.button("Lijst Wissen"):
        st.session_state.watchlist = []
        save_list([])
        st.rerun()

# 4. Dashboard Main
st.title("🚀 AI Swing Terminal | 1-5 Dagen Horizon")

# QUICK SCAN
t_scan = st.text_input("🔍 Directe Analyse", "NVDA").upper()
res = analyze_swing(t_scan)

if res:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="metric-card"><p>SCORE</p><p class="status-bold" style="color:{res["COL"]}">{res["S"]}%</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><p>AI PREDICTION (3D)</p><p class="status-bold">{res["AI_T"]:+.2f}%</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><p>AI MOMENTUM</p><p class="status-bold">{res["AI_M"]}</p></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="metric-card"><p>ADVIES</p><p class="status-bold" style="color:{res["COL"]}">{res["STAT"]}</p></div>', unsafe_allow_html=True)

    st.write(f"**Trade Setup:** Entry: `${res['P']:.2f}` | Target: `${res['T1']:.2f}` | Stop: `${res['SL']:.2f}`")

# LIVE WATCHLIST
st.write("---")
@st.fragment(run_every=15)
def render_list():
    st.subheader("🔄 Real-Time Swing Monitor")
    
    # Custom Table Header
    cols = st.columns([1, 1, 1, 1, 1, 1])
    headers = ["Ticker", "Prijs", "Score", "Advies", "AI Trend", "Target"]
    for col, h in zip(cols, headers): col.write(f"**{h}**")

    for ticker in st.session_state.watchlist:
        d = analyze_swing(ticker)
        if d:
            row = st.columns([1, 1, 1, 1, 1, 1])
            row[0].write(f"**{d['T']}**")
            row[1].write(f"${d['P']:.2f}")
            row[2].write(f"{d['S']}%")
            row[3].markdown(f"<span style='color:{d['COL']}'>{d['STAT']}</span>", unsafe_allow_html=True)
            row[4].write(f"{d['AI_T']:+.1f}%")
            row[5].write(f"${d['T1']:.2f}")

render_list()




