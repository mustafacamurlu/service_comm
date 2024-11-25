from flask import Flask, request, jsonify
import os
import pika
import json
import sys

app = Flask(__name__)

# Environment variables and URLs
RABBITMQ_BROKER = os.getenv('RABBITMQ_BROKER', 'rabbitmq-service')
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS', 'guest')
QUEUE = 'data-stream'

# Set up credentials for RabbitMQ
credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)

# Function to create a RabbitMQ connection and channel
def create_rabbitmq_channel():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_BROKER, credentials=credentials))
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE)
        return connection, channel
    except Exception as e:
        print(f"Error creating RabbitMQ connection: {e}")
        sys.stdout.flush()
        return None, None

# Establish initial connection and channel
connection, channel = create_rabbitmq_channel()

# Endpoint to add energy data
@app.route('/onboard_data', methods=['POST'])
def add_energy_data():
    data = request.get_json()
    try:
        # Publish to RabbitMQ
        publish_to_rabbitmq(data)
        return jsonify({"status": "Data added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Function to publish data to RabbitMQ
def publish_to_rabbitmq(data):
    global connection, channel
    try:
        if channel is None or channel.is_closed:
            connection, channel = create_rabbitmq_channel()

        if channel:
            message = json.dumps(data)
            channel.basic_publish(exchange='', routing_key=QUEUE, body=message)
            sys.stdout.flush()
        else:
            raise Exception("Failed to connect to RabbitMQ")
    except Exception as e:
        print(f"Error publishing to RabbitMQ: {e}")
        sys.stdout.flush()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
