import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import os

# --- OPSLAG ---
def save_watchlist(watchlist):
    with open("watchlist_data.txt", "w") as f:
        f.write(",".join(watchlist))

def load_watchlist():
    if os.path.exists("watchlist_data.txt"):
        with open("watchlist_data.txt", "r") as f:
            data = f.read().strip()
            return [t.strip().upper() for t in data.split(",") if t.strip()]
    return ["AAPL", "NVDA"]

# 1. Pagina Setup
st.set_page_config(page_title="AI Precision Dashboard PRO", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; color: #ffffff !important; }
    [data-testid="stSidebar"] { background-color: #050505 !important; border-right: 1px solid #333 !important; }
    .card { border: 1px solid #333; padding: 15px; border-radius: 10px; background: #050505; margin-bottom: 10px; }
    .val { font-weight: bold; font-size: 1.1em; }
    </style>
""", unsafe_allow_html=True)

# 2. De Strenge Analyse Logica
def analyze_stock_strict(ticker):
    try:
        # We halen nu 130 dagen op voor de 4-maands trend (Intermediate)
        data = yf.Ticker(ticker).history(period="150d")
        if data.empty: return None

        # A. 1 DAG CHANGE & MONEYFLOW (Score 0-10)
        change_pct = ((data['Close'].iloc[-1] / data['Close'].iloc[-2]) - 1) * 100
        change_score = min(10, abs(int(change_pct * 3)))
        
        # B. 3 DAG CANDLE HEALTH
        last_3 = data.tail(3)
        candle = "Strong Bullish" if last_3['Close'].iloc[-1] > last_3['Open'].iloc[-1] else "Neutral"
        
        # C. ACCUMULATION (Volume check)
        vol_avg = data['Volume'].tail(10).mean()
        acc_score = "Extreme" if data['Volume'].iloc[-1] > vol_avg * 1.2 else "Neutral"
        
        # D. SHORT TERM DIRECTION (1 week trend)
        st_dir = "Rally" if data['Close'].iloc[-1] > data['Close'].tail(5).mean() else "Pullback"
        
        # E. INTERMEDIATE TREND (4 maanden - NIEUW)
        # We vergelijken de prijs met het 80-daags gemiddelde
        intermediate_avg = data['Close'].tail(80).mean()
        it_trend = "Bullish" if data['Close'].iloc[-1] > intermediate_avg else "Bearish"

        # --- PUNTENTELLING (STRENG: 5 INDICATOREN) ---
        bull_points = 0
        if change_pct > 0: bull_points += 1
        if candle == "Strong Bullish": bull_points += 1
        if acc_score == "Extreme": bull_points += 1
        if st_dir == "Rally": bull_points += 1
        if it_trend == "Bullish": bull_points += 1 # De extra drempel
        
        long_q = int((bull_points / 5) * 100)
        short_q = 100 - long_q
        
        # Status bepaling op basis van 90/10 en 60/40 regels
        if long_q >= 90: overall, color = "Strong Bullish", "#39d353"
        elif long_q >= 60: overall, color = "Mild Bullish", "#aff5b4"
        elif short_q >= 80: overall, color = "Strong Bearish", "#f85149"
        elif short_q >= 60: overall, color = "Mild Bearish", "#fca5a5"
        else: overall, color = "Neutral", "#d29922"

        # Breakout check
        res = data['High'].tail(100).max()
        curr = data['Close'].iloc[-1]
        breakout = "CONFIRMED" if curr >= res * 0.99 else "WATCH"

        return {
            "T": ticker, "P": curr, "O": overall, "COL": color, "LQ": long_q, "SQ": short_q,
            "C1": change_score, "C3": candle, "ACC": acc_score, "DIR": st_dir, 
            "IT": it_trend, "BR": breakout, "CH": change_pct
        }
    except: return None

# 3. Sidebar
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = load_watchlist()

with st.sidebar:
    st.title("📋 Instellingen")
    multi_input = st.text_area("Tickers (bijv: AAPL, NVDA)")
    if st.button("Toevoegen"):
        new = [t.strip().upper() for t in multi_input.split(",") if t.strip()]
        st.session_state.watchlist = list(dict.fromkeys(st.session_state.watchlist + new))
        save_watchlist(st.session_state.watchlist)
        st.rerun()
    if st.button("Wissen"):
        st.session_state.watchlist = []
        save_watchlist([])
        st.rerun()

# 4. Dashboard
st.title("🏹 AI Precision Terminal (Strict Mode)")

# Snel-scan
target = st.text_input("Snelle Scan", "AAPL").upper()
d = analyze_stock_strict(target)
if d:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="card"><div style="color:#8b949e; font-size:0.8em;">OVERALL</div><div class="val" style="color:{d["COL"]}">{d["O"]}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="card"><div style="color:#8b949e; font-size:0.8em;">4-MAAND TREND</div><div class="val">{d["IT"]}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="card"><div style="color:#8b949e; font-size:0.8em;">LONG QUALITY</div><div class="val">{d["LQ"]}%</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="card"><div style="color:#8b949e; font-size:0.8em;">SHORT QUALITY</div><div class="val">{d["SQ"]}%</div></div>', unsafe_allow_html=True)

st.write("---")

# 5. LIVE WATCHLIST
@st.fragment(run_every=10)
def show_list():
    st.subheader("🔄 Live Monitor")
    if not st.session_state.watchlist: return

    # Tabel Koppen
    st.markdown("""
        <div style="display: flex; font-weight: bold; border-bottom: 2px solid #333; padding: 10px; color: #8b949e; font-size: 0.85em;">
            <div style="width: 10%;">Ticker</div>
            <div style="width: 15%;">Overall Score</div>
            <div style="width: 10%;">Long Q</div>
            <div style="width: 10%;">Short Q</div>
            <div style="width: 15%;">Int. Trend (4m)</div>
            <div style="width: 15%;">Direction</div>
            <div style="width: 15%;">Breakout</div>
            <div style="width: 10%;">Change</div>
        </div>
    """, unsafe_allow_html=True)

    for t in st.session_state.watchlist:
        res = analyze_stock_strict(t)
        if res:
            st.markdown(f"""
                <div style="display: flex; align-items: center; padding: 10px; border-bottom: 1px solid #111;">
                    <div style="width: 10%;"><b>{res['T']}</b></div>
                    <div style="width: 15%; color:{res['COL']}; font-weight:bold;">{res['O']}</div>
                    <div style="width: 10%;">{res['LQ']}%</div>
                    <div style="width: 10%;">{res['SQ']}%</div>
                    <div style="width: 15%;">{res['IT']}</div>
                    <div style="width: 15%;">{res['DIR']}</div>
                    <div style="width: 15%;">{res['BR']}</div>
                    <div style="width: 10%; color:{'#39d353' if res['CH'] > 0 else '#f85149'}">{res['CH']:+.2f}%</div>
                </div>
            """, unsafe_allow_html=True)

show_list()



