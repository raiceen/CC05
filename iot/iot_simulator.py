import requests
import time
import random

API_URL = "http://raiceen.pythonanywhere.com/data"
# Add headers to POST request
headers = {
    'Content-Type': 'application/json',
    'X-API-Key': 'DEVICE_SECRET_123'
}

response = requests.post(API_URL, json=payload, headers=headers)
print("Starting IoT Simulator...")
print(f"Sending data to: {API_URL}")

while True:
    payload = {
        "device_id": "sensor-1",
        "temperature": round(random.uniform(18.0, 32.0), 1),
        "humidity": round(random.uniform(40.0, 80.0), 1)
    }

    try:
        response = requests.post(API_URL, json=payload)
        print(f"Status: {response.status_code}, Data: {payload}")
    except Exception as e:
        print(f"Error: {str(e)}")

    time.sleep(10)  # Send every 10 seconds for testing