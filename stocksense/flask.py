import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json
import os
import time

# User data file
USER_DATA_FILE = "users.json"

# Load/save users
def load_users():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(users, f)

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'users' not in st.session_state:
    st.session_state.users = load_users()
if 'candle_data' not in st.session_state:
    st.session_state.candle_data = pd.DataFrame(columns=["time", "open", "high", "low", "close"])
if 'trading_active' not in st.session_state:
    st.session_state.trading_active = False
if 'symbol' not in st.session_state:
    st.session_state.symbol = "AAPL"
if 'last_price' not in st.session_state:
    st.session_state.last_price = {}
if 'sold_price' not in st.session_state:
    st.session_state.sold_price = {}
if 'last_update_time' not in st.session_state:
    st.session_state.last_update_time = 0
if 'stock_data_cache' not in st.session_state:
    st.session_state.stock_data_cache = {}
if 'company_name_cache' not in st.session_state:
    st.session_state.company_name_cache = {}

# Fetch stock data from yfinance with caching
def get_stock_data(symbol, period="1d", interval="1m"):
    cache_key = f"{symbol}_{period}_{interval}"
    current_time = time.time()
    
    if cache_key in st.session_state.stock_data_cache:
        cached_data, timestamp = st.session_state.stock_data_cache[cache_key]
        if current_time - timestamp < 60:
            return cached_data

    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period=period, interval=interval)
        if df.empty:
            st.warning(f"No data for {symbol}. Using mock data. 📉")
            df = pd.DataFrame([{
                "time": datetime.now(),
                "open": 100.0,
                "high": 100.5,
                "low": 99.5,
                "close": 100.2
            }])
        else:
            df = df.reset_index().rename(columns={"Datetime": "time", "Open": "open", "High": "high", "Low": "low", "Close": "close"})
        st.session_state.stock_data_cache[cache_key] = (df, current_time)
        return df
    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {str(e)} 🚨")
        return pd.DataFrame([{
            "time": datetime.now(),
            "open": 100.0,
            "high": 100.5,
            "low": 99.5,
            "close": 100.2
        }])

# Fetch company name with caching
def get_company_name(symbol):
    if symbol in st.session_state.company_name_cache:
        return st.session_state.company_name_cache[symbol]

    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        company_name = info.get("longName", "Unknown Company")
        st.session_state.company_name_cache[symbol] = company_name
        return company_name
    except Exception as e:
        st.error(f"Error fetching company name for {symbol}: {str(e)} 🚨")
        st.session_state.company_name_cache[symbol] = "Unknown Company"
        return "Unknown Company"

# Simulate real-time candle updates every second
def update_candle_data(symbol):
    data = get_stock_data(symbol, period="1d", interval="1m")
    if not data.empty:
        latest_candle = data.iloc[-1]
        volatility = (data["high"].max() - data["low"].min()) * 0.1 or 1.0
        new_open = latest_candle["close"]
    else:
        new_open = st.session_state.last_price.get(symbol, 100.0)
        volatility = 1.0

    new_high = new_open + np.random.uniform(0, volatility)
    new_low = new_open - np.random.uniform(0, volatility)
    new_close = new_open + np.random.uniform(-volatility * 0.5, volatility * 0.5)
    
    new_candle = {
        "time": datetime.now(),
        "open": new_open,
        "high": new_high,
        "low": new_low,
        "close": new_close
    }
    st.session_state.candle_data = pd.concat(
        [st.session_state.candle_data, pd.DataFrame([new_candle])], ignore_index=True
    )
    if len(st.session_state.candle_data) > 60:
        st.session_state.candle_data = st.session_state.candle_data.iloc[-60:]
    st.session_state.last_price[symbol] = new_close

