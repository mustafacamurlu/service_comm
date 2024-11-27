from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import psycopg2
import os
from datetime import datetime
from pydantic import BaseModel
import pika
import json
import threading
import requests
import sys

app = FastAPI()

RULE_SERVICE_URL = 'http://rule-service:8080/get_rules'

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv('DB_NAME', 'alarmdb'),
        user=os.getenv('DB_USER', 'admin'),
        password=os.getenv('DB_PASSWORD', 'admin'),
        host=os.getenv('DB_HOST', 'postgres-alarm-service')
    )

class Alarm(BaseModel):
    rule_id: int
    device_id: str
    data_type: str
    value: float
    threshold_value: float
    comparison_operator: str
    alarm_description: str

# Create an alarm
@app.post("/add_alarm")
async def add_alarm(alarm: Alarm):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO alarms (rule_id, device_id, data_type, value, threshold_value, comparison_operator, timestamp, alarm_description)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (alarm.rule_id, alarm.device_id, alarm.data_type, alarm.value, alarm.threshold_value, alarm.comparison_operator, datetime.now(), alarm.alarm_description))

        conn.commit()
        cursor.close()
        conn.close()
        return JSONResponse(content={"status": "Alarm added successfully"}, status_code=201)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Get all alarms or alarms by device_id
@app.get("/get_alarms")
async def get_alarms(device_id: str = None):
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
        return JSONResponse(content=alarms_list, status_code=200)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Update an alarm by ID
@app.put("/update_alarm/{alarm_id}")
async def update_alarm(alarm_id: int, alarm: Alarm):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE alarms
            SET rule_id = %s, device_id = %s, data_type = %s, value = %s, threshold_value = %s, comparison_operator = %s, timestamp = %s, alarm_description = %s
            WHERE id = %s
        """, (alarm.rule_id, alarm.device_id, alarm.data_type, alarm.value, alarm.threshold_value, alarm.comparison_operator, datetime.now(), alarm.alarm_description, alarm_id))

        conn.commit()
        cursor.close()
        conn.close()
        return JSONResponse(content={"status": "Alarm updated successfully"}, status_code=200)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Delete an alarm by ID
@app.delete("/delete_alarm/{alarm_id}")
async def delete_alarm(alarm_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM alarms WHERE id = %s", (alarm_id,))

        conn.commit()
        cursor.close()
        conn.close()
        return JSONResponse(content={"status": "Alarm deleted successfully"}, status_code=200)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Function to check rules and create alarms
def check_rules_and_create_alarms(device_id, data_type, value):
    try:
        print(f"Checking rules for device: {device_id}, data_type: {data_type}, value: {value}")
        sys.stdout.flush()
        # Fetch the applicable rules for this metric and device from rule service
        response = requests.get(f"{RULE_SERVICE_URL}?device_id={device_id}")
        if response.status_code != 200:
            print(f"Error fetching rules: {response.status_code}")
            sys.stdout.flush()
            return

        rules = response.json()

        applicable_rules = [rule for rule in rules if rule['data_type'] == data_type]

        print(f"Applicable rules: {applicable_rules}")
        sys.stdout.flush()

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

            # Insert alarm into the database if the rule is triggered
            if rule_triggered:
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()

                    cursor.execute("""
                        INSERT INTO alarms (rule_id, device_id, data_type, value, threshold_value, comparison_operator, timestamp, alarm_description)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (rule_id, device_id, data_type, value, threshold_value, comparison_operator, datetime.now(), f"Alarm triggered: {rule_description} (Severity: {severity})"))

                    conn.commit()
                    cursor.close()
                    conn.close()
                    print(f"Alarm added to database: {rule_description} (Severity: {severity})")

                except Exception as db_exception:
                    print(f"Error inserting alarm into database: {db_exception}")

    except Exception as e:
        print(f"Exception in check_rules_and_create_alarms: {e}")

# RabbitMQ Consumer
# RabbitMQ Consumer
def rabbitmq_consumer():
    def callback(ch, method, properties, body):
        try:
            data = json.loads(body)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        device_id = item.get('device_id')
                        data_type = item.get('data_type')
                        value = item.get('value')

                        if device_id and data_type and value is not None:
                            check_rules_and_create_alarms(device_id, data_type, value)
                        else:
                            print(f"Invalid data item received from RabbitMQ: {item}")
                    else:
                        print(f"Invalid list element, expected dict but got: {type(item).__name__}")
            else:
                print(f"Received message is not a list: {type(data).__name__}")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
        except Exception as e:
            print(f"Unexpected error in callback: {e}")

    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq-service'))
    channel = connection.channel()
    channel.queue_declare(queue='data-change')

    channel.basic_consume(queue='data-change', on_message_callback=callback, auto_ack=True)
    print('Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()


@app.on_event("startup")
def startup_event():
    threading.Thread(target=rabbitmq_consumer, daemon=True).start()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8080)
