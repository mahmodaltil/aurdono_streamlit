import streamlit as st

def main():
    st.title("Smart Entrance Control System")
    
    # Add header and description
    st.header("System Status")
    st.write("This is a monitoring interface for the Smart Entrance Control System.")
    
    # Create a placeholder for status
    status_container = st.empty()
    
    # Display system information
    st.subheader("System Information")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(label="Temperature", value="25°C")
        st.metric(label="Humidity", value="60%")
    
    with col2:
        st.metric(label="Door Status", value="Closed")
        st.metric(label="System Status", value="Online")
    
    # Add a section for recent activities
    st.subheader("Recent Activities")
    activities = [
        "Door opened by authorized user",
        "Temperature check: Normal",
        "System health check: Passed",
        "Door closed automatically"
    ]
    
    for activity in activities:
        st.text(activity)

if __name__ == "__main__":
    main()
