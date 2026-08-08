# Use official lightweight Python 3.12 image as base
FROM python:3.12-slim

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory inside the container
WORKDIR /workspace

# Install essential system dependencies (git, build tools for packages if required)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project specification, configuration, and source code files
COPY pyproject.toml README.md ./
COPY app/ ./app/

# Install project dependencies from the declared runtime metadata.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Expose port for FastAPI server / web dashboard
EXPOSE 8000

# Set default command to run the FastAPI application via python -m uvicorn
CMD ["python", "-m", "uvicorn", "app.api.app:app", "--host", "0.0.0.0", "--port", "8000"]