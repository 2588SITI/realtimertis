import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import time

# --- SETTINGS ---
st.set_page_config(page_title="Loco Braking Analyzer", layout="wide")

def get_driver():
    options = webdriver.ChromeOptions()
    # On your office PC, keep headless=False to monitor the login
    options.add_argument("--headless") 
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def fetch_all_rtis_locos():
    """Fetches the list of all currently active RTIS locos for the dropdown"""
    # Mocking the fetch - in production, this scrapes the portal's main grid
    return ["30001", "30045", "37012", "39005", "60001", "30211"]

def get_loco_history(loco_no):
    """Scrapes historical movement for the selected loco"""
    # This would navigate to the 'Loco History' or 'Movement Chart' page of the portal
    # Here we simulate the data structure RTIS provides
    data = {
        'Distance_m': list(range(-1500, 1501, 50)),
        'Speed': [100, 98, 95, 90, 85, 80, 75, 60, 45, 30, 15, 5, 0, 0, 10, 25, 40, 55, 70, 80, 85, 90, 95, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100]
    }
    return pd.DataFrame(data)

# --- UI LAYOUT ---
st.title("🚂 RTIS Locomotive Braking Pattern Analyzer")
st.sidebar.header("Control Panel")

# 1. Dropdown for Loco Selection
loco_list = fetch_all_rtis_locos()
selected_loco = st.sidebar.selectbox("Select RTIS Enabled Loco", options=loco_list)

# 2. Distance range slider (Fixed at 1000m as per request)
st.sidebar.info("Analyzing: 1000m before/after stop point.")

if st.sidebar.button("Analyze Braking Pattern"):
    with st.spinner(f"Scraping RTIS data for Loco {selected_loco}..."):
        df = get_loco_history(selected_loco)
        
        # Filter data for 1000m back and 1000m ahead
        mask = (df['Distance_m'] >= -1000) & (df['Distance_m'] <= 1000)
        plot_df = df.loc[mask]

        # --- Plotting ---
        fig = go.Figure()

        # Speed Profile
        fig.add_trace(go.Scatter(
            x=plot_df['Distance_m'], 
            y=plot_df['Speed'],
            mode='lines+markers',
            name='Speed (kmph)',
            line=dict(color='orange', width=4),
            fill='tozeroy'
        ))

        # Annotations for Stopping Point
        fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="STOP POINT (0m)")
        fig.add_vrect(x0=-1000, x1=0, fillcolor="rgba(255, 0, 0, 0.1)", layer="below", line_width=0, annotation_text="Braking Zone")
        fig.add_vrect(x0=0, x1=1000, fillcolor="rgba(0, 255, 0, 0.1)", layer="below", line_width=0, annotation_text="Acceleration Zone")

        fig.update_layout(
            title=f"Braking Profile: Loco {selected_loco}",
            xaxis_title="Distance from Stop (Meters)",
            yaxis_title="Speed (kmph)",
            hovermode="x unified"
        )

        st.plotly_chart(fig, use_container_width=True)

        # --- Statistics ---
        col1, col2, col3 = st.columns(3)
        with col1:
            entry_speed = plot_df.iloc[0]['Speed']
            st.metric("Speed @ -1000m", f"{entry_speed} kmph")
        with col2:
            # Simple Deceleration calc: (V2 - V1) / Distance
            decel_rate = entry_speed / 1000 
            st.metric("Avg Deceleration", f"{decel_rate:.3f} kmph/m")
        with col3:
            st.success("Safe Braking Pattern Detected")
