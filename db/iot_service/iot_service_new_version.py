from flask import Flask, request, jsonify
import psycopg2
from datetime import datetime
import os

app = Flask(__name__)

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv('DB_NAME', 'energydb'),
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

        if isinstance(data, list):
            for item in data:
                timestamp = datetime.strptime(item['timestamp'], '%Y-%m-%d %H:%M:%S')
                cursor.execute("INSERT INTO energy_data (device_id, timestamp, type, value) VALUES (%s, %s, %s, %s)",
                               (item['device_id'], timestamp, item['type'], item['value']))
                check_rules_and_create_alarms(cursor, item['device_id'], item['type'], item['value'])
        else:
            timestamp = datetime.strptime(data['timestamp'], '%Y-%m-%d %H:%M:%S')
            cursor.execute("INSERT INTO energy_data (device_id, timestamp, type, value) VALUES (%s, %s, %s, %s)",
                           (data['device_id'], timestamp, data['type'], data['value']))
            check_rules_and_create_alarms(cursor, data['device_id'], data['type'], data['value'])

        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "Energy data added successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400

def check_rules_and_create_alarms(cursor, device_id, type, value):
    try:
        # Fetch the applicable rules for this metric and device
        select_rules_query = """
            SELECT id, comparison_operator, threshold_value, rule_description, severity, consecutive_count
            FROM rules
            WHERE type = %s AND device_id = %s
        """
        cursor.execute(select_rules_query, (type, device_id))
        rules = cursor.fetchall()

        # Evaluate each rule
        for rule in rules:
            rule_id, comparison_operator, threshold_value, rule_description, severity, consecutive_count = rule
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

            # If the rule requires multiple consecutive instances to exceed the threshold
            if rule_triggered:
                # Fetch recent values from the database
                cursor.execute("""
                    SELECT value
                    FROM energy_data
                    WHERE type = %s AND device_id = %s
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (type, device_id, consecutive_count))
                recent_values = cursor.fetchall()

                # Count the number of consecutive values that exceed the threshold
                count = 0
                for recent_value in recent_values:
                    recent_value = recent_value[0]
                    if ((comparison_operator == '>' and float(recent_value) > threshold_value) or
                        (comparison_operator == '<' and float(recent_value) < threshold_value) or
                        (comparison_operator == '>=' and float(recent_value) >= threshold_value) or
                        (comparison_operator == '<=' and float(recent_value) <= threshold_value) or
                        (comparison_operator == '=' and float(recent_value) == threshold_value)):
                        count += 1
                    else:
                        break

                # If the number of consecutive values exceeds the required count, create an alarm
                if count >= consecutive_count:
                    insert_alarm_query = """
                        INSERT INTO alarms (rule_id, device_id, type, value, threshold_value, comparison_operator, timestamp, alarm_description)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    alarm_description = f"Alarm triggered: {rule_description} (Severity: {severity})"
                    cursor.execute(insert_alarm_query, (
                        rule_id, device_id, type, value, threshold_value, comparison_operator, datetime.now(), alarm_description
                    ))

    except Exception as error:
        print(f"Error checking rules or inserting alarm: {error}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
