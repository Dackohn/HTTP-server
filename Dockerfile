FROM python:3.11-slim

WORKDIR /app

COPY src/ ./

EXPOSE 8000

CMD ["python", "Multithreaded_http_server.py", "./contents"]
