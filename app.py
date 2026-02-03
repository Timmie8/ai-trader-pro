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
        d15 = t.history(period="2d", interval="15m")
        d1h = t.history(period="5d", interval="1h")
        dd = t.history(period="100d", interval="1d")

        if dd.empty or d1h.empty: return None

        curr_p = dd['Close'].iloc[-1]

        # --- AI METHODE 1: Trend Regressie (Score op basis van 3-daagse forecast) ---
        y = dd['Close'].tail(30).values.reshape(-1, 1)
        X = np.array(range(len(y))).reshape(-1, 1)
        model = LinearRegression().fit(X, y)
        ai_pred_3d = float(model.predict(np.array([[len(y) + 3]]))[0][0])
        ai_trend_bullish = ai_pred_3d > curr_p

        # --- AI METHODE 2: Momentum Score (0-100%) ---
        # We berekenen hoe sterk de huidige versnelling is
        short_mom = dd['Close'].pct_change(3).iloc[-1]
        long_mom = dd['Close'].pct_change(10).iloc[-1]
        
        # De momentum score is hoog als short-term momentum positief is EN sterker dan long-term
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
            "ticker": ticker, "price": curr_p, 
            "ai_mom": mom_val, # De nieuwe losse score
            "score1h": score_1h, 
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

# Tabel Headers inclusief AI Momentum
cols = st.columns([1, 1, 1.2, 1.2, 1, 2])
names = ["Ticker", "Prijs", "AI Momentum", "1u Score", "Safe Entry", "Eindoordeel"]
for col, name in zip(cols, names): col.write(f"**{name}**")

for t in tickers:
    d = analyze_ticker(t)
    if d:
        r = st.columns([1, 1, 1.2, 1.2, 1, 2])
        r[0].write(f"**{d['ticker']}**")
        r[1].write(f"${d['price']:.2f}")
        
        # AI Momentum los weergegeven
        mom_col = "#00ff88" if d['ai_mom'] == 100 else ("#7fff00" if d['ai_mom'] == 50 else "#ff4b4b")
        r[2].markdown(f"<span style='color:{mom_col}; font-weight:bold;'>{d['ai_mom']}%</span>", unsafe_allow_html=True)
        
        # 1u Score
        c1h = "#00ff88" if d['score1h'] == 100 else ("#7fff00" if d['score1h'] == 50 else "#ff4b4b")
        r[3].markdown(f"<span style='color:{c1h}'>{d['score1h']}%</span>", unsafe_allow_html=True)
        
        r[4].write("✅" if d['safe'] else "❌")
        r[5].markdown(f"<span style='color:{d['color']}; font-weight:bold;'>{d['status']}</span>", unsafe_allow_html=True)









