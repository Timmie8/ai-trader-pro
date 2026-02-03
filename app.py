import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import os
import time

# --- OPSLAG LOGICA ---
def save_watchlist(watchlist):
    with open("watchlist_data.txt", "w") as f:
        f.write(",".join(watchlist))

def load_watchlist():
    if os.path.exists("watchlist_data.txt"):
        with open("watchlist_data.txt", "r") as f:
            data = f.read().strip()
            return [t.strip().upper() for t in data.split(",") if t.strip()]
    return ["AAPL", "NVDA"]

# 1. Pagina Setup & Styling
st.set_page_config(page_title="AI Precision Dashboard", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; color: #ffffff !important; }
    [data-testid="stSidebar"] { background-color: #050505 !important; border-right: 1px solid #333 !important; }
    .card { border: 1px solid #333; padding: 15px; border-radius: 10px; background: #050505; margin-bottom: 10px; }
    .label { color: #8b949e; font-size: 0.8em; text-transform: uppercase; }
    .val { font-weight: bold; font-size: 1.1em; }
    </style>
""", unsafe_allow_html=True)

# 2. Indicator Analyse Functie
def analyze_stock(ticker):
    try:
        data = yf.Ticker(ticker).history(period="100d")
        if data.empty: return None

        # 1 Day Change & Score
        change_pct = ((data['Close'].iloc[-1] / data['Close'].iloc[-2]) - 1) * 100
        change_score = min(10, abs(int(change_pct * 3)))
        
        # 3 Day Candle & Accumulation
        last_3 = data.tail(3)
        candle = "Strong Bullish" if last_3['Close'].iloc[-1] > last_3['Open'].iloc[-1] else "Neutral"
        vol_avg = data['Volume'].tail(10).mean()
        acc_score = "Extreme Accumulation" if data['Volume'].iloc[-1] > vol_avg * 1.2 else "Neutral"
        
        # Direction & Trends
        direction = "Strong Rally" if data['Close'].iloc[-1] > data['Close'].tail(5).mean() else "Pullback"
        
        # Trade Quality & Overall (90/10 regel)
        bull_points = 0
        if change_pct > 0: bull_points += 1
        if candle == "Strong Bullish": bull_points += 1
        if acc_score == "Extreme Accumulation": bull_points += 1
        if direction == "Strong Rally": bull_points += 1
        
        long_q = int((bull_points / 4) * 100)
        short_q = 100 - long_q
        
        if long_q >= 90: overall, color = "Strong Bullish", "#39d353"
        elif long_q >= 60: overall, color = "Mild Bullish", "#aff5b4"
        elif short_q >= 90: overall, color = "Strong Bearish", "#f85149"
        elif short_q >= 60: overall, color = "Mild Bearish", "#fca5a5"
        else: overall, color = "Neutral", "#d29922"

        res = data['High'].max()
        curr = data['Close'].iloc[-1]
        breakout = "CONFIRMED" if curr >= res * 0.99 else "WATCH"

        return {
            "T": ticker, "P": curr, "O": overall, "COL": color, "LQ": long_q, "SQ": short_q,
            "C1": change_score, "MF": "Bullish" if change_pct > 0 else "Bearish", 
            "C3": candle, "ACC": acc_score, "DIR": direction, "BR": breakout
        }
    except: return None

# 3. Sidebar voor Multi-Ticker Input
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = load_watchlist()

with st.sidebar:
    st.title("📋 Portfolio Beheer")
    multi_input = st.text_area("Voeg tickers toe (komma-gescheiden)", placeholder="AAPL, TSLA, NVDA, BTC-USD")
    if st.button("Toevoegen aan Lijst"):
        new_tickers = [t.strip().upper() for t in multi_input.split(",") if t.strip()]
        st.session_state.watchlist = list(dict.fromkeys(st.session_state.watchlist + new_tickers))
        save_watchlist(st.session_state.watchlist)
        st.rerun()
    
    if st.button("Lijst Wissen"):
        st.session_state.watchlist = []
        save_watchlist([])
        st.rerun()

# 4. Dashboard Hoofdscherm
st.title("🏹 AI Precision Trading Dashboard")

# SNEL-SCAN (Individueel)
target = st.text_input("🔍 Snelle Ticker Scan", "AAPL").upper()
d = analyze_stock(target)
if d:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="card"><div class="label">Overall Summary</div><div class="val" style="color:{d["COL"]}">{d["O"]}</div><br><div class="label">Breakout</div><div class="val">{d["BR"]}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="card"><div class="label">Long Trade Quality</div><div class="val">{d["LQ"]}%</div><br><div class="label">Short Trade Quality</div><div class="val">{d["SQ"]}%</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="card"><div class="label">1 Day Price Change</div><div class="val">Score: {d["C1"]}</div><br><div class="label">Direction</div><div class="val">{d["DIR"]}</div></div>', unsafe_allow_html=True)

st.write("---")

# 5. LIVE WATCHLIST (Update elke 10 sec)
@st.fragment(run_every=10)
def show_live_watchlist():
    st.subheader("🔄 Live Watchlist (Update elke 10s)")
    if not st.session_state.watchlist:
        st.info("De lijst is leeg. Voeg aandelen toe via de sidebar.")
        return

    # Tabel Koppen
    st.markdown("""
        <div style="display: flex; font-weight: bold; border-bottom: 2px solid #333; padding: 10px; color: #8b949e; font-size: 0.9em;">
            <div style="width: 10%;">Ticker</div>
            <div style="width: 10%;">Prijs</div>
            <div style="width: 15%;">Overall Score</div>
            <div style="width: 10%;">Long Q</div>
            <div style="width: 10%;">Short Q</div>
            <div style="width: 15%;">3D Candle</div>
            <div style="width: 15%;">Direction</div>
            <div style="width: 15%;">Breakout</div>
        </div>
    """, unsafe_allow_html=True)

    for t in st.session_state.watchlist:
        res = analyze_stock(t)
        if res:
            # Rij-kleur aanpassen op basis van status
            bg_style = "background: rgba(57, 211, 83, 0.05);" if "Bullish" in res['O'] else "background: transparent;"
            
            st.markdown(f"""
                <div style="display: flex; align-items: center; padding: 10px; border-bottom: 1px solid #111; {bg_style}">
                    <div style="width: 10%;"><b>{res['T']}</b></div>
                    <div style="width: 10%; font-family: monospace;">${res['P']:.2f}</div>
                    <div style="width: 15%; color:{res['COL']}; font-weight:bold;">{res['O']}</div>
                    <div style="width: 10%;">{res['LQ']}%</div>
                    <div style="width: 10%;">{res['SQ']}%</div>
                    <div style="width: 15%;">{res['C3']}</div>
                    <div style="width: 15%;">{res['DIR']}</div>
                    <div style="width: 15%; font-size: 0.9em;">{res['BR']}</div>
                </div>
            """, unsafe_allow_html=True)

show_live_watchlist()


