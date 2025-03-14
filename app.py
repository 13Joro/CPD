import os
import sys
import time
import requests
import json
import base64

from dotenv import load_dotenv
from flask import Flask, request, redirect, url_for, render_template  # Import render_template
from flasgger import Swagger, swag_from
from pixoo import Channel, Pixoo
from PIL import Image

from swag import definitions
from swag import passthrough

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

pixoo = Pixoo(
    pixoo_host,
    pixoo_screen,
    pixoo_debug
)

app = Flask(__name__)
app.config['SWAGGER'] = _helpers.get_swagger_config()

swagger = Swagger(app, template=_helpers.get_additional_swagger_template())
definitions.create(swagger)

@app.route('/', methods=['GET'])
def home():
    return redirect(url_for('inventory'))  # Redirect to /inventory instead of /apidocs


@app.route('/health', methods=['GET'])
def health():
    return 'OK'

# Inventory route
@app.route('/inventory')
def inventory():
    # Flash the fixed values to the Divoom device
    pixoo.draw_text_at_location_rgb(
        "PCs: 20",  # Text for number of computers
        5,                             # X coordinate (adjust as needed)
        5,                             # Y coordinate (adjust as needed)
        255,                           # R value (for red color)
        255,                           # G value (for green color)
        255                            # B value (for blue color)
    )

    pixoo.draw_text_at_location_rgb(
        "Floor: 500",  # Text for total floor area
        5,                                       # X coordinate (adjust as needed)
        25,                                      # Y coordinate (adjust as needed)
        255,                                     # R value (for red color)
        255,                                     # G value (for green color)
        255                                      # B value (for blue color)
    )

    pixoo.draw_text_at_location_rgb(
        "Inv: 50",  # Text for total floor area
        5,                                       # X coordinate (adjust as needed)
        45,                                      # Y coordinate (adjust as needed)
        255,                                     # R value (for red color)
        255,                                     # G value (for green color)
        255                                      # B value (for blue color)
    )

    pixoo.push()  # Push the update to the Divoom device
    return render_template('inventory.html')

# ... (rest of your existing routes)

if __name__ == '__main__':
    app.run(
        debug=_helpers.parse_bool_value(os.environ.get('PIXOO_REST_DEBUG', 'false')),
        host=os.environ.get('PIXOO_REST_HOST', '127.0.0.1'),
        port=os.environ.get('PIXOO_REST_PORT', '5000')
    )