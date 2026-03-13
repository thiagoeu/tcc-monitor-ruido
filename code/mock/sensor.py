import requests
import random
import time

while True:

    payload = {
        "sensor_id": "room1",
        "db": random.uniform(40, 90)
    }

    requests.post("http://api:3000/noise", json=payload)

    time.sleep(2)