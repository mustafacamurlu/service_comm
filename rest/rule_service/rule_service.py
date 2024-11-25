from flask import Flask, request, jsonify
import psycopg2
from datetime import datetime
import os

app = Flask(__name__)

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv('DB_NAME', 'rulesdb'),
        user=os.getenv('DB_USER', 'admin'),
        password=os.getenv('DB_PASSWORD', 'admin'),
        host=os.getenv('DB_HOST', 'localhost')
    )

@app.route('/add_rule', methods=['POST'])
def add_rule():
    data = request.get_json()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO rules (device_id, data_type, comparison_operator, threshold_value, rule_description, severity, consecutive_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (data['device_id'], data['data_type'], data['comparison_operator'], data['threshold_value'], data['rule_description'], data['severity'], data['consecutive_count']))

        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "Rule added successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/remove_rule/<int:rule_id>', methods=['DELETE'])
def remove_rule(rule_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM rules WHERE id = %s", (rule_id,))

        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "Rule removed successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/update_rule/<int:rule_id>', methods=['PUT'])
def update_rule(rule_id):
    data = request.get_json()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE rules
            SET device_id = %s, data_type = %s, comparison_operator = %s, threshold_value = %s, rule_description = %s, severity = %s, consecutive_count = %s
            WHERE id = %s
        """, (data['device_id'], data['data_type'], data['comparison_operator'], data['threshold_value'], data['rule_description'], data['severity'], data['consecutive_count'], rule_id))

        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "Rule updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/get_rules', methods=['GET'])
def get_rules():
    device_id = request.args.get('device_id')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if device_id:
            cursor.execute("SELECT * FROM rules WHERE device_id = %s", (device_id,))
        else:
            cursor.execute("SELECT * FROM rules")

        rules = cursor.fetchall()

        rules_list = []
        for rule in rules:
            rules_list.append({
                "id": rule[0],
                "device_id": rule[1],
                "data_type": rule[2],
                "comparison_operator": rule[3],
                "threshold_value": rule[4],
                "rule_description": rule[5],
                "severity": rule[6],
                "consecutive_count": rule[7]
            })

        cursor.close()
        conn.close()
        return jsonify(rules_list), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
