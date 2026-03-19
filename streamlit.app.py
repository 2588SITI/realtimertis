import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime

# --- SETTINGS & CONFIG ---
st.set_page_config(page_title="RTIS Braking Analyzer", layout="wide")

# Replace these with your actual portal details
PORTAL_URL = "https://rtis.cris.org.in" # Update to your specific URL
USER_ID = "YOUR_ID"
PASS_WD = "YOUR_PASSWORD"

def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # Critical for Streamlit Cloud Linux Environment
    options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")
    
    return webdriver.Chrome(service=service, options=options)

def scrape_rtis_data():
    driver = get_driver()
    try:
        driver.get(PORTAL_URL)
        wait = WebDriverWait(driver, 15)
        
        # 1. Automated Login (Adjust IDs based on your F12 inspection)
        # wait.until(EC.presence_of_element_located((By.ID, "txtUser"))).send_keys(USER_ID)
        # driver.find_element(By.ID, "txtPass").send_keys(PASS_WD)
        # driver.find_element(By.ID, "btnLogin").click()
        
        # 2. Wait for the Data Table to appear
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        
        # 3. Read Table into Pandas
        dfs = pd.read_html(driver.page_source)
        df = max(dfs, key=len) # Pick the largest table (usually the data grid)
        
        # Clean data (Mocking columns - update to match your portal)
        df['Timestamp'] = datetime.now()
        return df
    except Exception as e:
        st.error(f"Scraping failed: {e}")
        return None
    finally:
        driver.quit()

# --- BRAKING CALCULATIONS ---
def calculate_deceleration(df):
    if len(df) < 2: return df
    df = df.sort_values('Timestamp')
    # Convert kmph to m/s and calculate delta
    df['Speed_ms'] = df['Speed'] * (5/18)
    df['Time_diff'] = df['Timestamp'].diff().dt.total_seconds()
    df['Deceleration'] = df['Speed_ms'].diff() / df['Time_diff']
    return df

# --- UI LAYOUT ---
st.title("🚂 RTIS Real-Time Braking Profile")
st.info("Monitoring active locomotives for heavy braking exceptions.")

if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame()

col1, col2 = st.columns([3, 1])

if st.sidebar.button("Fetch Live RTIS Data"):
    raw_data = scrape_rtis_data()
    if raw_data is not None:
        st.session_state.history = pd.concat([st.session_state.history, raw_data]).tail(100)
        st.session_state.history = calculate_deceleration(st.session_state.history)

with col1:
    if not st.session_state.history.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=st.session_state.history['Timestamp'], y=st.session_state.history['Speed'], name="Speed (kmph)"))
        
        # Highlight Heavy Braking (Decel < -0.5 m/s^2)
        braking = st.session_state.history[st.session_state.history['Deceleration'] < -0.5]
        fig.add_trace(go.Scatter(x=braking['Timestamp'], y=braking['Speed'], mode='markers', name="Heavy Braking", marker=dict(color='red', size=10)))
        
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Latest Alerts")
    if not st.session_state.history.empty:
        latest = st.session_state.history.iloc[-1]
        st.metric("Current Speed", f"{latest['Speed']} Kmph")
        if latest['Deceleration'] < -0.6:
            st.error("⚠️ Emergency Braking Detected")
