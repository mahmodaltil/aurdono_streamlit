import streamlit as st
import requests
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Arduino Cloud API configuration
ARDUINO_API_URL = "https://api2.arduino.cc/iot/v2"
CLIENT_ID = os.getenv("ARDUINO_CLIENT_ID")
CLIENT_SECRET = os.getenv("ARDUINO_CLIENT_SECRET")
DEVICE_ID = os.getenv("ARDUINO_DEVICE_ID")

def get_arduino_token():
    """Get access token from Arduino Cloud"""
    try:
        response = requests.post(
            "https://api2.arduino.cc/iot/v1/clients/token",
            data={
                "grant_type": "client_credentials",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "audience": "https://api2.arduino.cc/iot"
            }
        )
        return response.json().get("access_token")
    except Exception as e:
        st.error(f"Failed to get Arduino token: {str(e)}")
        return None

def get_device_status(token):
    """Get device status from Arduino Cloud"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{ARDUINO_API_URL}/devices/{DEVICE_ID}",
            headers=headers
        )
        return response.json()
    except Exception as e:
        st.error(f"Failed to get device status: {str(e)}")
        return None

def get_serial_monitor(token):
    """Get serial monitor data from Arduino Cloud"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{ARDUINO_API_URL}/devices/{DEVICE_ID}/serial",
            headers=headers
        )
        return response.json()
    except Exception as e:
        st.error(f"Failed to get serial data: {str(e)}")
        return None

def main():
    st.title("Smart Entrance Control System")
    
    # Check for API credentials
    if not all([CLIENT_ID, CLIENT_SECRET, DEVICE_ID]):
        st.error("""
        Please set up your Arduino Cloud API credentials in a .env file:
        ```
        ARDUINO_CLIENT_ID=your_client_id
        ARDUINO_CLIENT_SECRET=your_client_secret
        ARDUINO_DEVICE_ID=your_device_id
        ```
        You can get these from the Arduino Cloud IoT API section.
        """)
        return
    
    # Initialize session state
    if 'token' not in st.session_state:
        st.session_state.token = None
    if 'connected' not in st.session_state:
        st.session_state.connected = False
    
    # Connection section
    if not st.session_state.connected:
        if st.button("Connect to Arduino"):
            token = get_arduino_token()
            if token:
                st.session_state.token = token
                st.session_state.connected = True
                st.success("Connected to Arduino Cloud!")
    
    # If connected, show controls and monitoring
    if st.session_state.connected:
        # Create columns for controls
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Refresh Data"):
                serial_data = get_serial_monitor(st.session_state.token)
                if serial_data:
                    st.text_area("Serial Monitor Output", serial_data.get("data", "No data available"), height=300)
        
        with col2:
            device_status = get_device_status(st.session_state.token)
            if device_status:
                st.metric("Device Status", device_status.get("status", "Unknown"))
                st.metric("Last Update", datetime.now().strftime("%H:%M:%S"))

if __name__ == "__main__":
    main()
