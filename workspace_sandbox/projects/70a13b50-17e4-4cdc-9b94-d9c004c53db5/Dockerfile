# Container build configuration
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN pip install --no-cache-dir black isort

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]