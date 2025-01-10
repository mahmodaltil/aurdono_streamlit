import streamlit as st
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def open_arduino_web_editor():
    driver = setup_driver()
    
    # Open Arduino Web Editor
    driver.get("https://app.arduino.cc/sketches/9dde49f6-08e5-4bc5-8dab-33849adbb868")
    
    # Wait for the device selection button
    wait = WebDriverWait(driver, 10)
    unknown_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "_device-name_12ggg_205")))
    unknown_button.click()
    
    # Find and fill the search input
    search_input = wait.until(EC.presence_of_element_located((By.ID, "react-aria6138362191-:r10:")))
    search_input.send_keys("DOIT ESP32 DEVKIT V1")
    search_input.send_keys(Keys.TAB)
    search_input.send_keys(Keys.ENTER)
    
    # Open Serial Monitor
    serial_monitor = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "_open-serial-monitor-button_1y7x9_356")))
    serial_monitor.click()
    
    # Switch to Serial Monitor window
    driver.get("https://app.arduino.cc/sketches/monitor")
    
    # Change baud rate to 115200
    baud_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "_x-small_wmean_200")))
    baud_button.click()
    baud_115200 = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='115200']")))
    baud_115200.click()
    
    return driver

def get_serial_output(driver):
    try:
        serial_output = driver.find_element(By.CLASS_NAME, "serial-output").text
        return serial_output
    except:
        return "Waiting for serial output..."

def main():
    st.title("Smart Entrance Control System")
    
    if 'driver' not in st.session_state:
        st.session_state.driver = None
    
    if st.button("Connect to Arduino"):
        st.session_state.driver = open_arduino_web_editor()
        st.success("Connected to Arduino Web Editor!")
    
    if st.session_state.driver:
        # Create a placeholder for the serial output
        serial_output = st.empty()
        
        # Continuously update the serial output
        while True:
            output = get_serial_output(st.session_state.driver)
            serial_output.text_area("Serial Monitor Output:", output, height=400)
            time.sleep(1)

if __name__ == "__main__":
    main()
