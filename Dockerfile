FROM python:3.10-slim
WORKDIR /app
COPY . .
CMD ["uvicorn", "satquery.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
