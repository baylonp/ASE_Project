FROM python:3.12-slim

WORKDIR /app

COPY app.py .
COPY requirements.txt .

RUN pip3 install -r requirements.txt

EXPOSE 5000

CMD flask run --host=0.0.0.0 --port=5000 --cert=/run/secrets/admin_service_secrets_cert --key=/run/secrets/admin_service_secrets_key