import psycopg2
import os
from datetime import datetime
import pika
import json
import sys

RABBITMQ_BROKER = os.getenv('RABBITMQ_BROKER', 'rabbitmq-service')
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS', 'guest')
QUEUE = os.getenv('QUEUE', 'data-stream')
DATA_CHANGE_QUEUE = os.getenv('DATA_CHANGE_QUEUE', 'data-change')

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv('DB_NAME', 'datadb'),
        user=os.getenv('DB_USER', 'admin'),
        password=os.getenv('DB_PASSWORD', 'admin'),
        host=os.getenv('DB_HOST', 'postgres-iot-service')
    )

def consume_from_rabbitmq():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_BROKER, credentials=credentials))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE)
    data_change_connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_BROKER, credentials=credentials))
    data_change_channel = data_change_connection.channel()
    data_change_channel.queue_declare(queue=DATA_CHANGE_QUEUE)

    def callback(ch, method, properties, body):
        data = json.loads(body)
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            for item in data:
                timestamp = datetime.strptime(item['timestamp'], '%Y-%m-%d %H:%M:%S')
                cursor.execute("INSERT INTO data (device_id, timestamp, data_type, value) VALUES (%s, %s, %s, %s)",
                               (item['device_id'], timestamp, item['data_type'], item['value']))

            # Publish the whole data to data-change queue
            data_change_channel.basic_publish(exchange='', routing_key=DATA_CHANGE_QUEUE, body=json.dumps(data))

            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Error processing message from RabbitMQ: {e}")
            sys.stdout.flush()

    channel.basic_consume(queue=QUEUE, on_message_callback=callback, auto_ack=True)
    print(f"Waiting for messages from RabbitMQ queue '{QUEUE}'...")
    sys.stdout.flush()
    channel.start_consuming()

if __name__ == '__main__':
    # Run the RabbitMQ consumer in the main thread
    consume_from_rabbitmq()
