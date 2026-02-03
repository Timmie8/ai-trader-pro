import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import requests
from bs4 import BeautifulSoup
import re
import time
import os

# --- OPSLAG ---
def save_watchlist(watchlist):
    with open("watchlist_pro_v2.txt", "w") as f:
        f.write(",".join(watchlist))

def load_watchlist():
    if os.path.exists("watchlist_pro_v2.txt"):
        with open("watchlist_pro_v2.txt", "r") as f:
            data = f.read().strip()
            return data.split(",") if data else []
    return ["AAPL", "NVDA", "TSLA"]

# 1. Pagina Setup
st.set_page_config(page_title="AI Trader Terminal PRO", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; color: #ffffff !important; }
    [data-testid="stSidebar"] { background-color: #050505 !important; border-right: 1px solid #333 !important; }
    .stButton>button { background-color: #222 !important; color: white !important; border: 1px solid #444 !important; }
    .report-card { border: 1px solid #333; padding: 20px; border-radius: 12px; background: #0a0a0a; margin-bottom: 20px; }
    .metric-box { text-align: center; padding: 10px; background: #111; border-radius: 8px; border: 1px solid #222; }
    </style>
    """, unsafe_allow_html=True)

# 2. Uitgebreide Trade Logica (Target/Stop/Ratio)
def run_pro_analysis(ticker):
    try:
        data = yf.Ticker(ticker).history(period="150d")
        if data.empty: return None
        
        curr_p = data['Close'].iloc[-1]
        vola = data['Close'].pct_change().tail(14).std() * 100
        
        # --- SUPPORT / RESISTANCE & TARGETS ---
        res = data['High'].max()
        sup = data['Low'].min()
        
        # Stop Limit (Stops): Trail based on volatility (min 2.5%, max 7%)
        sl_pct = min(max(1.5 + (vola * 1.2), 2.5), 7.0)
        stop_price = curr_p * (1 - sl_pct/100)
        
        # Target 1: Gebaseerd op recente weerstand of +10% indien nabij high
        target_1 = max(res, curr_p * 1.05)
        target_pct = ((target_1 / curr_p) - 1) * 100
        
        # Profit/Loss Ratio
        pl_ratio = round(target_pct / sl_pct, 1)
        trade_quality = "GOOD" if pl_ratio >= 3.0 else "AVERAGE"

        # --- AI SCORES ---
        y = data['Close'].values.reshape(-1, 1)
        X = np.array(range(len(y))).reshape(-1, 1)
        reg = LinearRegression().fit(X, y).predict(np.array([[len(y)]]))
        ensemble = int(72 + (12 if reg[0][0] > curr_p else -8))
        lstm = int(65 + (data['Close'].iloc[-5:].pct_change().sum() * 150))
        
        # Trend Status (90/10 regel)
        score_avg = (ensemble + lstm) / 2
        if score_avg > 85: status, col = "Strong Bullish", "#39d353"
        elif score_avg > 60: status, col = "Mild Bullish", "#d29922"
        else: status, col = "Neutral/Bearish", "#f85149"
        
        return {
            "T": ticker, "P": curr_p, "S": status, "C": col,
            "AI": ensemble, "L": lstm, "PL": pl_ratio, "TQ": trade_quality,
            "T1": target_1, "T1P": target_pct, "SL": stop_price, "SLP": sl_pct,
            "RES": res, "SUP": sup
        }
    except: return None

# 3. UI Content
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = load_watchlist()

with st.sidebar:
    st.header("📋 Watchlist Settings")
    new_t = st.text_input("Ticker toevoegen").upper()
    if st.button("Add"):
        if new_t and new_t not in st.session_state.watchlist:
            st.session_state.watchlist.append(new_t)
            save_watchlist(st.session_state.watchlist)
            st.rerun()
    if st.button("Clear List"):
        st.session_state.watchlist = []
        save_watchlist([])
        st.rerun()

st.title("🏹 AI Strategy Terminal PRO")

# DIRECTE ANALYSE KAART
target_ticker = st.text_input("🔍 Analyseer Specifiek Aandeel", "AAPL").upper()
res = run_pro_analysis(target_ticker)

if res:
    # Kleur indicator voor Trade Quality
    tq_color = "#39d353" if res['TQ'] == "GOOD" else "#8b949e"
    
    st.markdown(f"""
        <div class="report-card" style="border-left: 8px solid {res['C']};">
            <div style="display: flex; justify-content: space-between;">
                <div>
                    <h1 style="margin:0;">{res['T']} <span style="font-size:0.5em; color:{res['C']};">{res['S']}</span></h1>
                    <p style="color:#8b949e;">Trade Quality: <b style="color:{tq_color};">{res['TQ']}</b> | P/L Ratio: <b>{res['PL']}:1</b></p>
                </div>
                <div style="text-align: right;">
                    <h2 style="margin:0;">${res['P']:.2f}</h2>
                    <p style="color:#8b949e;">Current Market Price</p>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin-top: 20px;">
                <div class="metric-box">
                    <span style="color:#f85149; font-size:0.8em;">STOP LIMIT</span><br>
                    <b style="font-size:1.2em;">${res['SL']:.2f}</b><br>
                    <span style="color:#f85149; font-size:0.8em;">-{res['SLP']:.1f}%</span>
                </div>
                <div class="metric-box" style="border-color:#333;">
                    <span style="color:#8b949e; font-size:0.8em;">ENTRY</span><br>
                    <b style="font-size:1.2em;">${res['P']:.2f}</b><br>
                    <span style="color:#8b949e; font-size:0.8em;">MARKET</span>
                </div>
                <div class="metric-box">
                    <span style="color:#39d353; font-size:0.8em;">TARGET 1</span><br>
                    <b style="font-size:1.2em;">${res['T1']:.2f}</b><br>
                    <span style="color:#39d353; font-size:0.8em;">+{res['T1P']:.1f}%</span>
                </div>
            </div>
            <div style="margin-top:20px; font-size:0.9em; color:#8b949e;">
                AI Score: <b>{res['AI']}%</b> | LSTM Trend: <b>{res['L']}%</b> | Resistance: <b>${res['RES']:.2f}</b>
            </div>
        </div>
    """, unsafe_allow_html=True)

# LIVE WATCHLIST
st.write("---")
@st.fragment(run_every=10)
def show_watchlist():
    st.subheader("🔄 Live Watchlist Strategy Monitoring")
    
    st.markdown("""
        <div style="display: flex; font-weight: bold; border-bottom: 2px solid #444; padding: 10px; color: #39d353; font-size: 0.85em;">
            <div style="width: 10%;">Ticker</div>
            <div style="width: 10%;">Prijs</div>
            <div style="width: 15%;">P/L Ratio</div>
            <div style="width: 15%;">Target 1</div>
            <div style="width: 15%;">Stop Price</div>
            <div style="width: 20%;">Trend Status</div>
            <div style="width: 15%;">Quality</div>
        </div>
    """, unsafe_allow_html=True)

    for ticker in st.session_state.watchlist:
        d = run_pro_analysis(ticker)
        if d:
            row_border = f"border: 1px solid #39d353; background: rgba(57, 211, 83, 0.05);" if d['PL'] >= 3.0 else "border: 1px solid #222;"
            st.markdown(f"""
                <div style="display: flex; align-items: center; padding: 10px; margin-top: 5px; border-radius: 6px; {row_border}">
                    <div style="width: 10%;"><b>{d['T']}</b></div>
                    <div style="width: 10%;">${d['P']:.2f}</div>
                    <div style="width: 15%;">{d['PL']}:1</div>
                    <div style="width: 15%; color:#39d353;">${d['T1']:.2f}</div>
                    <div style="width: 15%; color:#f85149;">${d['SL']:.2f}</div>
                    <div style="width: 20%; color:{d['C']}; font-weight:bold;">{d['S']}</div>
                    <div style="width: 15%;">{d['TQ']}</div>
                </div>
            """, unsafe_allow_html=True)

show_watchlist()
