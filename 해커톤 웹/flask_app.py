from flask import Flask, render_template, jsonify, send_from_directory, url_for
import threading
import time
import os
import serial
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import geocoder
from datetime import datetime

app = Flask(__name__)
app.static_folder = 'static'

current_distance = 0
current_color = "red"
EMERGENCY_EMAIL = "quitev4@gmail.com"  
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "alswalsw00@gmail.com"  
SENDER_PASSWORD = "ajm0829^^"  

def get_current_location():
    try:
        g = geocoder.ip('me')
        if g.latlng:
            return {
                'latitude': g.latlng[0],
                'longitude': g.latlng[1],
                'address': g.address
            }
    except Exception as e:
        print(f"Location error: {e}")
    return None

def send_emergency_email(location_data):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = EMERGENCY_EMAIL
        msg['Subject'] = "EMERGENCY: Walking Stick Broken - Help Needed"

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if location_data:
            body = f"""
            EMERGENCY ALERT - Walking Stick Broken

            Time: {current_time}
            Location Information:
            - Latitude: {location_data['latitude']}
            - Longitude: {location_data['longitude']}
            - Address: {location_data['address']}

            Google Maps Link: https://www.google.com/maps?q={location_data['latitude']},{location_data['longitude']}

            Immediate assistance is required at this location.
            """
        else:
            body = f"""
            EMERGENCY ALERT - Walking Stick Broken

            Time: {current_time}
            Location Information: Unable to determine location

            Immediate assistance is required.
            """

        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)

        print("Emergency email sent successfully")
    except Exception as e:
        print(f"Email sending error: {e}")

def read_bluetooth():
    global current_distance, current_color
    try:
        ser = serial.Serial('/dev/tty.HC-06', 9600, timeout=1)
        while True:
            if ser.in_waiting:
                try:
                    data = ser.readline().decode().strip()
                    if data == "지팡이가 넘어졌어요.":  
                        location_data = get_current_location()
                        send_emergency_email(location_data)
                    elif data in ("red", "green", "other"):
                        current_color = data
                except Exception as e:
                    print(f"Bluetooth reading error: {e}")
            time.sleep(0.1)
    except Exception as e:
        print(f"Serial connection error: {e}")

@app.route('/')
def index():
    return render_template('index.html', distance=current_distance, color=current_color)

@app.route('/get_distance_and_color')
def get_distance_and_color():
    return jsonify({
        'distance': current_distance,
        'color': current_color,
        'audio_urls': {
            'distance_10': url_for('static', filename='distance_10.mp3'),
            'distance_20': url_for('static', filename='distance_20.mp3'),
            'distance_30': url_for('static', filename='distance_30.mp3'),
            'red_signal': url_for('static', filename='red_signal.mp3'),
            'green_signal': url_for('static', filename='green_signal.mp3'),
            'other_signal': url_for('static', filename='other_signal.mp3')
        }
    })

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

if __name__ == '__main__':
    os.makedirs(app.static_folder, exist_ok=True)
    bluetooth_thread = threading.Thread(target=read_bluetooth)
    bluetooth_thread.daemon = True
    bluetooth_thread.start()
    app.run(host='127.0.0.1', port=8100, debug=True)