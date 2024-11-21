FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt app.py ./
RUN pip install -r requirements.txt
EXPOSE 3000
CMD ["flask", "run", "--host=0.0.0.0", "--port=3000"]
