FROM python:3.11-slim

WORKDIR /app

COPY src/server.py src/client.py ./

EXPOSE 8000

CMD ["python", "server.py", "./contents"]
