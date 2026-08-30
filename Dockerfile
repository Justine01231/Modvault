FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# The image builds all three services; the command is chosen at runtime
# (docker-compose passes the entrypoint per service):
#   python -m app.main            (Telegram bot)
#   python -m app.webhook         (GitHub webhook server)
#   python -m app.dashboard.main  (web dashboard + API)

EXPOSE 8000 8080

CMD ["python", "-m", "app.main"]
