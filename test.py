import requests
import time

while True:
    interface_data = requests.get('http://127.0.0.1:8000/detect_screen_interaction')

    print(interface_data.json())

    time.sleep(0.2)