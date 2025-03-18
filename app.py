import os
import sys
import time
import threading
import csv
from dotenv import load_dotenv
from flask import Flask, request, redirect, url_for, render_template, jsonify
from pixoo import Pixoo

import _helpers

load_dotenv()

pixoo_host = os.environ.get('PIXOO_HOST', 'Pixoo64')
pixoo_screen = int(os.environ.get('PIXOO_SCREEN_SIZE', 64))
pixoo_debug = _helpers.parse_bool_value(os.environ.get('PIXOO_DEBUG', 'false'))
pixoo_test_connection_retries = int(os.environ.get('PIXOO_TEST_CONNECTION_RETRIES', sys.maxsize))

print(f"[DEBUG] Attempting to connect to Pixoo at {pixoo_host}")

for connection_test_count in range(pixoo_test_connection_retries + 1):
    if _helpers.try_to_request(f'http://{pixoo_host}/get'):
        print(f"[DEBUG] Connection successful on attempt {connection_test_count + 1}")
        break
    else:
        print(f"[ERROR] Connection attempt {connection_test_count + 1} failed. Retrying...")
        if connection_test_count == pixoo_test_connection_retries:
            sys.exit(f"[FATAL] Failed to connect to [{pixoo_host}]. Exiting.")
        time.sleep(5)  # Reduced retry wait time for quicker debugging

pixoo = Pixoo(pixoo_host, pixoo_screen, pixoo_debug)

app = Flask(__name__)

INVENTORY_FILE = "inventory.csv"

def initialize_inventory():
    """Ensure the inventory file exists with default values."""
    if not os.path.exists(INVENTORY_FILE):
        with open(INVENTORY_FILE, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["PCs", "Floor", "Inv"])  # Headers
            writer.writerow([0, 0, 0])  # Default values

def read_inventory():
    """Read inventory values from CSV."""
    with open(INVENTORY_FILE, "r") as file:
        reader = csv.reader(file)
        next(reader)  # Skip headers
        return list(map(int, next(reader)))  # Convert values to integers

def update_inventory(pcs=None, floor=None, inv=None):
    """Update inventory values in CSV."""
    data = read_inventory()
    if pcs is not None:
        data[0] = max(0, pcs)  # Ensure non-negative PCs
    if floor is not None:
        data[1] = max(0, floor)  # Ensure non-negative Floor
    if inv is not None:
        data[2] = max(0, inv)  # Ensure non-negative Inv
    
    with open(INVENTORY_FILE, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["PCs", "Floor", "Inv"])  # Headers
        writer.writerow(data)

def update_pixoo_display():
    """Continuously updates the Divoom Pixoo64 display with real-time clock & inventory data."""
    while True:
        try:
            current_time = time.strftime("%H:%M:%S")  # Get current time in HH:MM:SS format
            pcs, floor, inv = read_inventory()  # Read inventory data

            print(f"[DEBUG] Updating Pixoo display with time: {current_time}, PCs: {pcs}, Floor: {floor}, Inv: {inv}")

            # Clear previous screen (optional)
            pixoo.clear()

            # Draw Clock (Centered horizontally)
            pixoo.draw_text_at_location_rgb(current_time, 16, 5, 0, 255, 0)  # Green for time

            # Draw Inventory Data
            pixoo.draw_text_at_location_rgb("---------------------------------------------", 0, 10, 255, 255, 255)
            pixoo.draw_text_at_location_rgb(f"PCs: {pcs}", 10, 15, 255, 255, 255)
            pixoo.draw_text_at_location_rgb("---------------------------------------------", 0, 20, 255, 255, 255)
            pixoo.draw_text_at_location_rgb(f"Floor: {floor}", 10, 25, 255, 255, 255)
            pixoo.draw_text_at_location_rgb("---------------------------------------------", 0, 30, 255, 255, 255)
            pixoo.draw_text_at_location_rgb(f"Inv: {inv}", 10, 35, 255, 255, 255)
            pixoo.draw_text_at_location_rgb("---------------------------------------------", 0, 40, 255, 255, 255)

            pixoo.push()  # Update Pixoo screen
            time.sleep(1)  # Update every second
        
        except Exception as e:
            print(f"[ERROR] Failed to update Pixoo display: {e}")

# Start the real-time clock thread
clock_thread = threading.Thread(target=update_pixoo_display, daemon=True)
clock_thread.start()

@app.route('/')
def home():
    return redirect(url_for('inventory'))

@app.route('/inventory')
def inventory():
    pcs, floor, inv = read_inventory()
    return render_template('inventory.html', pcs=pcs, floor=floor, inv=inv)

@app.route('/update', methods=['GET'])
def update():
    try:
        pcs = request.args.get("pcs", type=int)
        floor = request.args.get("floor", type=int)
        inv = request.args.get("inv", type=int)

        update_inventory(pcs=pcs, floor=floor, inv=inv)

        return jsonify({
            "status": "success",
            "message": f"Updated inventory - PCs: {pcs}, Floor: {floor}, Inv: {inv}"
        }), 200

    except ValueError:
        return jsonify({"status": "error", "message": "Invalid input"}), 400

if __name__ == '__main__':
    initialize_inventory()
    print("[DEBUG] Starting Flask server...")
    app.run(
        debug=_helpers.parse_bool_value(os.environ.get('PIXOO_REST_DEBUG', 'false')),
        host=os.environ.get('PIXOO_REST_HOST', '127.0.0.1'),
        port=int(os.environ.get('PIXOO_REST_PORT', '5000'))
    )