# Login Page
def login():
    st.markdown("""
        <style>
        body {
            background: linear-gradient(45deg, #1a1a2e, #16213e, #2a1a3e, #1a2e2a);
            background-size: 400%;
            animation: gradientShift 15s ease infinite;
            overflow: auto;
            font-family: 'Arial', sans-serif;
        }
        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        .video-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
            z-index: -2;
            opacity: 0.3;
        }
        .ticker-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
            z-index: -1;
        }
        .ticker {
            position: absolute;
            top: 20px;
            white-space: nowrap;
            font-size: 16px;
            color: #00ffcc;
            opacity: 0.3;
            animation: tickerMove 30s linear infinite;
        }
        @keyframes tickerMove {
            0% { transform: translateX(100%); }
            100% { transform: translateX(-100%); }
        }
        @keyframes fadeIn {
            0% { opacity: 0; transform: translateY(-20px); }
            100% { opacity: 1; transform: translateY(0); }
        }
        @keyframes float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
            100% { transform: translateY(0px); }
        }
        .login-title {
            color: #00ffcc;
            font-size: 36px;
            font-weight: bold;
            text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
            margin-bottom: 10px;
            animation: typing 2s steps(30, end), blink-caret 0.75s step-end infinite;
            white-space: nowrap;
            overflow: hidden;
            border-right: 3px solid #00ffcc;
        }
        @keyframes typing {
            from { width: 0; }
            to { width: 100%; }
        }
        @keyframes blink-caret {
            from, to { border-color: transparent; }
            50% { border-color: #00ffcc; }
        }
        .welcome-text {
            color: #e0e0e0;
            font-size: 18px;
            margin: 20px auto;
            max-width: 600px;
            animation: slideIn 1s ease-in-out;
        }
        .features-wrapper {
            width: 100%;
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }
        .features-section {
            display: flex !important;
            flex-wrap: nowrap !important;
            justify-content: space-between !important;
            gap: 20px !important;
            margin: 40px 0 !important;
            min-width: 1000px !important;
            box-sizing: border-box !important;
        }
        .feature-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 20px;
            flex: 0 0 220px !important;
            text-align: center;
            animation: slideIn 1.5s ease-in-out;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            box-sizing: border-box !important;
        }
        .feature-card:hover {
            transform: scale(1.05);
            box-shadow: 0 0 15px rgba(0, 255, 255, 0.3);
        }
        .feature-icon {
            font-size: 30px;
            color: #00ffcc;
            margin-bottom: 10px;
        }
        .feature-title {
            color: #ffffff;
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .feature-desc {
            color: #b0b0b0;
            font-size: 14px;
        }
        .testimonials-section {
            margin: 40px 0;
            padding: 0 20px;
        }
        .testimonial {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 20px;
            margin: 20px auto;
            max-width: 600px;
            animation: slideIn 2s ease-in-out;
            border-left: 4px solid #00ffcc;
        }
        .testimonial-text {
            color: #e0e0e0;
            font-size: 16px;
            font-style: italic;
            margin-bottom: 10px;
        }
        .testimonial-author {
            color: #00ffcc;
            font-size: 14px;
            text-align: right;
            font-weight: bold;
        }
        .cta-section {
            margin: 40px 0;
            text-align: center;
        }
        .cta-text {
            color: #e0e0e0;
            font-size: 18px;
            margin-bottom: 10px;
        }
        .stButton > button#cta-button {
            background: #ff00ff;
            color: #fff;
            padding: 10px 20px;
            border: none;
            border-radius: 25px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .stButton > button#cta-button:hover {
            background: #cc00cc;
            box-shadow: 0 0 15px #ff00ff;
            transform: scale(1.1);
        }
        .why-traderiser-section {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 30px;
            margin: 20px auto;
            max-width: 800px;
            text-align: center;
            animation: fadeIn 1s ease-in-out;
            backdrop-filter: blur(10px);
            box-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
        }
        .why-traderiser-title {
            color: #00ffcc;
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 20px;
            text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
        }
        .why-traderiser-text {
            color: #e0e0e0;
            font-size: 16px;
            margin-bottom: 20px;
            line-height: 1.5;
        }
        .why-traderiser-list {
            text-align: left;
            color: #b0b0b0;
            font-size: 14px;
            margin: 0 auto;
            max-width: 600px;
            list-style-type: none;
            padding: 0;
        }
        .why-traderiser-list li {
            margin: 10px 0;
            position: relative;
            padding-left: 25px;
        }
        .why-traderiser-list li:before {
            content: "✔";
            color: #00ffcc;
            position: absolute;
            left: 0;
            font-size: 16px;
        }
        .why-traderiser-closing {
            color: #e0e0e0;
            font-size: 16px;
            margin-top: 20px;
            font-style: italic;
        }
        .market-stats {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin: 40px 0;
            flex-wrap: wrap;
        }
        .stat-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 15px;
            width: 150px;
            text-align: center;
            animation: slideIn 1.5s ease-in-out;
        }
        .stat-title {
            color: #00ffcc;
            font-size: 14px;
        }
        .stat-value {
            color: #ffffff;
            font-size: 16px;
            font-weight: bold;
        }
        .user-counter {
            text-align: center;
            margin: 40px 0;
            color: #e0e0e0;
            font-size: 18px;
            animation: fadeIn 2s ease-in-out;
        }
        .counter-number {
            color: #00ffcc;
            font-weight: bold;
            display: inline-block;
            animation: countUp 3s ease-in-out;
        }
        @keyframes countUp {
            0% { transform: translateY(20px); opacity: 0; }
            100% { transform: translateY(0); opacity: 1; }
        }
        .login-input {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid #00ffcc;
            border-radius: 5px;
            padding: 10px;
            color: #fff;
            width: 100%;
            margin-bottom: 15px;
            transition: all 0.3s ease;
        }
        .login-input:hover {
            border-color: #ff00ff;
            box-shadow: 0 0 15px rgba(255, 0, 255, 0.5);
        }
        .login-input:focus {
            outline: none;
            box-shadow: 0 0 10px #00ffcc;
        }
        .login-button {
            background: #00ffcc;
            color: #1a1a2e;
            padding: 10px 20px;
            border: none;
            border-radius: 25px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            margin: 5px;
            width: 120px;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(0, 255, 204, 0.7); }
            70% { transform: scale(1.05); box-shadow: 0 0 0 10px rgba(0, 255, 204, 0); }
            100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(0, 255, 204, 0); }
        }
        .login-button:hover {
            background: #00ccaa;
            box-shadow: 0 0 15px #00ffcc;
            transform: scale(1.1);
        }
        .popup {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(0, 255, 204, 0.1));
            border-radius: 15px;
            padding: 40px;
            box-shadow: 0 0 30px rgba(0, 255, 255, 0.5);
            text-align: center;
            animation: popupFadeIn 0.5s ease-in-out;
            backdrop-filter: blur(10px);
            z-index: 1000;
            width: 90%;
            max-width: 400px;
        }
        .user-popup {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(0, 255, 204, 0.1));
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 0 30px rgba(0, 255, 255, 0.5);
            text-align: center;
            animation: popupFadeIn 0.5s ease-in-out;
            backdrop-filter: blur(10px);
            z-index: 1001;
            width: 90%;
            max-width: 400px;
        }
        @keyframes popupFadeIn {
            0% { opacity: 0; transform: translate(-50%, -60%) scale(0.9); }
            100% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
        }
        .popup-title {
            color: #00ffcc;
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 15px;
            text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
        }
        .popup-text {
            color: #e0e0e0;
            font-size: 16px;
            margin-bottom: 20px;
            line-height: 1.5;
        }
        .user-popup-text {
            color: #e0e0e0;
            font-size: 18px;
            line-height: 1.5;
        }
        .popup-buttons {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 20px;
        }
        .stButton > button#popup-register-btn {
            background: #ff00ff;
            color: #fff;
            padding: 12px 24px;
            border: none;
            border-radius: 25px;
            font-weight: bold;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s ease;
            animation: pulse 2s infinite;
        }
        .stButton > button#popup-register-btn:hover {
            background: #cc00cc;
            box-shadow: 0 0 15px #ff00ff;
            transform: scale(1.1);
        }
        .stButton > button#popup-close-btn {
            background: #ff5555;
            color: #fff;
            padding: 8px 16px;
            border: none;
            border-radius: 15px;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .stButton > button#popup-close-btn:hover {
            background: #cc4444;
            box-shadow: 0 0 10px #ff5555;
        }
        .footer {
            color: #888;
            font-size: 12px;
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.05);
        }
        .footer a {
            color: #00ffcc;
            text-decoration: none;
            margin: 0 10px;
        }
        .footer a:hover {
            text-decoration: underline;
        }
        @keyframes slideIn {
            0% { transform: translateX(-50px); opacity: 0; }
            100% { transform: translateX(0); opacity: 1; }
        }
        @media (max-width: 1000px) {
            .features-section {
                flex-wrap: wrap !important;
                justify-content: center !important;
                min-width: 0 !important;
            }
            .feature-card {
                flex: 0 0 45% !important;
                max-width: 300px;
                margin-bottom: 20px;
                margin-left:26px;
            }
        }
        @media (max-width: 768px) {
            .features-section {
                flex-direction: column !important;
                align-items: center !important;
                min-width: 0 !important;
            }
            .feature-card {
                flex: 0 0 100% !important;
                max-width: 300px !important;
                margin-bottom: 20px;
                padding: 15px !important;
            }
            .feature-icon {
                font-size: 24px !important;
            }
            .feature-title {
                font-size: 16px !important;
            }
            .feature-desc {
                font-size: 12px !important;
            }
            .market-stats {
                flex-direction: column !important;
                align-items: center !important;
            }
            .stat-card {
                width: 100% !important;
                max-width: 200px !important;
                margin-bottom: 20px;
                padding: 10px !important;
            }
            .stat-title {
                font-size: 12px !important;
            }
            .stat-value {
                font-size: 14px !important;
            }
            .login-container {
                max-width: 90% !important;
                padding: 20px !important;
            }
            .login-title {
                font-size: 28px !important;
            }
            .welcome-text {
                font-size: 16px !important;
                padding: 0 10px !important;
                max-width: 90% !important;
            }
            .popup, .user-popup {
                width: 90% !important;
                max-width: 320px !important;
                padding: 20px !important;
            }
            .popup-title {
                font-size: 24px !important;
            }
            .popup-text, .user-popup-text {
                font-size: 14px !important;
            }
            .stButton > button#popup-register-btn {
                padding: 10px 20px !important;
                font-size: 14px !important;
            }
            .stButton > button#popup-close-btn {
                padding: 6px 12px !important;
                font-size: 12px !important;
            }
            .popup-buttons {
                gap: 8px !important;
            }
            .user-counter {
                font-size: 16px !important;
            }
            .counter-number {
                font-size: 18px !important;
            }
            .cta-text {
                font-size: 16px !important;
            }
            .stButton > button#cta-button {
                padding: 8px 16px !important;
                font-size: 14px !important;
            }
            .why-traderiser-section {
                padding: 20px !important;
                max-width: 90% !important;
            }
            .why-traderiser-title {
                font-size: 24px !important;
            }
            .why-traderiser-text {
                font-size: 14px !important;
            }
            .why-traderiser-list {
                font-size: 12px !important;
            }
            .why-traderiser-closing {
                font-size: 14px !important;
            }
            .testimonial {
                max-width: 90% !important;
                padding: 15px !important;
            }
            .testimonial-text {
                font-size: 14px !important;
            }
            .testimonial-author {
                font-size: 12px !important;
            }
            .footer {
                font-size: 10px !important;
                padding: 15px !important;
            }
            .footer a {
                margin: 0 5px !important;
            }
            .login-button {
                width: 100px !important;
                padding: 8px 16px !important;
                font-size: 14px !important;
            }
        }
        @media (max-width: 480px) {
            .popup, .user-popup {
                width: 95% !important;
                max-width: 280px !important;
                padding: 15px !important;
            }
            .popup-title {
                font-size: 20px !important;
            }
            .popup-text, .user-popup-text {
                font-size: 12px !important;
            }
            .stButton > button#popup-register-btn {
                padding: 8px 16px !important;
                font-size: 12px !important;
            }
            .stButton > button#popup-close-btn {
                padding: 5px 10px !important;
                font-size: 10px !important;
            }
            .popup-buttons {
                gap: 6px !important;
            }
            .login-title {
                font-size: 24px !important;
            }
            .welcome-text {
                font-size: 14px !important;
            }
            .login-container {
                padding: 15px !important;
            }
            .feature-card {
                padding: 10px !important;
            }
            .feature-icon {
                font-size: 20px !important;
            }
            .feature-title {
                font-size: 14px !important;
            }
            .feature-desc {
                font-size: 10px !important;
            }
            .stat-card {
                padding: 8px !important;
            }
            .stat-title {
                font-size: 10px !important;
            }
            .stat-value {
                font-size: 12px !important;
            }
            .user-counter {
                font-size: 14px !important;
            }
            .counter-number {
                font-size: 16px !important;
            }
            .cta-text {
                font-size: 14px !important;
            }
            .stButton > button#cta-button {
                padding: 6px 12px !important;
                font-size: 12px !important;
            }
            .why-traderiser-section {
                padding: 15px !important;
            }
            .why-traderiser-title {
                font-size: 20px !important;
            }
            .why-traderiser-text {
                font-size: 12px !important;
            }
            .why-traderiser-list {
                font-size: 10px !important;
            }
            .why-traderiser-closing {
                font-size: 12px !important;
            }
            .testimonial {
                padding: 10px !important;
            }
            .testimonial-text {
                font-size: 12px !important;
            }
            .testimonial-author {
                font-size: 10px !important;
            }
            .footer {
                font-size: 8px !important;
                padding: 10px !important;
            }
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js"></script>
        <script>
        confetti({
            particleCount: 100,
            spread: 70,
            origin: { y: 0.6 }
        });
        </script>
    """, unsafe_allow_html=True)

    st.markdown("""
        <video class="video-bg" autoplay loop muted playsinline>
            <source src="/stocksense/static/stock.mp4" type="video/mp4">
            Your browser does not support the video tag.
        </video>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="ticker-bg">
            <div class="ticker">
                AAPL +2.3% • TSLA -1.5% • GOOGL +0.8% • MSFT -0.2% • AMZN +1.7% • NVDA -0.9% • META +1.2% • 
                AAPL +2.3% • TSLA -1.5% • GOOGL +0.8% • MSFT -0.2% • AMZN +1.7% • NVDA -0.9% • META +1.2%
            </div>
        </div>
    """, unsafe_allow_html=True)

    if 'show_popup' not in st.session_state:
        st.session_state.show_popup = True

    if st.session_state.show_popup:
        popup_container = st.container()
        with popup_container:
            st.markdown("""
                <div class="popup">
                    <h2 class="popup-title">🎉 Welcome to TradeRiser!</h2>
                    <p class="popup-text">Register now and get a $10,000 bonus to start trading!</p>
                    <div class="popup-buttons">
            """, unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Register Now 🚀", key="popup-register-btn"):
                    st.session_state.show_register = True
                    st.session_state.show_popup = False
                    st.rerun()
            with col2:
                if st.button("Close", key="popup-close-btn", type="secondary"):
                    st.session_state.show_popup = False
                    st.rerun()
            st.markdown("""
                    </div>
                </div>
            """, unsafe_allow_html=True)

    if 'show_user_popup' not in st.session_state:
        st.session_state.show_user_popup = False
    if 'user_popup_message' not in st.session_state:
        st.session_state.user_popup_message = ""

    if st.session_state.show_user_popup:
        st.markdown(f"""
            <div class="user-popup" id="user-popup">
                <p class="user-popup-text">{st.session_state.user_popup_message}</p>
            </div>
            <script>
                setTimeout(function() {{
                    var popup = document.getElementById("user-popup");
                    if (popup) {{
                        popup.style.display = "none";
                    }}
                }}, 4000);
            </script>
        """, unsafe_allow_html=True)
        st.session_state.show_user_popup = False

    st.markdown('<h1 class="login-title">🚀 TradeRiser: Login</h1>', unsafe_allow_html=True)
    st.markdown("""
        <div class="welcome-text">
            Welcome to TradeRiser, the ultimate platform for wealth creation! Trade stocks in real-time, 
            track your portfolio, and gain market insights to make smarter investment decisions. Join our 
            community of traders and start your journey to financial success today!
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="market-stats">
            <div class="stat-card">
                <div class="stat-title">S&P 500</div>
                <div class="stat-value">4,320.45 <span style="color: #00ff00;">+0.8%</span></div>
            </div>
            <div class="stat-card">
                <div class="stat-title">Dow Jones</div>
                <div class="stat-value">34,567.89 <span style="color: #ff0000;">-0.3%</span></div>
            </div>
            <div class="stat-card">
                <div class="stat-title">NASDAQ</div>
                <div class="stat-value">14,123.45 <span style="color: #00ff00;">+1.2%</span></div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="user-counter">
            Join <span class="counter-number">10,000+</span> Traders on TradeRiser!
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    username = st.text_input("Username 👤", key="login_username").strip()
    password = st.text_input("Password 🔒", type="password", key="login_password")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login 🔐"):
            users = st.session_state.users
            if username in users and users[username]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.show_user_popup = True
                st.session_state.user_popup_message = "Welcome Back! Start Trading 🚀📈"
                st.rerun()
            else:
                st.error("Invalid credentials 🚫")
    with col2:
        if st.button("Register 📝"):
            st.session_state.show_register = True
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="features-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="features-section">', unsafe_allow_html=True)
    st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📈</div>
            <div class="feature-title">Real-Time Trading</div>
            <div class="feature-desc">Trade stocks with live market data.</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">💼</div>
            <div class="feature-title">Portfolio Tracking</div>
            <div class="feature-desc">Monitor your investments effortlessly.</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <div class="feature-title">Market Insights</div>
            <div class="feature-desc">Get data-driven insights to succeed.</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">👥</div>
            <div class="feature-title">Community Support</div>
            <div class="feature-desc">Join a thriving trader community.</div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="testimonials-section">', unsafe_allow_html=True)
    st.markdown("""
        <div class="testimonial">
            <p class="testimonial-text">"TradeRiser helped me grow my portfolio by 30% in just 3 months!"</p>
            <p class="testimonial-author">- Sarah K., Active Trader</p>
        </div>
        <div class="testimonial">
            <p class="testimonial-text">"The real-time data and insights are a game-changer for my trading strategy."</p>
            <p class="testimonial-author">- Michael T., Investor</p>
        </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if 'show_why_traderiser' not in st.session_state:
        st.session_state.show_why_traderiser = False

    st.markdown("""
        <div class="cta-section">
            <p class="cta-text">Discover why TradeRiser is the best platform for traders!</p>
        </div>
    """, unsafe_allow_html=True)

    if st.button("Why TradeRiser? 🔍", key="cta-button"):
        st.session_state.show_why_traderiser = not st.session_state.show_why_traderiser

    if st.session_state.show_why_traderiser:
        st.markdown("""
            <div class="why-traderiser-section">
                <h2 class="why-traderiser-title">Why Choose TradeRiser?</h2>
                <p class="why-traderiser-text">
                    TradeRiser is designed to empower traders of all levels with the tools and insights needed to succeed in the stock market. 
                    Here’s why thousands of traders trust us:
                </p>
                <ul class="why-traderiser-list">
                    <li><strong>Real-Time Data:</strong> Access live market data to make informed decisions instantly.</li>
                    <li><strong>User-Friendly Interface:</strong> Navigate the platform with ease, whether you're a beginner or a pro.</li>
                    <li><strong>Advanced Analytics:</strong> Leverage powerful tools to analyze trends and predict market movements.</li>
                    <li><strong>Community Support:</strong> Join a vibrant community of traders to share strategies and insights.</li>
                    <li><strong>Secure Transactions:</strong> Trade with confidence knowing your data and funds are protected.</li>
                    <li><strong>24/7 Support:</strong> Get help whenever you need it with our dedicated support team.</li>
                </ul>
                <p class="why-traderiser-closing">
                    Start your trading journey with TradeRiser today and unlock your financial potential!
                </p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("""
        <div class="footer">
            <p>"The stock market is a device for transferring money from the impatient to the patient." - Warren Buffett</p>
            <p>
                <a href="#">About Us</a> | 
                <a href="#">Contact</a> | 
                <a href="#">Terms of Service</a> | 
                <a href="#">Privacy Policy</a>
            </p>
            <p>© 2025 TradeRiser. All rights reserved.</p>
        </div>
    """, unsafe_allow_html=True)

# Register
def register():
    st.markdown("""
        <style>
        .register-container {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 40px;
            box-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
            text-align: center;
            animation: fadeIn 1s ease-in-out;
            max-width: 400px;
            margin: 100px auto;
            backdrop-filter: blur(10px);
        }
        @media (max-width: 768px) {
            .register-container {
                max-width: 90% !important;
                padding: 20px !important;
            }
        }
        @media (max-width: 480px) {
            .register-container {
                max-width: 95% !important;
                padding: 15px !important;
            }
        }
        </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="register-container">', unsafe_allow_html=True)
    st.markdown('<h1 class="login-title">Register for TradeRiser 📝</h1>', unsafe_allow_html=True)
    username = st.text_input("New Username 👤")
    password = st.text_input("New Password 🔒", type="password")
    confirm_password = st.text_input("Confirm Password 🔑", type="password")
    if st.button("Register 📋"):
        users = st.session_state.users
        if username in users:
            st.error("Username already exists! 🚫")
        elif password != confirm_password:
            st.error("Passwords do not match! ⚠️")
        else:
            users[username] = {
                "password": password,
                "balance": 10000.0,
                "portfolio": {},
                "watchlist": [],
                "transactions": []
            }
            save_users(users)
            st.session_state.users = users
            st.success(f"Registered successfully! Welcome, {username}. You received a $10,000 bonus. 💰")
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.show_user_popup = True
            st.session_state.user_popup_message = "🎉 Congrats! $10,000 has been added to your account! 💰🚀"
            st.rerun()
    if st.button("Back to Login 🔙"):
        st.session_state.show_register = False
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Logout
def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.trading_active = False
    st.session_state.candle_data = pd.DataFrame(columns=["time", "open", "high", "low", "close"])
    st.session_state.last_update_time = 0
    st.session_state.stock_data_cache = {}
    st.session_state.company_name_cache = {}
    st.success("Logged out successfully! 👋")
    st.rerun()

# Calculate portfolio stats
def calculate_portfolio_stats(user_data):
    portfolio_value = 0.0
    total_shares = 0
    total_assets = 0
    net_profit_loss = 0.0
    portfolio_breakdown = []

    if user_data["portfolio"]:
        for symbol, details in user_data["portfolio"].items():
            current_price = st.session_state.last_price.get(symbol, get_stock_data(symbol).iloc[-1]["close"])
            asset_value = round(current_price * details["quantity"], 2)
            portfolio_value += asset_value
            total_shares += details["quantity"]
            total_assets += 1
            asset_profit_loss = round((current_price - details["avg_price"]) * details["quantity"], 2)
            net_profit_loss += asset_profit_loss
            portfolio_breakdown.append({
                "symbol": symbol,
                "quantity": details["quantity"],
                "avg_price": round(details["avg_price"], 2),
                "current_price": round(current_price, 2),
                "value": asset_value,
                "profit_loss": asset_profit_loss
            })

    net_profit_loss = round(net_profit_loss, 2)

    return {
        "portfolio_value": portfolio_value,
        "cash_balance": user_data["balance"],
        "total_shares": total_shares,
        "total_assets": total_assets,
        "net_profit_loss": net_profit_loss,
        "breakdown": portfolio_breakdown
    }

# Main app
def main_app():
    users = st.session_state.users
    user_data = users[st.session_state.username]

    st.sidebar.title(f"Welcome, {st.session_state.username} 👋")
    portfolio_stats = calculate_portfolio_stats(user_data)
    st.sidebar.write(f"Cash Balance 💵: ${portfolio_stats['cash_balance']:.2f}")
    st.sidebar.write(f"Portfolio Value 📈: ${portfolio_stats['portfolio_value']:.2f}")
    menu = ["Dashboard 📊", "Portfolio 💼", "Watchlist 👀", "History 📜"]
    choice = st.sidebar.selectbox("Menu", menu)
    if st.sidebar.button("Logout 🚪"):
        logout()

    st.markdown("""
        <style>
        .glass {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
            animation: fadeIn 0.5s ease-in-out;
        }
        @keyframes fadeIn {
            0% { opacity: 0; transform: translateY(-10px); }
            100% { opacity: 1; transform: translateY(0); }
        }
        .glass h3 {
            color: #ffffff;
            margin-bottom: 10px;
        }
        .glass p {
            color: #e0e0e0;
            margin: 5px 0;
        }
        .glass button {
            padding: 5px 10px;
            border-radius: 50px;
            border: none;
            cursor: pointer;
            margin: 5px;
            width: 100px;
            height: 40px;
            font-size: 16px;
            transition: all 0.3s ease;
        }
        .glass button:hover {
            transform: scale(1.1);
            box-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
        }
        .glass button.buy {
            background: #00ff00;
            color: #000;
        }
        .glass button.sell {
            background: #ff0000;
            color: #fff;
        }
        @media (max-width: 768px) {
            .glass {
                padding: 15px !important;
            }
            .glass h3 {
                font-size: 18px !important;
            }
            .glass p {
                font-size: 14px !important;
            }
            .glass button {
                width: 90px !important;
                height: 35px !important;
                font-size: 14px !important;
            }
        }
        @media (max-width: 480px) {
            .glass {
                padding: 10px !important;
            }
            .glass h3 {
                font-size: 16px !important;
            }
            .glass p {
                font-size: 12px !important;
            }
            .glass button {
                width: 80px !important;
                height: 30px !important;
                font-size: 12px !important;
            }
        }
        </style>
    """, unsafe_allow_html=True)

    if choice == "Dashboard 📊":
        symbol = st.text_input("Enter Ticker (e.g., AAPL, TSLA) 🎫", value=st.session_state.symbol, key="symbol_input").upper()
        st.session_state.symbol = symbol
        company_name = get_company_name(symbol)
        st.title(f"Trading Dashboard: {symbol} ({company_name}) 📈")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Start Trading 🚀"):
                st.session_state.trading_active = True
                data = get_stock_data(symbol, period="1d", interval="1m")
                st.session_state.candle_data = data[-60:] if not data.empty else pd.DataFrame([{
                    "time": datetime.now(),
                    "open": 100.0,
                    "high": 100.5,
                    "low": 99.5,
                    "close": 100.2
                }])
                st.session_state.last_price[symbol] = st.session_state.candle_data.iloc[-1]["close"]
                st.session_state.last_update_time = time.time()
                st.success(f"Started trading {symbol} 📈")
        with col2:
            if st.button("Stop Trading 🛑"):
                st.session_state.trading_active = False
                st.session_state.last_update_time = 0
                st.warning(f"Stopped trading {symbol} 🛑")

        current_price = st.session_state.last_price.get(symbol, get_stock_data(symbol).iloc[-1]["close"])
        bought_price = user_data["portfolio"].get(symbol, {}).get("avg_price", 0.0)
        sold_price = st.session_state.sold_price.get(symbol, 0.0)
        profit_loss = sold_price - bought_price if sold_price > 0 and bought_price > 0 else 0.0
        profit_color = "#00ff00" if profit_loss >= 0 else "#ff0000"
        profit_emoji = "📈" if profit_loss >= 0 else "📉"
        available_stocks = user_data["portfolio"].get(symbol, {}).get("quantity", 0)

  
        st.markdown('<h3>Current Price 📈</h3>', unsafe_allow_html=True)
        st.markdown(f'<p style="color: #00ff00;">${current_price:.2f}</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<h3>Trade Summary 💰</h3>', unsafe_allow_html=True)
        st.markdown(f'<p>Bought Price 🛒: ${bought_price:.2f}</p>', unsafe_allow_html=True)
        st.markdown(f'<p>Current Price 📊: ${current_price:.2f}</p>', unsafe_allow_html=True)
        st.markdown(f'<p>Sold Price 🏷️: ${sold_price:.2f}</p>', unsafe_allow_html=True)
        st.markdown(f'<p style="color: {profit_color};">Profit/Loss {profit_emoji}: ${profit_loss:.2f}</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        
        st.markdown('<h3>Available Stocks 📜</h3>', unsafe_allow_html=True)
        st.markdown(f'<p>{symbol}: {available_stocks} shares</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

      
        st.markdown('<h3>Trade 🛠️</h3>', unsafe_allow_html=True)
        quantity = st.number_input("Quantity 🔢", min_value=1, value=1, key="trade_qty")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Buy 🟢", key="buy_action", help="Buy shares"):
                price = st.session_state.last_price.get(symbol, get_stock_data(symbol).iloc[-1]["close"])
                total_cost = price * quantity
                if total_cost <= user_data["balance"]:
                    user_data["balance"] -= total_cost
                    if symbol in user_data["portfolio"]:
                        current_quantity = user_data["portfolio"][symbol]["quantity"]
                        current_avg_price = user_data["portfolio"][symbol]["avg_price"]
                        user_data["portfolio"][symbol]["quantity"] += quantity
                        user_data["portfolio"][symbol]["avg_price"] = (
                            (current_avg_price * current_quantity + price * quantity) / 
                            (current_quantity + quantity)
                        )
                    else:
                        user_data["portfolio"][symbol] = {"quantity": quantity, "avg_price": price}
                    user_data["transactions"].append({
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "symbol": symbol, "action": "Buy", "quantity": quantity,
                        "price": price, "total": total_cost
                    })
                    save_users(users)
                    st.session_state.last_price[symbol] = price
                    st.success(f"Bought {quantity} of {symbol} at ${price:.2f} 🎉")
                    st.rerun()
                else:
                    st.error("Insufficient balance! 🚫")
        with col2:
            if st.button("Sell 🔴", key="sell_action", help="Sell shares"):
                price = st.session_state.last_price.get(symbol, get_stock_data(symbol).iloc[-1]["close"])
                total_cost = price * quantity
                if symbol in user_data["portfolio"] and user_data["portfolio"][symbol]["quantity"] >= quantity:
                    user_data["portfolio"][symbol]["quantity"] -= quantity
                    user_data["balance"] += total_cost
                    if user_data["portfolio"][symbol]["quantity"] == 0:
                        del user_data["portfolio"][symbol]
                    user_data["transactions"].append({
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "symbol": symbol, "action": "Sell", "quantity": quantity,
                        "price": price, "total": total_cost
                    })
                    save_users(users)
                    st.session_state.last_price[symbol] = price
                    st.session_state.sold_price[symbol] = price
                    st.success(f"Sold {quantity} of {symbol} at ${price:.2f} 💸")
                    st.rerun()
                else:
                    st.error(f"Not enough shares to sell! You have {user_data['portfolio'].get(symbol, {}).get('quantity', 0)} shares of {symbol}. 🚫")
        st.markdown('</div>', unsafe_allow_html=True)

        # Real-time candlestick chart with controlled updates
        if st.session_state.trading_active or not st.session_state.candle_data.empty:
            chart_placeholder = st.empty()
            status_placeholder = st.empty()

            while st.session_state.trading_active:
                current_time = time.time()
                if current_time - st.session_state.last_update_time >= 1:
                    update_candle_data(symbol)
                    st.session_state.last_update_time = current_time

                    fig = go.Figure(data=[go.Candlestick(
                        x=st.session_state.candle_data["time"],
                        open=st.session_state.candle_data["open"],
                        high=st.session_state.candle_data["high"],
                        low=st.session_state.candle_data["low"],
                        close=st.session_state.candle_data["close"],
                        increasing_line_color='green',
                        decreasing_line_color='red'
                    )])
                    fig.update_layout(
                        title=f"{symbol} ({company_name}) Candlestick Chart 📉",
                        xaxis_title="Time ⏰",
                        yaxis_title="Price 💲",
                        xaxis_rangeslider_visible=True,
                        height=600,
                        template="plotly_dark",
                        showlegend=False,
                        xaxis=dict(
                            tickformat="%H:%M:%S",
                            tickangle=45,
                            nticks=10
                        ),
                        margin=dict(l=50, r=50, t=50, b=50)
                    )
                    fig.update_traces(
                        increasing_fillcolor='green',
                        decreasing_fillcolor='red',
                        selector=dict(type='candlestick')
                    )
                    chart_placeholder.plotly_chart(fig, use_container_width=True)
                    status_placeholder.write(f"Price updated to ${st.session_state.last_price[symbol]:.2f} at {datetime.now().strftime('%H:%M:%S')} ⏰")
                time.sleep(0.1)  # Reduce CPU usage

            # Display static chart when trading is stopped
            if not st.session_state.trading_active and not st.session_state.candle_data.empty:
                fig = go.Figure(data=[go.Candlestick(
                    x=st.session_state.candle_data["time"],
                    open=st.session_state.candle_data["open"],
                    high=st.session_state.candle_data["high"],
                    low=st.session_state.candle_data["low"],
                    close=st.session_state.candle_data["close"],
                    increasing_line_color='green',
                    decreasing_line_color='red'
                )])
                fig.update_layout(
                    title=f"{symbol} ({company_name}) Candlestick Chart 📉",
                    xaxis_title="Time ⏰",
                    yaxis_title="Price 💲",
                    xaxis_rangeslider_visible=True,
                    height=600,
                    template="plotly_dark",
                    showlegend=False,
                    xaxis=dict(
                        tickformat="%H:%M:%S",
                        tickangle=45,
                        nticks=10
                    ),
                    margin=dict(l=50, r=50, t=50, b=50)
                )
                fig.update_traces(
                    increasing_fillcolor='green',
                    decreasing_fillcolor='red',
                    selector=dict(type='candlestick')
                )
                chart_placeholder.plotly_chart(fig, use_container_width=True)

    elif choice == "Portfolio 💼":
        st.title("Portfolio 💼")
        stats = calculate_portfolio_stats(user_data)
        profit_color = "#00ff00" if stats["net_profit_loss"] >= 0 else "#ff0000"
        profit_emoji = "📈" if stats["net_profit_loss"] >= 0 else "📉"

      
        st.markdown('<h3>Account Summary 📋</h3>', unsafe_allow_html=True)
        st.markdown(f'<p>Cash Balance 💵: ${stats["cash_balance"]:.2f}</p>', unsafe_allow_html=True)
        st.markdown(f'<p>Portfolio Value 📈: ${stats["portfolio_value"]:.2f}</p>', unsafe_allow_html=True)
        st.markdown(f'<p>Total Assets 🏦: {stats["total_assets"]}</p>', unsafe_allow_html=True)
        st.markdown(f'<p>Total Shares 📜: {stats["total_shares"]}</p>', unsafe_allow_html=True)
        st.markdown(f'<p style="color: {profit_color};">Net Profit/Loss {profit_emoji}: ${stats["net_profit_loss"]:.2f}</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if stats["breakdown"]:
            
            st.markdown('<h3>Portfolio Breakdown 📊</h3>', unsafe_allow_html=True)
            breakdown_df = pd.DataFrame(stats["breakdown"])
            breakdown_df["profit_loss"] = breakdown_df["profit_loss"].apply(lambda x: f"${x:.2f}")
            breakdown_df["value"] = breakdown_df["value"].apply(lambda x: f"${x:.2f}")
            breakdown_df["avg_price"] = breakdown_df["avg_price"].apply(lambda x: f"${x:.2f}")
            breakdown_df["current_price"] = breakdown_df["current_price"].apply(lambda x: f"${x:.2f}")
            st.table(breakdown_df[["symbol", "quantity", "avg_price", "current_price", "value", "profit_loss"]])
            st.markdown('</div>', unsafe_allow_html=True)

          
            st.markdown('<h3>Portfolio Allocation 📈</h3>', unsafe_allow_html=True)
            fig = px.pie(
                breakdown_df,
                values="value",
                names="symbol",
                title="Portfolio Allocation by Value",
                template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.write("Your portfolio is empty. Start trading to add stocks! 📈")

    elif choice == "Watchlist 👀":
        st.title("Watchlist 👀")
        new_symbol = st.text_input("Add Symbol (e.g., AAPL) ➕").upper()
        if st.button("Add ➕"):
            if new_symbol and new_symbol not in user_data["watchlist"]:
                user_data["watchlist"].append(new_symbol)
                save_users(users)
                st.success(f"{new_symbol} added to watchlist! ✅")

        if user_data["watchlist"]:
           
            st.markdown('<h3>Your Watchlist 📋</h3>', unsafe_allow_html=True)
            watchlist_data = []
            for symbol in user_data["watchlist"]:
                current_price = st.session_state.last_price.get(symbol, get_stock_data(symbol).iloc[-1]["close"])
                previous_price = current_price * np.random.uniform(0.95, 1.05)
                percentage_change = ((current_price - previous_price) / previous_price) * 100
                watchlist_data.append({
                    "Symbol": symbol,
                    "Price": f"${current_price:.2f}",
                    "Change": f"{percentage_change:.2f}%",
                    "Action": symbol
                })
            watchlist_df = pd.DataFrame(watchlist_data)

            for index, row in watchlist_df.iterrows():
                col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
                with col1:
                    st.write(row["Symbol"])
                with col2:
                    st.write(row["Price"])
                with col3:
                    color = "#00ff00" if float(row["Change"].strip("%")) >= 0 else "#ff0000"
                    st.markdown(f'<p style="color: {color};">{row["Change"]}</p>', unsafe_allow_html=True)
                with col4:
                    if st.button(f"Trade {row['Symbol']}", key=f"trade_{row['Symbol']}"):
                        st.session_state.symbol = row["Symbol"]
                        st.session_state.trading_active = True
                        data = get_stock_data(row["Symbol"], period="1d", interval="1m")
                        st.session_state.candle_data = data[-60:]
                        if not data.empty:
                            st.session_state.last_price[row["Symbol"]] = data.iloc[-1]["close"]
                        st.rerun()

            remove_symbol = st.selectbox("Remove Symbol 🗑️", user_data["watchlist"])
            if st.button("Remove 🗑️"):
                user_data["watchlist"].remove(remove_symbol)
                save_users(users)
                st.success(f"{remove_symbol} removed from watchlist! ✅")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.write("Your watchlist is empty. 📭")

    elif choice == "History 📜":
        st.title("Transaction History 📜")
        if user_data["transactions"]:
         
            st.markdown('<h3>Your Transactions 📋</h3>', unsafe_allow_html=True)
            transactions_df = pd.DataFrame(user_data["transactions"])
            transactions_df["time"] = pd.to_datetime(transactions_df["time"])
            transactions_df = transactions_df.sort_values(by="time", ascending=False)
            transactions_df["time"] = transactions_df["time"].dt.strftime("%Y-%m-%d %H:%M:%S")
            
            profit_loss_list = []
            for _, row in transactions_df.iterrows():
                symbol = row["symbol"]
                if row["action"] == "Sell":
                    buy_transactions = transactions_df[
                        (transactions_df["symbol"] == symbol) & 
                        (transactions_df["action"] == "Buy") & 
                        (pd.to_datetime(transactions_df["time"]) < pd.to_datetime(row["time"]))
                    ]
                    if not buy_transactions.empty:
                        avg_buy_price = buy_transactions["price"].mean()
                        profit_loss = (row["price"] - avg_buy_price) * row["quantity"]
                    else:
                        profit_loss = 0.0
                else:
                    profit_loss = 0.0
                profit_loss_list.append(profit_loss)
            
            transactions_df["Profit/Loss"] = profit_loss_list
            transactions_df["Profit/Loss"] = transactions_df["Profit/Loss"].apply(lambda x: f"${x:.2f}")
            
            def color_profit_loss(val):
                color = "#00ff00" if float(val.strip("$")) >= 0 else "#ff0000"
                return f"color: {color}"
            
            styled_df = transactions_df.style.applymap(color_profit_loss, subset=["Profit/Loss"])
            st.table(styled_df)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.write("No transactions yet. 📭")

# Run the app
if not st.session_state.logged_in:
    if 'show_register' not in st.session_state or not st.session_state.show_register:
        login()
    else:
        register()
else:
    main_app()
