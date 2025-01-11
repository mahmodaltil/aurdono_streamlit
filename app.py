from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
from playwright.async_api import async_playwright
import asyncio
import threading
import time
import os
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
    logger.info('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')

async def setup_browser():
    """Initialize browser in headless mode"""
    try:
        logger.info("Starting Playwright and browser setup...")
        browser_context['playwright'] = await async_playwright().start()
        browser_context['browser'] = await browser_context['playwright'].chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-software-rasterizer',
                '--disable-setuid-sandbox'
            ]
        )
        browser_context['page'] = await browser_context['browser'].new_page()
        logger.info("Browser setup completed successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to setup browser: {str(e)}", exc_info=True)
        return False

async def connect_to_arduino():
    """Connect to Arduino Web Editor and setup device"""
    try:
        page = browser_context['page']
        logger.info("Connecting to Arduino Web Editor...")
        
        # Open Arduino login page
        await page.goto("https://app.arduino.cc/login", wait_until='networkidle')
        print("Opened Arduino login page.")
        await page.fill("input[name='email']", "bayan0mahmoud@gmail.com")  # أدخل البريد الإلكتروني
        await page.fill("input[name='password']", "0122333bm")  # أدخل كلمة المرور
        await page.click("button[type='submit']")  # اضغط على زر تسجيل الدخول
        await page.wait_for_navigation()  # انتظر حتى يتم الانتقال بعد تسجيل الدخول
        print("Logged in successfully.")

        # Navigate to Arduino Web Editor
        logger.debug("Navigating to Arduino Web Editor...")
        while True:
            try:
                print("Opening Arduino Web Editor...")
                await page.goto("https://app.arduino.cc/sketches", wait_until='networkidle')
                print("Successfully opened Arduino Web Editor.")
                print("Navigating to the specific Arduino sketch...")
                await page.goto("https://app.arduino.cc/sketches/9dde49f6-08e5-4bc5-8dab-33849adbb868?nav=Files", wait_until='networkidle')
                print("Navigated to the specific Arduino sketch.")
                print("All steps completed successfully.")
                break  # Exit loop on success
            except playwright._impl._errors.TargetClosedError:
                logger.error("Error: Connection to Arduino failed because the target page or browser was closed.")
                return False
            except Exception as e:
                logger.error(f"An unexpected error occurred: {e}")
                logger.info("Retrying connection...")
                await asyncio.sleep(5)  # Wait before retrying
        
        # Press the Monitor button
        await page.click("button._icon-button_1mzvx_160._play-pause-button_1akfd_177")
        print("Monitor button pressed.")
        await page.wait_for_navigation()  # انتظر حتى يتم تحميل صفحة المراقبة
        print("Switched to Serial Monitor.")

        # Wait for device selection button
        await page.wait_for_selector("._device-name_12ggg_205", timeout=30000)
        await page.click("._device-name_12ggg_205")
        print("Device selection button clicked.")

        # Search for ESP32 device
        search_input = await page.wait_for_selector("#react-aria1491380040-:r12:", timeout=30000)
        await search_input.type("DOIT ESP32 DEVKIT V1")
        await page.keyboard.press("Tab")
        await page.keyboard.press("Enter")
        print("ESP32 device selected.")

        # Open Serial Monitor
        await page.wait_for_selector("._open-serial-monitor-button_1y7x9_356", timeout=30000)
        await page.click("._open-serial-monitor-button_1y7x9_356")
        print("Serial Monitor opened.")

        # Set baud rate to 115200
        await page.wait_for_selector("._x-small_wmean_200", timeout=30000)
        await page.click("._x-small_wmean_200")
        await page.click('button:text("115200")')
        print("Baud rate set to 115200.")

        # Switch to Serial Monitor
        await page.goto("https://app.arduino.cc/sketches/monitor", wait_until='networkidle')
        print("Switched to Serial Monitor.")

        # Press the Run button
        await page.click("button._play-pause-button_1akfd_177")
        print("Run button pressed.")

        logger.info("Successfully connected to Arduino Web Editor")
        browser_context['connected'] = True
        return True
    except Exception as e:
        logger.error(f"Failed to connect to Arduino: {str(e)}", exc_info=True)
        return False

def parse_serial_data(data):
    """Parse serial data to extract fingerprint and user information"""
    try:
        if "Fingerprint ID:" in data:
            # Extract fingerprint ID
            fp_id = data.split("Fingerprint ID:")[1].strip().split()[0]
            return {
                'type': 'fingerprint_scan',
                'id': fp_id,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        elif "Enrolled fingerprint ID:" in data:
            # Extract enrolled fingerprint data
            fp_id = data.split("Enrolled fingerprint ID:")[1].strip().split()[0]
            return {
                'type': 'enrollment',
                'id': fp_id,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        elif "Total fingerprints:" in data:
            # Extract total fingerprints count
            count = data.split("Total fingerprints:")[1].strip().split()[0]
            return {
                'type':'status',
                'count': count,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        return {
            'type': 'raw',
            'data': data,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        logger.error(f"Error parsing serial data: {str(e)}")
        return {
            'type': 'error',
            'data': str(e),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

async def monitor_serial_output():
    """Monitor serial output in a separate thread"""
    while not browser_context['stop_monitor']:
        try:
            if browser_context['connected'] and browser_context['page']:
                logger.debug("Reading serial output...")
                output_element = await browser_context['page'].wait_for_selector(".serial-output", timeout=5000)
                new_output = await output_element.inner_text()
                
                if new_output!= browser_context['last_output']:
                    logger.debug(f"New serial output: {new_output}")
                    browser_context['last_output'] = new_output
                    parsed_data = parse_serial_data(new_output)
                    socketio.emit('serial_data', parsed_data)
        except Exception as e:
            logger.error(f"Error reading serial output: {str(e)}")
        
        await asyncio.sleep(1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/connect', methods=['POST'])
def connect():
    logger.info("Received connection request")
    if not browser_context['connected']:
        if asyncio.run(setup_browser()):
            if asyncio.run(connect_to_arduino()):
                # Start monitoring thread
                browser_context['stop_monitor'] = False
                asyncio.create_task(monitor_serial_output())  # use create_task instead of run
                logger.info("Connection successful")
                return jsonify({'success': True,'message': 'Connected successfully'})
            else:
                logger.error("Failed to connect to Arduino")
                return jsonify({'success': False,'message': 'Failed to connect to Arduino'})
        else:
            logger.error("Failed to setup browser")
            return jsonify({'success': False,'message': 'Failed to setup browser'})
    
    return jsonify({'success': False,'message': 'Already connected'})

@app.route('/disconnect', methods=['POST'])
def disconnect():
    try:
        logger.info("Received disconnect request")
        browser_context['stop_monitor'] = True
        browser_context['connected'] = False
        logger.info("Disconnected successfully")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Failed to disconnect: {str(e)}", exc_info=True)
        return jsonify({'success': False,'message': str(e)})

@app.route('/status')
def status():
    return jsonify({
        'connected': browser_context['connected'],
        'last_update': datetime.now().strftime("%H:%M:%S")
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)