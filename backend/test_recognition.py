"""
Test Recognition Endpoint
Quick test to see if face detection is working
"""
import requests
import base64
import cv2
import numpy as np

# Create a simple test image
print("Creating test image...")
test_image = np.zeros((480, 640, 3), dtype=np.uint8)
test_image[:] = (100, 100, 100)  # Gray background

# Encode to base64
_, buffer = cv2.imencode('.jpg', test_image)
img_base64 = base64.b64encode(buffer).decode('utf-8')
img_data_uri = f"data:image/jpeg;base64,{img_base64}"

# Send to recognition endpoint
print("Sending to /api/recognize endpoint...")
url = "http://localhost:5000/api/recognize"
payload = {"image": img_data_uri}

try:
    response = requests.post(url, json=payload, timeout=10)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {response.json()}")
except requests.exceptions.ConnectionError:
    print("ERROR: Could not connect to backend. Is it running on port 5000?")
except Exception as e:
    print(f"ERROR: {e}")
