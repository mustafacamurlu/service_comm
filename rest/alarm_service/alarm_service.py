from flask import Flask, request, jsonify
import psycopg2
import os
from datetime import datetime

app = Flask(__name__)

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv('DB_NAME', 'alarmdb'),
        user=os.getenv('DB_USER', 'admin'),
        password=os.getenv('DB_PASSWORD', 'admin'),
        host=os.getenv('DB_HOST', 'localhost')
    )

# Create an alarm
@app.route('/add_alarm', methods=['POST'])
def add_alarm():
    data = request.get_json()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO alarms (rule_id, device_id, data_type, value, threshold_value, comparison_operator, timestamp, alarm_description)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (data['rule_id'], data['device_id'], data['data_type'], data['value'], data['threshold_value'], data['comparison_operator'], datetime.now(), data['alarm_description']))

        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "Alarm added successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Get all alarms or alarms by device_id
@app.route('/get_alarms', methods=['GET'])
def get_alarms():
    device_id = request.args.get('device_id')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if device_id:
            cursor.execute("SELECT * FROM alarms WHERE device_id = %s", (device_id,))
        else:
            cursor.execute("SELECT * FROM alarms")

        alarms = cursor.fetchall()
        alarms_list = []
        for alarm in alarms:
            alarms_list.append({
                "id": alarm[0],
                "rule_id": alarm[1],
                "device_id": alarm[2],
                "data_type": alarm[3],
                "value": alarm[4],
                "threshold_value": alarm[5],
                "comparison_operator": alarm[6],
                "timestamp": alarm[7].strftime('%Y-%m-%d %H:%M:%S'),
                "alarm_description": alarm[8]
            })

        cursor.close()
        conn.close()
        return jsonify(alarms_list), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Update an alarm by ID
@app.route('/update_alarm/<int:alarm_id>', methods=['PUT'])
def update_alarm(alarm_id):
    data = request.get_json()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE alarms
            SET rule_id = %s, device_id = %s, data_type = %s, value = %s, threshold_value = %s, comparison_operator = %s, timestamp = %s, alarm_description = %s
            WHERE id = %s
        """, (data['rule_id'], data['device_id'], data['data_type'], data['value'], data['threshold_value'], data['comparison_operator'], datetime.now(), data['alarm_description'], alarm_id))

        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "Alarm updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Delete an alarm by ID
@app.route('/delete_alarm/<int:alarm_id>', methods=['DELETE'])
def delete_alarm(alarm_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM alarms WHERE id = %s", (alarm_id,))

        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "Alarm deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
