import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd

def get_driver():
    options = Options()
    # These 4 lines are MANDATORY for Streamlit Cloud
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # This prevents the "Automation Detected" block
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Main App Logic
st.title("🚂 RTIS Braking Profile Analyzer")

if st.button('Start Live Scraping'):
    with st.spinner('Accessing RTIS Portal... Please wait.'):
        driver = get_driver()
        try:
            driver.get("https://rtis.cris.org.in") # Replace with your actual URL
            
            # This is where we wait for the table to load
            time.sleep(5) 
            
            html = driver.page_source
            tables = pd.read_html(html)
            
            if tables:
                st.success("Data Found!")
                st.dataframe(tables[0])
            else:
                st.error("No data tables found on the page.")
                
        except Exception as e:
            st.error(f"Connection Failed: {e}")
        finally:
            driver.quit()
