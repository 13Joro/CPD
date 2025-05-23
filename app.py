import os
import time
import threading
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from pixoo import Pixoo
from PIL import Image, ImageDraw, ImageFont

load_dotenv()

pixoo_host = os.getenv('PIXOO_HOST', '10.108.32.240')  # Replace with your Pixoo IP
pixoo = Pixoo(pixoo_host)

app = Flask(__name__)

time_running = False
time_thread = None

# Declare global variables for GIF processing
gif_running = False
gif_thread = None

def load_pixel_sprite(img):
    img = img.convert("RGB")
    img = img.resize((64, 64))
    pixels = [[img.getpixel((x, y)) for x in range(img.width)] for y in range(img.height)]
    return pixels

def clear_pixoo():
    global gif_running, gif_thread
    gif_running = False  # Stop any running GIF
    if gif_thread is not None:
        gif_thread.join()  # Wait for the GIF thread to finish

    img = Image.new('RGB', (64, 64), color=(128, 128, 128))  # Gray background for visibility
    draw = ImageDraw.Draw(img)

    # Ensure the existence of LOGO_PATH
    LOGO_PATH = os.path.join(os.getcwd(), "static", "cloudstaff_logo.png")
    if os.path.exists(LOGO_PATH):
        logo = Image.open(LOGO_PATH).convert("RGB").resize((32, 32))
        img.paste(logo, (16, 5))

    default_font = ImageFont.load_default()
    text = "No image"
    w, h = draw.textbbox((0, 0), text, font=default_font)[2:]
    draw.text(((64 - w) // 2, 40), text, font=default_font, fill=(255, 255, 255))

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
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Ensure BASE_DIR is defined
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

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Ensure BASE_DIR is defined
    file_path = os.path.join(BASE_DIR, "static", "uploaded", "uploaded_image.gif")
    file.save(file_path)
    
    frames = []
    with Image.open(file_path) as img:
        for frame_index in range(img.n_frames):
            img.seek(frame_index)
            frame_pixels = load_pixel_sprite(img)
            frames.append(frame_pixels)

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
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Ensure BASE_DIR is defined
    img_file_name = f"{employee_name.lower().replace(' ', '_')}.png"
    img_path = os.path.join(BASE_DIR, "static", "employees", img_file_name)

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

def update_time_in_real_time():
    global time_running
    while time_running:
        try:
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

            time.sleep(1)

        except Exception as e:
            print(f"Error updating real-time clock: {e}")

@app.route('/start_real_time_clock', methods=['POST'])
def start_real_time_clock():
    global time_running, time_thread
    if time_running:
        return jsonify({"status": "error", "message": "Real-time clock update already running."})

    time_running = True
    time_thread = threading.Thread(target=update_time_in_real_time)
    time_thread.start()
    return jsonify({"status": "success", "message": "Real-time clock update started."})

@app.route('/stop_real_time_clock', methods=['POST'])
def stop_real_time_clock():
    global time_running
    time_running = False
    if time_thread:
        time_thread.join()
    return jsonify({"status": "success", "message": "Real-time clock update stopped."})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)