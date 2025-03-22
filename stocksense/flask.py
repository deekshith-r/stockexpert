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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# User data file
USER_DATA_FILE = "users.json"

# Email configuration (Replace with your email and password)
EMAIL_ADDRESS = "4al20ai012@gmail.com"  # Replace with your Gmail email
EMAIL_PASSWORD = "kjjl srxd iidc gfrh"       # Replace with your Gmail password

# Load/save users
def load_users():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(users, f)

# Send email function
def send_email(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Failed to send email: {str(e)} 📧")
        return False

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'email' not in st.session_state:
    st.session_state.email = ""
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
if 'bought_price' not in st.session_state:
    st.session_state.bought_price = {}
if 'last_update_time' not in st.session_state:
    st.session_state.last_update_time = 0
if 'stock_data_cache' not in st.session_state:
    st.session_state.stock_data_cache = {}
if 'company_name_cache' not in st.session_state:
    st.session_state.company_name_cache = {}
if 'portfolio_history' not in st.session_state:
    st.session_state.portfolio_history = []
if 'current_price' not in st.session_state:
    st.session_state.current_price = 0.0
if 'market_news' not in st.session_state:
    st.session_state.market_news = []
if 'market_movers' not in st.session_state:
    st.session_state.market_movers = {"gainers": [], "losers": []}
if 'recent_data' not in st.session_state:
    st.session_state.recent_data = pd.DataFrame()
if 'price_alerts' not in st.session_state:
    st.session_state.price_alerts = []
if 'alert_popup' not in st.session_state:
    st.session_state.alert_popup = False
if 'alert_message' not in st.session_state:
    st.session_state.alert_message = ""
if 'buy_message' not in st.session_state:
    st.session_state.buy_message = ""
if 'sell_message' not in st.session_state:
    st.session_state.sell_message = ""
if 'popup_start_time' not in st.session_state:
    st.session_state.popup_start_time = time.time()
if 'show_popup' not in st.session_state:
    st.session_state.show_popup = True
if 'watchlist_last_update' not in st.session_state:
    st.session_state.watchlist_last_update = 0

# Preload essential data at startup
def preload_data():
    if st.session_state.recent_data.empty or not st.session_state.market_news or not st.session_state.market_movers:
        st.session_state.recent_data = fetch_recent_data()
        st.session_state.market_news = fetch_market_news()
        st.session_state.market_movers = fetch_market_movers()

# Fetch stock data from yfinance with caching
def get_stock_data(symbol, period="1d", interval="1m"):
    cache_key = f"{symbol}_{period}_{interval}"
    if cache_key in st.session_state.stock_data_cache:
        return st.session_state.stock_data_cache[cache_key]

    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period=period, interval=interval)
        if df.empty:
            df = pd.DataFrame([{
                "time": datetime.now(),
                "open": 100.0,
                "high": 100.5,
                "low": 99.5,
                "close": 100.2
            }])
        else:
            df = df.reset_index().rename(columns={"Datetime": "time", "Open": "open", "High": "high", "Low": "low", "Close": "close"})
        st.session_state.stock_data_cache[cache_key] = df
        return df
    except Exception:
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
    except Exception:
        st.session_state.company_name_cache[symbol] = "Unknown Company"
        return "Unknown Company"

# Fetch current price for a symbol
def get_current_price(symbol):
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period="1d", interval="1m")
        if not data.empty:
            return round(data["Close"][-1], 2)
        return 0.0
    except Exception:
        return 0.0

# Fetch market news using yfinance
def fetch_market_news():
    try:
        sp500 = yf.Ticker("^GSPC")
        news = sp500.news[:3]
        news_items = [item["title"] for item in news]
        if not news_items:
            news_items = [
                "Tech stocks rally as AI demand surges. 🚀",
                "Fed signals potential rate cuts in Q2 2025. 📉",
                "Crypto market sees 10% surge overnight. 💰"
            ]
        return news_items
    except Exception:
        return [
            "Tech stocks rally as AI demand surges. 🚀",
            "Fed signals potential rate cuts in Q2 2025. 📉",
            "Crypto market sees 10% surge overnight. 💰"
        ]

# Fetch market movers (10 companies each)
def fetch_market_movers():
    symbols = [
        "AAPL", "TSLA", "NVDA", "META", "GOOGL", "MSFT", "AMZN", "INTC", "CSCO", "ADBE",
        "ORCL", "IBM", "NFLX", "PYPL", "QCOM", "AMD", "TXN", "CRM", "UBER", "SNAP"
    ]
    gainers = []
    losers = []
    for symbol in symbols:
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(period="1d")
            if not data.empty:
                change = ((data["Close"][-1] - data["Open"][0]) / data["Open"][0]) * 100
                entry = {"symbol": symbol, "change": round(change, 2)}
                if change >= 0:
                    gainers.append(entry)
                else:
                    losers.append(entry)
        except Exception:
            continue
    gainers = sorted(gainers, key=lambda x: x["change"], reverse=True)[:10]
    losers = sorted(losers, key=lambda x: x["change"])[:10]
    if not gainers:
        gainers = [{"symbol": f"GAINER{i}", "change": 3.5 - i*0.2} for i in range(10)]
    if not losers:
        losers = [{"symbol": f"LOSER{i}", "change": -1.9 + i*0.2} for i in range(10)]
    return {"gainers": gainers, "losers": losers}

