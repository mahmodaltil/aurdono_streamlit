FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install chromium

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--config", "gunicorn_config.py", "--worker-class", "eventlet", "app:app"]
