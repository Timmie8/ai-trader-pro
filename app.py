import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

# 1. Dashboard Config
st.set_page_config(page_title="AI Precision Scalper", layout="wide")
st.markdown("<style>.stApp { background-color: #0b1117; color: #ffffff; }</style>", unsafe_allow_html=True)

def calculate_detailed_score(df):
    if df is None or len(df) < 5: return 0
    
    score = 0
    curr = df['Close'].iloc[-1]
    
    # Check 1: Prijs vs EMA 9 (40 punten)
    ema9 = df['Close'].ewm(span=9).mean().iloc[-1]
    if curr > ema9: score += 40
    
    # Check 2: Prijs richting (60 punten)
    if curr > df['Close'].iloc[-2]: score += 60
    
    return int(score)

def analyze_ticker(ticker):
    try:
        t = yf.Ticker(ticker)
        # Haal data op met extra checks
        d15 = t.history(period="2d", interval="15m")
        d1h = t.history(period="5d", interval="1h")
        if d1h.empty: d1h = t.history(period="5d", interval="60m") # Backup interval
        dd = t.history(period="100d", interval="1d")

        if dd.empty: return None

        # Scores berekenen
        s15 = calculate_detailed_score(d15)
        s1h = calculate_detailed_score(d1h)
        
        # Safe Entry (Daily High)
        curr_p = dd['Close'].iloc[-1]
        prev_h = dd['High'].iloc[-2]
        safe = curr_p > prev_h
        
        # AI Forecast
        y = dd['Close'].tail(20).values.reshape(-1, 1)
        X = np.array(range(len(y))).reshape(-1, 1)
        ai_val = ((float(LinearRegression().fit(X, y).predict(np.array([[23]]))[0][0]) / curr_p) - 1) * 100

        # Status logica
        if safe and s15 >= 70 and s1h >= 70: stat, col = "🚀 STRONG BUY", "#00ff88"
        elif s15 >= 70: stat, col = "👀 INTRADAY PUMP", "#7fff00"
        elif safe: stat, col = "✅ SWING READY", "#aff5b4"
        else: stat, col = "❌ BEARISH / WAIT", "#8b949e"

        # LET OP: Sleutels zijn nu consistent kleine letters
        return {
            "ticker": ticker, 
            "price": curr_p, 
            "score15": s15, 
            "score1h": s1h, 
            "status": stat, 
            "color": col, 
            "ai": ai_val, 
            "safe": safe
        }
    except Exception as e:
        return None

# --- UI ---
st.title("🏹 Multi-Timeframe Momentum Monitor")

# Gebruik een vaste lijst om te testen
watchlist = ["AAPL", "NVDA", "TSLA", "SGMT", "CENX", "AMD"]
tickers_input = st.text_input("Voeg tickers toe (bijv: AAPL, BTC-USD)", ",".join(watchlist))
tickers = [x.strip().upper() for x in tickers_input.split(",") if x.strip()]

if st.button("🔄 Refresh Data"):
    st.rerun()

# Tabel
cols = st.columns([1, 1, 1, 1, 1, 2, 1])
names = ["Ticker", "Prijs", "15m Score", "1h Score", "Safe Entry", "Advies", "AI 3D"]
for col, name in zip(cols, names): col.write(f"**{name}**")

for t in tickers:
    d = analyze_ticker(t)
    if d:
        r = st.columns([1, 1, 1, 1, 1, 2, 1])
        r[0].write(f"**{d['ticker']}**")
        r[1].write(f"${d['price']:.2f}")
        
        # Gebruik de juiste sleutelnamen: score15 en score1h
        c15 = "#00ff88" if d['score15'] >= 50 else "#ff4b4b"
        c1h = "#00ff88" if d['score1h'] >= 50 else "#ff4b4b"
        
        r[2].markdown(f"<span style='color:{c15}'>{d['score15']}%</span>", unsafe_allow_html=True)
        r[3].markdown(f"<span style='color:{c1h}'>{d['score1h']}%</span>", unsafe_allow_html=True)
        r[4].write("✅" if d['safe'] else "❌")
        r[5].markdown(f"<span style='color:{d['color']}; font-weight:bold;'>{d['status']}</span>", unsafe_allow_html=True)
        r[6].write(f"{d['ai']:+.1f}%")







