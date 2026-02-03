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
    return ["AAPL", "NVDA", "TSLA"]

# 1. Pagina Setup
st.set_page_config(page_title="AI Hybrid Strategy", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; color: #ffffff !important; }
    .card { border: 1px solid #333; padding: 15px; border-radius: 10px; background: #050505; margin-bottom: 10px; }
    .val { font-weight: bold; font-size: 1.1em; }
    </style>
""", unsafe_allow_html=True)

# 2. De Hybrid Analyse Logica (7 Factoren)
def analyze_hybrid(ticker):
    try:
        data = yf.Ticker(ticker).history(period="150d")
        if data.empty: return None

        curr_p = data['Close'].iloc[-1]
        
        # --- CATEGORIE 1: JOUW TIMING INDICATORS ---
        change_pct = ((curr_p / data['Close'].iloc[-2]) - 1) * 100
        candle = "Bullish" if data['Close'].iloc[-1] > data['Open'].iloc[-1] else "Neutral"
        vol_avg = data['Volume'].tail(10).mean()
        acc = "Accumulation" if data['Volume'].iloc[-1] > vol_avg * 1.15 else "Neutral"
        
        # --- CATEGORIE 2: TREND & DIRECTION ---
        st_dir = "Up" if curr_p > data['Close'].tail(5).mean() else "Down"
        it_trend = "Bullish" if curr_p > data['Close'].tail(80).mean() else "Bearish"

        # --- CATEGORIE 3: DE 2 AI MODELLEN ---
        # AI 1: Lineaire Regressie (Ensemble)
        y = data['Close'].tail(60).values.reshape(-1, 1)
        X = np.array(range(len(y))).reshape(-1, 1)
        reg = LinearRegression().fit(X, y)
        ai_pred = float(reg.predict(np.array([[len(y)]]))[0][0])
        ai_ensemble = "Bullish" if ai_pred > curr_p else "Bearish"
        
        # AI 2: LSTM Trend (Simulatie via 5-daags Momentum)
        lstm_score = data['Close'].iloc[-5:].pct_change().sum() * 100
        ai_lstm = "Bullish" if lstm_score > 0.5 else "Bearish"

        # --- DE HYBRIDE PUNTENTELLING (7 PUNTEN TOTAAL) ---
        bull_points = 0
        if change_pct > 0: bull_points += 1    # 1. Prijs
        if candle == "Bullish": bull_points += 1 # 2. Candle
        if acc == "Accumulation": bull_points += 1 # 3. Volume
        if st_dir == "Up": bull_points += 1      # 4. Korte Trend
        if it_trend == "Bullish": bull_points += 1 # 5. Lange Trend
        if ai_ensemble == "Bullish": bull_points += 1 # 6. AI Voorspelling
        if ai_lstm == "Bullish": bull_points += 1     # 7. AI Momentum
        
        long_q = int((bull_points / 7) * 100)
        short_q = 100 - long_q
        
        # Status op basis van jouw 90/10 en 60/40 regels
        if long_q >= 85: overall, color = "Strong Bullish", "#39d353"
        elif long_q >= 57: overall, color = "Mild Bullish", "#aff5b4"
        elif short_q >= 85: overall, color = "Strong Bearish", "#f85149"
        elif short_q >= 57: overall, color = "Mild Bearish", "#fca5a5"
        else: overall, color = "Neutral", "#d29922"

        return {
            "T": ticker, "P": curr_p, "O": overall, "COL": color, "LQ": long_q, "SQ": short_q,
            "AI_E": ai_ensemble, "AI_L": ai_lstm, "IT": it_trend, "DIR": st_dir, "CH": change_pct
        }
    except: return None

# 3. Sidebar
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = load_watchlist()

with st.sidebar:
    st.title("📋 Instellingen")
    multi_input = st.text_area("Voeg Tickers toe (bijv: AAPL, BTC-USD)")
    if st.button("Toevoegen"):
        new = [t.strip().upper() for t in multi_input.split(",") if t.strip()]
        st.session_state.watchlist = list(dict.fromkeys(st.session_state.watchlist + new))
        save_watchlist(st.session_state.watchlist)
        st.rerun()
    if st.button("Lijst Wissen"):
        st.session_state.watchlist = []
        save_watchlist([])
        st.rerun()

# 4. Dashboard
st.title("🏹 AI Hybrid Precision Terminal")

# Snel-scan Kaart
target = st.text_input("Zoek aandeel", "AAPL").upper()
d = analyze_hybrid(target)
if d:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="card"><div style="color:#8b949e; font-size:0.8em;">OVERALL SUMMARY</div><div class="val" style="color:{d["COL"]}">{d["O"]}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="card"><div style="color:#8b949e; font-size:0.8em;">AI ENSEMBLE</div><div class="val">{d["AI_E"]}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="card"><div style="color:#8b949e; font-size:0.8em;">AI LSTM MOMENTUM</div><div class="val">{d["AI_L"]}</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="card"><div style="color:#8b949e; font-size:0.8em;">LONG QUALITY</div><div class="val">{d["LQ"]}%</div></div>', unsafe_allow_html=True)

st.write("---")

# 5. LIVE MONITOR
@st.fragment(run_every=10)
def show_list():
    st.subheader("🔄 Live Hybrid Monitor (7-Factor Analysis)")
    if not st.session_state.watchlist: return

    # Tabel Headers
    st.markdown("""
        <div style="display: flex; font-weight: bold; border-bottom: 2px solid #333; padding: 10px; color: #8b949e; font-size: 0.85em;">
            <div style="width: 10%;">Ticker</div>
            <div style="width: 15%;">Overall Score</div>
            <div style="width: 10%;">Long Q</div>
            <div style="width: 10%;">Short Q</div>
            <div style="width: 15%;">AI Ensemble</div>
            <div style="width: 15%;">AI Momentum</div>
            <div style="width: 15%;">Int. Trend</div>
            <div style="width: 10%;">Change</div>
        </div>
    """, unsafe_allow_html=True)

    for t in st.session_state.watchlist:
        res = analyze_hybrid(t)
        if res:
            st.markdown(f"""
                <div style="display: flex; align-items: center; padding: 10px; border-bottom: 1px solid #111;">
                    <div style="width: 10%;"><b>{res['T']}</b></div>
                    <div style="width: 15%; color:{res['COL']}; font-weight:bold;">{res['O']}</div>
                    <div style="width: 10%;">{res['LQ']}%</div>
                    <div style="width: 10%;">{res['SQ']}%</div>
                    <div style="width: 15%; color:{'#39d353' if res['AI_E'] == 'Bullish' else '#f85149'};">{res['AI_E']}</div>
                    <div style="width: 15%; color:{'#39d353' if res['AI_L'] == 'Bullish' else '#f85149'};">{res['AI_L']}</div>
                    <div style="width: 15%;">{res['IT']}</div>
                    <div style="width: 10%; color:{'#39d353' if res['CH'] > 0 else '#f85149'}">{res['CH']:+.2f}%</div>
                </div>
            """, unsafe_allow_html=True)

show_list()



