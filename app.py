import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

# 1. Dashboard Config
st.set_page_config(page_title="AI Precision Scalper", layout="wide")
st.markdown("<style>.stApp { background-color: #0b1117; color: #ffffff; }</style>", unsafe_allow_html=True)

def calculate_detailed_score(df):
    if df is None or len(df) < 14: return 0
    
    score = 0
    curr = df['Close'].iloc[-1]
    
    # Check 1: Prijs vs EMA 9 (40 punten)
    ema9 = df['Close'].ewm(span=9).mean().iloc[-1]
    if curr > ema9: score += 40
    
    # Check 2: RSI Momentum (30 punten)
    delta = df['Close'].diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=13, adjust=False).mean()
    ema_down = down.ewm(com=13, adjust=False).mean()
    rs = ema_up / ema_down
    rsi = 100 - (100 / (1 + rs)).iloc[-1]
    if rsi > 50: score += 30
    
    # Check 3: Prijs richting (30 punten)
    if curr > df['Close'].iloc[-2]: score += 30
    
    return int(score)

def analyze_ticker(ticker):
    try:
        # Haal data op
        t = yf.Ticker(ticker)
        d15 = t.history(period="2d", interval="15m")
        d1h = t.history(period="5d", interval="60m")
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
        if safe and s15 > 60 and s1h > 60: stat, col = "🚀 STRONG BUY", "#00ff88"
        elif s15 > 70: stat, col = "👀 INTRADAY PUMP", "#7fff00"
        elif safe: stat, col = "✅ SWING READY", "#aff5b4"
        else: stat, col = "❌ BEARISH / WAIT", "#8b949e"

        return {"T": ticker, "P": curr_p, "15": s15, "1H": s1h, "S": stat, "C": col, "AI": ai_val, "SAFE": safe}
    except:
        return None

# --- UI ---
st.title("🏹 Multi-Timeframe Momentum Monitor")

# Gebruik een vaste lijst om te testen
watchlist = ["AAPL", "NVDA", "TSLA", "SGMT", "CENX", "AMD"]
tickers = st.text_input("Voeg tickers toe (gescheiden door komma's)", ",".join(watchlist)).upper().split(",")

if st.button("🔄 Refresh Data"):
    st.rerun()

# Tabel
cols = st.columns([1, 1, 1, 1, 1, 2, 1])
names = ["Ticker", "Prijs", "15m Momentum", "1h Momentum", "Safe Entry", "Advies", "AI 3D"]
for col, name in zip(cols, names): col.write(f"**{name}**")

for t in [x.strip() for x in tickers]:
    d = analyze_ticker(t)
    if d:
        r = st.columns([1, 1, 1, 1, 1, 2, 1])
        r[0].write(f"**{d['T']}**")
        r[1].write(f"${d['P']:.2f}")
        
        # Kleur de scores
        c15 = "#00ff88" if d['15'] > 50 else "#ff4b4b"
        c1h = "#00ff88" if d['1h'] > 50 else "#ff4b4b"
        
        r[2].markdown(f"<span style='color:{c15}'>{d['15']}%</span>", unsafe_allow_html=True)
        r[3].markdown(f"<span style='color:{c1h}'>{d['1h']}%</span>", unsafe_allow_html=True)
        r[4].write("✅" if d['SAFE'] else "❌")
        r[5].markdown(f"<span style='color:{d['C']}; font-weight:bold;'>{d['S']}</span>", unsafe_allow_html=True)
        r[6].write(f"{d['AI']:+.1f}%")






