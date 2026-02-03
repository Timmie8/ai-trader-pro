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

        # --- STAP 1: AI METHODE 1 (Regressie - Lange termijn verwachting) ---
        y = dd['Close'].tail(30).values.reshape(-1, 1)
        X = np.array(range(len(y))).reshape(-1, 1)
        model = LinearRegression().fit(X, y)
        ai_pred_3d = float(model.predict(np.array([[len(y) + 3]]))[0][0])
        ai_trend_bullish = ai_pred_3d > curr_p
        ai_pct = ((ai_pred_3d / curr_p) - 1) * 100

        # --- STAP 2: AI METHODE 2 (Momentum Ensemble - Sterkte van de golf) ---
        short_mom = dd['Close'].pct_change(3).iloc[-1]
        long_mom = dd['Close'].pct_change(10).iloc[-1]
        ai_mom_bullish = short_mom > long_mom

        # --- STAP 3: TECHNISCHE ANALYSE (1U WEERT ZWAARST) ---
        # 1-uurs score (60% van techniek)
        score_1h = 0
        ema9_1h = d1h['Close'].ewm(span=9).mean().iloc[-1]
        if d1h['Close'].iloc[-1] > ema9_1h: score_1h += 50
        if d1h['Close'].iloc[-1] > d1h['Close'].iloc[-2]: score_1h += 50
        
        # 15-minuten score (40% van techniek)
        score_15m = 0
        if not d15.empty:
            if d15['Close'].iloc[-1] > d15['Close'].ewm(span=9).mean().iloc[-1]: score_15m += 100

        # --- BESLUITVORMING ---
        ai_is_goed = ai_trend_bullish and ai_mom_bullish
        tech_is_goed = score_1h >= 50 # We willen minimaal een positieve 1-uurs trend
        safe_entry = curr_p > dd['High'].iloc[-2]

        if ai_is_goed and tech_is_goed and safe_entry:
            stat, col = "🚀 STRONG BUY (AI + TECH)", "#00ff88"
        elif ai_is_goed and tech_is_goed:
            stat, col = "💎 AI APPROVED (Wait for Breakout)", "#7fff00"
        elif ai_is_goed:
            stat, col = "🔍 AI POSITIVE (Tech Weak)", "#d29922"
        elif tech_is_goed:
            stat, col = "⚠️ TECH ONLY (AI Negative)", "#fca5a5"
        else:
            stat, col = "❌ AVOID", "#8b949e"

        return {
            "ticker": ticker, "price": curr_p, 
            "ai_status": "GOED" if ai_is_goed else "MATIG",
            "score1h": score_1h, "score15": score_15m,
            "status": stat, "color": col, "ai_val": ai_pct, "safe": safe_entry
        }
    except:
        return None

# --- UI ---
st.title("🏹 AI-First Precision Trader")
st.subheader("Besluitvorming: AI filtert het aandeel -> 1u Analyse bepaalt de kracht")

watchlist = ["AAPL", "NVDA", "TSLA", "SGMT", "CENX", "AMD"]
tickers_input = st.text_input("Tickers", ",".join(watchlist))
tickers = [x.strip().upper() for x in tickers_input.split(",") if x.strip()]

if st.button("🔄 Analyseer Markt"):
    st.rerun()

cols = st.columns([1, 1, 1, 1, 1, 1, 2])
names = ["Ticker", "Prijs", "AI Filter", "1u Score (Zwaar)", "15m Score", "Safe Entry", "Eindoordeel"]
for col, name in zip(cols, names): col.write(f"**{name}**")

for t in tickers:
    d = analyze_ticker(t)
    if d:
        r = st.columns([1, 1, 1, 1, 1, 1, 2])
        r[0].write(f"**{d['ticker']}**")
        r[1].write(f"${d['price']:.2f}")
        
        # AI Filter kleur
        ai_col = "#00ff88" if d['ai_status'] == "GOED" else "#ff4b4b"
        r[2].markdown(f"<span style='color:{ai_col}'>{d['ai_status']}</span>", unsafe_allow_html=True)
        
        # 1u Score (Zwaar meegewogen)
        c1h = "#00ff88" if d['score1h'] >= 100 else ("#7fff00" if d['score1h'] >= 50 else "#ff4b4b")
        r[3].markdown(f"<span style='color:{c1h}'>{d['score1h']}%</span>", unsafe_allow_html=True)
        
        r[4].write(f"{d['score15']}%")
        r[5].write("✅" if d['safe'] else "❌")
        r[6].markdown(f"<span style='color:{d['color']}; font-weight:bold;'>{d['status']}</span>", unsafe_allow_html=True)








