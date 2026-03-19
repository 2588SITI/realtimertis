import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import numpy as np

# --- 1. SYSTEM CONFIG ---
st.set_page_config(page_title="RTIS Braking Pattern", layout="wide")

def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Pointing to local Chrome for your office PC
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

# --- 2. DATA SOURCE (MOCKING RTIS FEED) ---
def get_rtis_enabled_locos():
    # In production, this scrapes the 'Live Summary' page of the RTIS portal
    return ["WAP7-30001", "WAP7-37012", "WAG9-31245", "WAG9-32001", "WAG12-60010"]

def fetch_loco_trajectory(loco_id):
    """
    Simulates fetching the last 5km of trajectory data for a loco.
    In production: Scrapes the 'Movement Log' for the selected Loco.
    """
    # Create a synthetic braking pattern centered at a stop
    dist = np.linspace(-1500, 1500, 60) # Meters relative to stop
    speed = []
    for d in dist:
        if d < 0: # Braking phase
            s = max(0, 100 + (d/10)) # Linear deceleration from 100 to 0
        else: # Acceleration phase
            s = min(100, (d/12)) # Acceleration from 0 up to 100
        speed.append(s)
    
    return pd.DataFrame({'Distance_m': dist, 'Speed': speed})

# --- 3. DASHBOARD UI ---
st.title("🚂 RTIS Braking Pattern & Stop Analysis")
st.markdown("---")

# Sidebar: Loco Selection
st.sidebar.header("Locomotive Filter")
all_locos = get_rtis_enabled_locos()
selected_loco = st.sidebar.selectbox("Select RTIS Enabled Loco", options=all_locos)

st.sidebar.markdown("### Analysis Parameters")
st.sidebar.write("📍 **Window:** -1000m to +1000m")
st.sidebar.write("🚩 **Reference:** Stopping Point (Speed=0)")

if st.sidebar.button("Generate Braking Pattern"):
    with st.spinner(f"Analyzing trajectory for {selected_loco}..."):
        # Fetching data
        df = fetch_loco_trajectory(selected_loco)
        
        # Filtering for the 1000m back/ahead requirement
        mask = (df['Distance_m'] >= -1000) & (df['Distance_m'] <= 1000)
        plot_df = df.loc[mask]

        # --- 4. VISUALIZATION ---
        fig = go.Figure()

        # Main Speed Line
        fig.add_trace(go.Scatter(
            x=plot_df['Distance_m'], 
            y=plot_df['Speed'],
            mode='lines+markers',
            name='Loco Speed',
            line=dict(color='cyan', width=3),
            fill='tozeroy'
        ))

        # Stop Point Indicator
        fig.add_vline(x=0, line_dash="dash", line_color="red", 
                      annotation_text="STOP POINT", annotation_position="top right")

        # Threshold Shading
        fig.add_vrect(x0=-1000, x1=0, fillcolor="red", opacity=0.1, 
                      layer="below", line_width=0, annotation_text="Braking Pattern")
        fig.add_vrect(x0=0, x1=1000, fillcolor="green", opacity=0.1, 
                      layer="below", line_width=0, annotation_text="Acceleration")

        fig.update_layout(
            template="plotly_dark",
            xaxis_title="Distance relative to Stop (Meters)",
            yaxis_title="Speed (Kmph)",
            title=f"Braking Curve: {selected_loco}",
            hovermode="x unified"
        )

        st.plotly_chart(fig, use_container_width=True)

        # --- 5. ANALYTICS TABLE ---
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Braking Analytics (-1000m to 0m)")
            entry_speed = plot_df.iloc[0]['Speed']
            avg_decel = entry_speed / 1000 # Kmph per meter
            st.write(f"**Approach Speed:** {entry_speed:.1f} Kmph")
            st.write(f"**Braking Slope:** {avg_decel:.4f} Kmph/m")
        
        with col2:
            st.subheader("Acceleration Analytics (0m to +1000m)")
            exit_speed = plot_df.iloc[-1]['Speed']
            st.write(f"**Exit Speed:** {exit_speed:.1f} Kmph")
            if exit_speed < 20:
                st.warning("⚠️ Slow Acceleration Detected")
            else:
                st.success("✅ Normal Acceleration")
