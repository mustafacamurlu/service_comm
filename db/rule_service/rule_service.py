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

@app.route('/add_rule', methods=['POST'])
def add_rule():
    data = request.get_json()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO rules (type, comparison_operator, threshold_value, rule_description, device_id, severity)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (data['type'], data['comparison_operator'], data['threshold_value'], data['rule_description'], data['device_id'], data['severity']))

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
            SET type = %s, comparison_operator = %s, threshold_value = %s, rule_description = %s, device_id = %s, severity = %s
            WHERE id = %s
        """, (data['type'], data['comparison_operator'], data['threshold_value'], data['rule_description'], data['device_id'], data['severity'], rule_id))

        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "Rule updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/get_rules', methods=['GET'])
def get_rules():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM rules")
        rules = cursor.fetchall()

        rules_list = []
        for rule in rules:
            rules_list.append({
                "id": rule[0],
                "type": rule[1],
                "comparison_operator": rule[2],
                "threshold_value": rule[3],
                "rule_description": rule[4],
                "device_id": rule[5],
                "severity": rule[6]
            })

        cursor.close()
        conn.close()
        return jsonify(rules_list), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
