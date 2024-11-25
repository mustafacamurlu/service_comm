FROM python:3.9-slim

RUN apt-get update && apt-get install -y gcc libpq-dev

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY alarm_service.py .

# Install RabbitMQ client dependencies and requests library
RUN pip install pika requests

EXPOSE 8080

CMD ["python", "alarm_service.py"]
