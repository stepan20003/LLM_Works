# Install psycopg2 in the correct environment
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

# Install psycopg2 in the current environment
RUN pip install psycopg2-binary

COPY . .

CMD ["python", "app/main.py"]