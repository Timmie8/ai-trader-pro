import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import os

# --- PERSISTENTIE ---
def save_list(watchlist):
    with open("swing_safe_watchlist.txt", "w") as f:
        f.write(",".join(watchlist))

def load_list():
    if os.path.exists("swing_safe_watchlist.txt"):
        with open("swing_safe_watchlist.txt", "r") as f:
            data = f.read().strip()
            return [t.strip().upper() for t in data.split(",") if t.strip()]
    return ["SGMT", "CENX", "NVDA", "AAPL"]

# 1. Setup
st.set_page_config(page_title="AI Safe-Entry Trader", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0b0e11; color: #e9eaeb; }
    .status-box { padding: 20px; border-radius: 10px; border: 1px solid #2b2f36; background: #161a1e; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# 2. De Swing Engine met Safe-Entry Filter
def analyze_safe_swing(ticker):
    try:
        data = yf.Ticker(ticker).history(period="60d")
        if data.empty: return None

        curr_p = data['Close'].iloc[-1]
        prev_high = data['High'].iloc[-2] # De High van gisteren
        prev_p = data['Close'].iloc[-2]
        
        # --- SAFE ENTRY CHECK ---
        # "Koop naar boven": Alleen BUY als we boven de high van gisteren handelen
        is_safe_entry = curr_p > prev_high
        
        # --- AI & TREND INDICATORS ---
        # AI 1: Trend Regressie (3 dagen vooruit)
        y = data['Close'].tail(20).values.reshape(-1, 1)
        X = np.array(range(len(y))).reshape(-1, 1)
        model = LinearRegression().fit(X, y)
        pred_3d = float(model.predict(np.array([[len(y) + 3]]))[0][0])
        ai_trend_score = ((pred_3d / curr_p) - 1) * 100
        
        # AI 2: Momentum
        mom_short = data['Close'].pct_change(3).sum()
        ai_mom_bullish = mom_short > 0

        # --- BEREKENING BASIS SCORE ---
        score = 0
        if ai_trend_score > 1.0: score += 25
        if ai_mom_bullish: score += 25
        if curr_p > data['Close'].ewm(span=9).mean().iloc[-1]: score += 25
        if data['Volume'].iloc[-1] > data['Volume'].tail(10).mean(): score += 25

        # --- DE FILTER OVERRIDE ---
        if not is_safe_entry:
            # Zelfs als de AI positief is, mag het geen BUY zijn als we onder de gisteren-high zitten
            final_status = "WAIT (No Breakout)"
            final_color = "#fca5a5" # Zacht rood/roze
            if score >= 50: 
                final_status = "WATCH (Setup Ready)"
                final_color = "#d29922" # Oranje: alles staat klaar, maar wacht op entry
        else:
            if score >= 75: 
                final_status = "STRONG BUY"
                final_color = "#00ff88"
            elif score >= 50: 
                final_status = "MILD BUY"
                final_color = "#7fff00"
            else:
                final_status = "NEUTRAL"
                final_color = "#888888"

        return {
            "T": ticker, "P": curr_p, "H": prev_high, "S": score, 
            "STAT": final_status, "COL": final_color, "SAFE": is_safe_entry,
            "AI_T": ai_trend_score
        }
    except: return None

# 3. UI & Watchlist
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = load_list()

with st.sidebar:
    st.header("Watchlist Control")
    t_input = st.text_input("Voeg Tickers toe")
    if st.button("Toevoegen"):
        st.session_state.watchlist.append(t_input.upper())
        save_list(st.session_state.watchlist)
        st.rerun()

st.title("🏹 AI Safe-Entry Swing Terminal")
st.info("Dit dashboard geeft pas een koop-signaal als de prijs boven de High van gisteren uitkomt (Koop naar boven).")

# LIVE TABEL
@st.fragment(run_every=15)
def show_table():
    cols = st.columns([1, 1, 1, 2, 1, 1])
    headers = ["Ticker", "Prijs", "Gister High", "Advies / Status", "AI Predict", "Entry Check"]
    for col, h in zip(cols, headers): col.write(f"**{h}**")

    for t in st.session_state.watchlist:
        d = analyze_safe_swing(t)
        if d:
            row = st.columns([1, 1, 1, 2, 1, 1])
            row[0].write(f"**{d['T']}**")
            row[1].write(f"${d['P']:.2f}")
            row[2].write(f"${d['H']:.2f}")
            row[3].markdown(f"<span style='color:{d['COL']}; font-weight:bold;'>{d['STAT']}</span>", unsafe_allow_html=True)
            row[4].write(f"{d['AI_T']:+.1f}%")
            row[5].write("✅ BOVEN HIGH" if d['SAFE'] else "❌ ONDER HIGH")

show_table()





