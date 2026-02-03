import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import os

# --- OPSLAG ---
def save_watchlist(watchlist):
    with open("watchlist_v3.txt", "w") as f:
        f.write(",".join(watchlist))

def load_watchlist():
    if os.path.exists("watchlist_v3.txt"):
        with open("watchlist_v3.txt", "r") as f:
            data = f.read().strip()
            return data.split(",") if data else []
    return ["AAPL", "NVDA", "TSLA"]

# 1. Pagina Setup
st.set_page_config(page_title="AI Precision Dashboard", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; color: #ffffff !important; }
    .card { border: 1px solid #333; padding: 15px; border-radius: 10px; background: #050505; margin-bottom: 10px; }
    .label { color: #8b949e; font-size: 0.8em; text-transform: uppercase; }
    .val { font-weight: bold; font-size: 1.1em; }
    </style>
""", unsafe_allow_html=True)

# 2. Indicator Functies op basis van jouw tekst
def analyze_stock(ticker):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="100d")
        if data.empty: return None

        # --- 1 DAG CHANGE & MONEYFLOW ---
        change_pct = ((data['Close'].iloc[-1] / data['Close'].iloc[-2]) - 1) * 100
        change_score = min(10, abs(int(change_pct * 3)))
        money_flow = "Neutral" if abs(change_pct) < 0.5 else ("Bullish" if change_pct > 0 else "Bearish")

        # --- 3 DAG CANDLE & ACCUMULATION ---
        last_3 = data.tail(3)
        candle = "Strong Bullish" if last_3['Close'].iloc[-1] > last_3['Open'].iloc[-1] else "Neutral"
        vol_avg = data['Volume'].tail(10).mean()
        acc_score = "Extreme Accumulation" if data['Volume'].iloc[-1] > vol_avg * 1.2 else "Neutral"
        
        # --- DIRECTION & TREND ---
        direction = "Strong Rally" if data['Close'].iloc[-1] > data['Close'].tail(5).mean() else "Pullback"
        
        # --- OVERALL & TRADE QUALITY (LONG VS SHORT) ---
        # Logica: Bereken indicators per kant
        bull_inds = 0
        if change_pct > 0: bull_inds += 1
        if candle == "Strong Bullish": bull_inds += 1
        if acc_score == "Extreme Accumulation": bull_inds += 1
        if direction == "Strong Rally": bull_inds += 1
        
        total_inds = 4
        long_q = int((bull_inds / total_inds) * 100)
        short_q = 100 - long_q
        
        overall = "Neutral"
        if long_q >= 90: overall = "Strong Bullish"
        elif long_q >= 60: overall = "Mild Bullish"
        elif short_q >= 90: overall = "Strong Bearish"
        elif short_q >= 60: overall = "Mild Bearish"

        # --- BREAKOUT STATUS ---
        res = data['High'].max()
        curr = data['Close'].iloc[-1]
        breakout = "WATCH" if curr < res else "CONFIRMED"

        return {
            "T": ticker, "P": curr, "O": overall, "LQ": long_q, "SQ": short_q,
            "C1": change_score, "MF": money_flow, "C3": candle, "ACC": acc_score,
            "DIR": direction, "BR": breakout, "RES": res
        }
    except: return None

# 3. Sidebar & Watchlist
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = load_watchlist()

with st.sidebar:
    st.title("Settings")
    new_t = st.text_input("Voeg Ticker toe").upper()
    if st.button("Toevoegen"):
        st.session_state.watchlist.append(new_t)
        save_watchlist(st.session_state.watchlist)
        st.rerun()

# 4. Dashboard Main
st.title("🏹 AI Precision Trading Dashboard")

# DIRECTE SCAN (VOORBEELD AAPL)
target = st.text_input("Analyseer Ticker", "AAPL").upper()
d = analyze_stock(target)

if d:
    st.markdown(f"### Resultaat voor {d['T']}")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
            <div class="card">
                <div class="label">Overall Summary</div>
                <div class="val" style="color:#39d353">{d['O']}</div>
                <br>
                <div class="label">Breakout Status</div>
                <div class="val">{d['BR']}</div>
            </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
            <div class="card">
                <div class="label">Long Trade Quality</div>
                <div class="val">{d['LQ']}%</div>
                <br>
                <div class="label">Short Trade Quality</div>
                <div class="val">{d['SQ']}%</div>
            </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
            <div class="card">
                <div class="label">1 Day Price Change</div>
                <div class="val">{d['C1']} (Score)</div>
                <br>
                <div class="label">1 Day Money Flow</div>
                <div class="val">{d['MF']}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="card" style="display: flex; justify-content: space-around; text-align: center;">
            <div><div class="label">3 Day Candle</div><div class="val">{d['C3']}</div></div>
            <div><div class="label">Accumulation</div><div class="val">{d['ACC']}</div></div>
            <div><div class="label">Direction</div><div class="val">{d['DIR']}</div></div>
        </div>
    """, unsafe_allow_html=True)

# WATCHLIST TABEL
st.write("---")
st.subheader("Live Portfolio Monitor")
@st.fragment(run_every=10)
def show_list():
    # Header
    cols = st.columns([1, 1, 1, 1, 1, 1, 1])
    cols[0].write("**Ticker**")
    cols[1].write("**Overall**")
    cols[2].write("**Long Q**")
    cols[3].write("**Short Q**")
    cols[4].write("**Candle**")
    cols[5].write("**Direction**")
    cols[6].write("**Breakout**")

    for t in st.session_state.watchlist:
        res = analyze_stock(t)
        if res:
            c = st.columns([1, 1, 1, 1, 1, 1, 1])
            c[0].write(f"**{res['T']}**")
            c[1].write(res['O'])
            c[2].write(f"{res['LQ']}%")
            c[3].write(f"{res['SQ']}%")
            c[4].write(res['C3'])
            c[5].write(res['DIR'])
            c[6].write(res['BR'])

show_list()

