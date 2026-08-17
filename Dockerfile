FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# APP_SECRET_KEY must be passed at runtime, e.g.:
#   docker run -e APP_SECRET_KEY=$(openssl rand -hex 32) -p 8000:8000 -v $(pwd)/data:/app/data bulk-resume-api
ENV DATA_DIR=/app/data
VOLUME ["/app/data"]

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
