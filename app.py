import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import os

# --- OPSLAG ---
def save_watchlist(watchlist):
    with open("watchlist_hybrid.txt", "w") as f:
        f.write(",".join(watchlist))

def load_watchlist():
    if os.path.exists("watchlist_hybrid.txt"):
        with open("watchlist_hybrid.txt", "r") as f:
            data = f.read().strip()
            return [t.strip().upper() for t in data.split(",") if t.strip()]
    return ["SGMT", "CENX", "AAPL"]

# 1. Pagina Setup
st.set_page_config(page_title="AI Hybrid - Risk Adjusted", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; color: #ffffff !important; }
    .card { border: 1px solid #333; padding: 15px; border-radius: 10px; background: #050505; margin-bottom: 10px; }
    .val { font-weight: bold; font-size: 1.1em; }
    </style>
""", unsafe_allow_html=True)

# 2. De Verbeterde Analyse Logica
def analyze_hybrid_v2(ticker):
    try:
        data = yf.Ticker(ticker).history(period="150d")
        if data.empty: return None

        curr_p = data['Close'].iloc[-1]
        prev_p = data['Close'].iloc[-2]
        change_pct = ((curr_p / prev_p) - 1) * 100
        
        # --- 1. TIMING INDICATORS ---
        candle = "Bullish" if curr_p > data['Open'].iloc[-1] else "Bearish"
        vol_avg = data['Volume'].tail(10).mean()
        acc = "Accumulation" if data['Volume'].iloc[-1] > vol_avg * 1.15 else "Distribution"
        
        # --- 2. TREND & AI ---
        it_trend = "Bullish" if curr_p > data['Close'].tail(80).mean() else "Bearish"
        
        y = data['Close'].tail(60).values.reshape(-1, 1)
        X = np.array(range(len(y))).reshape(-1, 1)
        reg = LinearRegression().fit(X, y)
        ai_pred = float(reg.predict(np.array([[len(y)]]))[0][0])
        ai_ensemble = "Bullish" if ai_pred > curr_p else "Bearish"

        # --- 3. PUNTENTELLING (7 BASISPUNTEN) ---
        bull_points = 0
        if change_pct > 0: bull_points += 1
        if candle == "Bullish": bull_points += 1
        if acc == "Accumulation": bull_points += 1
        if curr_p > data['Close'].tail(5).mean(): bull_points += 1 # Short term direction
        if it_trend == "Bullish": bull_points += 1
        if ai_ensemble == "Bullish": bull_points += 1
        if ai_pred > prev_p: bull_points += 1 # Momentum check

        # --- 4. DE "SGMT/CENX" CIRCUIT BREAKER (RISK OVERRIDE) ---
        # Als een aandeel hard valt, overrule de bull_points
        if change_pct < -5.0:
            bull_points = min(bull_points, 1) # Forceer naar Bearish/Neutral
        elif change_pct < -3.0:
            bull_points = min(bull_points, 3) # Forceer naar Mild Bearish/Neutral

        long_q = int((bull_points / 7) * 100)
        short_q = 100 - long_q
        
        # Status bepaling
        if long_q >= 85: overall, color = "Strong Bullish", "#39d353"
        elif long_q >= 57: overall, color = "Mild Bullish", "#aff5b4"
        elif short_q >= 85: overall, color = "Strong Bearish", "#f85149"
        elif short_q >= 57: overall, color = "Mild Bearish", "#fca5a5"
        else: overall, color = "Neutral", "#d29922"

        return {
            "T": ticker, "P": curr_p, "O": overall, "COL": color, "LQ": long_q, "SQ": short_q,
            "IT": it_trend, "AI": ai_ensemble, "CH": change_pct
        }
    except: return None

# 3. UI
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = load_watchlist()

with st.sidebar:
    st.title("📋 Portfolio")
    multi_input = st.text_area("Tickers (AAPL, SGMT, CENX)")
    if st.button("Update"):
        new = [t.strip().upper() for t in multi_input.split(",") if t.strip()]
        st.session_state.watchlist = list(dict.fromkeys(st.session_state.watchlist + new))
        save_watchlist(st.session_state.watchlist)
        st.rerun()

st.title("🏹 AI Hybrid Terminal (Risk-Adjusted)")

# Live Watchlist
@st.fragment(run_every=10)
def show_list():
    cols = st.columns([1, 2, 1, 1, 1, 1])
    headers = ["Ticker", "Overall Status", "Long Q", "Short Q", "Int. Trend", "Change"]
    for col, h in zip(cols, headers): col.write(f"**{h}**")

    for t in st.session_state.watchlist:
        res = analyze_hybrid_v2(t)
        if res:
            c = st.columns([1, 2, 1, 1, 1, 1])
            c[0].write(f"**{res['T']}**")
            c[1].markdown(f"<span style='color:{res['COL']}; font-weight:bold;'>{res['O']}</span>", unsafe_allow_html=True)
            c[2].write(f"{res['LQ']}%")
            c[3].write(f"{res['SQ']}%")
            c[4].write(res['IT'])
            c[5].markdown(f"<span style='color:{'#39d353' if res['CH'] > 0 else '#f85149'}'>{res['CH']:+.2f}%</span>", unsafe_allow_html=True)

show_list()




