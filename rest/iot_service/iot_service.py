from flask import Flask, request, jsonify
import psycopg2
import os
from datetime import datetime
import requests

app = Flask(__name__)

RULE_SERVICE_URL = os.getenv('RULE_SERVICE_URL', 'http://localhost:8080/get_rules')
ALARM_SERVICE_URL = os.getenv('ALARM_SERVICE_URL', 'http://localhost:8080/add_alarm')

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv('DB_NAME', 'datadb'),
        user=os.getenv('DB_USER', 'admin'),
        password=os.getenv('DB_PASSWORD', 'admin'),
        host=os.getenv('DB_HOST', 'localhost')
    )

@app.route('/add_data', methods=['POST'])
def add_energy_data():
    data = request.get_json()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        for item in data:
            timestamp = datetime.strptime(item['timestamp'], '%Y-%m-%d %H:%M:%S')
            cursor.execute("INSERT INTO data (device_id, timestamp, data_type, value) VALUES (%s, %s, %s, %s)",
                            (item['device_id'], timestamp, item['data_type'], item['value']))
            check_rules_and_create_alarms(item['device_id'], item['data_type'], item['value'])

        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "Energy data added successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400

def check_rules_and_create_alarms(device_id, data_type, value):
    try:
        # Fetch the applicable rules for this metric and device from rule service
        response = requests.get(f"{RULE_SERVICE_URL}?device_id={device_id}")
        if response.status_code != 200:
            print(f"Error fetching rules: {response.status_code}")
            return

        rules = response.json()

        applicable_rules = [rule for rule in rules if rule['data_type'] == data_type]

        # Evaluate each rule
        for rule in applicable_rules:
            rule_id = rule['id']
            comparison_operator = rule['comparison_operator']
            threshold_value = float(rule['threshold_value'])
            rule_description = rule['rule_description']
            severity = rule['severity']

            rule_triggered = False

            # Determine if the rule is violated based on the comparison operator
            if comparison_operator == '>' and value > threshold_value:
                rule_triggered = True
            elif comparison_operator == '<' and value < threshold_value:
                rule_triggered = True
            elif comparison_operator == '>=' and value >= threshold_value:
                rule_triggered = True
            elif comparison_operator == '<=' and value <= threshold_value:
                rule_triggered = True
            elif comparison_operator == '=' and value == threshold_value:
                rule_triggered = True

            # Create an alarm via REST API if the rule is triggered
            if rule_triggered:
                alarm_data = {
                    "rule_id": rule_id,
                    "device_id": device_id,
                    "data_type": data_type,
                    "value": value,
                    "threshold_value": threshold_value,
                    "comparison_operator": comparison_operator,
                    "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "alarm_description": f"Alarm triggered: {rule_description} (Severity: {severity})"
                }

                response = requests.post(ALARM_SERVICE_URL, json=alarm_data)
                if response.status_code != 201:
                    print(f"Error creating alarm: {response.status_code} - {response.text}")

    except Exception as error:
        print(f"Error checking rules or inserting alarm: {error}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
