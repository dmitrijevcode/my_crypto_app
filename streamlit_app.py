import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json
import os
from datetime import datetime
import hashlib
import time

# Create directory for storing user data if it doesn't exist
DATA_DIR = "user_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

import time

def get_crypto_data(symbols):
    """Gets current cryptocurrency prices using yfinance."""
    crypto_tickers = [f"{symbol}-USD" for symbol in symbols]
    data = {}
    
    for ticker in crypto_tickers:
        try:
            crypto = yf.Ticker(ticker)
            # Get the historical data
            hist = crypto.history(period="1d")
            # Check if there's data in the DataFrame
            if not hist.empty:
                price = hist.iloc[-1]['Close']
                # Extract symbol without '-USD'
                symbol = ticker.split('-')[0]
                data[symbol] = price
            else:
                st.warning(f"No data available for {ticker}")
            # Add a small delay between requests
            time.sleep(0.5)
        except Exception as e:
            st.warning(f"Failed to get data for {ticker}: {e}")
    
    return data

def hash_password(password):
    """Hashes the password for secure storage."""
    return hashlib.sha256(password.encode()).hexdigest()

def save_user_portfolio(username, portfolio):
    """Saves user portfolio to a JSON file."""
    file_path = os.path.join(DATA_DIR, f"{username}.json")
    
    # Add last update date
    data_to_save = {
        "portfolio": portfolio,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data_to_save, f, ensure_ascii=False)
    
    return True

def load_user_portfolio(username):
    """Loads user portfolio from a JSON file."""
    file_path = os.path.join(DATA_DIR, f"{username}.json")
    
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get("portfolio", {}), data.get("last_updated", "")
    
    return {}, ""

def user_exists(username):
    """Checks if a user exists."""
    return os.path.exists(os.path.join(DATA_DIR, f"{username}.json"))

def save_user_credentials(username, password_hash):
    """Saves user credentials."""
    users_file = os.path.join(DATA_DIR, "users.json")
    
    if os.path.exists(users_file):
        with open(users_file, 'r') as f:
            users = json.load(f)
    else:
        users = {}
    
    users[username] = password_hash
    
    with open(users_file, 'w') as f:
        json.dump(users, f)

def check_credentials(username, password_hash):
    """Verifies user credentials."""
    users_file = os.path.join(DATA_DIR, "users.json")
    
    if not os.path.exists(users_file):
        return False
    
    with open(users_file, 'r') as f:
        users = json.load(f)
    
    return username in users and users[username] == password_hash

# Session management
def init_session_state():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "portfolio" not in st.session_state:
        st.session_state.portfolio = {}
    if "last_updated" not in st.session_state:
        st.session_state.last_updated = ""

def login_user(username, password):
    password_hash = hash_password(password)
    if check_credentials(username, password_hash):
        st.session_state.authenticated = True
        st.session_state.username = username
        # Load user portfolio
        portfolio, last_updated = load_user_portfolio(username)
        st.session_state.portfolio = portfolio
        st.session_state.last_updated = last_updated
        return True
    return False

def register_user(username, password):
    if user_exists(username):
        return False
    
    password_hash = hash_password(password)
    save_user_credentials(username, password_hash)
    # Create empty portfolio
    save_user_portfolio(username, {})
    return True

def logout_user():
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.portfolio = {}
    st.session_state.last_updated = ""

# Main interface
def main():
    st.title("Cryptocurrency Portfolio")
    
    init_session_state()
    
    # Display login page if user is not authenticated
    if not st.session_state.authenticated:
        show_login_page()
    else:
        show_portfolio_page()

def show_login_page():
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login"):
            if login_user(username, password):
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Incorrect username or password")
    
    with tab2:
        st.subheader("Register New User")
        new_username = st.text_input("Username", key="reg_username")
        new_password = st.text_input("Password", type="password", key="reg_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
        
        if st.button("Register"):
            if new_password != confirm_password:
                st.error("Passwords do not match")
            elif not new_username or not new_password:
                st.error("Username and password cannot be empty")
            else:
                if register_user(new_username, new_password):
                    st.success("Registration successful! You can now login.")
                else:
                    st.error("User with this username already exists")

def show_portfolio_page():
    st.sidebar.write(f"Hello, {st.session_state.username}!")
    if st.sidebar.button("Logout"):
        logout_user()
        st.rerun()
    
    # Get list of all available cryptocurrencies
    default_coins = ["BTC", "ETH", "BNB", "ADA", "SOL", "XRP", "DOT", "DOGE", "LTC", "TON11419", "AVAX", "SUI20947", "ARB11841"]
    
    # Get current prices
    crypto_prices = get_crypto_data(default_coins)
    
    # Display and edit portfolio
    st.sidebar.header("Edit Portfolio")
    
    # Create a copy of the portfolio for editing
    edited_portfolio = st.session_state.portfolio.copy()
    
    # Select cryptocurrencies to display
    selected_coins = st.sidebar.multiselect(
        "Select cryptocurrencies to display",
        default_coins,
        default=[coin for coin in st.session_state.portfolio.keys() if coin in default_coins] or ["BTC", "ETH"]
    )
    
    # Edit amounts for selected cryptocurrencies
    for coin in selected_coins:
        current_amount = edited_portfolio.get(coin, 0.0)
        edited_portfolio[coin] = st.sidebar.number_input(
            f"{coin} (amount):",
            min_value=0.0,
            format="%.6f",
            value=float(current_amount)
        )
    
    # Button to save changes
    if st.sidebar.button("Save Changes"):
        # Remove zero values
        edited_portfolio = {k: v for k, v in edited_portfolio.items() if v > 0}
        
        # Save updated portfolio
        save_user_portfolio(st.session_state.username, edited_portfolio)
        st.session_state.portfolio = edited_portfolio
        st.session_state.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.sidebar.success("Portfolio successfully updated!")
    
    # Display last update information
    if st.session_state.last_updated:
        st.write(f"Last updated: {st.session_state.last_updated}")
    
    # Calculate portfolio value
    portfolio_for_display = {k: v for k, v in st.session_state.portfolio.items() if k in crypto_prices}
    total_value = sum(portfolio_for_display.get(coin, 0) * crypto_prices.get(coin, 0) for coin in portfolio_for_display)
    
    st.write(f"### Total Portfolio Value: **${total_value:,.2f}**")
    
    # Data table
    if portfolio_for_display:
        portfolio_data = pd.DataFrame({
            "Coin": list(portfolio_for_display.keys()),
            "Amount": list(portfolio_for_display.values()),
            "Price (USD)": [crypto_prices.get(coin, 0) for coin in portfolio_for_display],
            "Total Value (USD)": [portfolio_for_display[coin] * crypto_prices.get(coin, 0) for coin in portfolio_for_display]
        })
        
        # Sort by value (descending)
        portfolio_data = portfolio_data.sort_values(by="Total Value (USD)", ascending=False).reset_index(drop=True)
        
        st.dataframe(portfolio_data)
        
        # Visualization
        if total_value > 0:
            fig = px.pie(
                portfolio_data, 
                values="Total Value (USD)", 
                names="Coin", 
                title="Portfolio Distribution"
            )
            st.plotly_chart(fig)
        
            # Add bar chart for asset value comparison
            fig_bar = px.bar(
                portfolio_data, 
                x="Coin", 
                y="Total Value (USD)",
                title="Asset Values"
            )
            st.plotly_chart(fig_bar)
    else:
        st.info("Your portfolio is empty. Add cryptocurrencies in the sidebar.")

if __name__ == "__main__":
    main()
