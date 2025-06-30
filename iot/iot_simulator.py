import time
import random
import requests

# 1) Device credentials
DEVICE_ID = "simulator-001"

# 2) Endpoints
AUTH_URL = "https://raiceen.pythonanywhere.com/auth/device"
DATA_URL = "https://raiceen.pythonanywhere.com/data"

def get_token():
    """Authenticate our simulator and return a JWT."""
    resp = requests.post(AUTH_URL, json={"device_id": DEVICE_ID})
    resp.raise_for_status()
    token = resp.json().get("access_token")
    if not token:
        raise RuntimeError("No access_token in auth response")
    return token

def simulate_once(headers):
    """Generate random readings and POST them using the provided headers."""
    temperature = round(random.uniform(20.0, 30.0), 1)
    humidity    = round(random.uniform(40.0, 70.0), 1)
    payload = {
        "device_id": DEVICE_ID,
        "temperature": temperature,
        "humidity": humidity
    }

    resp = requests.post(DATA_URL, json=payload, headers=headers)
    print(f"Posted {payload} → {resp.status_code}", resp.text)

if __name__ == "__main__":
    # Fetch our JWT once
    token = get_token()
    headers = {
        "Content-Type": "application/json",
        "Authorization":  f"Bearer {token}"
    }

    # Send 10 readings, 5s apart
    for i in range(10):
        simulate_once(headers)
        time.sleep(5)
