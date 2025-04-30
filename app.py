import datetime
import os
import time
import threading
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from pixoo import Pixoo
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta


# Load environment variables
load_dotenv()

# Configure Pixoo
pixoo_host = os.getenv('PIXOO_HOST', '10.108.32.240')  # Replace with your Pixoo IP
pixoo = Pixoo(pixoo_host)

app = Flask(__name__)

# Get the base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ensure directories exist for uploaded images and employee pictures
os.makedirs(os.path.join(BASE_DIR, "static", "uploaded"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "static", "employees"), exist_ok=True)

# Path to the Cloudstaff logo
LOGO_PATH = os.path.join(BASE_DIR, "static", "cloudstaff_logo.png")

# Control variable for stopping GIF animation
gif_running = False
gif_thread = None

# Function to load pixel sprite from an image
def load_pixel_sprite(img):
    img = img.convert("RGB")
    img = img.resize((64, 64))
    pixels = []
    for y in range(img.height):
        row = []
        for x in range(img.width):
            row.append(img.getpixel((x, y)))
        pixels.append(row)

    return pixels

# Function to clear the Pixoo display with a logo and message
def clear_pixoo():
    global gif_running
    gif_running = False  # Stop any running GIF
    if gif_thread is not None:
        gif_thread.join()  # Wait for the GIF thread to finish

    img = Image.new('RGB', (64, 64), color=(128, 128, 128))  # Gray background for visibility
    draw = ImageDraw.Draw(img)

    # Load and place the Cloudstaff logo
    if os.path.exists(LOGO_PATH):
        logo = Image.open(LOGO_PATH).convert("RGB").resize((32, 32))
        img.paste(logo, (16, 5))

    # Use the default font for text
    default_font = ImageFont.load_default()
    text = "No image"

    # Calculate text size and placement
    w, h = draw.textbbox((0, 0), text, font=default_font)[2:]
    draw.text(((64 - w) // 2, 40), text, font=default_font, fill=(255, 255, 255))  # Position text below the logo

    # Send background image to Pixoo
    pixels = load_pixel_sprite(img)
    for y in range(len(pixels)):
        for x in range(len(pixels[y])):
            r, g, b = pixels[y][x]
            pixoo.draw_pixel_at_location_rgb(x, y, r, g, b)
    pixoo.push()

@app.route('/')
def home():
    return render_template('inventory.html')

@app.route('/clear_display', methods=['POST'])
def clear_display():
    clear_pixoo()
    return jsonify({"status": "success", "message": "Display cleared and ready for new images."})

def handle_image_upload(file, extension):
    uploaded_image_path = os.path.join(BASE_DIR, "static", "uploaded", f"uploaded_image.{extension}")
    file.save(uploaded_image_path)

    # Load and send the new image to Pixoo
    image_pixels = load_pixel_sprite(Image.open(uploaded_image_path))
    for y in range(len(image_pixels)):
        for x in range(len(image_pixels[y])):
            r, g, b = image_pixels[y][x]
            pixoo.draw_pixel_at_location_rgb(x, y, r, g, b)
    pixoo.push()

    return jsonify({"status": "success", "message": f"{extension.upper()} image uploaded and displayed"})

@app.route('/upload_image_png', methods=['POST'])
def upload_image_png():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"})

    file = request.files['file']
    clear_pixoo()  # Clear the display before updating
    
    file_extension = file.filename.split('.')[-1].lower()
    if file_extension not in ['png', 'jpg', 'jpeg']:
        return jsonify({"status": "error", "message": "Invalid image file type"})
    
    return handle_image_upload(file, file_extension)

def process_gif(file):
    global gif_running, gif_thread

    file_path = os.path.join(BASE_DIR, "static", "uploaded", "uploaded_image.gif")
    file.save(file_path)
    
    # Extract frames from GIF
    with Image.open(file_path) as img:
        frames = []
        for frame_index in range(img.n_frames):
            img.seek(frame_index)
            frame_pixels = load_pixel_sprite(img)
            frames.append(frame_pixels)

    # Function to display GIF animation
    def display_gif():
        global gif_running
        gif_running = True
        while gif_running:
            for frame in frames:
                if not gif_running:
                    return
                for y in range(len(frame)):
                    for x in range(len(frame[y])):
                        r, g, b = frame[y][x]
                        pixoo.draw_pixel_at_location_rgb(x, y, r, g, b)
                pixoo.push()
                time.sleep(0.1)

    # Start animation in a separate thread
    gif_thread = threading.Thread(target=display_gif)
    gif_thread.start()

    return jsonify({"status": "success", "message": "GIF uploaded and animated"})

@app.route('/upload_image_gif', methods=['POST'])
def upload_image_gif():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"})

    file = request.files['file']
    clear_pixoo()  # Clear the display before updating
    return process_gif(file)

@app.route('/view_profile', methods=['POST'])
def view_profile():
    employee_name = request.json.get('name')
    img_file_name = f"{employee_name.lower().replace(' ', '_')}.png"
    img_path = os.path.join(BASE_DIR, "static", "employees", img_file_name)

    # Debugging output
    print(f"Received request for employee: {employee_name}")
    print(f"Expected image path: {img_path}")

    if os.path.exists(img_path):
        print(f"Image found for {employee_name}, attempting to display.")
        load_and_display_image(img_path)
        return jsonify({"status": "success", "message": f"Displaying {employee_name}'s image on Pixoo."})
    else:
        print(f"Image not found for {employee_name}.")
        return jsonify({"status": "error", "message": f"Image for {employee_name} not found."})

def load_and_display_image(img_path):
    try:
        img = Image.open(img_path).convert("RGB")
        img = img.resize((64, 64))
        pixels = load_pixel_sprite(img)

        for y in range(len(pixels)):
            for x in range(len(pixels[y])):
                r, g, b = pixels[y][x]
                pixoo.draw_pixel_at_location_rgb(x, y, r, g, b)
        pixoo.push()
        print(f"Successfully pushed image to Pixoo device.")

    except Exception as e:
        print(f"Error displaying image: {e}")

@app.route('/display_time', methods=['POST'])
def display_time():
    display_time_on_pixoo()
    return jsonify({"status": "success", "message": "Time displayed on Pixoo."})

def display_time_on_pixoo():
    current_utc_time = datetime.utcnow()
    ph_time = current_utc_time + timedelta(hours=8)
    formatted_time = ph_time.strftime('%H:%M')

    img = Image.new('RGB', (64, 64), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    default_font = ImageFont.load_default()

    w, h = draw.textbbox((0, 0), formatted_time, font=default_font)[2:]
    draw.text(((64 - w) // 2, (64 - h) // 2), formatted_time, font=default_font, fill=(255, 255, 255))
    
    pixels = load_pixel_sprite(img)
    for y in range(len(pixels)):
        for x in range(len(pixels[y])):
            r, g, b = pixels[y][x]
            pixoo.draw_pixel_at_location_rgb(x, y, r, g, b)
    pixoo.push()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)