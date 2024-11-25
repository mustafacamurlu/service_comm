FROM python:3.9-slim

RUN apt-get update && apt-get install -y gcc libpq-dev

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY rule_service.py .

EXPOSE 8080

CMD ["python", "rule_service.py"]