# Fetch recent data for selected stocks
def fetch_recent_data():
    symbols = ["AAPL", "TSLA", "GOOGL", "MSFT", "AMZN", "NVDA", "META", "IBM", "ORCL", "INTC"]
    data_list = []
    for symbol in symbols:
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(period="1d", interval="1m")
            info = stock.info
            if not data.empty:
                latest = data.iloc[-1]
                change = ((latest["Close"] - data.iloc[0]["Open"]) / data.iloc[0]["Open"]) * 100
                data_list.append({
                    "Symbol": symbol,
                    "Price": round(latest["Close"], 2),
                    "Volume": int(latest["Volume"]),
                    "Change %": round(change, 2),
                    "52W High": round(info.get("fiftyTwoWeekHigh", 0), 2),
                    "52W Low": round(info.get("fiftyTwoWeekLow", 0), 2),
                    "Market Cap": round(info.get("marketCap", 0) / 1e9, 2),
                    "P/E Ratio": round(info.get("trailingPE", 0), 2)
                })
        except Exception:
            data_list.append({
                "Symbol": symbol,
                "Price": 100.0,
                "Volume": 1000000,
                "Change %": 0.0,
                "52W High": 110.0,
                "52W Low": 90.0,
                "Market Cap": 100.0,
                "P/E Ratio": 15.0
            })
    df = pd.DataFrame(data_list)
    df.index = range(1, len(df) + 1)  # Start index from 1
    return df

# Fetch watchlist data with real-time updates
def fetch_watchlist_data(symbols):
    data_list = []
    for symbol in symbols:
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(period="1d", interval="1m")
            info = stock.info
            if not data.empty:
                latest = data.iloc[-1]
                data_list.append({
                    "Ticker Symbol": symbol,
                    "Company Name": info.get("longName", "Unknown Company"),
                    "Price": round(latest["Close"], 2),
                    "Volume": int(latest["Volume"]),
                    "Industry": info.get("industry", "N/A"),
                    "Market Cap": round(info.get("marketCap", 0) / 1e9, 2),
                    "P/E Ratio": round(info.get("trailingPE", 0), 2)
                })
        except Exception:
            data_list.append({
                "Ticker Symbol": symbol,
                "Company Name": "Unknown Company",
                "Price": 100.0,
                "Volume": 1000000,
                "Industry": "N/A",
                "Market Cap": 100.0,
                "P/E Ratio": 15.0
            })
    df = pd.DataFrame(data_list)
    df.index = range(1, len(df) + 1)  # Start index from 1
    return df

# Simulate real-time candle updates
def update_candle_data(symbol):
    data = get_stock_data(symbol, period="1d", interval="1m")
    if not data.empty:
        latest_candle = data.iloc[-1]
        volatility = (data["high"].max() - data["low"].min()) * 0.05 or 0.5
        new_open = st.session_state.last_price.get(symbol, latest_candle["close"])
    else:
        new_open = st.session_state.last_price.get(symbol, 100.0)
        volatility = 0.5

    new_high = new_open + np.random.uniform(0, volatility)
    new_low = new_open - np.random.uniform(0, volatility)
    new_close = new_open + np.random.uniform(-volatility * 0.3, volatility * 0.3)
    
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
    if len(st.session_state.candle_data) > 15:  # Reduced to 15 candles
        st.session_state.candle_data = st.session_state.candle_data.iloc[-15:]
    st.session_state.last_price[symbol] = new_close
    st.session_state.current_price = new_close

# Check price alerts and send email
def check_price_alerts():
    if not st.session_state.logged_in:
        return
    user_data = st.session_state.users.get(st.session_state.username, {})
    if not user_data:
        return
    email = user_data.get("email", "")
    if not email:
        return
    alerts_to_remove = []
    for alert in st.session_state.price_alerts:
        symbol = alert.get("symbol", "")
        target_price = alert.get("target_price", 0.0)
        current_price = st.session_state.last_price.get(symbol, get_current_price(symbol))
        if current_price >= target_price:
            alert_message = f"Price Alert! 📢 {symbol} has reached ${current_price:.2f} (Target: ${target_price:.2f}) 🎯"
            st.session_state.alert_message = alert_message
            st.session_state.alert_popup = True
            subject = f"TradeRiser Price Alert: {symbol} 🚀"
            body = f"""
🌟 Dear {st.session_state.username}, 🌟

🎉 Great news! Your price alert for {symbol} has been triggered! 🎉

📊 {symbol} has reached ${current_price:.2f} (Target: ${target_price:.2f}) 🚀

💡 Keep an eye on the market and make your next move! Trade smart with TradeRiser! 📈

Happy Trading! 😊
The TradeRiser Team 🌟
"""
            send_email(email, subject, body)
            alerts_to_remove.append(alert)
    for alert in alerts_to_remove:
        st.session_state.price_alerts.remove(alert)
    user_data["price_alerts"] = st.session_state.price_alerts
    save_users(st.session_state.users)

