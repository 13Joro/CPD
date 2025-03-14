import os
import sys
import time
import threading
from dotenv import load_dotenv
from flask import Flask, request, redirect, url_for, render_template
from pixoo import Pixoo

import _helpers

load_dotenv()

pixoo_host = os.environ.get('PIXOO_HOST', 'Pixoo64')
pixoo_screen = int(os.environ.get('PIXOO_SCREEN_SIZE', 64))
pixoo_debug = _helpers.parse_bool_value(os.environ.get('PIXOO_DEBUG', 'false'))
pixoo_test_connection_retries = int(os.environ.get('PIXOO_TEST_CONNECTION_RETRIES', sys.maxsize))

for connection_test_count in range(pixoo_test_connection_retries + 1):
    if _helpers.try_to_request(f'http://{pixoo_host}/get'):
        break
    else:
        if connection_test_count == pixoo_test_connection_retries:
            sys.exit(f'Failed to connect to [{pixoo_host}]. Exiting.')
        else:
            time.sleep(30)

pixoo = Pixoo(pixoo_host, pixoo_screen, pixoo_debug)

app = Flask(__name__)

def update_pixoo_display():
    """Continuously updates the Divoom Pixoo64 display with real-time clock & inventory data."""
    while True:
        current_time = time.strftime("%H:%M:%S")  # Get current time in HH:MM:SS format

        # Clear previous screen (optional)
        pixoo.clear()

        # Draw Clock (Centered horizontally)
        pixoo.draw_text_at_location_rgb(
            current_time,  # Live time string
            16,  # X position (Centered for better alignment)
            5,   # Y position (Top)
            0, 255, 0  # Green color for time
        )

        # Draw Inventory Data (Below the Clock)
        pixoo.draw_text_at_location_rgb("UWIAN NA", 10, 20, 255, 255, 255)  # White text
        pixoo.draw_text_at_location_rgb("BOSS!!", 10, 35, 255, 255, 255) # White text
       

        pixoo.push()  # Update Pixoo screen
        time.sleep(1)  # Update every second

# Start the real-time clock thread
clock_thread = threading.Thread(target=update_pixoo_display, daemon=True)
clock_thread.start()

@app.route('/')
def home():
    return redirect(url_for('inventory'))

@app.route('/inventory')
def inventory():
    return render_template('inventory.html')

if __name__ == '__main__':
    app.run(
        debug=_helpers.parse_bool_value(os.environ.get('PIXOO_REST_DEBUG', 'false')),
        host=os.environ.get('PIXOO_REST_HOST', '127.0.0.1'),
        port=int(os.environ.get('PIXOO_REST_PORT', '5000'))
    )
