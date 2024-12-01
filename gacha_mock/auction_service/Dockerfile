FROM python:3.12-slim

WORKDIR /app

COPY mock_app.py .
COPY requirements.txt .

RUN pip3 install -r requirements.txt

EXPOSE 5004

CMD flask run --host=0.0.0.0 --port=5004
