import streamlit as st
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time
from datetime import datetime

def setup_driver():
    """Initialize Chrome driver in headless mode"""
    try:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(
            service=service,
            options=chrome_options,
            seleniumwire_options={
                'verify_ssl': False  # Ignore SSL verification
            }
        )
        return driver
    except Exception as e:
        st.error(f"Failed to setup browser: {str(e)}")
        return None

def connect_to_arduino(driver):
    """Connect to Arduino Web Editor and setup device"""
    try:
        # Navigate to Arduino Web Editor
        driver.get("https://app.arduino.cc/sketches/9dde49f6-08e5-4bc5-8dab-33849adbb868")
        
        # Wait for device selection button
        wait = WebDriverWait(driver, 10)
        unknown_button = wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, "_device-name_12ggg_205"))
        )
        unknown_button.click()
        
        # Find and fill the search input
        search_input = wait.until(
            EC.presence_of_element_located((By.ID, "react-aria6138362191-:r10:"))
        )
        search_input.send_keys("DOIT ESP32 DEVKIT V1")
        search_input.send_keys(Keys.TAB)
        search_input.send_keys(Keys.ENTER)
        
        # Open Serial Monitor
        serial_monitor = wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, "_open-serial-monitor-button_1y7x9_356"))
        )
        serial_monitor.click()
        
        # Switch to Serial Monitor window
        driver.get("https://app.arduino.cc/sketches/monitor")
        
        # Change baud rate to 115200
        baud_button = wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, "_x-small_wmean_200"))
        )
        baud_button.click()
        
        baud_115200 = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='115200']"))
        )
        baud_115200.click()
        
        return True
    except Exception as e:
        st.error(f"Failed to connect to Arduino: {str(e)}")
        return False

def get_serial_output(driver):
    """Get serial monitor output"""
    try:
        output_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "serial-output"))
        )
        return output_element.text
    except:
        return "Waiting for serial output..."

def main():
    st.title("Smart Entrance Control System")
    
    # Initialize session state
    if 'driver' not in st.session_state:
        st.session_state.driver = None
    if 'connected' not in st.session_state:
        st.session_state.connected = False
    
    # Connection section
    if not st.session_state.connected:
        if st.button("Connect to Arduino"):
            # Setup driver
            driver = setup_driver()
            if driver:
                st.session_state.driver = driver
                
                # Connect to Arduino
                if connect_to_arduino(driver):
                    st.session_state.connected = True
                    st.success("Connected to Arduino Web Editor!")
    
    # If connected, show controls and monitoring
    if st.session_state.connected and st.session_state.driver:
        # Create columns for controls
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Refresh Data"):
                output = get_serial_output(st.session_state.driver)
                st.text_area("Serial Monitor Output", output, height=300)
        
        with col2:
            st.metric("Connection Status", "Connected")
            st.metric("Last Update", datetime.now().strftime("%H:%M:%S"))
    
    # Cleanup on session end
    if st.session_state.driver:
        try:
            st.session_state.driver.quit()
        except:
            pass

if __name__ == "__main__":
    main()