# Login Page
def login():
    st.markdown("""
        <style>
        body {
            background: linear-gradient(45deg, #0d1b2a, #1b263b, #2a1a3e, #1a2e2a);
            background-size: 400%;
            animation: gradientShift 15s ease infinite;
            font-family: 'Roboto', sans-serif;
        }
        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
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
            opacity: 0.5;
            animation: tickerMove 30s linear infinite;
        }
        @keyframes tickerMove {
            0% { transform: translateX(100%); }
            100% { transform: translateX(-100%); }
        }
        @keyframes neonPulse {
            0% { text-shadow: 0 0 5px #00ffcc, 0 0 10px #00ffcc, 0 0 15px #00ffcc; }
            50% { text-shadow: 0 0 10px #00ffcc, 0 0 20px #00ffcc, 0 0 30px #00ffcc; }
            100% { text-shadow: 0 0 5px #00ffcc, 0 0 10px #00ffcc, 0 0 15px #00ffcc; }
        }
        @keyframes techySlideIn {
            0% { opacity: 0; transform: translateY(20px); }
            100% { opacity: 1; transform: translateY(0); }
        }
        .login-title {
            color: #00ffcc;
            font-size: 36px;
            font-weight: bold;
            text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
            margin-bottom: 10px;
            animation: neonPulse 2s infinite;
            text-align: center;
        }
        .welcome-text {
            color: #e0e0e0;
            font-size: 18px;
            margin: 20px auto;
            max-width: 600px;
            animation: techySlideIn 0.8s ease-in-out;
            text-align: center;
        }
        .features-section {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 15px;
            margin: 30px 0;
        }
        .feature-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 15px;
            width: 180px;
            text-align: center;
            animation: techySlideIn 1s ease-in-out;
        }
        .feature-icon {
            font-size: 28px;
            color: #00ffcc;
            margin-bottom: 8px;
        }
        .feature-title {
            color: #ffffff;
            font-size: 16px;
            font-weight: bold;
        }
        .feature-desc {
            color: #b0b0b0;
            font-size: 12px;
        }
        .market-stats {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin: 30px 0;
            flex-wrap: wrap;
        }
        .stat-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 10px;
            width: 130px;
            text-align: center;
            animation: techySlideIn 1s ease-in-out;
        }
        .stat-title {
            color: #00ffcc;
            font-size: 12px;
        }
        .stat-value {
            color: #ffffff;
            font-size: 14px;
            font-weight: bold;
        }
        .testimonials-section {
            margin: 30px 0;
            padding: 0 15px;
        }
        .testimonial {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 15px;
            margin: 15px auto;
            max-width: 500px;
            animation: techySlideIn 1.2s ease-in-out;
            border-left: 3px solid #00ffcc;
        }
        .testimonial-text {
            color: #e0e0e0;
            font-size: 14px;
            font-style: italic;
            margin-bottom: 8px;
        }
        .testimonial-author {
            color: #00ffcc;
            font-size: 12px;
            text-align: right;
            font-weight: bold;
        }
        .why-traderiser-section {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 20px;
            margin: 15px auto;
            max-width: 700px;
            text-align: center;
            animation: techySlideIn 0.8s ease-in-out;
            backdrop-filter: blur(8px);
            box-shadow: 0 0 15px rgba(0, 255, 255, 0.2);
        }
        .why-traderiser-title {
            color: #00ffcc;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 15px;
            text-shadow: 0 0 8px rgba(0, 255, 255, 0.5);
        }
        .why-traderiser-text {
            color: #e0e0e0;
            font-size: 14px;
            margin-bottom: 15px;
        }
        .why-traderiser-list {
            text-align: left;
            color: #b0b0b0;
            font-size: 12px;
            margin: 0 auto;
            max-width: 500px;
            list-style-type: none;
            padding: 0;
        }
        .why-traderiser-list li {
            margin: 8px 0;
            position: relative;
            padding-left: 20px;
        }
        .why-traderiser-list li:before {
            content: "✔";
            color: #00ffcc;
            position: absolute;
            left: 0;
            font-size: 14px;
        }
        .popup {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(0, 255, 204, 0.1));
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 0 20px rgba(0, 255, 255, 0.5);
            text-align: center;
            animation: popupFadeIn 0.5s ease-in-out, popupFadeOut 0.5s ease-in-out 1.5s;
            backdrop-filter: blur(8px);
            z-index: 1000;
            width: 90%;
            max-width: 350px;
        }
        @keyframes popupFadeIn {
            0% { opacity: 0; transform: translate(-50%, -60%) scale(0.9); }
            100% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
        }
        @keyframes popupFadeOut {
            0% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
            100% { opacity: 0; transform: translate(-50%, -60%) scale(0.9); }
        }
        .popup-title {
            color: #00ffcc;
            font-size: 24px;
            font-weight: bold;
            text-shadow: 0 0 8px rgba(0, 255, 255, 0.5);
        }
        .popup-text {
            color: #e0e0e0;
            font-size: 14px;
            margin-bottom: 15px;
        }
        .login-button {
            background: #00ffcc;
            color: #1a1a2e;
            padding: 8px 16px;
            border: none;
            border-radius: 20px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            margin: 5px;
            width: 100px;
        }
        .login-button:hover {
            background: #00ccaa;
            box-shadow: 0 0 15px #00ffcc;
            transform: scale(1.1);
        }
        .center-buttons {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 10px;
        }
        .center-why-traderiser {
            display: flex;
            justify-content: center;
            margin: 20px 0;
        }
        .alert-popup {
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 255, 204, 0.2);
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 0 15px rgba(0, 255, 255, 0.5);
            text-align: center;
            animation: alertFadeIn 0.5s ease-in-out, alertFadeOut 0.5s ease-in-out 3.5s;
            z-index: 1000;
            width: 90%;
            max-width: 400px;
        }
        @keyframes alertFadeIn {
            0% { opacity: 0; transform: translateX(-50%) translateY(-20px); }
            100% { opacity: 1; transform: translateX(-50%) translateY(0); }
        }
        @keyframes alertFadeOut {
            0% { opacity: 1; transform: translateX(-50%) translateY(0); }
            100% { opacity: 0; transform: translateX(-50%) translateY(-20px); }
        }
        .alert-text {
            color: #00ffcc;
            font-size: 14px;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="ticker-bg">
            <div class="ticker">
                AAPL +2.3% • TSLA -1.5% • GOOGL +0.8% • MSFT -0.2% • AMZN +1.7% • NVDA -0.9% • META +1.2% • 
                AAPL +2.3% • TSLA -1.5% • GOOGL +0.8% • MSFT -0.2% • AMZN +1.7% • NVDA -0.9% • META +1.2%
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Show popup for 2 seconds only once per session
    current_time = time.time()
    if st.session_state.show_popup and (current_time - st.session_state.popup_start_time) <= 2:
        with st.container():
            st.markdown("""
                <div class="popup">
                    <h2 class="popup-title">🎉 Welcome to TradeRiser!</h2>
                    <p class="popup-text">Register now for a $10,000 bonus! 💰</p>
                </div>
            """, unsafe_allow_html=True)
    elif st.session_state.show_popup and (current_time - st.session_state.popup_start_time) > 2:
        st.session_state.show_popup = False  # Prevent the popup from reappearing

    st.markdown('<h1 class="login-title">🚀 TradeRiser: Login</h1>', unsafe_allow_html=True)
    st.markdown("""
        <div class="welcome-text">
            Welcome to TradeRiser! Trade stocks, track your portfolio, and unlock financial success with real-time data and insights. 📈
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

    username = st.text_input("Username 👤", key="login_username").strip()
    password = st.text_input("Password 🔒", type="password", key="login_password")
    st.markdown('<div class="center-buttons">', unsafe_allow_html=True)
    login_btn = st.button("Login 🔐", key="login_btn")
    register_btn = st.button("Register 📝", key="register_btn")
    st.markdown('</div>', unsafe_allow_html=True)

    if login_btn:
        users = st.session_state.users
        if username in users and users[username]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.email = users[username]["email"]
            st.session_state.price_alerts = users[username].get("price_alerts", [])
            st.success("Welcome back! 🚀")
            st.rerun()
        else:
            st.error("Invalid credentials 🚫")
    if register_btn:
        st.session_state.show_register = True
        st.rerun()

    st.markdown("""
        <div class="features-section">
            <div class="feature-card">
                <div class="feature-icon">📈</div>
                <div class="feature-title">Real-Time Trading</div>
                <div class="feature-desc">Live market data.</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">💼</div>
                <div class="feature-title">Portfolio Tracking</div>
                <div class="feature-desc">Monitor investments.</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <div class="feature-title">Market Insights</div>
                <div class="feature-desc">Data-driven success.</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">👥</div>
                <div class="feature-title">Community</div>
                <div class="feature-desc">Join traders.</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

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

    st.markdown('<div class="center-why-traderiser">', unsafe_allow_html=True)
    if st.button("Why TradeRiser? 🔍", key="why_traderiser_btn"):
        st.session_state.show_why_traderiser = not st.session_state.show_why_traderiser
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.show_why_traderiser:
        st.markdown("""
            <div class="why-traderiser-section">
                <h2 class="why-traderiser-title">Why Choose TradeRiser?</h2>
                <p class="why-traderiser-text">
                    TradeRiser empowers traders with tools and insights to succeed in the stock market. 🚀
                </p>
                <ul class="why-traderiser-list">
                    <li><strong>Real-Time Data:</strong> Access live market data.</li>
                    <li><strong>User-Friendly:</strong> Easy navigation for all levels.</li>
                    <li><strong>Advanced Analytics:</strong> Analyze trends and predict movements.</li>
                    <li><strong>Community:</strong> Share strategies with other traders.</li>
                    <li><strong>Secure:</strong> Your data and funds are protected.</li>
                    <li><strong>Support:</strong> 24/7 dedicated support team.</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

# Register Page
def register():
    st.markdown("""
        <style>
        .register-container {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 0 15px rgba(0, 255, 255, 0.2);
            text-align: center;
            animation: techySlideIn 0.8s ease-in-out;
            max-width: 350px;
            margin: 80px auto;
            backdrop-filter: blur(8px);
        }
        </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="register-container">', unsafe_allow_html=True)
    st.markdown('<h1 class="login-title">Register 📝</h1>', unsafe_allow_html=True)
    username = st.text_input("New Username 👤", key="register_username")
    email = st.text_input("Email 📧", key="register_email")
    password = st.text_input("New Password 🔒", type="password", key="register_password")
    confirm_password = st.text_input("Confirm Password 🔑", type="password", key="register_confirm_password")
    st.markdown('<div class="center-buttons">', unsafe_allow_html=True)
    register_btn = st.button("Register 📋", key="register_submit_btn")
    back_btn = st.button("Back to Login 🔙", key="back_to_login_btn")
    st.markdown('</div>', unsafe_allow_html=True)

    if register_btn:
        users = st.session_state.users
        if username in users:
            st.error("Username already exists! 🚫")
        elif password != confirm_password:
            st.error("Passwords do not match! ⚠️")
        elif not email:
            st.error("Please provide an email address! 📧")
        else:
            users[username] = {
                "password": password,
                "email": email,
                "balance": 10000.0,
                "portfolio": {},
                "watchlist": [],
                "transactions": [],
                "price_alerts": []
            }
            save_users(users)
            st.session_state.users = users
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.email = email
            st.session_state.price_alerts = []
            subject = "Welcome to TradeRiser! 🎉"
            body = f"""
🌟 Hello {username}! Welcome to TradeRiser! 🌟

🎉 You're now part of the TradeRiser family! We've added a $10,000 bonus to your account to kickstart your trading journey! 💰

🚀 Explore amazing features like:
- Real-Time Trading 📈
- Portfolio Tracking 💼
- Market Insights 📊
- Price Alerts 🔔

💡 Start trading now and watch your wealth grow! If you need help, our support team is here for you 24/7! 🤝

Happy Trading! 😊
The TradeRiser Team 🌟
"""
            if send_email(email, subject, body):
                st.success(f"Welcome, {username}! $10,000 bonus added. A welcome email has been sent to {email}. 💰")
            else:
                st.warning(f"Welcome, {username}! $10,000 bonus added. Failed to send welcome email. 💰")
            st.rerun()
    if back_btn:
        st.session_state.show_register = False
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Logout
def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.email = ""
    st.session_state.trading_active = False
    st.session_state.candle_data = pd.DataFrame(columns=["time", "open", "high", "low", "close"])
    st.session_state.last_update_time = 0
    st.session_state.price_alerts = []
    st.session_state.alert_popup = False
    st.session_state.alert_message = ""
    st.session_state.bought_price = {}
    st.session_state.sold_price = {}
    st.session_state.current_price = 0.0
    st.session_state.buy_message = ""
    st.session_state.sell_message = ""
    st.session_state.show_popup = True  # Reset popup state on logout
    st.session_state.watchlist_last_update = 0
    st.success("Logged out! 👋")
    st.rerun()

# Calculate portfolio stats
def calculate_portfolio_stats(user_data):
    portfolio_value = 0.0
    total_shares = 0
    total_assets = 0
    net_profit_loss = 0.0
    breakdown = []

    for symbol, details in user_data.get("portfolio", {}).items():
        current_price = st.session_state.last_price.get(symbol, get_current_price(symbol))
        asset_value = round(current_price * details["quantity"], 2)
        portfolio_value += asset_value
        total_shares += details["quantity"]
        total_assets += 1
        asset_profit_loss = round((current_price - details["avg_price"]) * details["quantity"], 2)
        net_profit_loss += asset_profit_loss
        breakdown.append({
            "symbol": symbol,
            "quantity": details["quantity"],
            "avg_price": details["avg_price"],
            "current_price": current_price,
            "value": asset_value,
            "profit_loss": asset_profit_loss
        })

    st.session_state.portfolio_history.append({"time": datetime.now(), "value": portfolio_value + user_data["balance"]})
    if len(st.session_state.portfolio_history) > 50:
        st.session_state.portfolio_history = st.session_state.portfolio_history[-50:]

    return {
        "portfolio_value": portfolio_value,
        "cash_balance": user_data["balance"],
        "total_shares": total_shares,
        "total_assets": total_assets,
        "net_profit_loss": net_profit_loss,
        "breakdown": breakdown
    }

# Main App
def main_app():
    users = st.session_state.users
    user_data = users.get(st.session_state.username, {})
    if not user_data:
        st.error("User data not found. Please log in again.")
        return

    st.markdown("""
        <style>
        .glass {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            backdrop-filter: blur(8px);
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            margin-bottom: 15px;
        }
        .glass h3 {
            color: #00ffcc;
            text-shadow: 0 0 5px rgba(0, 255, 255, 0.5);
            font-size: 18px;
        }
        .glass p {
            color: #e0e0e0;
            font-size: 14px;
        }
        .glass button {
            padding: 6px 12px;
            border-radius: 20px;
            border: none;
            cursor: pointer;
            margin: 5px;
            transition: all 0.3s ease;
        }
        .glass button:hover {
            transform: scale(1.1);
            box-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
        }
        .buy-btn { background: #00ff00; color: #000; }
        .sell-btn { background: #ff0000; color: #fff; }
        .trade-message {
            margin-top: 8px;
            font-weight: bold;
            font-size: 14px;
        }
        .premium-section {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(0, 255, 204, 0.1));
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
            backdrop-filter: blur(8px);
        }
        .premium-title {
            color: #ff00ff;
            font-size: 24px;
            font-weight: bold;
            text-shadow: 0 0 10px rgba(255, 0, 255, 0.5);
            margin-bottom: 15px;
        }
        .premium-subtitle {
            color: #e0e0e0;
            font-size: 16px;
            margin-bottom: 20px;
        }
        .premium-features {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 15px;
        }
        .premium-feature-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 15px;
            width: 200px;
            text-align: center;
            transition: transform 0.3s ease;
        }
        .premium-feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 0 15px rgba(255, 0, 255, 0.3);
        }
        .premium-feature-icon {
            font-size: 30px;
            color: #ff00ff;
            margin-bottom: 10px;
        }
        .premium-feature-title {
            color: #ffffff;
            font-size: 16px;
            font-weight: bold;
        }
        .premium-feature-desc {
            color: #b0b0b0;
            font-size: 12px;
        }
        .premium-more {
            color: #00ffcc;
            font-size: 14px;
            font-style: italic;
            margin-top: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Preload data at startup
    preload_data()

    # Show alert popup if there’s an alert
    if st.session_state.alert_popup:
        st.markdown(f"""
            <div class="alert-popup">
                <p class="alert-text">{st.session_state.alert_message}</p>
            </div>
        """, unsafe_allow_html=True)
        time.sleep(4)
        st.session_state.alert_popup = False
        st.session_state.alert_message = ""

    # Sidebar
    st.sidebar.title(f"Welcome, {st.session_state.username} 👋")
    portfolio_stats = calculate_portfolio_stats(user_data)
    st.sidebar.write(f"Cash: ${portfolio_stats['cash_balance']:.2f} 💵")
    st.sidebar.write(f"Portfolio: ${portfolio_stats['portfolio_value']:.2f} 📈")
    menu = [
        "Dashboard 📊", "Portfolio 💼", "Watchlist 👀", "Transactions 📜",
        "Profile Settings 🔧", "Market News 📰", "Market Movers 📊",
        "Learning Resources 📖", "TradeRiser Premium 💎", "Risk Calculator ⚖️",
        "Recent Data 📈", "Price Alerts 🔔"
    ]
    choice = st.sidebar.selectbox("Menu", menu)
    if st.sidebar.button("Logout 🚪"):
        logout()

    # Check Price Alerts (only when necessary)
    check_price_alerts()

    # Dashboard
    if choice == "Dashboard 📊":
        symbol = st.text_input("Ticker (e.g., AAPL) 🎫", value=st.session_state.symbol).upper()
        st.session_state.symbol = symbol
        company_name = get_company_name(symbol)
        st.title(f"Dashboard: {symbol} ({company_name}) 📈")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Start Trading 🚀"):
                st.session_state.trading_active = True
                data = get_stock_data(symbol)
                st.session_state.candle_data = data[-15:]
                st.session_state.last_price[symbol] = st.session_state.candle_data.iloc[-1]["close"]
                st.session_state.current_price = st.session_state.last_price[symbol]
                st.session_state.last_update_time = time.time()
        with col2:
            if st.button("Stop Trading 🛑"):
                st.session_state.trading_active = False

        # Current Price
        price_placeholder = st.empty()
        current_price = st.session_state.current_price if st.session_state.current_price > 0 else get_current_price(symbol)
        price_placeholder.markdown(f'<div class="glass"><h3>Current Price</h3><p style="color: #00ff00;">${current_price:.2f}</p></div>', unsafe_allow_html=True)

        # Trade Summary
        bought_price = st.session_state.bought_price.get(symbol, 0.0)
        sold_price = st.session_state.sold_price.get(symbol, 0.0)
        profit_loss = (sold_price - bought_price) if sold_price > 0 else 0.0
        available_stocks = user_data["portfolio"].get(symbol, {"quantity": 0})["quantity"]
        st.markdown(f"""
            <div class="glass">
                <h3>Trade Summary 💰</h3>
                <p>Bought Price 🛒: ${bought_price:.2f}</p>
                <p>Current Price 📊: ${current_price:.2f}</p>
                <p>Sold Price 🏷️: ${sold_price:.2f}</p>
                <p>Profit/Loss 📈: <span style="color: {'#00ff00' if profit_loss >= 0 else '#ff0000'}">${profit_loss:.2f}</span></p>
                <h4>Available Stocks 📜</h4>
                <p>{symbol}: {available_stocks} shares</p>
            </div>
        """, unsafe_allow_html=True)

        # Buy/Sell
        st.markdown('<div class="glass"><h3>Trade 🛠️</h3>', unsafe_allow_html=True)
        quantity = st.number_input("Quantity 🔢", min_value=1, value=1, key="trade_qty")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Buy 🟢", key="buy_btn"):
                price = st.session_state.current_price if st.session_state.current_price > 0 else get_current_price(symbol)
                if price <= 0:
                    st.error("Cannot buy: Current price is zero! 🚫")
                else:
                    total_cost = price * quantity
                    if total_cost <= user_data["balance"]:
                        user_data["balance"] -= total_cost
                        if symbol in user_data["portfolio"]:
                            current_qty = user_data["portfolio"][symbol]["quantity"]
                            current_avg = user_data["portfolio"][symbol]["avg_price"]
                            user_data["portfolio"][symbol]["quantity"] += quantity
                            user_data["portfolio"][symbol]["avg_price"] = (
                                (current_avg * current_qty + price * quantity) / (current_qty + quantity)
                            )
                        else:
                            user_data["portfolio"][symbol] = {"quantity": quantity, "avg_price": price}
                        user_data["transactions"].append({
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "symbol": symbol, "action": "Buy", "quantity": quantity, "price": price, "total": total_cost
                        })
                        st.session_state.bought_price[symbol] = price
                        st.session_state.current_price = price
                        st.session_state.buy_message = f"Bought {quantity} shares at ${price:.2f}"
                        save_users(users)
                    else:
                        st.error("Insufficient funds! 🚫")
        with col2:
            if st.button("Sell 🔴", key="sell_btn"):
                price = st.session_state.current_price if st.session_state.current_price > 0 else get_current_price(symbol)
                if price <= 0:
                    st.error("Cannot sell: Current price is zero! 🚫")
                else:
                    if symbol in user_data["portfolio"] and user_data["portfolio"][symbol]["quantity"] >= quantity:
                        total_cost = price * quantity
                        user_data["portfolio"][symbol]["quantity"] -= quantity
                        user_data["balance"] += total_cost
                        if user_data["portfolio"][symbol]["quantity"] == 0:
                            del user_data["portfolio"][symbol]
                        user_data["transactions"].append({
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "symbol": symbol, "action": "Sell", "quantity": quantity, "price": price, "total": total_cost
                        })
                        st.session_state.sold_price[symbol] = price
                        st.session_state.current_price = price
                        st.session_state.sell_message = f"Sold {quantity} shares at ${price:.2f}"
                        save_users(users)
                    else:
                        st.error("Not enough shares! 🚫")

        # Display Buy/Sell Messages
        if st.session_state.buy_message:
            st.markdown(f'<p class="trade-message" style="color: #00ff00;">{st.session_state.buy_message}</p>', unsafe_allow_html=True)
        if st.session_state.sell_message:
            st.markdown(f'<p class="trade-message" style="color: #ff0000;">{st.session_state.sell_message}</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Candlestick chart
        if not st.session_state.candle_data.empty:
            chart_placeholder = st.empty()
            fig = go.Figure()
            if st.session_state.trading_active:
                while st.session_state.trading_active:
                    current_time = time.time()
                    if current_time - st.session_state.last_update_time >= 5:  # Update every 5 seconds
                        update_candle_data(symbol)
                        st.session_state.last_update_time = current_time
                        current_price = st.session_state.current_price
                        price_placeholder.markdown(f'<div class="glass"><h3>Current Price</h3><p style="color: #00ff00;">${current_price:.2f}</p></div>', unsafe_allow_html=True)
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
                            title=f"{symbol} Candlestick Chart",
                            xaxis_title="Time",
                            yaxis_title="Price",
                            xaxis_rangeslider_visible=True,
                            height=500,
                            template="plotly_dark",
                            xaxis=dict(tickformat="%H:%M:%S", tickangle=45, nticks=8),
                        )
                        chart_placeholder.plotly_chart(fig, use_container_width=True)
                    time.sleep(0.1)
            else:
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
                    title=f"{symbol} Candlestick Chart",
                    xaxis_title="Time",
                    yaxis_title="Price",
                    xaxis_rangeslider_visible=True,
                    height=500,
                    template="plotly_dark",
                    xaxis=dict(tickformat="%H:%M:%S", tickangle=45, nticks=8),
                )
                chart_placeholder.plotly_chart(fig, use_container_width=True)

    # Portfolio
    elif choice == "Portfolio 💼":
        st.title("Portfolio 💼")
        stats = calculate_portfolio_stats(user_data)
        st.markdown(f"""
            <div class="glass">
                <h3>Account Summary</h3>
                <p>Cash: ${stats['cash_balance']:.2f}</p>
                <p>Portfolio Value: ${stats['portfolio_value']:.2f}</p>
                <p>Net P/L: <span style="color: {'#00ff00' if stats['net_profit_loss'] >= 0 else '#ff0000'}">${stats['net_profit_loss']:.2f}</span></p>
            </div>
        """, unsafe_allow_html=True)

        if stats["breakdown"]:
            st.markdown('<div class="glass"><h3>Holdings</h3>', unsafe_allow_html=True)
            breakdown_df = pd.DataFrame(stats["breakdown"])
            breakdown_df.index = range(1, len(breakdown_df) + 1)  # Start index from 1
            st.table(breakdown_df)
            st.markdown('</div>', unsafe_allow_html=True)

            if st.session_state.portfolio_history:
                df = pd.DataFrame(st.session_state.portfolio_history)
                fig = px.line(df, x="time", y="value", title="Portfolio Performance", template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)

    # Watchlist
    elif choice == "Watchlist 👀":
        st.title("Watchlist 👀")
        new_symbol = st.text_input("Add Symbol ➕").upper()
        if st.button("Add ➕"):
            if new_symbol and new_symbol not in user_data["watchlist"]:
                user_data["watchlist"].append(new_symbol)
                save_users(users)
                st.success(f"{new_symbol} added! ✅")

        if user_data["watchlist"]:
            st.markdown('<div class="glass"><h3>Your Watchlist</h3>', unsafe_allow_html=True)
            watchlist_placeholder = st.empty()
            while True:
                current_time = time.time()
                if current_time - st.session_state.watchlist_last_update >= 5:  # Update every 5 seconds
                    watchlist_data = fetch_watchlist_data(user_data["watchlist"])
                    watchlist_placeholder.table(watchlist_data)
                    st.session_state.watchlist_last_update = current_time
                time.sleep(0.1)
                break  # Break the loop to prevent infinite rerun in Streamlit
            st.markdown('</div>', unsafe_allow_html=True)

    # Transactions
    elif choice == "Transactions 📜":
        st.title("Transactions 📜")
        if user_data["transactions"]:
            st.markdown('<div class="glass"><h3>Transaction History</h3>', unsafe_allow_html=True)
            transactions_df = pd.DataFrame(user_data["transactions"])
            transactions_df = transactions_df.sort_values(by="time", ascending=False)
            transactions_df.index = range(1, len(transactions_df) + 1)  # Start index from 1
            st.table(transactions_df)
            st.markdown('</div>', unsafe_allow_html=True)

    # Profile Settings
    elif choice == "Profile Settings 🔧":
        st.title("Profile Settings 🔧")
        st.markdown('<div class="glass"><h3>Update Profile</h3>', unsafe_allow_html=True)
        new_username = st.text_input("New Username", value=st.session_state.username)
        new_email = st.text_input("New Email", value=st.session_state.email)
        new_password = st.text_input("New Password", type="password")
        if st.button("Update Profile"):
            if new_username != st.session_state.username and new_username in users:
                st.error("Username already exists! 🚫")
            else:
                old_username = st.session_state.username
                users[new_username] = users.pop(old_username)
                if new_password:
                    users[new_username]["password"] = new_password
                users[new_username]["email"] = new_email
                st.session_state.username = new_username
                st.session_state.email = new_email
                save_users(users)
                st.success("Profile updated! ✅")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # Market News
    elif choice == "Market News 📰":
        st.title("Market News 📰")
        st.markdown('<div class="glass"><h3>Latest Updates</h3>', unsafe_allow_html=True)
        for news in st.session_state.market_news:
            st.write(f"- {news}")
        st.markdown('</div>', unsafe_allow_html=True)

    # Market Movers
    elif choice == "Market Movers 📊":
        st.title("Market Movers 📊")
        st.markdown('<div class="glass"><h3>Top Gainers</h3>', unsafe_allow_html=True)
        for gainer in st.session_state.market_movers["gainers"]:
            st.write(f"- {gainer['symbol']}: +{gainer['change']}%")
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="glass"><h3>Top Losers</h3>', unsafe_allow_html=True)
        for loser in st.session_state.market_movers["losers"]:
            st.write(f"- {loser['symbol']}: {loser['change']}%")
        st.markdown('</div>', unsafe_allow_html=True)

    # Learning Resources
    elif choice == "Learning Resources 📖":
        st.title("Learning Resources 📖")
        st.markdown('<div class="glass"><h3>Trading Guides</h3>', unsafe_allow_html=True)
        st.write("- [Beginner’s Guide to Trading](#)")
        st.write("- [Understanding Candlestick Charts](#)")
        st.write("- [Risk Management Tips](#)")
        st.markdown('</div>', unsafe_allow_html=True)

    # TradeRiser Premium
    elif choice == "TradeRiser Premium 💎":
        st.title("TradeRiser Premium 💎")
        st.markdown("""
            <div class="premium-section">
                <h2 class="premium-title">Unlock TradeRiser Premium! 💎</h2>
                <p class="premium-subtitle">Elevate your trading experience with exclusive features designed for serious traders. 🚀</p>
                <div class="premium-features">
                    <div class="premium-feature-card">
                        <div class="premium-feature-icon">📊</div>
                        <div class="premium-feature-title">Advanced Analytics</div>
                        <div class="premium-feature-desc">In-depth market trends and predictions.</div>
                    </div>
                    <div class="premium-feature-card">
                        <div class="premium-feature-icon">🔔</div>
                        <div class="premium-feature-title">Priority Alerts</div>
                        <div class="premium-feature-desc">Real-time notifications first.</div>
                    </div>
                    <div class="premium-feature-card">
                        <div class="premium-feature-icon">📚</div>
                        <div class="premium-feature-title">Exclusive Insights</div>
                        <div class="premium-feature-desc">Daily reports and strategies.</div>
                    </div>
                    <div class="premium-feature-card">
                        <div class="premium-feature-icon">🤝</div>
                        <div class="premium-feature-title">Priority Support</div>
                        <div class="premium-feature-desc">24/7 dedicated assistance.</div>
                    </div>
                    <div class="premium-feature-card">
                        <div class="premium-feature-icon">💻</div>
                        <div class="premium-feature-title">Custom Dashboard</div>
                        <div class="premium-feature-desc">Personalize your trading setup.</div>
                    </div>
                    <div class="premium-feature-card">
                        <div class="premium-feature-icon">📈</div>
                        <div class="premium-feature-title">Real-Time Portfolio</div>
                        <div class="premium-feature-desc">Track your portfolio instantly.</div>
                    </div>
                    <div class="premium-feature-card">
                        <div class="premium-feature-icon">🤖</div>
                        <div class="premium-feature-title">AI Predictions</div>
                        <div class="premium-feature-desc">AI-driven market forecasts.</div>
                    </div>
                    <div class="premium-feature-card">
                        <div class="premium-feature-icon">👥</div>
                        <div class="premium-feature-title">Premium Community</div>
                        <div class="premium-feature-desc">Join elite traders.</div>
                    </div>
                    <div class="premium-feature-card">
                        <div class="premium-feature-icon">📉</div>
                        <div class="premium-feature-title">Advanced Charting</div>
                        <div class="premium-feature-desc">Enhanced charting tools.</div>
                    </div>
                    <div class="premium-feature-card">
                        <div class="premium-feature-icon">📝</div>
                        <div class="premium-feature-title">Trading Strategies</div>
                        <div class="premium-feature-desc">Personalized strategies.</div>
                    </div>
                </div>
                <p class="premium-more">And Many More! ✨</p>
            </div>
        """, unsafe_allow_html=True)

        if st.button("Join Waitlist"):
            subject = "TradeRiser Premium Waitlist Confirmation 🎉"
            body = f"""
🌟 Dear {st.session_state.username}, 🌟

🎉 Thank you for joining the TradeRiser Premium waitlist! You're one step closer to unlocking a world of exclusive features! 💎

🚀 Get ready for early access to these amazing features:
- 📊 **Advanced Analytics**: Dive deep into market trends and predictions! 📈
- 🔔 **Priority Alerts**: Be the first to get real-time notifications! 🚨
- 📚 **Exclusive Insights**: Daily market reports and expert strategies! 📖
- 🤝 **Priority Support**: 24/7 dedicated support just for you! 💬
- 💻 **Custom Dashboard**: Personalize your trading experience! 🖥️
- 📈 **Real-Time Portfolio Tracking**: Monitor your portfolio instantly! 📉
- 🤖 **AI-Driven Predictions**: Leverage AI for smarter trades! 🧠
- 👥 **Premium Community Access**: Network with elite traders! 🌐
- 📉 **Advanced Charting Tools**: Enhanced tools for better analysis! 📊
- 📝 **Personalized Trading Strategies**: Tailored strategies for success! ✍️
- ✨ **And Many More!**: Stay tuned for even more exciting features! 🎁

💡 We'll notify you as soon as TradeRiser Premium is available! Keep an eye on your inbox! 📧

Happy Trading! 😊
The TradeRiser Team 🌟
"""
            if send_email(st.session_state.email, subject, body):
                st.success("You’ve joined the TradeRiser Premium waitlist! A confirmation email has been sent. 💎")
            else:
                st.warning("You’ve joined the TradeRiser Premium waitlist! Failed to send confirmation email. 💎")

    # Risk Calculator
    elif choice == "Risk Calculator ⚖️":
        st.title("Risk Calculator ⚖️")
        st.markdown('<div class="glass"><h3>Calculate Your Risk</h3>', unsafe_allow_html=True)
        symbol = st.text_input("Ticker (e.g., AAPL)", value=st.session_state.symbol, key="risk_symbol").upper()
        current_price = st.session_state.last_price.get(symbol, get_current_price(symbol))
        risk_quantity = st.number_input("Quantity for Risk Calculation", min_value=1, value=1, key="risk_qty_standalone")
        stop_loss = st.number_input("Stop Loss Price", min_value=0.0, value=current_price * 0.95)
        take_profit = st.number_input("Take Profit Price", min_value=0.0, value=current_price * 1.05)
        potential_loss = (current_price - stop_loss) * risk_quantity
        potential_profit = (take_profit - current_price) * risk_quantity
        st.write(f"Potential Loss: ${potential_loss:.2f}")
        st.write(f"Potential Profit: ${potential_profit:.2f}")
        st.markdown('</div>', unsafe_allow_html=True)

    # Recent Data
    elif choice == "Recent Data 📈":
        st.title("Recent Data 📈")
        st.markdown('<div class="glass"><h3>Live Stock Data</h3>', unsafe_allow_html=True)
        if not st.session_state.recent_data.empty:
            recent_data_df = st.session_state.recent_data
            recent_data_df.index = range(1, len(recent_data_df) + 1)  # Start index from 1
            st.table(recent_data_df)
        else:
            st.write("Fetching data...")
        st.markdown('</div>', unsafe_allow_html=True)

    # Price Alerts
    elif choice == "Price Alerts 🔔":
        st.title("Price Alerts 🔔")
        st.markdown('<div class="glass"><h3>Set Price Alerts</h3>', unsafe_allow_html=True)
        new_symbol = st.text_input("Add Symbol for Alert ➕").upper()
        if new_symbol:
            company_name = get_company_name(new_symbol)
            current_price = get_current_price(new_symbol)
            st.write(f"Company: {company_name}")
            st.write(f"Current Price: ${current_price:.2f}")
        target_price = st.number_input("Target Price", min_value=0.0, value=0.0)
        if st.button("Set Alert 🔔"):
            if new_symbol and target_price > 0:
                alert = {"symbol": new_symbol, "target_price": target_price}
                st.session_state.price_alerts.append(alert)
                user_data["price_alerts"] = st.session_state.price_alerts
                save_users(users)
                st.success(f"Alert set for {new_symbol} at ${target_price:.2f}! You’ll receive an email when the price is reached.")
            else:
                st.error("Please enter a valid symbol and target price! 🚫")

        if st.session_state.price_alerts:
            st.markdown('<h3>Active Alerts</h3>', unsafe_allow_html=True)
            for alert in st.session_state.price_alerts:
                st.write(f"{alert['symbol']}: ${alert['target_price']:.2f}")
        st.markdown('</div>', unsafe_allow_html=True)

# Run the app
if not st.session_state.logged_in:
    if 'show_register' not in st.session_state or not st.session_state.show_register:
        login()
    else:
        register()
else:
    main_app()
