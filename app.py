import os
import time
import threading
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from pixoo import Pixoo
from PIL import Image

# Load environment variables
load_dotenv()

# Configure Pixoo
pixoo_host = os.environ.get('PIXOO_HOST', '10.108.32.240')  # Replace with your Pixoo IP
pixoo = Pixoo(pixoo_host)

app = Flask(__name__)

# Get the base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Inventory data
inventory_data = {
    "pcs": 5,
    "floor": 500,
    "inv": 10
}

# Function to load pixel sprite from an image
def load_pixel_sprite(image_path):
    img = Image.open(image_path).convert("RGB")
    img = img.resize((10, 10))  # Ensure sprite is 10x10

    pixels = []
    for y in range(img.height):
        row = []
        for x in range(img.width):
            row.append(img.getpixel((x, y)))
        pixels.append(row)

    return pixels

# Load animation frames
frame_paths = [
    os.path.join(BASE_DIR, "static", "animations", "pixil-layer-0.png"),
    os.path.join(BASE_DIR, "static", "animations", "pixil-layer-1.png"),
    os.path.join(BASE_DIR, "static", "animations", "pixil-layer-2.png"),
    os.path.join(BASE_DIR, "static", "animations", "pixil-layer-3.png"),
]

# Check if files exist
for path in frame_paths:
    print(f"Checking: {path} - Exists: {os.path.exists(path)}")

animation_frames = [load_pixel_sprite(path) for path in frame_paths]

# Global flag to control animation loop
running_animation = True

def draw_static_ui():
    """ Draws the static UI on the Pixoo. """
    for y in range(64):
        for x in range(64):
            pixoo.draw_pixel_at_location_rgb(x, y, 255, 255, 255)  # White background

    pixoo.draw_text("PCS:", (15, 10), (0, 0, 0))
    pixoo.draw_text(f"{inventory_data['pcs']}", (50, 10), (0, 0, 0))

    pixoo.draw_text("FLOOR:", (15, 35), (0, 0, 0))
    pixoo.draw_text(f"{inventory_data['floor']}", (50, 35), (0, 0, 0))

    pixoo.draw_text("INV:", (15, 55), (0, 0, 0))
    pixoo.draw_text(f"{inventory_data['inv']}", (50, 55), (0, 0, 0))

    pixoo.push()  # Send to Pixoo

def animate_sprite():
    """ Continuously animates the sprite inside the first box without erasing UI. """
    sprite_x, sprite_y = 6, 6

    while running_animation:
        for frame in animation_frames:
            for y in range(10):
                for x in range(10):
                    pixoo.draw_pixel_at_location_rgb(sprite_x + x, sprite_y + y, 255, 255, 255)  # White background

            for y in range(len(frame)):
                for x in range(len(frame[y])):
                    r, g, b = frame[y][x]
                    pixoo.draw_pixel_at_location_rgb(sprite_x + x, sprite_y + y, r, g, b)

            pixoo.push()
            time.sleep(1)

# Start UI and Animation in separate threads
threading.Thread(target=draw_static_ui, daemon=True).start()
threading.Thread(target=animate_sprite, daemon=True).start()

@app.route('/')
def home():
    return 'Pixoo Inventory Dashboard'

@app.route('/inventory')
def inventory():
    return render_template('inventory.html', 
                           pcs=inventory_data["pcs"], 
                           floor=inventory_data["floor"], 
                           inv=inventory_data["inv"])

@app.route('/update')
def update_inventory():
    pcs = request.args.get("pcs", type=int)
    floor = request.args.get("floor", type=int)
    inv = request.args.get("inv", type=int)

    if pcs is not None:
        inventory_data["pcs"] = pcs
    if floor is not None:
        inventory_data["floor"] = floor
    if inv is not None:
        inventory_data["inv"] = inv

    draw_static_ui()  # Update Pixoo display after change

    return jsonify({"status": "success", "updated_inventory": inventory_data})

@app.route('/reset', methods=['POST'])
def reset_inventory():
    inventory_data["pcs"] = 0
    inventory_data["floor"] = 0
    inventory_data["inv"] = 0

    draw_static_ui()  # Update Pixoo display after reset

    return jsonify({"status": "success", "message": "Inventory reset to default values"})

if __name__ == '__main__':
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        running_animation = False  # Stop animation when exiting
