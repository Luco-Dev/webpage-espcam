from flask import Flask, Response, render_template_string
import serial
import threading
import logging

app = Flask(__name__)

# Disable Werkzeug request logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Serial port configuration
serial_port = '/dev/ttyACM1'  # Update this to your serial port
baud_rate = 4000000

# Global variable to store the latest image
latest_image = None

import time

latest_image = None
image_counter = 0
last_time = time.time()

def read_serial():
    global latest_image, image_counter, last_time
    with serial.Serial(serial_port, baud_rate, timeout=1) as ser:
        while True:
            # Send the trigger character 'C' sasda
            ser.write(b'C')

            # Wait for the start bytes
            if ser.read(2) == b'\xA5\x5A':
                # Read the length of the image data
                len_bytes = ser.read(2)
                if len(len_bytes) == 2:
                    image_len = int.from_bytes(len_bytes, byteorder='little')
                    print(image_len)
                    # Read the image data
                    image_data = ser.read(image_len)
                    if len(image_data) == image_len:
                        # Save the image data to a file
                        with open('latest.jpg', 'wb') as f:
                            f.write(image_data)
                        latest_image = image_data
                        image_counter += 1

                        # Print statistics every 10 images
                        if image_counter % 100 == 0:
                            current_time = time.time()
                            elapsed_time = current_time - last_time
                            fps = 100 / elapsed_time
                            print(f"Images received: {image_counter}, FPS: {fps:.2f}")
                            last_time = current_time

@app.route('/')
def index():
    return render_template_string('''
        <html>
            <body>
                <img id="image" src="/image_feed" />
                <script>
                    setInterval(function() {
                        var img = document.getElementById('image');
                        img.src = '/image_feed?' + new Date().getTime();
                    }, 0.001); // Poll every 100 milliseconds
                </script>
            </body>
        </html>
    ''')

@app.route('/image_feed')
def image_feed():
    global latest_image
    if latest_image:
        return Response(latest_image, mimetype='image/jpeg')
    else:
        return Response(status=204)

if __name__ == '__main__':
    # Start the serial reading thread
    serial_thread = threading.Thread(target=read_serial)
    serial_thread.daemon = True
    serial_thread.start()

    # Start the Flask web server
    app.run(host='0.0.0.0', port=5000, debug=False)
