import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from datetime import datetime

# --- CONFIGURATION ---
PORTAL_URL = "https://your-internal-railway-portal.gov.in" # Update this
USERNAME = "your_official_id"
PASSWORD = "your_password"

# --- SELENIUM SCRAPER FUNCTION ---
def scrape_rtis_live():
    chrome_options = Options()
    chrome_options.add_argument("--headless") # Runs without opening a window
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        driver.get(PORTAL_URL)
        # Standard login sequence
        driver.find_element(By.ID, "user_id").send_keys(USERNAME)
        driver.find_element(By.ID, "pass").send_keys(PASSWORD)
        driver.find_element(By.ID, "login_btn").click()
        
        time.sleep(3) # Wait for page load
        
        # Scrape the table (Assume ID 'rtis_table')
        table_element = driver.find_element(By.ID, "rtis_table")
        html_content = table_element.get_attribute('outerHTML')
        
        df = pd.read_html(html_content)[0]
        # Standardize columns (update names based on your portal)
        df = df[['Loco_No', 'Speed', 'Latitude', 'Longitude']]
        df['Timestamp'] = datetime.now()
        return df
    except Exception as e:
        st.error(f"Scraping Error: {e}")
        return None
    finally:
        driver.quit()

# --- BRAKING ANALYSIS LOGIC ---
def process_braking(df_history):
    if len(df_history) < 2:
        return df_history
    
    # Calculate Acceleration (m/s^2)
    # v_diff in m/s, t_diff in seconds
    df_history = df_history.sort_values('Timestamp')
    df_history['Speed_ms'] = df_history['Speed'] * (5/18)
    df_history['Time_diff'] = df_history['Timestamp'].diff().dt.total_seconds()
    df_history['Deceleration'] = df_history['Speed_ms'].diff() / df_history['Time_diff']
    
    return df_history

# --- STREAMLIT UI ---
st.set_page_config(page_title="RTIS Live Braking Analyzer", layout="wide")
st.title("🚂 RTIS Live Braking Profile (ADEE TRO)")

if 'journey_data' not in st.session_state:
    st.session_state.journey_data = pd.DataFrame()

# Sidebar Controls
target_loco = st.sidebar.text_input("Enter Loco Number", value="30001")
auto_refresh = st.sidebar.checkbox("Enable Live Tracking")

if auto_refresh:
    new_data = scrape_rtis_live()
    if new_data is not None:
        # Filter for our specific Loco and append to history
        loco_update = new_data[new_data['Loco_No'] == target_loco]
        st.session_state.journey_data = pd.concat([st.session_state.journey_data, loco_update]).drop_duplicates()
        st.session_state.journey_data = process_braking(st.session_state.journey_data)

# Dashboard Layout
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"Speed Profile: Loco {target_loco}")
    if not st.session_state.journey_data.empty:
        fig = go.Figure()
        
        # Plot Speed
        fig.add_trace(go.Scatter(
            x=st.session_state.journey_data['Timestamp'], 
            y=st.session_state.journey_data['Speed'],
            mode='lines+markers',
            name='Speed (kmph)',
            line=dict(color='royalblue', width=3)
        ))
        
        # Highlight Heavy Braking (Deceleration < -0.5 m/s^2)
        heavy_braking = st.session_state.journey_data[st.session_state.journey_data['Deceleration'] < -0.5]
        fig.add_trace(go.Scatter(
            x=heavy_braking['Timestamp'], 
            y=heavy_braking['Speed'],
            mode='markers',
            name='Heavy Braking Event',
            marker=dict(color='red', size=12, symbol='x')
        ))
        
        fig.update_layout(xaxis_title="Time", yaxis_title="Speed (kmph)")
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Current Status")
    if not st.session_state.journey_data.empty:
        current = st.session_state.journey_data.iloc[-1]
        st.metric("Current Speed", f"{current['Speed']} kmph")
        st.metric("Lat/Long", f"{current['Latitude']}, {current['Longitude']}")
        
        if current['Deceleration'] < -0.6:
            st.error("⚠️ Emergency Braking Detected!")
        elif current['Deceleration'] < -0.3:
            st.warning("Service Braking in Progress")

# Auto-refresh logic (every 30 seconds)
if auto_refresh:
    time.sleep(30)
    st.rerun()
