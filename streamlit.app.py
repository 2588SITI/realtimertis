import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def scrape_rtis_fixed():
    chrome_options = Options()
    
    # 1. CRITICAL: Don't use headless mode while debugging "spinning"
    # Once it works, you can turn --headless back on.
    # chrome_options.add_argument("--headless") 
    
    # 2. Make the browser look like a real Chrome user
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        st.write("🔄 Connecting to Portal...")
        driver.get("https://your-internal-portal-url.com") # Replace with actual URL

        # 3. Explicit Wait: Instead of time.sleep, wait for the USERNAME box to appear
        wait = WebDriverWait(driver, 20)
        user_field = wait.until(EC.presence_of_element_located((By.ID, "username_id"))) # Update ID
        
        user_field.send_keys("YOUR_ID")
        driver.find_element(By.ID, "password_id").send_keys("YOUR_PASS") # Update ID
        driver.find_element(By.ID, "login_button").click()

        st.write("✅ Login Successful. Waiting for Table Data...")

        # 4. Wait specifically for the TABLE to load (this stops the 'ghol ghol' spinning)
        # Replace 'table_id' with the actual ID of the RTIS data grid
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        
        # Get the page source and close driver immediately to free memory
        html_content = driver.page_source
        df_list = pd.read_html(html_content)
        
        # Find the correct table from the list (usually the largest one)
        df = max(df_list, key=len)
        return df

    except Exception as e:
        st.error(f"❌ Error: {e}")
        return None
    finally:
        driver.quit()

# Streamlit Trigger
if st.button('Fetch Live Braking Data'):
    data = scrape_rtis_fixed()
    if data is not None:
        st.success("Data Fetched!")
        st.dataframe(data)
