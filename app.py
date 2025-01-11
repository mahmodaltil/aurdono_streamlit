from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
from playwright.sync_api import sync_playwright
import threading
import time
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key')
socketio = SocketIO(app, 
    cors_allowed_origins="*",
    async_mode='eventlet',
    ping_timeout=60,
    ping_interval=25,
    manage_session=False
)

# Global variables for browser state
browser_context = {
    'playwright': None,
    'browser': None,
    'page': None,
    'connected': False,
    'last_output': '',
    'monitor_thread': None,
    'stop_monitor': False
}

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

def setup_browser():
    """Initialize browser in headless mode"""
    try:
        browser_context['playwright'] = sync_playwright().start()
        browser_context['browser'] = browser_context['playwright'].chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        browser_context['page'] = browser_context['browser'].new_page()
        return True
    except Exception as e:
        print(f"Failed to setup browser: {str(e)}")
        return False

def connect_to_arduino():
    """Connect to Arduino Web Editor and setup device"""
    try:
        page = browser_context['page']
        
        # Navigate to Arduino Web Editor
        page.goto("https://app.arduino.cc/sketches")
        
        # Wait for device selection button
        page.wait_for_selector("._device-name_12ggg_205")
        page.click("._device-name_12ggg_205")
        
        # Search for ESP32 device
        search_input = page.wait_for_selector("#react-aria6138362191-:r10:")
        search_input.type("DOIT ESP32 DEVKIT V1")
        page.keyboard.press("Tab")
        page.keyboard.press("Enter")
        
        # Open Serial Monitor
        page.wait_for_selector("._open-serial-monitor-button_1y7x9_356")
        page.click("._open-serial-monitor-button_1y7x9_356")
        
        # Switch to Serial Monitor
        page.goto("https://app.arduino.cc/sketches/monitor")
        
        # Set baud rate to 115200
        page.wait_for_selector("._x-small_wmean_200")
        page.click("._x-small_wmean_200")
        page.click('button:text("115200")')
        
        browser_context['connected'] = True
        return True
    except Exception as e:
        print(f"Failed to connect to Arduino: {str(e)}")
        return False

def monitor_serial_output():
    """Monitor serial output in a separate thread"""
    while not browser_context['stop_monitor']:
        try:
            if browser_context['connected'] and browser_context['page']:
                output_element = browser_context['page'].wait_for_selector(".serial-output")
                new_output = output_element.inner_text()
                
                if new_output != browser_context['last_output']:
                    browser_context['last_output'] = new_output
                    socketio.emit('serial_data', {'data': new_output})
        except Exception as e:
            print(f"Error reading serial output: {str(e)}")
        
        time.sleep(1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/connect', methods=['POST'])
def connect():
    if not browser_context['connected']:
        if setup_browser() and connect_to_arduino():
            # Start monitoring thread
            browser_context['stop_monitor'] = False
            browser_context['monitor_thread'] = threading.Thread(target=monitor_serial_output)
            browser_context['monitor_thread'].start()
            return jsonify({'success': True, 'message': 'Connected successfully'})
    
    return jsonify({'success': False, 'message': 'Failed to connect'})

@app.route('/disconnect', methods=['POST'])
def disconnect():
    try:
        browser_context['stop_monitor'] = True
        if browser_context['monitor_thread']:
            browser_context['monitor_thread'].join()
        
        if browser_context['page']:
            browser_context['page'].close()
        if browser_context['browser']:
            browser_context['browser'].close()
        if browser_context['playwright']:
            browser_context['playwright'].stop()
        
        browser_context['connected'] = False
        browser_context['last_output'] = ''
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/status')
def status():
    return jsonify({
        'connected': browser_context['connected'],
        'last_update': datetime.now().strftime("%H:%M:%S")
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
