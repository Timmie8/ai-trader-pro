import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

# 1. Dashboard Config
st.set_page_config(page_title="AI-First Swing Trader", layout="wide")
st.markdown("<style>.stApp { background-color: #0b1117; color: #ffffff; }</style>", unsafe_allow_html=True)

def analyze_ticker(ticker):
    try:
        t = yf.Ticker(ticker)
        d1h = t.history(period="5d", interval="1h")
        dd = t.history(period="100d", interval="1d")

        if dd.empty or d1h.empty: return None

        curr_p = dd['Close'].iloc[-1]
        prev_close = dd['Close'].iloc[-2]
        
        # --- NIEUW: Berekening 24u Percentage ---
        pct_change = ((curr_p - prev_close) / prev_close) * 100

        # --- AI METHODE 1: Trend Regressie ---
        y = dd['Close'].tail(30).values.reshape(-1, 1)
        X = np.array(range(len(y))).reshape(-1, 1)
        model = LinearRegression().fit(X, y)
        ai_pred_3d = float(model.predict(np.array([[len(y) + 3]]))[0][0])
        ai_trend_bullish = ai_pred_3d > curr_p

        # --- AI METHODE 2: Momentum Score (0-100%) ---
        short_mom = dd['Close'].pct_change(3).iloc[-1]
        long_mom = dd['Close'].pct_change(10).iloc[-1]
        mom_val = 0
        if short_mom > 0: mom_val += 50
        if short_mom > long_mom: mom_val += 50
        ai_mom_bullish = mom_val >= 50

        # --- TECHNISCHE ANALYSE ---
        score_1h = 0
        ema9_1h = d1h['Close'].ewm(span=9).mean().iloc[-1]
        if d1h['Close'].iloc[-1] > ema9_1h: score_1h += 50
        if d1h['Close'].iloc[-1] > d1h['Close'].iloc[-2]: score_1h += 50
        
        safe_entry = curr_p > dd['High'].iloc[-2]

        # --- EINDOORDEEL ---
        ai_is_goed = ai_trend_bullish and ai_mom_bullish
        if ai_is_goed and score_1h >= 50 and safe_entry:
            stat, col = "🚀 STRONG BUY", "#00ff88"
        elif ai_is_goed and score_1h >= 50:
            stat, col = "💎 AI + TECH READY", "#7fff00"
        elif ai_is_goed:
            stat, col = "🔍 AI ONLY (Wait)", "#d29922"
        else:
            stat, col = "❌ AVOID", "#8b949e"

        return {
            "ticker": ticker, "price": curr_p, "pct": pct_change,
            "ai_mom": mom_val, "score1h": score_1h, 
            "status": stat, "color": col, "safe": safe_entry
        }
    except:
        return None

# --- UI ---
st.title("🏹 AI-First Momentum Terminal")

watchlist = ["AAPL", "NVDA", "TSLA", "SGMT", "CENX", "AMD"]
tickers_input = st.text_input("Tickers", ",".join(watchlist))
tickers = [x.strip().upper() for x in tickers_input.split(",") if x.strip()]

if st.button("🔄 Ververs Analyse"):
    st.rerun()

# Tabel Headers inclusief % Verandering
cols = st.columns([1, 1.2, 1, 1, 1, 1, 2])
names = ["Ticker", "Prijs (%)", "AI Mom", "1u Score", "Safe Entry", "Eindoordeel"]
# Merk op: we gebruiken 6 kolommen voor de headers, maar 7 in de loop voor de verdeling
for col, name in zip(cols, names): col.write(f"**{name}**")

for t in tickers:
    d = analyze_ticker(t)
    if d:
        r = st.columns([1, 1.2, 1, 1, 1, 1, 2])
        r[0].write(f"**{d['ticker']}**")
        
        # Prijs + Gekleurde Percentage
        pct_col = "#00ff88" if d['pct'] >= 0 else "#ff4b4b"
        r[1].markdown(f"${d['price']:.2f} <span style='color:{pct_col}; font-size:0.8em;'>({d['pct']:+.2f}%)</span>", unsafe_allow_html=True)
        
        # AI Momentum
        mom_col = "#00ff88" if d['ai_mom'] == 100 else ("#7fff00" if d['ai_mom'] == 50 else "#ff4b4b")
        r[2].write(f"{d['ai_mom']}%")
        
        # 1u Score
        r[3].write(f"{d['score1h']}%")
        
        r[4].write("✅" if d['safe'] else "❌")
        r[5].markdown(f"<span style='color:{d['color']}; font-weight:bold;'>{d['status']}</span>", unsafe_allow_html=True)










