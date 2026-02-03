import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import os

# --- PERSISTENTIE ---
def save_list(watchlist):
    with open("multi_timeframe_watchlist.txt", "w") as f:
        f.write(",".join(watchlist))

def load_list():
    if os.path.exists("multi_timeframe_watchlist.txt"):
        with open("multi_timeframe_watchlist.txt", "r") as f:
            data = f.read().strip()
            return [t.strip().upper() for t in data.split(",") if t.strip()]
    return ["SGMT", "CENX", "NVDA", "AAPL"]

# 1. Dashboard Setup
st.set_page_config(page_title="AI Multi-Timeframe Trader", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0b1117; color: #e6edf3; }
    .status-card { background: #161b22; border: 1px solid #30363d; padding: 10px; border-radius: 8px; text-align: center; }
    .score-val { font-size: 1.2em; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 2. De Multi-Timeframe Engine
def get_score(data, span=20):
    """Berekent een basis momentum score voor een dataset"""
    if data.empty: return 0
    curr = data['Close'].iloc[-1]
    ema = data['Close'].ewm(span=9).mean().iloc[-1]
    # Score gebaseerd op prijs vs EMA en prijs vs vorig slot
    score = 0
    if curr > ema: score += 50
    if curr > data['Close'].iloc[-2]: score += 50
    return score

def analyze_multi_timeframe(ticker):
    try:
        # Data ophalen voor verschillende timeframes
        # Opmerking: yfinance staat maximaal 60 dagen 15m data toe
        d_15m = yf.download(ticker, period="5d", interval="15m", progress=False)
        d_1h = yf.download(ticker, period="15d", interval="1h", progress=False)
        d_daily = yf.download(ticker, period="60d", interval="1d", progress=False)

        if d_daily.empty: return None

        # --- SCORES BEREKENEN ---
        score_15m = get_score(d_15m)
        score_1h = get_score(d_1h)
        
        # --- DAILY & SAFE ENTRY ---
        curr_p = d_daily['Close'].iloc[-1]
        prev_high = d_daily['High'].iloc[-2]
        is_safe_entry = curr_p > prev_high
        
        # AI Trend Voorspelling (Daily)
        y = d_daily['Close'].tail(20).values.reshape(-1, 1)
        X = np.array(range(len(y))).reshape(-1, 1)
        model = LinearRegression().fit(X, y)
        pred_3d = float(model.predict(np.array([[len(y) + 3]]))[0][0])
        ai_trend = ((pred_3d / curr_p) - 1) * 100

        # --- TOTALE STRATEGIE ---
        # Een aandeel is "Sterk" als alle timeframes > 50 scoren
        total_strength = (score_15m + score_1h) / 2
        
        if is_safe_entry and total_strength >= 75 and ai_trend > 0:
            status, col = "🚀 STRONG BUY", "#00ff88"
        elif is_safe_entry and total_strength >= 50:
            status, col = "✅ MILD BUY", "#7fff00"
        elif not is_safe_entry and total_strength >= 75:
            status, col = "👀 WATCH (Intraday Strong)", "#d29922"
        else:
            status, col = "❌ WAIT / BEARISH", "#8b949e"

        return {
            "T": ticker, "P": curr_p, "H": prev_high, 
            "S15": score_15m, "S1H": score_1h, 
            "STAT": status, "COL": col, "SAFE": is_safe_entry, "AI": ai_trend
        }
    except: return None

# 3. Sidebar & Watchlist
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = load_list()

with st.sidebar:
    st.header("Watchlist")
    t_input = st.text_input("Tickers (komma-gescheiden)")
    if st.button("Toevoegen"):
        new_list = [x.strip().upper() for x in t_input.split(",") if x.strip()]
        st.session_state.watchlist = list(set(st.session_state.watchlist + new_list))
        save_list(st.session_state.watchlist)
        st.rerun()
    if st.button("Reset Lijst"):
        st.session_state.watchlist = []
        save_list([])
        st.rerun()

# 4. Dashboard
st.title("🏹 AI Multi-Timeframe Swing Terminal")

@st.fragment(run_every=30)
def render_dashboard():
    # Tabel Header
    st.markdown("""
        <div style="display: flex; font-weight: bold; border-bottom: 2px solid #30363d; padding: 10px; color: #8b949e;">
            <div style="width: 10%;">Ticker</div>
            <div style="width: 10%;">Prijs</div>
            <div style="width: 10%;">15m Score</div>
            <div style="width: 10%;">1h Score</div>
            <div style="width: 20%;">Safe Entry Check</div>
            <div style="width: 25%;">Overall Advies</div>
            <div style="width: 15%;">AI 3D Forecast</div>
        </div>
    """, unsafe_allow_html=True)

    for t in st.session_state.watchlist:
        d = analyze_multi_timeframe(t)
        if d:
            safe_text = "✅ BOVEN GISTEREN HIGH" if d['SAFE'] else "❌ ONDER GISTEREN HIGH"
            safe_col = "#39d353" if d['SAFE'] else "#f85149"
            
            st.markdown(f"""
                <div style="display: flex; align-items: center; padding: 10px; border-bottom: 1px solid #21262d;">
                    <div style="width: 10%;"><b>{d['T']}</b></div>
                    <div style="width: 10%;">${d['P']:.2f}</div>
                    <div style="width: 10%; color:#7fff00;">{d['S15']}%</div>
                    <div style="width: 10%; color:#00ff88;">{d['S1H']}%</div>
                    <div style="width: 20%; color:{safe_col}; font-size: 0.85em;">{safe_text}</div>
                    <div style="width: 25%; color:{d['COL']}; font-weight:bold;">{d['STAT']}</div>
                    <div style="width: 15%;">{d['AI']:+.2f}%</div>
                </div>
            """, unsafe_allow_html=True)

render_dashboard()





