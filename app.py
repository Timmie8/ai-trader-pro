import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import os

# --- OPSLAG ---
def save_list(watchlist):
    with open("multi_tf_v2.txt", "w") as f:
        f.write(",".join(watchlist))

def load_list():
    if os.path.exists("multi_tf_v2.txt"):
        with open("multi_tf_v2.txt", "r") as f:
            data = f.read().strip()
            return [t.strip().upper() for t in data.split(",") if t.strip()]
    return ["AAPL", "NVDA", "TSLA"]

# 1. Dashboard Config
st.set_page_config(page_title="AI Multi-TF Pro", layout="wide")
st.markdown("<style>.stApp { background-color: #0b1117; color: #ffffff; }</style>", unsafe_allow_html=True)

# 2. Robuuste Data Analyse
def get_clean_data(ticker, p, i):
    try:
        # We gebruiken yf.Ticker().history omdat dit stabieler is dan download()
        df = yf.Ticker(ticker).history(period=p, interval=i)
        return df if not df.empty else None
    except:
        return None

def analyze_ticker(ticker):
    # Haal 3 lagen data op
    d15 = get_clean_data(ticker, "5d", "15m")
    d1h = get_clean_data(ticker, "15d", "6h") # 1h data is soms beperkt, 6h of 1h proberen
    dd = get_clean_data(ticker, "100d", "1d")

    if dd is None: return None # Basis data moet er zijn

    # --- SCORES ---
    def calc_score(df):
        if df is None or len(df) < 2: return 0
        c = df['Close'].iloc[-1]
        m = df['Close'].rolling(window=9).mean().iloc[-1]
        return 100 if c > m else 0

    s15 = calc_score(d15)
    s1h = calc_score(d1h)
    
    # --- SAFE ENTRY ---
    curr_p = dd['Close'].iloc[-1]
    prev_h = dd['High'].iloc[-2]
    safe = curr_p > prev_h
    
    # AI Trend
    y = dd['Close'].tail(20).values.reshape(-1, 1)
    X = np.array(range(len(y))).reshape(-1, 1)
    model = LinearRegression().fit(X, y)
    ai_p = float(model.predict(np.array([[len(y)+3]]))[0][0])
    ai_val = ((ai_p / curr_p) - 1) * 100

    # Status
    if safe and s1h == 100 and s15 == 100: stat, col = "🚀 STRONG BUY", "#00ff88"
    elif safe: stat, col = "✅ MILD BUY", "#7fff00"
    elif s15 == 100: stat, col = "👀 WATCH (15m Up)", "#d29922"
    else: stat, col = "❌ WAIT", "#8b949e"

    return {"T": ticker, "P": curr_p, "H": prev_h, "15": s15, "1H": s1h, "S": stat, "C": col, "AI": ai_val, "SAFE": safe}

# 3. Sidebar
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = load_list()

with st.sidebar:
    st.header("Watchlist")
    new_t = st.text_input("Ticker(s) toevoegen (bijv: AAPL, BTC-USD)")
    if st.button("Toevoegen"):
        for t in new_t.split(","):
            if t.strip() not in st.session_state.watchlist:
                st.session_state.watchlist.append(t.strip().upper())
        save_list(st.session_state.watchlist)
        st.rerun()
    if st.button("Lijst wissen"):
        st.session_state.watchlist = []
        save_list([])
        st.rerun()

# 4. Main UI
st.title("🏹 AI Multi-Timeframe Terminal")

if not st.session_state.watchlist:
    st.warning("Voeg tickers toe in de sidebar om te beginnen.")
else:
    # Tabel Headers
    h_cols = st.columns([1, 1, 1, 1, 1, 2, 1])
    h_names = ["Ticker", "Prijs", "15m Score", "1h Score", "Safe Entry", "Advies", "AI 3D"]
    for col, name in zip(h_cols, h_names): col.write(f"**{name}**")

    for ticker in st.session_state.watchlist:
        with st.spinner(f'Laden van {ticker}...'):
            d = analyze_ticker(ticker)
            if d:
                r = st.columns([1, 1, 1, 1, 1, 2, 1])
                r[0].write(f"**{d['T']}**")
                r[1].write(f"${d['P']:.2f}")
                r[2].write(f"{d['15']}%")
                r[3].write(f"{d['1H']}%")
                r[4].write("✅" if d['SAFE'] else "❌")
                r[5].markdown(f"<span style='color:{d['C']}; font-weight:bold;'>{d['S']}</span>", unsafe_allow_html=True)
                r[6].write(f"{d['AI']:+.1f}%")
            else:
                st.error(f"Geen data gevonden voor {ticker}. Controleer de ticker-naam.")






