import json
import requests
import sys

# Define the data file and URL
data_file = "data.json"
url = "http://192.168.49.2:30081/onboard_data"

# Read the data from the JSON file
try:
    with open(data_file, 'r') as f:
        data = json.load(f)
except Exception as e:
    print(f"Error reading data file: {e}")
    sys.exit(1)

# Split the data into batches of 5 items
batches = [data[i:i + 5] for i in range(0, len(data), 5)]

# Loop through each batch and send a POST request
for batch in batches:
    try:
        response = requests.post(url, json=batch, headers={"Content-Type": "application/json"})
    except Exception as e:
        print(f"Error sending batch: {e}")

