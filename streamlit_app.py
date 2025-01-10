import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime

def connect_to_arduino():
    # Initialize session
    session = requests.Session()
    
    try:
        # Login to Arduino Web Editor (you'll need to add your credentials)
        login_url = "https://auth.arduino.cc/login"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        # Store the session in streamlit state
        st.session_state.arduino_session = session
        return True
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return False

def open_serial_monitor():
    if 'arduino_session' not in st.session_state:
        return "Not connected to Arduino"
    
    try:
        # Access the serial monitor URL
        monitor_url = "https://app.arduino.cc/sketches/9dde49f6-08e5-4bc5-8dab-33849adbb868"
        response = st.session_state.arduino_session.get(monitor_url)
        
        if response.status_code == 200:
            return "Connected to Serial Monitor"
        else:
            return f"Error accessing Serial Monitor: {response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    st.title("Smart Entrance Control System")
    
    # Initialize session state for values
    if 'temperature' not in st.session_state:
        st.session_state.temperature = 25
    if 'humidity' not in st.session_state:
        st.session_state.humidity = 60
    if 'door_status' not in st.session_state:
        st.session_state.door_status = "Closed"
    if 'last_update' not in st.session_state:
        st.session_state.last_update = datetime.now()
    if 'connected' not in st.session_state:
        st.session_state.connected = False
    if 'serial_output' not in st.session_state:
        st.session_state.serial_output = ""
    if 'activities' not in st.session_state:
        st.session_state.activities = []
    
    # Add header and description
    st.header("System Status")
    st.write("This is a monitoring interface for the Smart Entrance Control System.")
    
    # Connection button
    if not st.session_state.connected:
        if st.button("Connect to Arduino"):
            if connect_to_arduino():
                st.session_state.connected = True
                st.success("Connected to Arduino Web Editor!")
                # Open Serial Monitor
                result = open_serial_monitor()
                st.info(result)
    
    # Display connection status
    status = "Connected" if st.session_state.connected else "Disconnected"
    st.sidebar.write(f"Status: {status}")
    
    # Display system information
    st.subheader("System Information")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(label="Temperature", value=f"{st.session_state.temperature}°C")
        st.metric(label="Humidity", value=f"{st.session_state.humidity}%")
    
    with col2:
        st.metric(label="Door Status", value=st.session_state.door_status)
        st.metric(label="Last Update", value=st.session_state.last_update.strftime("%H:%M:%S"))
    
    # If connected, show controls and data
    if st.session_state.connected:
        # Create columns for controls
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Open Door"):
                st.session_state.serial_output += "\nSending open door command..."
        
        with col2:
            if st.button("Close Door"):
                st.session_state.serial_output += "\nSending close door command..."
        
        # Display serial output
        st.text_area("Serial Monitor Output", st.session_state.serial_output, height=400)
        
        # Auto-refresh button
        if st.button("Refresh Data"):
            new_data = open_serial_monitor()
            st.session_state.serial_output += f"\n{new_data}"
            st.experimental_rerun()
    
    # Add a section for recent activities
    st.subheader("Recent Activities")
    
    # Add activity log
    for activity in st.session_state.activities:
        st.text(activity)
    
    # Simulate new data (in real implementation, this would come from Arduino)
    if st.button("Simulate New Data"):
        import random
        st.session_state.temperature = round(random.uniform(20, 30), 1)
        st.session_state.humidity = round(random.uniform(50, 70))
        new_status = "Open" if st.session_state.door_status == "Closed" else "Closed"
        st.session_state.door_status = new_status
        st.session_state.last_update = datetime.now()
        
        # Add to activity log
        activity = f"[{st.session_state.last_update.strftime('%H:%M:%S')}] "
        activity += f"Temperature: {st.session_state.temperature}°C, "
        activity += f"Humidity: {st.session_state.humidity}%, "
        activity += f"Door: {st.session_state.door_status}"
        st.session_state.activities.insert(0, activity)
        
        # Keep only last 10 activities
        st.session_state.activities = st.session_state.activities[:10]
        st.experimental_rerun()

if __name__ == "__main__":
    main()
