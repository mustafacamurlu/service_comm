import json
import random
import sys
from datetime import datetime, timedelta

def generate_energy_data(device_id, start_timestamp, num_samples):
    data = []
    current_time = datetime.strptime(start_timestamp, '%Y-%m-%d %H:%M:%S')
    for _ in range(num_samples):
        energy_consumption = round(random.uniform(10.0, 60.0), 2)
        data.append({
            "device_id": device_id,
            "timestamp": current_time.strftime('%Y-%m-%d %H:%M:%S'),
            "data_type": "energy",
            "value": energy_consumption
        })
        current_time += timedelta(seconds=1)
    return data

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python generate_energy_data_script.py <device_id> <start_timestamp> <num_samples>")
        sys.exit(1)

    device_id = sys.argv[1]
    start_timestamp = sys.argv[2]
    num_samples = int(sys.argv[3])

    energy_data = generate_energy_data(device_id, start_timestamp, num_samples)

    with open('data.json', 'w') as f:
        json.dump(energy_data, f, indent=2)

    print("data.json created.")